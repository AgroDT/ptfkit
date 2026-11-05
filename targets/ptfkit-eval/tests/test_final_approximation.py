"""Independent checks for cluster weighting and the explicit mass-basis extension."""

import importlib
import math
import sys
from pathlib import Path

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
benchmark = importlib.import_module('evaluation.experiments.meta_v3_3.final_approximation')


def test_residual_metrics_weight_samples_instead_of_points():
    result = benchmark.residual_summary([np.array([2.0]), np.zeros(3)])
    assert result['samples'] == 2
    assert result['observations'] == 4
    assert result['rmse'] == pytest.approx(math.sqrt(2))
    assert result['bias'] == result['mae'] == 1
    assert result['p95_absolute_error'] == 2


def test_bootstrap_keeps_all_points_of_a_sample_together():
    result = benchmark.residual_summary([np.zeros(100), np.full(100, 10.0)], bootstrap=1000)
    # Two independent sample clusters produce means 0, 5, 10; 200-point IID draws would be narrow.
    assert result['bootstrap_95']['bias'] == [0, 10]
    repeated = benchmark.residual_summary([np.zeros(1), np.full(1000, 10.0)], bootstrap=1000)
    assert repeated['bias'] == result['bias'] == 5
    assert repeated['bootstrap_95']['bias'] == result['bootstrap_95']['bias']


def test_mass_basis_can_exceed_one_without_becoming_volume_fraction():
    parameters = {'theta_s': 2.0, 'theta_r': 0.5, 'alpha': 1.0, 'n': 2.0}
    values = benchmark.predict('van_genuchten_m1_v1', parameters, np.array([0.0, 1.0]), 5.0)
    # w(0)=w_s; w(1)=w_r+(w_s-w_r)/2 in kg/kg.
    assert values == pytest.approx([2.0, 1.25])
    with pytest.raises(ValueError, match='water contents'):
        benchmark.predict('van_genuchten_m1_v1', parameters, np.array([0.0, 1.0]), 1.0)


def test_under_determined_curve_is_not_counted_as_failed_optimizer():
    points = [
        {
            'basis': 'volumetric_water_content',
            'source_id': 'source',
            'sample_id': 'sample',
            'pressure_kpa': float(h),
            'observed': 0.4 - 0.05 * h,
        }
        for h in range(4)
    ]
    result = benchmark.fit_curve(points, 'van_genuchten_m1_v1')
    assert result['status'] == 'ineligible'
    assert result['reasons'] == ['insufficient_observations_or_distinct_pressures']
    assert result['rmse'] is None
    assert not result['converged']
