import runpy
from fractions import Fraction
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ('size', 'missing', 'atomic_risk', 'ensemble_risk', 'atomic_loss', 'ensemble_loss'),
    [
        (1, False, Fraction(1, 2), Fraction(3, 8), Fraction(1, 2), Fraction(3, 8)),
        (3, False, Fraction(3, 8), Fraction(11, 32), Fraction(3, 7), Fraction(429, 1120)),
        (3, True, Fraction(3, 8), Fraction(25, 72), Fraction(9, 20), Fraction(91, 240)),
    ],
)
def test_exhaustive_group_ratio_diagnostic(
    *,
    size: int,
    missing: bool,
    atomic_risk: Fraction,
    ensemble_risk: Fraction,
    atomic_loss: Fraction,
    ensemble_loss: Fraction,
):
    script = Path(__file__).resolve().parents[3] / 'evaluation/experiments/group_ratio/calibrate.py'
    namespace = runpy.run_path(str(script))
    result = namespace['calibrate'](size, missing_high_sample=missing)
    # Risks follow the four equally probable two-group training states.
    # CV losses follow the eight equally probable three-group datasets.
    assert result['expected_equal_fold_conditional_risk'] == pytest.approx(
        {'atomic': float(atomic_risk), 'ensemble': float(ensemble_risk)}
    )
    assert result['expected_sample_weighted_outer_loss'] == pytest.approx(
        {'atomic': float(atomic_loss), 'ensemble': float(ensemble_loss)}
    )
    assert len(result['datasets']) == 8
    for dataset in result['datasets']:
        high_count = sum(dataset['group_states'])
        total = 3 + (size - 1) * high_count
        for strategy in dataset['strategies'].values():
            assert strategy['total_sample_count'] == total
            assert strategy['eligible_sample_count'] == total - (high_count if missing else 0)
        assert len(dataset['draws']) == 10
        assert sum(Fraction(draw['probability']) for draw in dataset['draws']) == 1
        assert dataset['bootstrap_complete_probability'] == '2/9'
        complete = [draw for draw in dataset['draws'] if draw['status'] == 'complete']
        assert len(complete) == 1
        assert complete[0]['multiplicities'] == (1, 1, 1)
        assert complete[0]['split_failure_reason'] is None
        assert {
            draw['split_failure_reason']
            for draw in dataset['draws']
            if draw['status'] != 'complete'
        } == {'insufficient_groups_for_requested_folds'}
        assert complete[0]['strategies'] == {
            kind: evidence['sample_weighted_outer_loss']
            for kind, evidence in dataset['strategies'].items()
        }
    assert result['uncertainty_status'] == 'not_qualified_no_interval'
