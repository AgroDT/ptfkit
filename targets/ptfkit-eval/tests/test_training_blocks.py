from dataclasses import replace

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    GroupedSample,
    IndependentTrainingAllocation,
    IndependentTrainingRiskPlan,
    LogPressureLossPlan,
    allocate_independent_training_blocks,
)


def plan():
    return IndependentTrainingRiskPlan(
        population_id='iid_original_groups',
        learner_id='training_only_selector',
        grouping='source',
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
        maximum_sample_loss=1,
        minimum_group_size=1,
        maximum_group_size=3,
        training_groups_per_block=2,
        test_groups_per_block=1,
        n_blocks=2,
    )


def roster():
    return tuple(
        GroupedSample(f'source{index}', f'sample{sample}', f'profile{sample}')
        for index in range(6)
        for sample in range(1 + index % 3)
    )


def roles(allocation: IndependentTrainingAllocation):
    return tuple(
        (
            block.block_id,
            tuple(group.group_id for group in block.training_groups),
            tuple(group.group_id for group in block.test_groups),
        )
        for block in allocation.blocks
    )


def test_exact_disjoint_roles_preserve_every_original_sample_and_unequal_group():
    samples = roster()
    allocation = allocate_independent_training_blocks(samples, plan=plan(), seed=17)
    assert len(allocation.blocks) == 2
    all_groups = []
    for block in allocation.blocks:
        assert len(block.training_groups) == 2
        assert len(block.test_groups) == 1
        all_groups.extend((*block.training_groups, *block.test_groups))
    assert len({group.group_id for group in all_groups}) == 6
    assert sorted(key for group in all_groups for key in group.samples) == sorted(
        (sample.source_id, sample.sample_id) for sample in samples
    )
    for group in all_groups:
        index = int(group.group_id[0].removeprefix('source'))
        assert group.samples == tuple(
            (f'source{index}', f'sample{i}') for i in range(1 + index % 3)
        )


def test_assignment_ignores_input_order_sample_counts_and_source_group_profiles():
    samples = roster()
    original = allocate_independent_training_blocks(samples, plan=plan(), seed=17)
    assert allocate_independent_training_blocks(reversed(samples), plan=plan(), seed=17) == original
    single = tuple(GroupedSample(f'source{i}', 'only', None) for i in range(6))
    assert roles(allocate_independent_training_blocks(single, plan=plan(), seed=17)) == roles(
        original
    )
    assert roles(allocate_independent_training_blocks(samples, plan=plan(), seed=18)) != roles(
        original
    )


def test_profiles_are_source_local_and_never_split_or_fallback_within_blocks():
    samples = tuple(
        GroupedSample(source, f'{profile}_{index}', profile)
        for source in ('a', 'b', 'c')
        for profile in ('p', 'q')
        for index in range(2)
    )
    profile_plan = replace(plan(), grouping='profile')
    allocation = allocate_independent_training_blocks(samples, plan=profile_plan, seed=17)
    groups = [
        g for block in allocation.blocks for g in (*block.training_groups, *block.test_groups)
    ]
    assert {g.group_id for g in groups} == {(s, p) for s in ('a', 'b', 'c') for p in ('p', 'q')}
    assert all(
        g.samples == tuple((g.group_id[0], f'{g.group_id[1]}_{i}') for i in range(2))
        for g in groups
    )
    missing = (replace(samples[0], profile_id=None), *samples[1:])
    with pytest.raises(EvaluationDocumentError, match='missing profile'):
        allocate_independent_training_blocks(missing, plan=profile_plan, seed=17)


@pytest.mark.parametrize('change', ['missing', 'extra', 'duplicate', 'blank', 'seed'])
def test_allocation_rejects_roster_changes_without_dropping_or_copying_groups(change: str):
    samples = roster()
    seed = 17
    if change == 'missing':
        samples = tuple(s for s in samples if s.source_id != 'source0')
    elif change == 'extra':
        samples = (*samples, GroupedSample('extra', 'sample'))
    elif change == 'duplicate':
        samples = (*samples, samples[0])
    elif change == 'blank':
        samples = (replace(samples[0], sample_id=' '), *samples[1:])
    else:
        seed = True
    with pytest.raises(EvaluationDocumentError):
        allocate_independent_training_blocks(samples, plan=plan(), seed=seed)
