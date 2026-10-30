import runpy
from fractions import Fraction
from math import comb
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[3]
    / 'evaluation/experiments/selector_training_law/calibrate.py'
)


@pytest.mark.parametrize('population', ['equal_binary', 'informative_four'])
def test_complete_selector_exact_law_preserves_size_weighting_failures_and_joint_coverage(
    population: str,
):
    result = runpy.run_path(str(SCRIPT))['calibrate'](population=population, n_blocks=12)
    informative = population == 'informative_four'
    success = Fraction(23, 32) if informative else Fraction(1, 2)
    mass = Fraction(11, 256) if informative else Fraction(1, 32)
    conditional = Fraction(11, 184) if informative else Fraction(1, 16)
    assert Fraction(result['training_success_probability']) == success
    assert Fraction(result['risk_mass_on_success']) == mass
    assert Fraction(result['successful_training_mean_risk']) == conditional
    assert Fraction(result['population_late_sample_fraction']) == (
        Fraction(5, 12) if informative else Fraction(1, 2)
    )
    assert result['unconditional_model_risk'] is None
    assert len(result['local_cases']) == (64 if informative else 8)
    assert len(result['cases']) == (6188 if informative else 91)
    assert sum(Fraction(c['probability']) for c in result['local_cases']) == 1
    assert sum(Fraction(c['probability']) for c in result['cases']) == 1
    assert Fraction(result['joint_coverage_probability']) >= Fraction(19, 20)
    assert Fraction(result['conditional_error_and_issued_probability']) <= Fraction(1, 20)
    # With n=12 and alpha=.05 the Hoeffding success radius is strictly
    # between 5/12 and 6/12. Issuance therefore requires at least six successes.
    issue_probability = sum(
        comb(12, k) * success**k * (1 - success) ** (12 - k) for k in range(6, 13)
    )
    assert Fraction(result['conditional_interval_issue_probability']) == issue_probability
    if informative:
        expected = {
            (False, 1, '0'): Fraction(75, 256),
            (False, 1, '1/8'): Fraction(63, 256),
            (False, 3, '0'): Fraction(23, 256),
            (False, 3, '3/8'): Fraction(23, 256),
            (True, 1, '0'): Fraction(27, 128),
            (True, 3, '0'): Fraction(9, 128),
        }
    else:
        expected = {
            (False, 1, '0'): Fraction(1, 4),
            (False, 1, '1/8'): Fraction(1, 4),
            (True, 1, '0'): Fraction(1, 2),
        }
    assert {
        (s['failed_training'], s['test_size'], s['loss_sum']): Fraction(s['probability'])
        for s in result['sufficient_states']
    } == expected
    for case in result['cases']:
        counts = case['sufficient_state_counts']
        states = result['sufficient_states']
        assert case['bound']['status'] == 'computed'
        assert case['bound']['training_failure_count'] == sum(
            count for count, state in zip(counts, states, strict=True) if state['failed_training']
        )
        assert case['bound']['test_sample_count'] == sum(
            count * state['test_size'] for count, state in zip(counts, states, strict=True)
        )


def test_actual_refit_ties_and_informative_majorities_remain_visible_in_local_traces():
    law = runpy.run_path(str(SCRIPT))['local_law']('informative_four')
    tied = []
    unequal = []
    for trace in law.traces:
        first, second = trace['training_states']
        fit = trace['block']['selection']['folds'][0]['ensemble']['outer_fit']
        if first.split('_')[0] != second.split('_')[0]:
            if first.split('_')[1] == second.split('_')[1]:
                tied.append(trace)
                assert fit['switch_suction_kpa'] is None
                assert fit['reason'] == 'unidentifiable_boundary'
                assert trace['block']['evidence']['training_failure_reason'] == fit['reason']
                assert trace['block']['evidence']['test_groups'][0]['sample_losses'] is None
            else:
                unequal.append(trace)
                larger = first if first.endswith('three') else second
                expected = 5 if larger.startswith('early') else 10
                assert fit['switch_suction_kpa'] == expected
                assert fit['loss_gap'] == pytest.approx(1 / 16)
    assert len(tied) == len(unequal) == 16
    assert sum(Fraction(c['probability']) for c in tied) == Fraction(9, 32)
    assert sum(Fraction(c['probability']) for c in unequal) == Fraction(3, 16)


@pytest.mark.parametrize('population', ['equal_binary', 'informative_four'])
def test_paired_complete_selector_compares_joint_success_and_retains_asymmetric_fit_failures(
    population: str,
):
    result = runpy.run_path(str(SCRIPT))['calibrate_pair'](population=population, n_blocks=12)
    informative = population == 'informative_four'
    success = Fraction(23, 32) if informative else Fraction(1, 2)
    assert Fraction(result['joint_training_success_probability']) == success
    assert Fraction(result['risk_difference_mass_on_joint_success']) == success / 16
    assert Fraction(result['joint_success_mean_risk_difference']) == Fraction(1, 16)
    assert Fraction(result['difference_of_marginal_successful_training_risks']) == (
        Fraction(1559, 23552) if informative else Fraction(1, 16)
    )
    assert result['unconditional_model_risk_difference'] is None
    assert len(result['local_cases']) == (64 if informative else 8)
    assert len(result['cases']) == (455 if informative else 13)
    assert sum(Fraction(case['probability']) for case in result['cases']) == 1
    assert Fraction(result['joint_coverage_probability']) >= Fraction(19, 20)
    assert Fraction(result['conditional_error_and_issued_probability']) <= Fraction(1, 20)
    assert Fraction(result['conditional_interval_issue_probability']) == sum(
        comb(12, k) * success**k * (1 - success) ** (12 - k) for k in range(6, 13)
    )
    failed = [
        c for c in result['local_cases'] if c['paired_block']['right']['training_failure_reason']
    ]
    assert failed
    assert sum(Fraction(c['probability']) for c in failed) == 1 - success
    for case in failed:
        block = case['paired_block']
        assert block['left']['training_failure_reason'] is None
        assert block['left']['test_groups'][0]['sample_losses'] is not None
        assert block['right']['test_groups'][0]['sample_losses'] is None
