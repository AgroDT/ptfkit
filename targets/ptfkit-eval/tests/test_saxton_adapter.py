import copy
import json
import math

import pytest
from ptfkit import get_manifest

from ptfkit_eval import (
    FunctionCurveCandidate,
    ModelEvaluationError,
    PlanValidationError,
    evaluate_candidate,
    evaluate_saxton2006_h_theta,
    load_evaluation_plan,
)
from ptfkit_eval.documents import canonical_json


def _plan() -> dict:
    return {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'saxton',
                'kind': 'function_curve',
                'function': 'calc_ptf_saxton2006',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'log10',
                },
                'target': {
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                    'material_basis': 'fine_earth',
                    'denominator_basis': 'bulk_volume',
                },
                'prediction': {'kind': 'model_adapter', 'id': 'saxton2006_h_theta'},
            }
        ],
    }


def test_saxton_curve_uses_all_three_source_segments():
    # theta_s=0.5 from rho_N=1.325, theta_33=0.25 from A=33*0.25^2.
    parameters = {
        'normal_density': 1.325,
        'air_entry_tension': 1,
        'retention_a': 2.0625,
        'retention_b': 2,
    }
    for pressure, expected in [(0, 0.5), (1, 0.5), (17, 0.375), (33, 0.25), (132, 0.125)]:
        assert evaluate_saxton2006_h_theta(parameters, pressure) == pytest.approx(expected)
    assert evaluate_saxton2006_h_theta(parameters, 1500) == pytest.approx(math.sqrt(0.001375))
    with pytest.raises(ModelEvaluationError, match='0 to 1500'):
        evaluate_saxton2006_h_theta(parameters, math.nextafter(1500, math.inf))


def test_native_saxton_manifest_curve_matches_source_table_3_and_endpoints():
    candidate = load_evaluation_plan(_plan()).candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    # Source Table 3 sand: 88% sand, 5% clay and 2.5% OM.
    points = evaluate_candidate(
        candidate, [0, 33, 1500], {'sand': 0.88, 'clay': 0.05, 'organic_matter': 2.5}
    ).points
    assert [point.value for point in points] == pytest.approx([0.46, 0.10, 0.05], abs=0.005)
    manifest = json.loads(canonical_json(get_manifest()))
    outputs = next(f for f in manifest['functions'] if f['id'] == 'calc_ptf_saxton2006')['outputs']
    fields = {field['name']: field['measurement'] for field in outputs}
    assert fields['theta_s']['conditions'][0]['value'] == 0
    assert fields['theta_33']['conditions'][0]['value'] == 33
    assert fields['theta_1500']['conditions'][0]['value'] == 1500
    assert fields['plant_available_water']['conditions'] == []


@pytest.mark.parametrize(
    'parameters',
    [
        {'normal_density': 2.65},
        {'normal_density': 0.53},
        {'air_entry_tension': -1},
        {'air_entry_tension': 0},
        {'air_entry_tension': 33},
        {'retention_a': 0},
        {'retention_b': 0},
    ],
)
def test_saxton_rejects_nonphysical_curve_parameters(parameters: dict):
    values = {
        'normal_density': 1.325,
        'air_entry_tension': 1,
        'retention_a': 2.0625,
        'retention_b': 2,
    }
    # rho_N=0.53 would itself be physical; make theta_33=0.9 exceed its theta_s=0.8.
    if parameters.get('normal_density') == 0.53:
        parameters = {**parameters, 'retention_a': 33 * 0.9**2}
    with pytest.raises(ModelEvaluationError):
        evaluate_saxton2006_h_theta({**values, **parameters}, 10)


def test_saxton_does_not_reuse_unreviewed_identically_shaped_functions():
    manifest = json.loads(canonical_json(get_manifest()))
    function = copy.deepcopy(
        next(f for f in manifest['functions'] if f['id'] == 'calc_ptf_saxton2006')
    )
    function['id'] = 'unreviewed_saxton_clone'
    manifest['functions'].append(function)
    plan = _plan()
    plan['candidates'][0]['function'] = function['id']
    with pytest.raises(PlanValidationError) as caught:
        load_evaluation_plan(plan, manifest=manifest)
    assert 'adapter.function_unsupported' in {d.code for d in caught.value.diagnostics}


def test_saxton_native_bad_air_entry_remains_an_execution_failure():
    candidate = load_evaluation_plan(_plan()).candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    with pytest.raises(ModelEvaluationError, match='nonphysical'):
        evaluate_candidate(candidate, [10], {'sand': 0.04, 'clay': 0.582, 'organic_matter': 7.24})


@pytest.mark.parametrize(
    'inputs',
    [
        {'sand': 0.8, 'clay': 0.4, 'organic_matter': 2.5},
        {'sand': 0.1, 'clay': math.nextafter(0.6, math.inf), 'organic_matter': 2.5},
        {'sand': 0.88, 'clay': 0.05, 'organic_matter': math.nextafter(8, math.inf)},
        {'sand': True, 'clay': 0, 'organic_matter': 2.5},
        {'sand': float('nan'), 'clay': 0.05, 'organic_matter': 2.5},
    ],
)
def test_saxton_adapter_rejects_invalid_input_domain_before_native_evaluation(inputs: dict):
    candidate = load_evaluation_plan(_plan()).candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    with pytest.raises(ModelEvaluationError, match='Saxton inputs'):
        evaluate_candidate(candidate, [33], inputs)


def test_saxton_fixed_output_execution_also_checks_joint_input_constraints():
    plan = _plan()
    plan['schema_version'] = 2
    plan['candidates'][0]['kind'] = 'function_points'
    plan['candidates'][0]['prediction'] = {
        'kind': 'fixed_outputs',
        'names': ['theta_33', 'theta_1500'],
    }
    candidate = load_evaluation_plan(plan).candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    with pytest.raises(ModelEvaluationError, match='sand\\+clay'):
        evaluate_candidate(candidate, [33], {'sand': 0.8, 'clay': 0.4, 'organic_matter': 2.5})
