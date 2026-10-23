import json
import random
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Literal

import pytest
from _resampling_fixtures import resampling_result
from _selection_diagnostic_fixtures import diagnostic_result

from ptfkit_eval import (
    ConvexPairFit,
    EvaluationDocumentError,
    LearnedNestedSelection,
    SelectionResamplingPlan,
    load_retention_dataset,
    resample_selection_procedure,
    select_learned_retention_candidates,
)
from ptfkit_eval.documents import canonical_json


PLAN = SelectionResamplingPlan(protocol='learned', seed=91, n_resamples=2, minimum_groups=6)


class ControlledGroupDraws:
    """Replicate 0 doubles the two-sample group; replicate 1 retains all groups."""

    def __init__(self, seed: int) -> None:
        """Require the registered bootstrap seed and provide two exact draw sequences."""
        assert seed == 91
        self.draws = iter((0, 0, 1, 2, 3, 4, 5, 6, 0, 1, 2, 3, 4, 5, 6, 7))

    def randrange(self, stop: int) -> int:
        """Return original-group indices without affecting the selector's own RNG."""
        assert stop == 8
        return next(self.draws)


@pytest.mark.parametrize('grouping', ['source', 'profile'])
def test_group_multiplicity_retrains_weights_with_original_cluster_identity_and_sample_balance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, grouping: Literal['source', 'profile']
):
    result = resampling_result(tmp_path, grouping=grouping)
    monkeypatch.setattr('ptfkit_eval.resampling.Random', ControlledGroupDraws)
    resampled = resample_selection_procedure(result, plan=PLAN)
    assert resampled.status == 'completed'
    assert resampled.uncertainty_status == 'not_estimated_retraining_sensitivity_only'
    assert resampled.complete_replicate_count == 2
    first = resampled.replicates[0]
    assert isinstance(first.selection, LearnedNestedSelection)
    assert [entry.count for entry in first.multiplicities] == [2, 1, 1, 1, 1, 1, 1, 0]
    assert first.unique_group_count == 7
    assert len(first.samples) == 10  # Four high-target occurrences plus six single-sample groups.
    assert len(first.observations) == 20
    assert len(first.selection.splits.groups) == 7
    high = [sample for sample in first.samples if sample.source_id == 'source_0']
    assert len(high) == 4
    assert Counter(sample.original_sample_id for sample in high) == {'one': 2, 'two': 2}
    assert {sample.group_id for sample in high} == {
        ('source_0', 'profile_one' if grouping == 'profile' else '')
    }
    observed = Counter(observation.original_observation_id for observation in first.observations)
    assert observed['source_0_one_1'] == 2
    assert observed['source_7_one_1'] == 0
    refit_seen = False
    for fold in first.selection.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, ConvexPairFit)
        sources = {source for source, _ in fit.training_groups}
        # Independent oracle: group 0 contributes 2 samples * 2 occurrences;
        # every other retained group contributes exactly one low-target sample.
        expected = 4 / (4 + len(sources) - 1) if 'source_0' in sources else 0
        refit_seen |= 'source_0' in sources
        assert fit.left_weight == pytest.approx(expected)
        outer = first.selection.splits.folds[fold.fold_id]
        assert set(fit.training_groups).isdisjoint(outer.test_groups)
        for evidence in fold.ensemble.inner_scores[0].folds:
            assert isinstance(evidence.fit, ConvexPairFit)
            training = {source for source, _ in evidence.fit.training_groups}
            expected_inner = 4 / (4 + len(training) - 1) if 'source_0' in training else 0
            assert evidence.fit.left_weight == pytest.approx(expected_inner)
    assert refit_seen
    assert len(resampled.replicates[1].samples) == 9


def test_failed_low_diversity_draws_are_retained_without_retrying_or_inflating_groups(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    class OneGroupDraws:
        def __init__(self, seed: int) -> None:
            assert seed == 91
            self.calls = 0

        def randrange(self, stop: int) -> int:
            assert stop == 8
            self.calls += 1
            assert self.calls <= 16
            return 0

    result = resampling_result(tmp_path)
    monkeypatch.setattr('ptfkit_eval.resampling.Random', OneGroupDraws)
    resampled = resample_selection_procedure(result, plan=PLAN)
    assert len(resampled.replicates) == 2
    assert resampled.complete_replicate_count == 0
    for replicate in resampled.replicates:
        assert replicate.status == 'insufficient_evidence'
        assert replicate.unique_group_count == 1
        assert len(replicate.samples) == 16
        assert replicate.selection.splits.reason == 'insufficient_groups_for_requested_folds'
        assert replicate.selection.folds == ()
        assert replicate.selection.splits.groups[0].group_id == ('source_0', '')


def test_original_source_fallback_cannot_flip_to_profiles_when_missing_group_is_omitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    class OmitMissingProfileGroup:
        def __init__(self, seed: int) -> None:
            assert seed == 91
            self.draws = iter((1, 1, 2, 3, 4, 5, 6, 7) * 2)

        def randrange(self, stop: int) -> int:
            assert stop == 8
            return next(self.draws)

    result = resampling_result(tmp_path, grouping='profile', source_fallback=True)
    assert result.learned_selection is not None
    assert result.learned_selection.splits.effective_grouping == 'source'
    monkeypatch.setattr('ptfkit_eval.resampling.Random', OmitMissingProfileGroup)
    resampled = resample_selection_procedure(result, plan=PLAN)
    assert resampled.grouping == 'source'
    assert all(
        replicate.selection.splits.effective_grouping == 'source'
        for replicate in resampled.replicates
    )
    assert all(
        group.group_id[1] == ''
        for replicate in resampled.replicates
        for group in replicate.selection.splits.groups
    )


def test_seed_and_record_order_are_reproducible_without_global_random_state_changes(tmp_path: Path):
    result = resampling_result(tmp_path)
    state = random.getstate()
    first = resample_selection_procedure(result, plan=PLAN)
    document = json.loads(canonical_json(result.plan.dataset.document))
    document['samples'].reverse()
    document['observations'].reverse()
    reordered = replace(
        result,
        plan=replace(result.plan, dataset=load_retention_dataset(document)),
        points=result.points[::-1],
    )
    second = resample_selection_procedure(reordered, plan=PLAN)
    assert first.replicates == second.replicates
    assert random.getstate() == state


def test_fixed_selection_uses_the_same_draw_law_and_keeps_registered_ensembles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    class IdentityDraws:
        def __init__(self, seed: int) -> None:
            assert seed == 91
            self.draws = iter(tuple(range(6)) * 2)

        def randrange(self, stop: int) -> int:
            assert stop == 6
            return next(self.draws)

    result = diagnostic_result(tmp_path)
    monkeypatch.setattr('ptfkit_eval.resampling.Random', IdentityDraws)
    output = resample_selection_procedure(result, plan=replace(PLAN, protocol='fixed'))
    assert output.complete_replicate_count == 2
    for replicate in output.replicates:
        assert replicate.selection.protocols[0].mean_outer_loss == pytest.approx(1 / 64)
        assert replicate.selection.protocols[1].mean_outer_loss == pytest.approx(1 / 16)


def test_original_group_gate_reports_insufficient_evidence_before_any_draw(tmp_path: Path):
    result = resample_selection_procedure(
        resampling_result(tmp_path), plan=replace(PLAN, minimum_groups=99)
    )
    assert result.reason == 'too_few_original_groups'
    assert result.replicates == ()


def test_targetless_sample_occurrences_remain_in_retraining_coverage_denominators(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    result = resampling_result(tmp_path)
    assert result.learned_selection is not None
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    dataset['observations'] = [
        row for row in dataset['observations'] if row['source_id'] != 'source_7'
    ]
    result = replace(
        result,
        plan=replace(result.plan, dataset=load_retention_dataset(dataset)),
        points=tuple(point for point in result.points if point.source_id != 'source_7'),
    )
    assert result.learned_selection is not None
    policy = result.learned_selection.plan
    policy = replace(
        policy,
        fixed=replace(policy.fixed, minimum_coverage=0.5),
        ensembles=tuple(
            replace(ensemble, minimum_training_groups=1) for ensemble in policy.ensembles
        ),
    )
    result = replace(
        result, learned_selection=select_learned_retention_candidates(result, plan=policy)
    )
    monkeypatch.setattr('ptfkit_eval.resampling.Random', ControlledGroupDraws)
    output = resample_selection_procedure(result, plan=PLAN)
    second = output.replicates[1]
    assert len(second.samples) == 9
    assert any(sample.source_id == 'source_7' for sample in second.samples)
    assert all(strategy.total_sample_count == 9 for strategy in second.selection.protocols)
    assert all(strategy.eligible_sample_count == 8 for strategy in second.selection.protocols)


def test_mismatched_original_group_identity_is_rejected_before_materializing_draws(tmp_path: Path):
    result = resampling_result(tmp_path)
    assert result.learned_selection is not None
    selected = result.learned_selection
    bad = replace(selected.splits.groups[0], group_id=('invented_source', ''))
    result = replace(
        result,
        learned_selection=replace(
            selected, splits=replace(selected.splits, groups=(bad, *selected.splits.groups[1:]))
        ),
    )
    with pytest.raises(EvaluationDocumentError, match='preserve original source/profile'):
        resample_selection_procedure(result, plan=PLAN)


@pytest.mark.parametrize(
    'changes',
    [
        {'protocol': 'unknown'},
        {'seed': True},
        {'n_resamples': 1},
        {'minimum_groups': 1},
    ],
)
def test_invalid_resampling_contracts_fail(changes: dict[str, object]):
    with pytest.raises(EvaluationDocumentError):
        replace(PLAN, **changes)
