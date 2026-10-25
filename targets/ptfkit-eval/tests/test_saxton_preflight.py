import math
import runpy
from collections.abc import Callable
from pathlib import Path

import pytest


def _evaluate() -> Callable[[object, object, object], dict]:
    return runpy.run_path(
        str(
            Path(__file__).resolve().parents[3]
            / 'evaluation/experiments/hybras/saxton_preflight.py'
        )
    )['evaluate_raw_predictors']


def test_saxton_preflight_converts_texture_percentages_and_preserves_om_percentage():
    result = _evaluate()(88, 5, 2.5)
    assert result['status'] == 'executed_preflight_only'
    assert result['reasons'] == []
    # Source Table 3 sand case, rounded at its reported precision.
    outputs = result['native_outputs']
    assert outputs['theta_1500'] == pytest.approx(0.05, abs=0.005)
    assert outputs['theta_33'] == pytest.approx(0.10, abs=0.005)
    assert outputs['theta_s'] == pytest.approx(0.46, abs=0.005)
    assert outputs['saturated_conductivity'] == pytest.approx(108.1, abs=0.05)


def test_saxton_preflight_retains_invalid_outputs_instead_of_clipping():
    with pytest.warns(RuntimeWarning, match='invalid value'):
        result = _evaluate()(97.99, 0, 0.471)
    assert result['status'] == 'executed_preflight_only'
    assert result['native_outputs']['theta_1500'] == pytest.approx(-0.00561768647)
    assert result['native_outputs']['retention_b'] is None
    assert 'nonfinite_native_output' in result['reasons']
    assert 'water_anchor_order_or_physical_bounds' in result['reasons']


@pytest.mark.parametrize(
    ('sand', 'clay', 'om', 'expected'),
    [
        (20, 60, 2.5, 'executed_preflight_only'),
        (20, math.nextafter(60, math.inf), 2.5, 'not_executed'),
        (20, 50, 8, 'executed_preflight_only'),
        (20, 50, math.nextafter(8, math.inf), 'not_executed'),
        (80, 30, 2.5, 'not_executed'),
        (20, 50, None, 'not_executed'),
    ],
)
def test_saxton_preflight_respects_source_input_limits(
    sand: float, clay: float, om: float | None, expected: str
):
    result = _evaluate()(sand, clay, om)
    assert result['status'] == expected
    if expected == 'not_executed':
        assert result['reasons']
        assert 'native_outputs' not in result
