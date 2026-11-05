import json
from dataclasses import replace
from pathlib import Path

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    NestedDomainPlan,
    RetentionRunPlan,
    diagnose_learned_applicability,
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


EXAMPLE = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_retention/run.json'


def _plan() -> RetentionRunPlan:
    plan = load_retention_run_plan(EXAMPLE)
    return replace(plan, approximations=(), bootstrap=replace(plan.bootstrap, n_resamples=16))


def test_learned_inner_and_locked_outer_domains_use_training_predictors_only():
    result = execute_retention_run(_plan())
    learned, assessment = result.learned_selection, result.learned_applicability
    assert learned is not None
    assert assessment is not None
    assert assessment.status == 'computed'
    assert len(assessment.folds) == 30
    outer_frames = [fold for fold in assessment.folds if fold.inner_fold_id is None]
    assert len(outer_frames) == 6
    assert all(fold.selected_by_inner_validation for fold in outer_frames)
    for frame in assessment.folds:
        outer = learned.splits.folds[frame.outer_fold_id]
        training = (
            outer.training_groups
            if frame.inner_fold_id is None
            else outer.inner[frame.inner_fold_id].training_groups
        )
        assert frame.domain.plan.training_groups == training
        assert set(training).isdisjoint(frame.domain.plan.test_groups)
        if frame.domain.plan.candidate_id != 'trained_convex_pair':
            continue
        left, right = frame.domain.members
        assert left.member_id == 'left:clapp'
        assert right.member_id == 'right:vereecken'
        assert left.bounds[0].categories == ('sandy_loam',)
        # The example declares sand = 55 + source index + sample index.
        source_indices = [ord(source[-1]) - ord('a') for source, _ in training]
        lower, upper = 55 + min(source_indices), 56 + max(source_indices)
        sand = next(bound for bound in right.bounds if bound.input == 'sand')
        assert (sand.lower, sand.upper) == (lower, upper)
        for sample in frame.samples:
            value = 55 + ord(sample.source_id[-1]) - ord('a') + int(sample.sample_id[-1]) - 1
            assert sample.status == ('inside' if lower <= value <= upper else 'outside')


def test_domain_gate_cannot_change_training_weights_or_locked_choices():
    plan = _plan()
    assert plan.learned_selection is not None
    baseline = execute_retention_run(plan)
    changed = execute_retention_run(
        replace(
            plan,
            learned_selection=replace(
                plan.learned_selection,
                empirical_domains=NestedDomainPlan(minimum_training_groups=99),
            ),
        )
    )
    assert baseline.learned_selection is not None
    assert changed.learned_selection is not None
    assert changed.learned_selection.folds == baseline.learned_selection.folds
    assert changed.learned_selection.protocols == baseline.learned_selection.protocols
    assert changed.learned_applicability is not None
    assert all(
        sample.status == 'insufficient_evidence'
        for fold in changed.learned_applicability.folds
        for sample in fold.samples
    )


def test_outer_predictor_shift_cannot_expand_its_training_bounds():
    plan = _plan()
    before = execute_retention_run(plan)
    assert before.learned_selection is not None
    held_out = {source for source, _ in before.learned_selection.splits.folds[0].test_groups}
    dataset = json.loads(canonical_json(plan.dataset.document))
    for sample in dataset['samples']:
        if sample['source_id'] in held_out:
            for feature in sample['features']:
                if feature['id'] == 'sand':
                    feature['value'] = 80
    after = execute_retention_run(replace(plan, dataset=load_retention_dataset(dataset)))
    assert after.learned_selection is not None
    assert (
        before.learned_selection.folds[0].ensemble.outer_fit
        == after.learned_selection.folds[0].ensemble.outer_fit
    )
    assert before.learned_applicability is not None
    assert after.learned_applicability is not None
    old_frames = [
        frame
        for frame in before.learned_applicability.folds
        if frame.outer_fold_id == 0 and frame.partition == 'outer_test'
    ]
    new_frames = [
        frame
        for frame in after.learned_applicability.folds
        if frame.outer_fold_id == 0 and frame.partition == 'outer_test'
    ]
    assert len(old_frames) == len(new_frames) == 2
    for old, new in zip(old_frames, new_frames, strict=True):
        assert [member.bounds for member in old.domain.members] == [
            member.bounds for member in new.domain.members
        ]
        assert all(sample.status == 'outside' for sample in new.samples)


def test_observations_cannot_change_domain_labels_or_bounds():
    result = execute_retention_run(_plan())
    assert result.learned_applicability is not None
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    dataset['observations'] = []
    changed = replace(result, plan=replace(result.plan, dataset=load_retention_dataset(dataset)))
    assert (
        diagnose_learned_applicability(changed, policy=NestedDomainPlan(minimum_training_groups=2))
        == result.learned_applicability
    )


def test_learned_domain_artifact_integrity_and_replay(tmp_path: Path):
    plan = _plan()
    result = execute_retention_run(plan)
    output = write_retention_run(result, tmp_path / 'run')
    assert 'Learned selection input-domain diagnostics' in read_retention_run_report(output)
    saved = json.loads((output / 'learned-applicability.json').read_text('utf-8'))
    assert len(saved['folds']) == 30
    replay_plan = replace(
        load_retention_run_plan(output / 'run-plan.json'),
        approximations=(),
        bootstrap=plan.bootstrap,
    )
    replay = execute_retention_run(replay_plan)
    assert replay.learned_applicability == result.learned_applicability


def test_missing_learned_selection_is_rejected():
    result = execute_retention_run(_plan())
    with pytest.raises(EvaluationDocumentError, match='learned selection'):
        diagnose_learned_applicability(
            replace(result, learned_selection=None),
            policy=NestedDomainPlan(minimum_training_groups=2),
        )
