"""Hand-calculated contracts for full-ledger scoring and missing-member ensembles."""

import math

import pytest
from evaluation.experiments.meta_v3_3.pointwise_wrc import (
    align_predictions,
    held_out_ensembles,
    nominations,
    score,
)


def point(source: str, sample: str, pressure: float, model: str, error: float) -> dict:
    return {
        'basis': 'volumetric_water_content',
        'source_id': source,
        'sample_id': sample,
        'pressure_kpa': pressure,
        'observed': 0.0,
        'predicted': error,
        'function': model,
    }


def test_equal_sample_weight_precedes_square_root_and_coverage_uses_full_ledger():
    points = [point('A', 'a', 1, 'm', 0), point('A', 'a', 2, 'm', 2), point('B', 'a', 1, 'm', 4)]
    ledger = [*points, point('C', 'a', 1, 'm', 0)]
    result = score(points, ledger)
    assert result['sample_balanced_rmse'] == pytest.approx(3)
    assert result['rmse'] == pytest.approx(math.sqrt(20 / 3))
    assert result['sample_balanced_mae'] == pytest.approx(2.5)
    assert result['sample_balanced_bias'] == pytest.approx(2.5)
    assert result['mae'] == pytest.approx(2)
    assert result['point_coverage'] == 0.75
    assert result['sample_coverage'] == pytest.approx(2 / 3)


def test_held_out_targets_do_not_select_members_and_one_member_is_retained():
    points = [point('train', 'a', 1, f'm{i}', float(i)) for i in range(6)]
    points += [point('test', 'b', 1, 'm0', 10), point('test', 'b', 1, 'm5', 0)]
    ledger = [points[0], points[-1]]
    predictions, folds = held_out_ensembles(points, ledger)
    fold = next(f for f in folds if f['held_out_source'] == 'test')
    assert fold['selected']['top_3'] == ['m0', 'm1', 'm2']
    assert fold['selected']['top_5'] == ['m0', 'm1', 'm2', 'm3', 'm4']
    result = next(
        p for p in predictions if p['source_id'] == 'test' and p['function'] == 'ensemble:top_3'
    )
    assert result['predicted'] == 10
    assert result['n_members'] == 1
    assert result['ensemble_members'] == ['m0']
    altered = [{**p, 'observed': 100} if p['source_id'] == 'test' else p for p in points]
    _, altered_folds = held_out_ensembles(altered, ledger)
    assert (
        next(f for f in altered_folds if f['held_out_source'] == 'test')['selected']
        == fold['selected']
    )


def test_mean_and_median_use_only_available_training_eligible_members():
    points = [point('train', 'a', 1, f'm{i}', float(i)) for i in range(4)]
    points += [point('test', 'b', 1, f'm{i}', value) for i, value in enumerate((1, 2, 12))]
    points += [point('test', 'b', 1, 'unseen_in_training', 1000)]
    results, _ = held_out_ensembles(points, [points[0], points[-1]])
    held = {p['function']: p for p in results if p['source_id'] == 'test'}
    assert held['ensemble:median']['predicted'] == 2
    assert held['ensemble:all_available_mean']['predicted'] == 5
    assert held['ensemble:all_available_mean']['n_members'] == 3


def test_alignment_rejects_interpolated_targets_and_duplicates():
    p = point('A', 'a', 1, 'm', 0.2)
    with pytest.raises(ValueError, match='Interpolated targets'):
        align_predictions([{**p, 'target_reconstruction': {'method': 'interpolation'}}], [p])
    with pytest.raises(ValueError, match='Duplicate model'):
        align_predictions([p, p], [p])
    with pytest.raises(ValueError, match='no experimental'):
        align_predictions([{**p, 'pressure_kpa': 2}], [p])
    assert len(align_predictions([p, {**p, 'water_conditioned': True}], [p])) == 1


def test_pareto_and_thresholds_preserve_accuracy_coverage_tradeoff():
    rows = [
        {'model': 'accurate', 'sample_balanced_rmse': 0.01, 'point_coverage': 0.1},
        {'model': 'wide', 'sample_balanced_rmse': 0.1, 'point_coverage': 0.6},
        {'model': 'dominated', 'sample_balanced_rmse': 0.2, 'point_coverage': 0.5},
    ]
    result = nominations(rows)
    assert result['best_accuracy']['model'] == 'accurate'
    assert result['pareto'] == ['accurate', 'wide']
    assert result['high_coverage']['25']['model'] == 'wide'
    assert result['high_coverage']['50']['model'] == 'wide'
    assert result['high_coverage']['75'] is None
    assert result['compromise']['model'] == 'wide'
