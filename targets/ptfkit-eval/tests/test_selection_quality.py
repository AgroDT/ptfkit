import math
from dataclasses import replace
from pathlib import Path

import pytest
from _selection_diagnostic_fixtures import diagnostic_result

from ptfkit_eval import (
    EvaluationDocumentError,
    RetentionComparison,
    RetentionQualityError,
    RetentionRunResult,
    diagnose_selection_curves,
    selection_prediction_frames,
)


def _outer_predictions(
    result: RetentionRunResult, predictions: tuple[RetentionComparison, ...]
) -> RetentionRunResult:
    selection = result.learned_selection
    assert selection is not None
    fold = selection.folds[0]
    changed = replace(fold, ensemble=replace(fold.ensemble, predictions=predictions))
    return replace(
        result, learned_selection=replace(selection, folds=(changed, *selection.folds[1:]))
    )


def test_frames_keep_inner_outer_protocol_and_candidate_scopes(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    frames = selection_prediction_frames(result)
    assert len(frames) == 48
    for protocol in ('fixed', 'learned'):
        for strategy in ('atomic', 'ensemble'):
            outer = [
                frame
                for frame in frames
                if frame.protocol == protocol
                and frame.strategy == strategy
                and frame.inner_fold_id is None
            ]
            assert len(outer) == 3
            assert sorted(sample for frame in outer for sample in frame.samples) == [
                (f'source_{index}', 'one') for index in range(6)
            ]
    for frame in frames:
        assert set(frame.training_groups).isdisjoint(frame.held_out_groups)
        assert frame.status == 'assessed'
        assert len(frame.predictions) == 6
        expected = 0.625 if frame.candidate_id in ('sand_a', 'trained') else 0.75
        assert [point.predicted for point in frame.predictions] == [expected] * 6


def test_physical_diagnostics_keep_every_holdout_curve_separate(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    quality = diagnose_selection_curves(result)
    assert len(quality) == 96
    assert all(curve.status == 'diagnosed' for curve in quality)
    assert all(curve.quality.point_count == 3 for curve in quality)
    assert all(curve.quality.diagnostics == () for curve in quality)
    assert all(
        (curve.quality.minimum_suction_kpa, curve.quality.maximum_suction_kpa) == (1, 100)
        for curve in quality
    )
    assert sum(curve.partition == 'outer_test' for curve in quality) == 24
    assert result.selection_quality == ()  # The diagnostic API does not mutate a run.


def test_unphysical_nonmonotone_predictions_are_reported_without_reading_targets(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    assert result.learned_selection is not None
    original = result.learned_selection.folds[0].ensemble.predictions
    key = original[0].source_id, original[0].sample_id
    values: dict[float, float] = {1: 0.25, 10: 1.25, 100: -0.125}
    changed = tuple(
        replace(point, predicted=values[point.suction_kpa], observed=math.nan)
        if (point.source_id, point.sample_id) == key
        else point
        for point in original
    )
    altered = _outer_predictions(result, changed)
    quality = diagnose_selection_curves(altered)
    selected = [
        curve
        for curve in quality
        if curve.protocol == 'learned'
        and curve.strategy == 'ensemble'
        and curve.outer_fold_id == 0
        and curve.inner_fold_id is None
        and (curve.source_id, curve.sample_id) == key
    ]
    assert len(selected) == 1
    findings = selected[0].quality.diagnostics
    assert [finding.code for finding in findings] == [
        'water_outside_physical_bounds',
        'water_outside_physical_bounds',
        'increasing_water_with_suction',
    ]
    assert [finding.points[0].water_content for finding in findings[:2]] == [1.25, -0.125]
    assert [point.suction_kpa for point in findings[2].points] == [1, 10]
    assert altered.learned_selection is not None
    assert altered.learned_selection.folds[0].ensemble.predictions == changed
    assert (
        altered.learned_selection.folds[0].ensemble.outer_fit
        == result.learned_selection.folds[0].ensemble.outer_fit
    )


def test_missing_targets_are_no_prediction_records_not_empty_valid_curves(tmp_path: Path):
    result = diagnostic_result(tmp_path, missing_target=True)
    quality = diagnose_selection_curves(result)
    missing = [curve for curve in quality if curve.source_id == 'source_5']
    assert len(missing) == 16
    assert all(curve.status == 'no_predictions' for curve in missing)
    assert all(curve.quality.minimum_suction_kpa is None for curve in missing)
    assert all(curve.quality.diagnostics == () for curve in missing)
    assert all(curve.status == 'diagnosed' for curve in quality if curve.source_id != 'source_5')


@pytest.mark.parametrize('change', ['training_sample', 'duplicate_pressure', 'wrong_fit_roles'])
def test_invalid_heldout_prediction_provenance_is_rejected(tmp_path: Path, change: str):
    result = diagnostic_result(tmp_path)
    assert result.learned_selection is not None
    fold = result.learned_selection.folds[0]
    assert fold.ensemble.outer_fit is not None
    predictions = fold.ensemble.predictions
    if change == 'training_sample':
        training_source = fold.ensemble.outer_fit.training_groups[0][0]
        result = _outer_predictions(
            result, (replace(predictions[0], source_id=training_source), *predictions[1:])
        )
    elif change == 'duplicate_pressure':
        result = _outer_predictions(result, (*predictions, predictions[0]))
    else:
        bad_fit = replace(fold.ensemble.outer_fit, training_groups=(('undeclared', ''),))
        altered = replace(fold, ensemble=replace(fold.ensemble, outer_fit=bad_fit))
        result = replace(
            result,
            learned_selection=replace(
                result.learned_selection, folds=(altered, *result.learned_selection.folds[1:])
            ),
        )
    with pytest.raises(EvaluationDocumentError):
        diagnose_selection_curves(result)


@pytest.mark.parametrize('tolerance', [-1, math.inf, True])
def test_invalid_tolerance_is_rejected_even_without_selection_frames(
    tmp_path: Path, tolerance: float
):
    result = replace(diagnostic_result(tmp_path), selection=None, learned_selection=None)
    with pytest.raises(RetentionQualityError):
        diagnose_selection_curves(result, monotonicity_tolerance=tolerance)
