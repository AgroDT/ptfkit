import math
import runpy
from fractions import Fraction
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[3] / 'evaluation/experiments/sigmoid_training_law/calibrate.py'
)


@pytest.mark.parametrize('population', ['equal_binary', 'informative_four'])
def test_complete_sigmoid_training_matches_exact_rational_oracles_and_coverage(population: str):
    result = runpy.run_path(str(SCRIPT))['calibrate'](population=population, n_blocks=12)
    informative = population == 'informative_four'
    p = Fraction(23, 32) if informative else Fraction(1, 2)
    assert Fraction(result['rational_mismatch_loss']) == Fraction(2, 225)
    assert Fraction(result['training_success_probability']) == p
    assert Fraction(result['risk_mass_on_success']) == (
        Fraction(11, 3600) if informative else Fraction(1, 450)
    )
    assert Fraction(result['successful_training_mean_risk']) == (
        Fraction(22, 5175) if informative else Fraction(1, 225)
    )
    assert result['unconditional_model_risk'] is None
    assert len(result['local_cases']) == (64 if informative else 8)
    assert len(result['cases']) == (6188 if informative else 91)
    assert sum(Fraction(case['probability']) for case in result['cases']) == 1
    # Independent binomial tails: at n=12, success CI misses only at <=3
    # successes for p=23/32; at p=1/2 it misses at 0 or 12 successes.
    miss = (
        sum(math.comb(12, k) * p**k * (1 - p) ** (12 - k) for k in range(4))
        if informative
        else Fraction(1, 2048)
    )
    assert Fraction(result['joint_coverage_probability']) == 1 - miss
    issuance = sum(math.comb(12, k) * p**k * (1 - p) ** (12 - k) for k in range(6, 13))
    assert Fraction(result['conditional_interval_issue_probability']) == issuance
    assert Fraction(result['conditional_error_and_issued_probability']) == 0
    failures = [
        case
        for case in result['local_cases']
        if case['block']['evidence']['training_failure_reason']
    ]
    assert sum(Fraction(case['probability']) for case in failures) == 1 - p
    for case in failures:
        fit = case['block']['selection']['folds'][0]['ensemble']['outer_fit']
        assert fit['reason'] == 'unidentifiable_sigmoid_parameters'
        assert fit['parameters'] is None
        assert case['block']['evidence']['test_groups'][0]['sample_losses'] is None
    if informative:
        majority = next(
            c for c in result['local_cases'] if c['training_states'] == ['early_one', 'late_three']
        )
        fit = majority['block']['selection']['folds'][0]['ensemble']['outer_fit']
        assert fit['parameters'] == [10, 2 * math.log(2)]
        assert fit['training_loss'] == pytest.approx(float(Fraction(1, 450)), rel=1e-14)
        assert fit['loss_gap'] == pytest.approx(float(Fraction(1, 225)), rel=1e-14)
