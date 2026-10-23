import runpy
from fractions import Fraction
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[3] / 'evaluation/experiments/blend_training_law/calibrate.py'
)


@pytest.mark.parametrize('population', ['equal_binary', 'informative_four'])
def test_complete_blend_training_law_matches_independent_oracles_and_scaled_coverage(
    population: str,
):
    result = runpy.run_path(str(SCRIPT))['calibrate'](population=population, n_blocks=12)
    informative = population == 'informative_four'
    assert Fraction(result['training_success_probability']) == (
        Fraction(23, 32) if informative else Fraction(1, 2)
    )
    assert Fraction(result['risk_mass_on_success']) == (
        Fraction(11, 2048) if informative else Fraction(1, 256)
    )
    assert Fraction(result['successful_training_mean_risk']) == (
        Fraction(11, 1472) if informative else Fraction(1, 128)
    )
    assert result['unconditional_model_risk'] is None
    assert len(result['local_cases']) == (64 if informative else 8)
    assert len(result['cases']) == (6188 if informative else 91)
    assert sum(Fraction(case['probability']) for case in result['cases']) == 1
    assert Fraction(result['joint_coverage_probability']) >= Fraction(19, 20)
    assert Fraction(result['conditional_error_and_issued_probability']) <= Fraction(1, 20)
    failures = [
        c for c in result['local_cases'] if c['block']['evidence']['training_failure_reason']
    ]
    assert sum(Fraction(c['probability']) for c in failures) == (
        Fraction(9, 32) if informative else Fraction(1, 2)
    )
    for case in failures:
        fit = case['block']['selection']['folds'][0]['ensemble']['outer_fit']
        assert fit['reason'] == 'unidentifiable_blend_interval'
        assert fit['interval_kpa'] is None
        assert case['block']['evidence']['test_groups'][0]['sample_losses'] is None
    if informative:
        majority = next(
            c for c in result['local_cases'] if c['training_states'] == ['early_one', 'late_three']
        )
        fit = majority['block']['selection']['folds'][0]['ensemble']['outer_fit']
        assert fit['interval_kpa'] == [10, 100]
        assert fit['training_loss'] == Fraction(1, 256)
        assert fit['loss_gap'] == Fraction(1, 128)


@pytest.mark.parametrize('metric', ['mae', 'mse'])
@pytest.mark.parametrize('population', ['equal_binary', 'informative_four'])
def test_point_risk_uses_unchanged_full_learner_and_exact_finite_population_truths(
    metric: str,
    population: str,
):
    result = runpy.run_path(str(SCRIPT))['calibrate'](
        population=population,
        n_blocks=12,
        metric=metric,
    )
    informative = population == 'informative_four'
    mismatch_loss = Fraction(1, 20) if metric == 'mae' else Fraction(1, 80)
    # Sample-majority rule: success 23/32; normalized mass 11/32, or 1/4.
    assert Fraction(result['training_success_probability']) == (
        Fraction(23, 32) if informative else Fraction(1, 2)
    )
    assert Fraction(result['risk_mass_on_success']) == mismatch_loss * (
        Fraction(11, 32) if informative else Fraction(1, 4)
    )
    assert Fraction(result['successful_training_mean_risk']) == mismatch_loss * (
        Fraction(11, 23) if informative else Fraction(1, 2)
    )
    assert len(result['local_cases']) == (64 if informative else 8)
    assert len(result['cases']) == (6188 if informative else 91)
    assert Fraction(result['joint_coverage_probability']) == (
        Fraction(79147917377670960618897997173, 79228162514264337593543950336)
        if informative
        else Fraction(130959, 131072)
    )
    for case in result['local_cases']:
        block = case['block']
        assert len(block['point_losses']) == (3 if case['test_state'].endswith('three') else 1)
        for sample in block['point_losses']:
            assert sample['expected_point_count'] == 5
            if block['evidence']['training_failure_reason']:
                assert sample['loss'] is None
                assert sample['reason'] == 'training_failed'
            else:
                assert sample['point_count'] == 5
                assert sample['loss'] in (0, float(mismatch_loss))
                assert sample['reason'] is None
