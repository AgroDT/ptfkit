"""Protect the reviewed Staring class-to-retention evaluation path."""

import copy
import json
import math
from decimal import Decimal, localcontext

import pytest
from ptfkit import get_manifest

from ptfkit_eval import (
    AdapterPrediction,
    AtomicCurve,
    AxisSpec,
    CurveExecutionError,
    FunctionCurveCandidate,
    ModelEvaluationError,
    PlanValidationError,
    TargetSpec,
    evaluate_candidate,
    evaluate_van_genuchten_mualem_h_theta,
    load_evaluation_plan,
)
from ptfkit_eval.documents import canonical_json


def _plan(function: str = 'calc_ptf_wosten2001_class_parameters') -> dict:
    return {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'staring',
                'kind': 'function_curve',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'log10',
                },
                'target': {
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                    'material_basis': 'soil',
                    'denominator_basis': 'bulk_volume',
                },
                'function': function,
                'prediction': {'kind': 'model_adapter', 'id': 'wosten2001_h_theta'},
            }
        ],
    }


@pytest.mark.parametrize(
    ('soil_class', 'theta_s', 'theta_h100'),
    [('b1', 0.43, 0.210), ('b16', 0.80, 0.622), ('o1', 0.36, 0.124)],
)
def test_published_class_predictions_include_mineral_and_organic_soils(
    soil_class: str,
    theta_s: float,
    theta_h100: float,
):
    # Independent rounded entries from Wosten (2001), Table 4, h=-100 cm.
    candidate = load_evaluation_plan(_plan()).candidates[0]
    assert isinstance(candidate, FunctionCurveCandidate)
    values = evaluate_candidate(candidate, [0, 9.80665], {'soil_class': soil_class}).points
    assert values[0].value == theta_s
    assert values[1].value == pytest.approx(theta_h100, abs=0.0005)


def test_mualem_exponent_is_distinct_from_vereecken_m_equal_one():
    parameters = {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.01, 'n': 2.0}
    assert evaluate_van_genuchten_mualem_h_theta(parameters, 100) == pytest.approx(
        0.1 + 0.4 / math.sqrt(2)
    )


@pytest.mark.parametrize(
    ('alpha', 'suction', 'shape'),
    [
        (1e308, 1e308, 1.01),
        (1e-308, 1e-308, 2),
        (3, 1 / 3, 1e16),
        (0.01, 100, math.nextafter(1.0, 2.0)),
    ],
)
def test_mualem_adapter_preserves_extreme_pressure_and_shape_limits(
    alpha: float,
    suction: float,
    shape: float,
):
    # Decimal evaluates the original power expression, independently of log-space code.
    with localcontext() as context:
        context.prec = 100
        n = Decimal(shape)
        power = (Decimal(alpha) * Decimal(suction)) ** n
        effective = (1 + power) ** (-(1 - 1 / n))
        expected = float(Decimal('0.1') + Decimal('0.4') * effective)
    actual = evaluate_van_genuchten_mualem_h_theta(
        {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': alpha, 'n': shape},
        suction,
    )
    assert actual == pytest.approx(expected, rel=2e-14)


@pytest.mark.parametrize(
    ('parameters', 'suction', 'message'),
    [
        ({'n': 1}, 10, 'n > 1'),
        ({'alpha': 0}, 10, 'alpha must be positive'),
        ({'theta_r': 0.5}, 10, 'theta_r < theta_s'),
        ({}, -1, 'nonnegative magnitude'),
    ],
)
def test_mualem_adapter_rejects_invalid_physical_parameters(
    parameters: dict,
    suction: float,
    message: str,
):
    with pytest.raises(ModelEvaluationError, match=message):
        evaluate_van_genuchten_mualem_h_theta(
            {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.01, 'n': 2, **parameters},
            suction,
        )


def test_unreviewed_function_cannot_reuse_an_adapter_by_matching_parameter_names():
    manifest = json.loads(canonical_json(get_manifest()))
    function = copy.deepcopy(
        next(
            item
            for item in manifest['functions']
            if item['id'] == 'calc_ptf_wosten2001_class_parameters'
        )
    )
    function['id'] = 'unreviewed_same_parameters'
    manifest['functions'].append(function)
    with pytest.raises(PlanValidationError) as caught:
        load_evaluation_plan(_plan(function['id']), manifest=manifest)
    assert 'adapter.function_unsupported' in {item.code for item in caught.value.diagnostics}
    candidate = FunctionCurveCandidate(
        'bypass',
        AxisSpec('matric_potential', 'kilopascal', 'magnitude', 'linear'),
        TargetSpec('volumetric_water_content', 'volume_fraction', 'soil', 'bulk_volume'),
        AtomicCurve(function['id'], AdapterPrediction('wosten2001_h_theta')),
    )
    with pytest.raises(CurveExecutionError, match='not reviewed'):
        evaluate_candidate(candidate, [10], {'soil_class': 'b1'}, manifest=manifest)
