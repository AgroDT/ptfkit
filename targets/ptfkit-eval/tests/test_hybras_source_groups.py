"""Protect transitive reference blocking without modifying measured records."""

import copy
import runpy
from pathlib import Path

import pytest

from ptfkit_eval import GroupedSample, NestedGroupPlan, build_nested_group_folds


def _namespace() -> dict:
    root = Path(__file__).resolve().parents[3]
    return runpy.run_path(str(root / 'evaluation/experiments/hybras/group_sources.py'))


def test_references_connect_transitively_before_projecting_a_selected_subset():
    connect = _namespace()['reference_components']
    references = {
        'a': ('paper 1', None),
        'b': ('paper 1', 'paper 2'),
        'c': ('paper 2', None),
        'd': ('unrelated', None),
        'e': (None, ''),
        'f': (' ', None),
        'g': ('paper 1 ', None),
    }
    mapping = connect(references)
    assert mapping['a'] == mapping['b'] == mapping['c']
    assert mapping['d'] == 'd'
    assert mapping['e'] == 'e'
    assert mapping['f'] == 'f'
    assert mapping['g'] == 'g'
    reordered = {k: tuple(reversed(v)) for k, v in reversed(tuple(references.items()))}
    assert connect(reordered) == mapping
    # B is not selected, but its reference bridge still makes A and C inseparable.
    document: dict = {
        'samples': [
            {'source_id': s, 'sample_id': s, 'profile_id': s, 'features': []}
            for s in ('a', 'c', 'd')
        ],
        'observations': [
            {'id': s, 'source_id': s, 'sample_id': s, 'suction_kpa': 33.0484105, 'value': 0.2}
            for s in ('a', 'c', 'd')
        ],
        'target': {'material_basis': 'unspecified'},
    }
    before = copy.deepcopy(document)
    updated, lineage = _namespace()['apply_groups'](document, mapping)
    assert document == before
    assert [s['original_source_id'] for s in lineage] == ['a', 'c', 'd']
    for original, remapped in zip(before['observations'], updated['observations'], strict=True):
        assert {**remapped, 'source_id': original['source_id']} == original
    assert updated['target'] == before['target']


def test_linked_sources_stay_together_in_outer_and_inner_roles():
    connect = _namespace()['reference_components']
    references = {
        'a': ('shared', None),
        'b': ('shared', None),
        **{f'source_{i}': (f'paper_{i}', None) for i in range(5)},
    }
    mapping = connect(references)
    result = build_nested_group_folds(
        [GroupedSample(mapping[source], source, source) for source in references],
        plan=NestedGroupPlan(seed=41, outer_folds=3, inner_folds=2),
    )
    assert result.status == 'computed'
    assert len(result.groups) == 6
    block = next(g for g in result.groups if any(sample[1] == 'a' for sample in g.samples))
    assert {sample[1] for sample in block.samples} == {'a', 'b'}
    assert sum(block.group_id in fold.test_groups for fold in result.folds) == 1
    for fold in result.folds:
        assert not set(fold.training_groups).intersection(fold.test_groups)
        for inner in fold.inner:
            assert set(inner.training_groups).isdisjoint(inner.validation_groups)
            assert set(inner.training_groups).union(inner.validation_groups) == set(
                fold.training_groups
            )


def test_unmapped_sources_cannot_silently_retain_an_independent_group():
    document = {'samples': [{'source_id': 'unknown', 'sample_id': 's', 'profile_id': 'p'}]}
    with pytest.raises(ValueError, match='absent from the reviewed workbook'):
        _namespace()['apply_groups'](document, {})
