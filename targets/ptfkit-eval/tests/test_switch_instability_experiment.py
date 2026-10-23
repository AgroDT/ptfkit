import runpy
from fractions import Fraction
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ('size', 'atomic_risk', 'switch_risk_mass', 'switch_success', 'atomic_cv', 'switch_cv'),
    [
        (1, Fraction(1, 8), Fraction(1, 32), Fraction(1, 2), Fraction(1, 8), None),
        (3, Fraction(7, 64), Fraction(3, 64), Fraction(1), Fraction(13, 112), Fraction(3, 56)),
    ],
)
def test_switch_training_failure_law_and_exact_population_oracles(
    *,
    size: int,
    atomic_risk: Fraction,
    switch_risk_mass: Fraction,
    switch_success: Fraction,
    atomic_cv: Fraction,
    switch_cv: Fraction | None,
):
    script = (
        Path(__file__).resolve().parents[3]
        / 'evaluation/experiments/switch_instability/calibrate.py'
    )
    namespace = runpy.run_path(str(script))
    result = namespace['calibrate'](size)
    oracle = result['training_law_oracle']
    assert Fraction(oracle['atomic']['unconditional_mean_risk']) == atomic_risk
    assert Fraction(oracle['ensemble']['failure_probability']) == 1 - switch_success
    assert Fraction(oracle['ensemble']['risk_mass_on_success']) == switch_risk_mass
    assert (
        Fraction(oracle['ensemble']['conditional_mean_risk']) == switch_risk_mass / switch_success
    )
    if switch_cv is None:
        assert oracle['ensemble']['unconditional_mean_risk'] is None
    else:
        assert Fraction(oracle['ensemble']['unconditional_mean_risk']) == switch_risk_mass
    strategies = result['crossfit_strategy']
    assert strategies['atomic']['unconditional_mean_loss'] == pytest.approx(float(atomic_cv))
    if switch_cv is None:
        assert strategies['ensemble']['unconditional_mean_loss'] is None
        assert strategies['ensemble']['complete_dataset_probability'] == '1/4'
        assert strategies['ensemble']['conditional_mean_complete_dataset_loss'] == 0
    else:
        assert strategies['ensemble']['complete_dataset_probability'] == '1'
        assert strategies['ensemble']['unconditional_mean_loss'] == pytest.approx(float(switch_cv))


@pytest.mark.parametrize(
    ('size', 'switch_success', 'switch_risk_mass'),
    [(1, Fraction(1, 2), Fraction(1, 32)), (3, Fraction(1), Fraction(3, 64))],
)
def test_switch_trajectories_preserve_identification_failures_and_group_law(
    *,
    size: int,
    switch_success: Fraction,
    switch_risk_mass: Fraction,
):
    script = (
        Path(__file__).resolve().parents[3]
        / 'evaluation/experiments/switch_instability/calibrate.py'
    )
    result = runpy.run_path(str(script))['calibrate'](size)
    fitted = []
    failed = []
    risk_mass_from_fits = Fraction(0)
    assert len(result['datasets']) == 8
    for dataset in result['datasets']:
        baseline = dataset['selection']
        for fold, split in zip(baseline['folds'], baseline['splits']['folds'], strict=True):
            fit = fold['ensemble']['outer_fit']
            assert fit['training_groups'] == split['training_groups']
            assert {tuple(group) for group in fit['training_groups']}.isdisjoint(
                tuple(group) for group in split['test_groups']
            )
            boundary = fit['switch_suction_kpa']
            if boundary is None:
                failed.append(fit)
                assert fit['reason'] == 'unidentifiable_boundary'
                assert fit['loss_gap'] == pytest.approx(0)
            else:
                fitted.append(boundary)
                # Known middle-pressure mismatch loss is 1/8. Size weights
                # refer to the independent population, not the held-out row.
                mismatch_size = size if boundary == 5 else 1
                risk_mass_from_fits += Fraction(mismatch_size, 8 * (1 + size)) / 24
        assert len(dataset['draws']) == 10
        assert sum(Fraction(draw['probability']) for draw in dataset['draws']) == 1
        assert dataset['bootstrap_complete_probability']['atomic'] == '2/9'
        heterogeneous = len(set(dataset['group_states'])) > 1
        expected = '0' if size == 1 and heterogeneous else '2/9'
        assert dataset['bootstrap_complete_probability']['ensemble'] == expected
        for draw in dataset['draws']:
            copied_samples = draw['selection']['splits']['groups']
            assert len(copied_samples) == sum(count > 0 for count in draw['multiplicities'])
            for item in draw['sample_map']:
                assert item['source_id'] == item['group_id'][0]
    assert set(fitted) == {5, 10}
    assert Fraction(len(fitted), 24) == switch_success
    assert len(failed) == (12 if size == 1 else 0)
    assert risk_mass_from_fits == switch_risk_mass
    assert result['uncertainty_status'] == 'not_qualified_no_interval'
