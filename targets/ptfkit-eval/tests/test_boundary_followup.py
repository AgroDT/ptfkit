import math
import runpy
from pathlib import Path

import numpy as np
import pytest


def _namespace() -> dict:
    return runpy.run_path(
        str(
            Path(__file__).resolve().parents[3]
            / 'evaluation/experiments/retention_coverage/boundary_followup.py'
        )
    )


def test_independent_van_genuchten_jacobian_has_hand_derived_values():
    function = _namespace()['vg_curve_and_jacobian']
    curve, jacobian = function(np.array([0, 10]), np.array([0.1, 0.3, 0.1, 2]))
    assert curve == pytest.approx([0.3, 0.1 + 0.2 / math.sqrt(2)])
    assert jacobian[0] == pytest.approx([0, 1, 0, 0])
    assert jacobian[1] == pytest.approx(
        [
            1 - 1 / math.sqrt(2),
            1 / math.sqrt(2),
            -1 / math.sqrt(2),
            -0.2 * math.log(2) / (4 * math.sqrt(2)),
        ]
    )
    _, fourth_power = function(np.array([10]), np.array([0.1, 0.3, 0.1, 4]))
    effective = 2**-0.75
    assert fourth_power[0] == pytest.approx(
        [
            1 - effective,
            effective,
            -3 * effective,
            -0.2 * effective * math.log(2) / 16,
        ]
    )


def test_exact_linear_control_distinguishes_sign_selection_from_coverage():
    control = _namespace()['linear_control']
    for coupling in (0, 2):
        design = np.eye(5)[:, :4]
        design[0, 1] = coupling
        outcomes = [
            control(np.array([coupling * value, value, 0, 0, 1]), design, 0.5)
            for value in (-2, -0.5, 0.5, 2)
        ]
        # SSE and coefficient variance factor are one, including the coupled design.
        assert [item['selected'] for item in outcomes] == [False, False, True, True]
        assert [item['covered'] for item in outcomes] == [False, True, True, False]
