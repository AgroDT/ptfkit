"""Source-derived Cosby parameters, dry support and verified class coordinates."""

import copy
import math

import pytest
from ptfkit import get_manifest

from ptfkit_eval import (
    ModelEvaluationError,
    FunctionCurveCandidate,
    RunInputTrace,
    bind_retention_inputs,
    evaluate_candidate,
    evaluate_cosby1984_dry_h_theta,
    load_evaluation_plan,
)
from ptfkit_eval.documents import object_mapping, object_records, plain


def _function() -> dict:
    return dict(
        next(
            f
            for f in object_records(get_manifest()['functions'])
            if f['id'] == 'calc_ptf_cosby1984_univariate'
        )
    )


def _sample() -> dict:
    features: list[dict] = [
        {
            'id': 'texture',
            'kind': 'categorical',
            'value': 'sand',
            'origin': 'measured',
            'review_status': 'confirmed',
            'category_system': 'clapp1978.UsdaTextureClass',
            'source_cells': ['HYBRAS!L4'],
        }
    ]
    # Published Table 2 sand coordinates, not measured sample percentages.
    for component, value in [('sand', 92), ('silt', 5), ('clay', 3)]:
        binding = next(b for b in object_records(_function()['inputs']) if b['name'] == component)
        descriptor = object_mapping(binding['measurement'])
        features.append(
            {
                'id': component,
                'kind': 'numeric',
                'value': value,
                'origin': 'derived',
                'review_status': 'confirmed',
                'source_cells': [f'Cosby1984:Table2:{component}'],
                'measurement': plain(
                    {
                        k: descriptor[k]
                        for k in (
                            'quantity',
                            'unit',
                            'basis',
                            'method',
                            'particle_size',
                            'conditions',
                        )
                    }
                ),
                'derivation': {
                    'method': 'cosby1984_table2_class_midpoint_v1',
                    'source_feature': 'texture',
                },
            }
        )
    for feature in features[1:]:
        feature['measurement']['conditions'] = ()
    return {'features': features}


def _traces(sample: dict, function: dict | None = None) -> tuple[RunInputTrace, ...]:
    return bind_retention_inputs(
        _function() if function is None else function,
        sample,
        {'sand': 'sand', 'silt': 'silt', 'clay': 'clay'},
        manifest=get_manifest(),
    )


def test_verified_class_coordinates_bind_without_claiming_measured_texture():
    sample = _sample()
    traces = _traces(sample)
    assert [trace.value for trace in traces] == [92, 5, 3]
    assert all(trace.reasons == () for trace in traces)
    assert all(f['origin'] == 'derived' for f in sample['features'][1:])
    outputs = object_records(_function()['outputs'])
    assert all(
        object_mapping(o['measurement'])['role'] == 'uncertainty'
        for o in outputs
        if str(o['name']).startswith('sd_')
    )


@pytest.mark.parametrize(
    'change',
    [
        'wrong_value',
        'wrong_class',
        'blocked_class',
        'estimated_class',
        'wrong_system',
        'missing_reference',
        'measured_midpoint',
        'wrong_unit',
        'mixed_class_references',
        'unknown_function',
    ],
)
def test_derived_predictors_require_the_registered_source_specific_proof(change: str):
    sample = _sample()
    function = _function()
    source, sand = sample['features'][:2]
    if change == 'wrong_value':
        sand['value'] = math.nextafter(92, math.inf)
    elif change == 'wrong_class':
        source['value'] = 'clay'
    elif change == 'blocked_class':
        source['review_status'] = 'blocked'
    elif change == 'estimated_class':
        source['origin'] = 'estimated'
    elif change == 'wrong_system':
        source['category_system'] = 'unreviewed_classes'
    elif change == 'missing_reference':
        sand.pop('derivation')
    elif change == 'measured_midpoint':
        sand['origin'] = 'measured'
    elif change == 'wrong_unit':
        sand['measurement']['unit'] = 'mass_fraction'
        sand['value'] = 0.92
    elif change == 'mixed_class_references':
        sample['features'].append({**copy.deepcopy(source), 'id': 'another_texture'})
        sand['derivation']['source_feature'] = 'another_texture'
    else:
        function['id'] = 'unreviewed_function'
    assert all('unverified_derivation' in t.reasons for t in _traces(sample, function))


def test_dry_adapter_inverts_base_ten_reference_head_without_a_wet_plateau():
    parameters = {'mean_b': 2, 'mean_log_psi_s': 2, 'mean_theta_s': 0.5}
    assert evaluate_cosby1984_dry_h_theta(parameters, 100) == 0.5
    assert evaluate_cosby1984_dry_h_theta(parameters, 400) == pytest.approx(0.25)
    with pytest.raises(ModelEvaluationError, match='no registered wet branch'):
        evaluate_cosby1984_dry_h_theta(parameters, math.nextafter(100, 0))


def test_native_midpoint_adapter_converts_volume_percent_and_pressure_units():
    plan = load_evaluation_plan(
        {
            'schema_version': 1,
            'ptfkit_manifest_schema_version': 1,
            'candidates': [
                {
                    'id': 'cosby',
                    'kind': 'function_curve',
                    'function': 'calc_ptf_cosby1984_univariate',
                    'axis': {
                        'quantity': 'matric_potential',
                        'unit': 'kilopascal',
                        'convention': 'magnitude',
                        'transform': 'log10',
                    },
                    'target': {
                        'quantity': 'volumetric_water_content',
                        'unit': 'volume_fraction',
                        'material_basis': 'mineral_soil',
                        'denominator_basis': 'bulk_volume',
                    },
                    'prediction': {
                        'kind': 'model_adapter',
                        'id': 'cosby1984_class_midpoint_dry_h_theta',
                    },
                }
            ],
        }
    )
    candidate = plan.candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    curve = evaluate_candidate(candidate, [9.80665], {'sand': 92, 'silt': 5, 'clay': 3})
    # Source Table 5, with Table 2 sand midpoint, evaluated at 100 cm head.
    b = 2.91 + 0.159 * 3
    head = 10 ** (1.88 - 0.0131 * 92)
    theta = (48.9 - 0.126 * 92) / 100
    assert curve.points[0].value == pytest.approx(theta * (100 / head) ** (-1 / b))
    with pytest.raises(ModelEvaluationError, match='complete Table 2 class midpoint'):
        evaluate_candidate(candidate, [9.80665], {'sand': 50, 'silt': 30, 'clay': 20})
