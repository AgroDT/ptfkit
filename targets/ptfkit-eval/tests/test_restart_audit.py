import runpy
from pathlib import Path

import pytest


def test_restart_verifier_uses_independent_plateau_and_power_objectives():
    namespace = runpy.run_path(
        str(
            Path(__file__).resolve().parents[3]
            / 'evaluation/experiments/hybras/summarize_restarts.py'
        )
    )
    observations = [
        {'suction_kpa': 0, 'water_content': 0.4},
        {'suction_kpa': 4, 'water_content': 0.35},
    ]
    # theta(0)=0.5, theta(4)=0.1+0.4/sqrt(4)=0.3;
    # independent squared residuals: 0.1^2 + (-0.05)^2 = 0.0125.
    values = {'theta_r': 0.1, 'theta_s': 0.5, 'air_entry': 1, 'lambda': 0.5}
    assert namespace['independent_objective'](values, observations) == pytest.approx(0.0125)
    attempts = [{'converged': True, 'values': [0.5, 1, 0.5], 'sum_squared_error': 0.0125}]
    assert (
        namespace['verify_attempts'](
            attempts, ('theta_s', 'air_entry', 'lambda'), observations, fixed={'theta_r': 0.1}
        )
        == 1
    )
    attempts[0]['sum_squared_error'] = 0.01
    with pytest.raises(ValueError, match='independent Brooks-Corey equation'):
        namespace['verify_attempts'](
            attempts, ('theta_s', 'air_entry', 'lambda'), observations, fixed={'theta_r': 0.1}
        )
