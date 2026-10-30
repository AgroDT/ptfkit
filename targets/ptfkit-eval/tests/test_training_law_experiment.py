import runpy
from fractions import Fraction
from pathlib import Path

import pytest


@pytest.mark.parametrize(('size', 'total'), [(1, False), (3, False), (1, True), (3, True)])
def test_independent_training_law_exact_coverage_retains_failures_and_defined_targets(
    *,
    size: int,
    total: bool,
):
    script = (
        Path(__file__).resolve().parents[3]
        / 'evaluation/experiments/training_law_risk/calibrate.py'
    )
    result = runpy.run_path(str(script))['calibrate'](
        n_blocks=12, high_group_size=size, total_learner=total
    )
    assert len(result['cases']) == 455
    assert sum(Fraction(case['probability']) for case in result['cases']) == 1
    assert Fraction(result['joint_coverage_probability']) >= Fraction(19, 20)
    assert Fraction(result['conditional_error_and_issued_probability']) <= Fraction(1, 20)
    assert 0 < Fraction(result['conditional_interval_issue_probability']) <= 1
    assert Fraction(result['training_success_probability']) == (1 if total else Fraction(1, 2))
    expected_mass = Fraction(1, 2) if total else Fraction(size, 2 * (1 + size))
    assert Fraction(result['risk_mass_on_success']) == expected_mass
    assert Fraction(result['successful_training_mean_risk']) == (
        Fraction(1, 2) if total else Fraction(size, 1 + size)
    )
    for case in result['cases']:
        first, second, third, fourth = case['state_pair_counts']
        bound = case['bound']
        assert bound['training_failure_count'] == (0 if total else third + fourth)
        assert bound['test_sample_count'] == first + third + size * (second + fourth)
        assert bound['status'] == 'computed'
        assert (bound['unconditional_model_risk_interval'] is not None) == total
    assert (result['unconditional_model_risk'] is not None) == total
