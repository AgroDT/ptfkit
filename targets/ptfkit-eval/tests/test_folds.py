from collections import Counter
from dataclasses import replace

import pytest

from ptfkit_eval import (
    GroupedSample,
    GroupValidationError,
    NestedGroupPlan,
    build_nested_group_folds,
)


SAMPLES = tuple(
    GroupedSample(f'source_{index}', f'sample_{sample}', 'profile')
    for index in range(6)
    for sample in range(2)
)
PLAN = NestedGroupPlan(seed=9123, outer_folds=3, inner_folds=2)


def test_whole_groups_are_held_out_once_and_outer_test_never_enters_inner_validation():
    result = build_nested_group_folds(SAMPLES, plan=PLAN)
    assert result.status == 'computed'
    all_groups = {membership.group_id for membership in result.groups}
    assert len(all_groups) == 6
    assert all(len(membership.samples) == 2 for membership in result.groups)
    held_out = Counter(group for fold in result.folds for group in fold.test_groups)
    assert held_out == dict.fromkeys(all_groups, 1)
    for outer in result.folds:
        training, test = set(outer.training_groups), set(outer.test_groups)
        assert training.isdisjoint(test)
        assert training | test == all_groups
        assert len(test) == 2
        inner_held_out = Counter(group for fold in outer.inner for group in fold.validation_groups)
        assert inner_held_out == dict.fromkeys(training, 1)
        for inner in outer.inner:
            assert set(inner.training_groups).isdisjoint(inner.validation_groups)
            assert set(inner.training_groups) | set(inner.validation_groups) == training
            assert test.isdisjoint((*inner.training_groups, *inner.validation_groups))


def test_assignment_is_input_order_independent_with_an_explicit_seed():
    result = build_nested_group_folds(SAMPLES, plan=PLAN)
    assert result == build_nested_group_folds(reversed(SAMPLES), plan=PLAN)
    assert result.folds != build_nested_group_folds(SAMPLES, plan=replace(PLAN, seed=47)).folds


def test_profile_fallback_applies_to_the_whole_roster():
    samples = (*SAMPLES[:-1], replace(SAMPLES[-1], profile_id=None))
    rejected = build_nested_group_folds(samples, plan=replace(PLAN, grouping='profile'))
    assert rejected.reason == 'missing_profile_ids'
    fallback = build_nested_group_folds(
        samples, plan=replace(PLAN, grouping='profile', missing_profiles='source')
    )
    assert fallback.effective_grouping == 'source'
    assert fallback.groups == build_nested_group_folds(samples, plan=PLAN).groups


def test_insufficient_inner_groups_return_no_partial_outer_evidence():
    result = build_nested_group_folds(SAMPLES[:6], plan=PLAN)
    assert result.reason == 'insufficient_groups_for_requested_folds'
    assert result.folds == ()


def test_duplicate_sample_identities_are_rejected_before_group_assignment():
    with pytest.raises(GroupValidationError, match='Duplicate'):
        build_nested_group_folds([SAMPLES[0], SAMPLES[0]], plan=PLAN)
