import math
import runpy
from pathlib import Path

import numpy as np
import pytest


def test_gaussian_mean_control_distinguishes_boundary_coverage_and_fit_selection():
    script = (
        Path(__file__).resolve().parents[3] / 'evaluation/experiments/profile_coverage/calibrate.py'
    )
    assess = runpy.run_path(str(script))['assess_sample']
    outcomes = []
    for z in (-2, -0.5, 0.5, 2):
        # n=2, SSE about the unconstrained mean is 1; F(1,1) median is 1.
        sample = np.array([(z - 1) / math.sqrt(2), (z + 1) / math.sqrt(2)])
        outcomes.append(assess(sample, 0, 0.5))
    assert [item['covered'] for item in outcomes] == [True, True, True, False]
    assert [item['interior_fit'] for item in outcomes] == [False, False, True, False]
    # The largest positive sample reaches the upper box boundary as well.
    assert outcomes[-1]['upper_boundary_fit']
    assert all(item['available'] for item in outcomes)
    assert [item['unconstrained_t_covered'] for item in outcomes] == [False, True, True, False]


def test_profile_coverage_simulation_replays_and_keeps_denominators():
    script = (
        Path(__file__).resolve().parents[3] / 'evaluation/experiments/profile_coverage/calibrate.py'
    )
    calibrate = runpy.run_path(str(script))['calibrate']
    result = calibrate(repetitions=12, seed=17)
    assert result == calibrate(repetitions=12, seed=17)
    assert [item['truth'] for item in result['scenarios']] == [0, 0.02, 0.5, 1]
    for item in result['scenarios']:
        assert item['generated'] == item['available'] == 12
        assert (
            item['interior_available'] + item['lower_boundary_fits'] + item['upper_boundary_fits']
            == 12
        )
        assert 0 <= item['interior_covered'] <= item['interior_available']
        assert item['interior_covered'] <= item['covered'] <= item['available']
    with pytest.raises(ValueError, match='Repetitions'):
        calibrate(repetitions=0, seed=17)
