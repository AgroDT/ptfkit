import copy
import math
from pathlib import Path

import pytest

from ptfkit_eval import (
    AdapterPrediction,
    FunctionCurveCandidate,
    ModelAdapterSpec,
    ModelParameterSpec,
    OutputPrediction,
    PlanValidationError,
    RangeGatedCurveCandidate,
    load_evaluation_plan,
)


def _measurement(
    quantity: str,
    unit: str,
    role: str,
    *,
    material: str = 'fine_earth',
    denominator: str = 'bulk_volume',
) -> dict[str, object]:
    return {
        'quantity': quantity,
        'unit': unit,
        'basis': {'material': material, 'denominator': denominator},
        'role': role,
    }


def _manifest() -> dict[str, object]:
    return {
        'schema_version': 1,
        'units': {
            'kilopascal': {
                'conversion': {'dimension': 'pressure', 'scale_to_si': 1000.0, 'offset_to_si': 0.0}
            },
            'centimeter_water_head': {
                'conversion': {'dimension': 'pressure', 'scale_to_si': 98.0665, 'offset_to_si': 0.0}
            },
            'volume_fraction': {
                'conversion': {'dimension': 'volume_ratio', 'scale_to_si': 1.0, 'offset_to_si': 0.0}
            },
            'volume_percent': {
                'conversion': {
                    'dimension': 'volume_ratio',
                    'scale_to_si': 0.01,
                    'offset_to_si': 0.0,
                }
            },
        },
        'quantities': {
            'matric_potential': {'units': ['kilopascal', 'centimeter_water_head']},
            'volumetric_water_content': {'units': ['volume_fraction', 'volume_percent']},
        },
        'functions': [
            {
                'id': 'calc_ptf_direct',
                'models': {'h_theta': None, 'k_h': None},
                'inputs': [
                    {
                        'kind': 'numeric',
                        'name': 'pressure',
                        'measurement': _measurement(
                            'matric_potential',
                            'centimeter_water_head',
                            'predictor',
                            denominator='not_applicable',
                        ),
                    }
                ],
                'outputs': [
                    {
                        'kind': 'numeric',
                        'name': 'theta',
                        'measurement': _measurement(
                            'volumetric_water_content', 'volume_fraction', 'prediction'
                        ),
                    }
                ],
            },
            {
                'id': 'calc_ptf_parameters',
                'models': {'h_theta': 'Synthetic retention model', 'k_h': None},
                'inputs': [],
                'outputs': [
                    {
                        'kind': 'numeric',
                        'name': 'theta_s',
                        'measurement': _measurement(
                            'volumetric_water_content', 'volume_fraction', 'model_parameter'
                        ),
                    }
                ],
            },
        ],
    }


def _axis() -> dict[str, object]:
    return {
        'quantity': 'matric_potential',
        'unit': 'kilopascal',
        'convention': 'magnitude',
        'transform': 'log10',
    }


def _target() -> dict[str, object]:
    return {
        'quantity': 'volumetric_water_content',
        'unit': 'volume_percent',
        'material_basis': 'fine_earth',
        'denominator_basis': 'bulk_volume',
    }


def _direct_plan() -> dict[str, object]:
    return {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'direct_curve',
                'kind': 'function_curve',
                'axis': _axis(),
                'target': _target(),
                'function': 'calc_ptf_direct',
                'prediction': {'kind': 'output', 'name': 'theta'},
            }
        ],
    }


def _adapter() -> ModelAdapterSpec:
    return ModelAdapterSpec(
        id='synthetic_h_theta',
        model_kind='h_theta',
        axis_quantity='matric_potential',
        axis_unit='centimeter_water_head',
        axis_convention='magnitude',
        target_quantity='volumetric_water_content',
        target_unit='volume_fraction',
        target_material_basis='fine_earth',
        target_denominator_basis='bulk_volume',
        parameters=(
            ModelParameterSpec(
                output='theta_s',
                quantity='volumetric_water_content',
                unit='volume_fraction',
                material_basis='fine_earth',
                denominator_basis='bulk_volume',
            ),
        ),
    )


def _composite_plan() -> dict[str, object]:
    return {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'composite_curve',
                'kind': 'range_gated_curve',
                'axis': _axis(),
                'target': _target(),
                'members': [
                    {
                        'id': 'wet',
                        'function': 'calc_ptf_parameters',
                        'prediction': {'kind': 'model_adapter', 'id': 'synthetic_h_theta'},
                        'interval': {
                            'lower': {'value': 0.1, 'inclusive': True},
                            'upper': {'value': 33.0, 'inclusive': True},
                        },
                    },
                    {
                        'id': 'dry',
                        'function': 'calc_ptf_parameters',
                        'prediction': {'kind': 'model_adapter', 'id': 'synthetic_h_theta'},
                        'interval': {
                            'lower': {'value': 10.0, 'inclusive': True},
                            'upper': {'value': 1500.0, 'inclusive': True},
                        },
                    },
                ],
                'routing': {
                    'gap': 'reject',
                    'extrapolation': 'reject',
                    'transitions': [
                        {
                            'kind': 'blend',
                            'left_member': 'wet',
                            'right_member': 'dry',
                            'interval': {
                                'lower': {'value': 10.0, 'inclusive': True},
                                'upper': {'value': 33.0, 'inclusive': True},
                            },
                            'weighting': 'linear',
                        }
                    ],
                },
                'provenance': {'kind': 'fixed', 'source': 'Independent fixture.'},
            }
        ],
    }


def _diagnostic_codes(error: PlanValidationError) -> set[str]:
    return {diagnostic.code for diagnostic in error.diagnostics}


def _first_candidate(source: dict[str, object]) -> dict[str, object]:
    candidates = source['candidates']
    assert isinstance(candidates, list)
    candidate = candidates[0]
    assert isinstance(candidate, dict)
    return candidate


def test_resolves_a_direct_curve_with_dimensionally_convertible_units():
    plan = load_evaluation_plan(_direct_plan(), manifest=_manifest())

    candidate = plan.candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    assert candidate.curve.function == 'calc_ptf_direct'
    assert candidate.curve.prediction == OutputPrediction('theta')


def test_loads_a_yaml_plan_before_manifest_resolution(tmp_path: Path):
    plan_path = tmp_path / 'plan.yaml'
    plan_path.write_text(
        """\
schema_version: 1
ptfkit_manifest_schema_version: 1
candidates:
  - id: direct_curve
    kind: function_curve
    axis:
      quantity: matric_potential
      unit: kilopascal
      convention: magnitude
      transform: log10
    target:
      quantity: volumetric_water_content
      unit: volume_percent
      material_basis: fine_earth
      denominator_basis: bulk_volume
    function: calc_ptf_direct
    prediction: {kind: output, name: theta}
""",
        encoding='utf-8',
    )

    plan = load_evaluation_plan(plan_path, manifest=_manifest())

    assert plan.candidates[0].id == 'direct_curve'


def test_resolves_a_registered_adapter_against_the_packaged_ptfkit_manifest():
    source = {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'clapp_retention',
                'kind': 'function_curve',
                'axis': _axis(),
                'target': {
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                    'material_basis': 'mineral_soil',
                    'denominator_basis': 'bulk_volume',
                },
                'function': 'calc_ptf_clapp1978',
                'prediction': {'kind': 'model_adapter', 'id': 'clapp1978_h_theta'},
            }
        ],
    }
    adapter = ModelAdapterSpec(
        id='clapp1978_h_theta',
        model_kind='h_theta',
        axis_quantity='matric_potential',
        axis_unit='centimeter_water_head',
        axis_convention='magnitude',
        target_quantity='volumetric_water_content',
        target_unit='volume_fraction',
        target_material_basis='mineral_soil',
        target_denominator_basis='bulk_volume',
        parameters=(
            ModelParameterSpec(
                'b', 'campbell_b', 'dimensionless', 'mineral_soil', 'not_applicable'
            ),
            ModelParameterSpec(
                'saturation_suction',
                'matric_potential',
                'centimeter_water_head',
                'mineral_soil',
                'not_applicable',
            ),
            ModelParameterSpec(
                'saturated_water_content',
                'volumetric_water_content',
                'volume_fraction',
                'mineral_soil',
                'bulk_volume',
            ),
        ),
    )

    plan = load_evaluation_plan(source, model_adapters={adapter.id: adapter})

    candidate = plan.candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    assert candidate.curve.function == 'calc_ptf_clapp1978'
    assert candidate.curve.prediction == AdapterPrediction('clapp1978_h_theta')


def test_rejects_an_unknown_function_before_execution():
    source = _direct_plan()
    candidate = _first_candidate(source)
    candidate['function'] = 'calc_ptf_missing'

    with pytest.raises(PlanValidationError) as raised:
        load_evaluation_plan(source, manifest=_manifest())

    assert _diagnostic_codes(raised.value) == {'manifest.unknown_function'}
    assert raised.value.diagnostics[0].path == '$.candidates[0].function'


def test_rejects_a_target_with_the_wrong_measurement_basis():
    source = _direct_plan()
    candidate = _first_candidate(source)
    target = candidate['target']
    assert isinstance(target, dict)
    target['denominator_basis'] = 'dry_mass'

    with pytest.raises(PlanValidationError) as raised:
        load_evaluation_plan(source, manifest=_manifest())

    assert 'measurement.basis_mismatch' in _diagnostic_codes(raised.value)


def test_resolves_adapter_members_and_builds_the_declared_router():
    plan = load_evaluation_plan(
        _composite_plan(),
        manifest=_manifest(),
        model_adapters={'synthetic_h_theta': _adapter()},
    )

    candidate = plan.candidates[0]
    assert isinstance(candidate, RangeGatedCurveCandidate)
    assert all(
        member.curve.prediction == AdapterPrediction('synthetic_h_theta')
        for member in candidate.members
    )
    midpoint = candidate.router.route(math.sqrt(330.0))
    assert midpoint[0].weight == pytest.approx(0.5)
    assert midpoint[1].weight == pytest.approx(0.5)


def test_rejects_an_unregistered_model_adapter():
    with pytest.raises(PlanValidationError) as raised:
        load_evaluation_plan(_composite_plan(), manifest=_manifest())

    assert _diagnostic_codes(raised.value) == {'manifest.unknown_adapter'}
    assert len(raised.value.diagnostics) == 2


def test_rejects_overlapping_members_without_a_transition():
    source = _composite_plan()
    candidate = _first_candidate(source)
    routing = candidate['routing']
    assert isinstance(routing, dict)
    routing['transitions'] = []

    with pytest.raises(PlanValidationError) as raised:
        load_evaluation_plan(
            source,
            manifest=_manifest(),
            model_adapters={'synthetic_h_theta': _adapter()},
        )

    assert 'composite.missing_transition' in _diagnostic_codes(raised.value)


def test_rejects_an_interval_whose_bounds_are_reversed():
    source = copy.deepcopy(_composite_plan())
    candidate = _first_candidate(source)
    members = candidate['members']
    assert isinstance(members, list)
    first = members[0]
    assert isinstance(first, dict)
    first['interval'] = {
        'lower': {'value': 100.0, 'inclusive': True},
        'upper': {'value': 10.0, 'inclusive': True},
    }

    with pytest.raises(PlanValidationError) as raised:
        load_evaluation_plan(
            source,
            manifest=_manifest(),
            model_adapters={'synthetic_h_theta': _adapter()},
        )

    assert 'composite.invalid_interval' in _diagnostic_codes(raised.value)


def test_rejects_a_manifest_schema_version_mismatch():
    manifest = _manifest()
    manifest['schema_version'] = 2

    with pytest.raises(PlanValidationError) as raised:
        load_evaluation_plan(_direct_plan(), manifest=manifest)

    assert _diagnostic_codes(raised.value) == {'manifest.schema_version_mismatch'}
