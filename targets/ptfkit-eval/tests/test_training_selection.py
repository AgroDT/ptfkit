from dataclasses import replace
from pathlib import Path
from typing import Literal

import pytest

from ptfkit_eval import (
    ConvexPairFit,
    ConvexPairPlan,
    EvaluationDocumentError,
    FixedSelectionPlan,
    GroupedSample,
    HardSwitchGridFit,
    HardSwitchGridPlan,
    IndependentTrainingRiskPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    allocate_independent_training_blocks,
    assess_independent_forecast_training,
    assess_independent_selection_training,
    execute_retention_run,
    load_retention_run_plan,
    select_grouped_forecast_holdout,
)
from ptfkit_eval.folds import GroupValidationError


LOSS = LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100)
SELECTOR = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('one', 'zero'),
        loss=LOSS,
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
    ),
    ensembles=(
        ConvexPairPlan(
            id='pair',
            left_candidate_id='one',
            right_candidate_id='zero',
            minimum_training_groups=1,
            minimum_mean_squared_contrast=1e-12,
        ),
    ),
)
BOUNDS = IndependentTrainingRiskPlan(
    population_id='controlled_block_fixture',
    learner_id='whole_constant_pair_selector',
    grouping='source',
    loss=LOSS,
    maximum_sample_loss=1,
    minimum_group_size=1,
    maximum_group_size=3,
    training_groups_per_block=4,
    test_groups_per_block=2,
    n_blocks=2,
)
KINDS: dict[str, Literal['atomic', 'ensemble']] = {'one': 'atomic', 'zero': 'atomic'}
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')


def fixture():
    # The allocation fixes roles before any target exists. Unequal training
    # group sizes in block 0 distinguish sample weighting from group weighting.
    initial = tuple(GroupedSample(f'g{i}', 's0', 'profile') for i in range(12))
    allocated = allocate_independent_training_blocks(initial, plan=BOUNDS, seed=71)
    sizes = {}
    targets = {}
    for index, block in enumerate(allocated.blocks):
        for position, group in enumerate(block.training_groups):
            sizes[group.group_id[0]] = 3 if index == 0 and position % 2 else 1
            targets[group.group_id[0]] = float(position % 2) if index == 0 else 0.25
        for group in block.test_groups:
            sizes[group.group_id[0]] = 1
            targets[group.group_id[0]] = float(index)
    samples = tuple(
        GroupedSample(source, f's{i}', 'profile')
        for source in sorted(sizes)
        for i in range(sizes[source])
    )
    candidates = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id='controlled',
            protocol_id='constant_forecasts',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(
                    s.source_id, s.sample_id, pressure, targets[s.source_id], value, s.profile_id
                )
                for s in samples
                for pressure in (1, 100)
            ),
        )
        for identifier, value in (('one', 1.0), ('zero', 0.0))
    )
    return samples, candidates


def assess(
    samples: tuple[GroupedSample, ...],
    candidates: tuple[RetentionCandidateComparisons, ...],
    *,
    selector: LearnedSelectionPlan = SELECTOR,
    bounds: IndependentTrainingRiskPlan = BOUNDS,
    strategy: Literal['atomic', 'ensemble'] = 'ensemble',
):
    return assess_independent_forecast_training(
        candidates,
        samples=samples,
        candidate_kinds=KINDS,
        selection_plan=selector,
        bounds=bounds,
        strategy=strategy,
        seed=71,
    )


def test_whole_selector_refits_each_block_with_sample_weighted_independent_oracle():
    samples, candidates = fixture()
    result = assess(samples, candidates)
    assert result.samples == samples
    assert result.candidates == candidates
    assert result.bound.status == 'computed'
    assert result.bound.training_failure_count == 0
    assert result.bound.test_sample_count == 4
    for index, block in enumerate(result.blocks):
        outer = block.selection.folds[0]
        fitted = outer.ensemble.outer_fit
        assert isinstance(fitted, ConvexPairFit)
        # Block 0 has six ones and two zeros; block 1 has four quarter values.
        expected = 0.75 if index == 0 else 0.25
        assert fitted.left_weight == pytest.approx(expected)
        assert set(fitted.training_groups) == {g.group_id for g in block.roles.training_groups}
        assert outer.atomic.candidate_id == ('one' if index == 0 else 'zero')
        assert {p.predicted for p in outer.ensemble.predictions} == {expected}
        assert [g.sample_losses for g in block.evidence.test_groups] == [(9 / 16,), (9 / 16,)]
        assert block.evidence.training_failure_reason is None
        assert block.selection.splits.method == 'explicit_group_holdout_inner_round_robin_v1'
        assert all(p.total_sample_count == 2 for p in block.selection.protocols)
        training = {g.group_id for g in block.roles.training_groups}
        for inner in block.selection.splits.folds[0].inner:
            assert set(inner.training_groups).isdisjoint(inner.validation_groups)
            assert set(inner.training_groups) | set(inner.validation_groups) == training
    assert result.bound.moments is not None
    # Four single-sample test groups, H=2, M=3: normalized size=1/3,
    # successful loss mass=(9/16)/3=3/16. Finite ratio is 9/16.
    assert result.bound.moments.normalized_mean_test_group_size == pytest.approx(1 / 3)
    assert result.bound.moments.normalized_mean_successful_loss_sum == pytest.approx(3 / 16)
    assert result.bound.unconditional_model_risk_interval is None


def test_test_targets_cannot_change_inner_scores_choices_or_refitted_parameters():
    samples, candidates = fixture()
    before = assess(samples, candidates)
    test = {key for b in before.blocks for g in b.roles.test_groups for key in g.samples}
    changed = tuple(
        replace(
            c,
            comparisons=tuple(
                replace(p, observed=1 - p.observed) if (p.source_id, p.sample_id) in test else p
                for p in c.comparisons
            ),
        )
        for c in candidates
    )
    after = assess(samples, changed)
    assert after.selector_sha256 == before.selector_sha256
    for left, right in zip(before.blocks, after.blocks, strict=True):
        for strategy in ('atomic', 'ensemble'):
            a, b = (
                getattr(left.selection.folds[0], strategy),
                getattr(right.selection.folds[0], strategy),
            )
            assert a.candidate_id == b.candidate_id
            assert a.inner_scores == b.inner_scores
            assert a.outer_fit == b.outer_fit
            assert [p.predicted for p in a.predictions] == [p.predicted for p in b.predictions]
        assert left.evidence.test_groups != right.evidence.test_groups


def test_hard_switch_boundary_is_retrained_per_block_on_its_own_training_curves():
    samples = tuple(GroupedSample(f'g{i}', 's0') for i in range(12))
    allocation = allocate_independent_training_blocks(samples, plan=BOUNDS, seed=71)
    curves = {}
    for index, block in enumerate(allocation.blocks):
        train = (0.75, 0.75, 0.25) if index == 0 else (0.75, 0.25, 0.25)
        test = (0.75, 0.25, 0.25) if index == 0 else (0.75, 0.75, 0.25)
        curves.update({g.group_id[0]: train for g in block.training_groups})
        curves.update({g.group_id[0]: test for g in block.test_groups})
    candidates = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id='controlled',
            protocol_id='switch_forecasts',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(s.source_id, s.sample_id, pressure, observed, value)
                for s in samples
                for pressure, observed in zip((1, 10, 100), curves[s.source_id], strict=True)
            ),
        )
        for identifier, value in (('one', 0.75), ('zero', 0.25))
    )
    selector = replace(
        SELECTOR,
        method='nested_two_curve_selection_v1',
        ensembles=(
            HardSwitchGridPlan(
                id='switch',
                left_candidate_id='one',
                right_candidate_id='zero',
                boundary_grid_kpa=(5, 10),
                boundary_member='left',
                minimum_training_groups=1,
                minimum_loss_gap=1e-12,
            ),
        ),
    )
    result = assess(samples, candidates, selector=selector)
    assert result.bound.status == 'computed'
    for index, block in enumerate(result.blocks):
        fit = block.selection.folds[0].ensemble.outer_fit
        assert isinstance(fit, HardSwitchGridFit)
        assert fit.switch_suction_kpa == (10 if index == 0 else 5)
        assert fit.training_loss == 0
        assert fit.loss_gap == pytest.approx(1 / 8)
        assert all(group.sample_losses == (1 / 8,) for group in block.evidence.test_groups)


def test_failed_training_is_retained_without_using_atomic_success_or_zero_model_losses():
    samples, candidates = fixture()
    impossible = replace(
        SELECTOR,
        ensembles=(
            replace(
                SELECTOR.ensembles[0],
                minimum_mean_squared_contrast=2,
            ),
        ),
    )
    result = assess(samples, candidates, selector=impossible)
    assert len(result.blocks) == 2
    assert result.bound.status == 'computed'
    assert result.bound.training_failure_count == 2
    assert result.bound.test_sample_count == 4
    assert result.bound.successful_training_mean_risk_interval is None
    assert result.bound.risk_mass_on_success_interval is not None
    assert result.bound.risk_mass_on_success_interval.upper > 0
    for block in result.blocks:
        assert block.selection.status == 'computed'  # Atomic success cannot rescue the ensemble.
        assert block.evidence.training_failure_reason == 'insufficient_inner_evidence'
        assert all(group.sample_losses is None for group in block.evidence.test_groups)
        assert block.selection.folds[0].ensemble.inner_scores[0].folds


def test_missing_successful_test_prediction_suppresses_inference_without_training_failure():
    samples, candidates = fixture()
    before = assess(samples, candidates)
    missing = before.blocks[0].roles.test_groups[0].samples[0]
    partial = tuple(
        replace(
            c, comparisons=tuple(p for p in c.comparisons if (p.source_id, p.sample_id) != missing)
        )
        for c in candidates
    )
    after = assess(samples, partial)
    assert after.bound.reason == 'incomplete_successful_block_test_losses'
    assert after.bound.training_failure_count == 0
    assert after.bound.moments is None
    assert len(after.blocks) == 2
    assert after.blocks[0].evidence.test_groups[0].sample_losses is None
    a, b = before.blocks[0].selection.folds[0], after.blocks[0].selection.folds[0]
    assert a.ensemble.outer_fit == b.ensemble.outer_fit
    assert a.ensemble.inner_scores == b.ensemble.inner_scores


@pytest.mark.parametrize('change', ['loss', 'grouping', 'unknown_row', 'partial_group', 'overlap'])
def test_invalid_inputs_are_rejected_before_any_records_can_disappear(change: str):
    samples, candidates = fixture()
    if change in ('loss', 'grouping', 'unknown_row'):
        bounds = BOUNDS
        if change == 'loss':
            bounds = replace(bounds, loss=replace(LOSS, upper_suction_kpa=10))
        elif change == 'grouping':
            bounds = replace(bounds, grouping='profile')
        else:
            candidates = (
                replace(
                    candidates[0],
                    comparisons=(
                        *candidates[0].comparisons,
                        replace(candidates[0].comparisons[0], source_id='unknown'),
                    ),
                ),
                candidates[1],
            )
        with pytest.raises(EvaluationDocumentError):
            assess(samples, candidates, bounds=bounds)
    else:
        roles = allocate_independent_training_blocks(samples, plan=BOUNDS, seed=71).blocks[0]
        training = roles.training_groups
        test = roles.test_groups
        keys = {k for g in (*training, *test) for k in g.samples}
        block_samples = tuple(s for s in samples if (s.source_id, s.sample_id) in keys)
        if change == 'overlap':
            test = (training[0], *test[1:])
        else:
            training = (replace(training[0], samples=()), *training[1:])
        with pytest.raises(GroupValidationError, match='partition'):
            select_grouped_forecast_holdout(
                candidates,
                samples=block_samples,
                candidate_kinds=KINDS,
                training_groups=training,
                test_groups=test,
                plan=SELECTOR,
            )


def test_native_adapter_repeats_full_learning_without_reusing_parent_fits():
    path = (
        Path(__file__).resolve().parents[3]
        / 'evaluation/examples/synthetic_conditional_risk/run.json'
    )
    plan = load_retention_run_plan(path)
    parent = execute_retention_run(replace(plan, bootstrap=replace(plan.bootstrap, n_resamples=16)))
    selector = plan.learned_selection
    assert selector is not None
    bounds = replace(
        BOUNDS,
        population_id='iid_binary_group_fixed_predictors_two_samples_v1',
        loss=selector.fixed.loss,
        minimum_group_size=2,
        maximum_group_size=2,
    )
    result = assess_independent_selection_training(
        parent, bounds=bounds, strategy='ensemble', seed=71
    )
    assert result.bound.status == 'computed'
    assert result.bound.test_sample_count == 8
    assert result.bound.training_failure_count == 0
    for block in result.blocks:
        assert block.selection.plan == selector
        fit = block.selection.folds[0].ensemble.outer_fit
        if fit is not None:
            assert len(fit.training_groups) == 4
            assert fit.training_sample_count == 8
        assert len(block.selection.folds) == 1
    # Parent predictions, selected candidates and fitted weights are not inputs.
    replay = assess_independent_selection_training(
        replace(parent, learned_selection=None), bounds=bounds, strategy='ensemble', seed=71
    )
    assert replay == result
