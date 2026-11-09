"""Protect exact common coordinates, independent mean oracles and profile grouping."""

import runpy
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from ptfkit_eval.cohorts import RetentionCandidateComparisons, RetentionCohortError
from ptfkit_eval.contracts import TargetSpec
from ptfkit_eval.folds import GroupedSample
from ptfkit_eval.metrics import RetentionComparison


def _compare() -> Callable:
    return runpy.run_path(
        str(Path(__file__).resolve().parents[3] / 'evaluation/experiments/meta_v3_3/ensembles.py')
    )['compare']


def _records() -> tuple[RetentionCandidateComparisons, RetentionCandidateComparisons]:
    # Unequal grids make point pooling differ from the required sample balancing.
    points = tuple(
        RetentionComparison('s', sample, pressure, 0.3, predicted, 'one_profile')
        for sample, pressure, predicted in [('a', 1, 0.1), ('a', 10, 0.1), ('b', 1, 0.3)]
    )
    left = RetentionCandidateComparisons(
        candidate_id='left',
        dataset_id='data',
        protocol_id='review',
        target=TargetSpec(
            'volumetric_water_content', 'volume_fraction', 'mineral_soil', 'bulk_volume'
        ),
        comparisons=points,
    )
    right = replace(
        left, candidate_id='right', comparisons=tuple(replace(p, predicted=0.5) for p in points)
    )
    return left, right


def test_mean_uses_equal_fixed_weights_and_sample_balanced_exact_common_errors():
    left, right = _records()
    samples = tuple(GroupedSample('s', name, 'one_profile') for name in ('a', 'b', 'missing'))
    result = _compare()((left, right), samples)
    rows = {r['id']: r for r in result['candidates']}
    mean = rows['mean_left_right']
    # Mean errors: a=(0,0), b=.1. Equal sample MSE is (.0+.01)/2.
    assert mean['metrics']['root_mean_squared_error'] == pytest.approx(0.005**0.5)
    assert mean['metrics']['mean_absolute_error'] == pytest.approx(0.05)
    assert mean['metrics']['mean_error'] == pytest.approx(0.05)
    assert mean['coverage'] == pytest.approx(2 / 3)
    assert mean['point_count'] == 3
    assert result['registration'][0]['weights'] == [0.5, 0.5]
    # Two horizons do not become independent profiles; no fitted weight fallback.
    assert result['learned_selection']['status'] == 'insufficient_evidence'
    assert result['learned_selection']['folds'] == []
    assert len(result['learned_selection']['splits']['groups']) == 1
    assert result['recommendation'] is None
    # Changing targets changes errors, but never the registered mean predictions.
    changed = tuple(
        replace(r, comparisons=tuple(replace(p, observed=0.7) for p in r.comparisons))
        for r in (left, right)
    )
    after = _compare()(changed, samples)
    assert [p['predicted'] for p in result['predictions']['mean_left_right']] == [
        p['predicted'] for p in after['predictions']['mean_left_right']
    ]


def test_mean_intersects_exact_pressures_and_rejects_incompatible_contracts():
    left, right = _records()
    samples = (GroupedSample('s', 'a', 'one_profile'), GroupedSample('s', 'b', 'one_profile'))
    right = replace(
        right,
        comparisons=tuple(
            replace(p, suction_kpa=1.000000001) if p.suction_kpa == 1 else p
            for p in right.comparisons
        ),
    )
    # Retain two shared pressures for the registered log-pressure learning loss.
    extra = RetentionComparison('s', 'a', 100, 0.3, 0.1, 'one_profile')
    left = replace(left, comparisons=(*left.comparisons, extra))
    right = replace(right, comparisons=(*right.comparisons, replace(extra, predicted=0.5)))
    result = _compare()((left, right), samples)
    assert result['pressure_support_kpa'] == [10, 100]
    assert all(r['point_count'] == 2 and r['common_n'] == 1 for r in result['candidates'])
    bad = replace(right, target=replace(right.target, material_basis='unspecified'))
    with pytest.raises(RetentionCohortError, match='share dataset, protocol, and target'):
        _compare()((left, bad), samples)


def test_empty_member_is_retained_as_empty_common_cohort():
    left, right = _records()
    result = _compare()(
        (left, replace(right, comparisons=())), (GroupedSample('s', 'a', 'one_profile'),)
    )
    assert result['status'] == 'empty_common_cohort'
    assert result['candidates'] == []


def test_single_pressure_mean_uses_point_loss_without_requiring_a_curve():
    left, right = _records()
    records = tuple(
        replace(r, comparisons=tuple(p for p in r.comparisons if p.suction_kpa == 1))
        for r in (left, right)
    )
    result = _compare()(
        records, (GroupedSample('s', 'a', 'one_profile'), GroupedSample('s', 'b', 'one_profile'))
    )
    assert result['pressure_support_kpa'] == [1]
    assert (
        result['learned_selection']['plan']['fixed']['loss']['method'] == 'single_pressure_mse_v1'
    )
    assert (
        result['learned_selection']['plan']['ensembles'][0]['method']
        == 'constant_convex_pair_single_pressure_v1'
    )
