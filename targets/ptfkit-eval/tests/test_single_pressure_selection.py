"""Protect one-pressure selection, exact coordinates and training-only ensemble weights."""

import hashlib
import json
import math
import runpy
from pathlib import Path

import pytest

from ptfkit_eval import (
    ConvexPairFit,
    EvaluationDocumentError,
    LogPressureLossPlan,
    RetentionComparison,
    RetentionLossError,
    SinglePressureLossPlan,
    evaluate_log_pressure_loss,
    evaluate_selection_loss,
    execute_retention_run,
    load_retention_run_plan,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


def _build(directory: Path) -> Path:
    root = Path(__file__).resolve().parents[3]
    namespace = runpy.run_path(str(root / 'evaluation/examples/synthetic_single_pressure/build.py'))
    return namespace['build'](directory)


@pytest.mark.parametrize('pressure', [0, 33])
def test_point_loss_is_squared_error_at_the_exact_declared_pressure(pressure: float):
    comparisons = [
        RetentionComparison('study', 'one', pressure, 0.2, 0.3),
        RetentionComparison('study', 'two', math.nextafter(pressure, math.inf), 0.2, 0.9),
    ]
    plan = SinglePressureLossPlan(suction_kpa=pressure)
    losses = evaluate_selection_loss(comparisons, plan=plan)
    assert losses[0].loss == pytest.approx(0.01)
    assert losses[0].point_count == 1
    assert losses[1].loss is None
    assert losses[1].point_count == 0
    with pytest.raises(RetentionLossError, match='log-pressure'):
        evaluate_log_pressure_loss(comparisons, plan=plan)


@pytest.mark.parametrize('pressure', [-1, math.nan, math.inf, True])
def test_invalid_point_domains_are_rejected(pressure: float):
    with pytest.raises(RetentionLossError, match='nonnegative'):
        SinglePressureLossPlan(suction_kpa=pressure)


def test_log_integral_still_rejects_equal_pressure_bounds():
    with pytest.raises(RetentionLossError, match='ordered'):
        LogPressureLossPlan(lower_suction_kpa=33, upper_suction_kpa=33)


def test_native_single_pressure_nested_selection_fits_and_replays(tmp_path: Path):
    path = _build(tmp_path / 'input')
    result = execute_retention_run(load_retention_run_plan(path))
    assert result.selection is not None
    assert result.selection.status == 'computed'
    assert all(f.atomic.choice.candidate_id == 'slr3' for f in result.selection.folds)
    learned = result.learned_selection
    assert learned is not None
    assert learned.status == 'computed'
    assert len(learned.folds) == 3
    assert len(result.points) == 12
    for fold in learned.folds:
        assert fold.atomic.candidate_id == 'slr3'
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, ConvexPairFit)
        assert fit.plan.method == 'constant_convex_pair_single_pressure_v1'
        # At 33 kPa the independent target is .25*.17577 + .75*.1848.
        assert fit.left_weight == pytest.approx(0.25, abs=2e-13)
        assert fold.ensemble.assessment is not None
        assert fold.ensemble.assessment.mean_loss == pytest.approx(0, abs=1e-28)
    first = write_retention_run(result, tmp_path / 'first')
    second = write_retention_run(
        execute_retention_run(load_retention_run_plan(path)), tmp_path / 'second'
    )
    assert (first / 'learned-selection.json').read_bytes() == (
        second / 'learned-selection.json'
    ).read_bytes()


def test_outer_target_changes_do_not_change_training_choices_or_weights(tmp_path: Path):
    path = _build(tmp_path / 'input')
    baseline = execute_retention_run(load_retention_run_plan(path)).learned_selection
    assert baseline is not None
    held_out = {g[1] for g in baseline.splits.folds[0].test_groups}
    dataset = json.loads((path.parent / 'dataset.json').read_bytes())
    for point in dataset['observations']:
        if point['sample_id'] in held_out:
            point['value'] = 0.17577
    raw = canonical_json(dataset)
    (path.parent / 'dataset.json').write_bytes(raw)
    run = json.loads(path.read_bytes())
    run['dataset']['sha256'] = hashlib.sha256(raw).hexdigest()
    path.write_bytes(canonical_json(run))
    changed = execute_retention_run(load_retention_run_plan(path)).learned_selection
    assert changed is not None
    before, after = baseline.folds[0], changed.folds[0]
    assert before.atomic.inner_scores == after.atomic.inner_scores
    assert before.atomic.candidate_id == after.atomic.candidate_id == 'slr3'
    assert before.ensemble.outer_fit == after.ensemble.outer_fit
    assert after.ensemble.assessment is not None
    assert after.ensemble.assessment.mean_loss == pytest.approx(0.0067725**2)


def test_point_learning_requires_the_explicit_matching_training_method(tmp_path: Path):
    path = _build(tmp_path / 'input')
    run = json.loads(path.read_bytes())
    run['learned_selection']['ensembles'][0]['method'] = 'constant_convex_pair_log_pressure_v1'
    path.write_bytes(canonical_json(run))
    with pytest.raises(EvaluationDocumentError, match='method must match'):
        load_retention_run_plan(path)


def test_unqualified_uncertainty_protocols_are_not_enabled_by_the_new_loss(tmp_path: Path):
    path = _build(tmp_path / 'input')
    run = json.loads(path.read_bytes())
    run['approximations'] = []
    path.write_bytes(canonical_json(run))
    with pytest.raises(EvaluationDocumentError, match='additional uncertainty protocols'):
        load_retention_run_plan(path)
