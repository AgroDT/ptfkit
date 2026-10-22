import math
import sys
from types import ModuleType, SimpleNamespace

import pytest

from ptfkit_eval import (
    FunctionCurveCandidate,
    RangeGatedCurveCandidate,
    evaluate_candidate,
    load_evaluation_plan,
)


def _axis() -> dict[str, object]:
    return {
        'quantity': 'matric_potential',
        'unit': 'kilopascal',
        'convention': 'magnitude',
        'transform': 'log10',
    }


def _target(unit: str = 'volume_fraction') -> dict[str, object]:
    return {
        'quantity': 'volumetric_water_content',
        'unit': unit,
        'material_basis': 'mineral_soil',
        'denominator_basis': 'bulk_volume',
    }


def _clapp_prediction() -> dict[str, object]:
    return {'kind': 'model_adapter', 'id': 'clapp1978_h_theta'}


def _direct_manifest() -> dict[str, object]:
    basis = {'material': 'mineral_soil', 'denominator': 'bulk_volume'}
    return {
        'schema_version': 1,
        'units': {
            'kilopascal': {
                'conversion': {'dimension': 'pressure', 'scale_to_si': 1000.0, 'offset_to_si': 0.0}
            },
            'centimeter_water_head': {
                'conversion': {
                    'dimension': 'pressure',
                    'scale_to_si': 98.0665,
                    'offset_to_si': 0.0,
                }
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
                'id': 'calc_fixture_curve',
                'module': 'ptfkit_eval_test_fixture',
                'callable': 'calc_fixture_curve',
                'models': {'h_theta': None, 'k_h': None},
                'inputs': [
                    {
                        'kind': 'numeric',
                        'name': 'pressure',
                        'measurement': {
                            'quantity': 'matric_potential',
                            'unit': 'centimeter_water_head',
                            'basis': {
                                'material': 'mineral_soil',
                                'denominator': 'not_applicable',
                            },
                            'role': 'predictor',
                        },
                    }
                ],
                'outputs': [
                    {
                        'kind': 'numeric',
                        'name': 'theta',
                        'measurement': {
                            'quantity': 'volumetric_water_content',
                            'unit': 'volume_fraction',
                            'basis': basis,
                            'role': 'prediction',
                        },
                    }
                ],
            }
        ],
    }


def test_executes_clapp1978_from_categorical_input_through_unit_conversions():
    plan = load_evaluation_plan(
        {
            'schema_version': 1,
            'ptfkit_manifest_schema_version': 1,
            'candidates': [
                {
                    'id': 'clapp_sand',
                    'kind': 'function_curve',
                    'axis': _axis(),
                    'target': _target('volume_percent'),
                    'function': 'calc_ptf_clapp1978',
                    'prediction': _clapp_prediction(),
                }
            ],
        }
    )
    candidate = plan.candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    half_wetness_suction_kpa = 3.50 * 2.0**4.05 * 0.0980665

    evaluated = evaluate_candidate(
        candidate,
        [0.0, half_wetness_suction_kpa],
        {'soil_texture': 'sand'},
    )

    assert [point.value for point in evaluated.points] == pytest.approx([39.5, 19.75])
    assert evaluated.points[1].contributions[0].function == 'calc_ptf_clapp1978'


def test_executes_a_direct_curve_output_with_a_resolved_axis_input(
    monkeypatch: pytest.MonkeyPatch,
):
    module = ModuleType('ptfkit_eval_test_fixture')

    def calc_fixture_curve(*, pressure: float) -> SimpleNamespace:
        return SimpleNamespace(theta=pressure / 200.0)

    module.__dict__['calc_fixture_curve'] = calc_fixture_curve
    monkeypatch.setitem(sys.modules, module.__name__, module)
    manifest = _direct_manifest()
    plan = load_evaluation_plan(
        {
            'schema_version': 1,
            'ptfkit_manifest_schema_version': 1,
            'candidates': [
                {
                    'id': 'direct_curve',
                    'kind': 'function_curve',
                    'axis': _axis(),
                    'target': _target('volume_percent'),
                    'function': 'calc_fixture_curve',
                    'prediction': {'kind': 'output', 'name': 'theta'},
                }
            ],
        },
        manifest=manifest,
    )
    candidate = plan.candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)

    evaluated = evaluate_candidate(
        candidate,
        [9.80665],
        {},
        manifest=manifest,
    )

    assert evaluated.points[0].value == pytest.approx(50.0)


def test_executes_and_traces_a_range_gated_clapp1978_ensemble():
    plan = load_evaluation_plan(
        {
            'schema_version': 1,
            'ptfkit_manifest_schema_version': 1,
            'candidates': [
                {
                    'id': 'texture_ensemble',
                    'kind': 'range_gated_curve',
                    'axis': _axis(),
                    'target': _target(),
                    'members': [
                        {
                            'id': 'wet',
                            'function': 'calc_ptf_clapp1978',
                            'prediction': _clapp_prediction(),
                            'interval': {
                                'lower': {'value': 0.1, 'inclusive': True},
                                'upper': {'value': 10.0, 'inclusive': True},
                            },
                        },
                        {
                            'id': 'dry',
                            'function': 'calc_ptf_clapp1978',
                            'prediction': _clapp_prediction(),
                            'interval': {
                                'lower': {'value': 1.0, 'inclusive': True},
                                'upper': {'value': 100.0, 'inclusive': True},
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
                                    'lower': {'value': 1.0, 'inclusive': True},
                                    'upper': {'value': 10.0, 'inclusive': True},
                                },
                                'weighting': 'linear',
                            }
                        ],
                    },
                    'provenance': {
                        'kind': 'fixed',
                        'source': 'Execution test with explicit range boundaries.',
                    },
                }
            ],
        }
    )
    candidate = plan.candidates[0]
    assert isinstance(candidate, RangeGatedCurveCandidate)

    evaluated = evaluate_candidate(
        candidate,
        [math.sqrt(10.0)],
        {
            'wet': {'soil_texture': 'sand'},
            'dry': {'soil_texture': 'clay'},
        },
    )

    point = evaluated.points[0]
    assert [item.member_id for item in point.contributions] == ['wet', 'dry']
    assert [item.weight for item in point.contributions] == pytest.approx([0.5, 0.5])
    assert point.contributions[0].value != point.contributions[1].value
    assert point.value == pytest.approx(
        sum(item.weight * item.value for item in point.contributions)
    )
