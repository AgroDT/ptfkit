"""Compare only identical scenario/cohort observations; retain non-recommendation status."""

# ruff: noqa: INP001 - Experiment-level descriptive comparison registration.

from __future__ import annotations

import math
from collections.abc import Callable
from itertools import combinations
from typing import cast

from ptfkit_eval.cohorts import RetentionCandidateComparisons
from ptfkit_eval.contracts import TargetSpec
from ptfkit_eval.folds import GroupedSample
from ptfkit_eval.metrics import RetentionComparison

from evaluation.experiments.meta_v3_3.ensembles import compare as grouped_compare


_RANK_TIE_TOLERANCE = 1e-12
_MINIMUM_MEMBERS = 2
_MINIMUM_PROFILES = 3
Metric = Callable[[list[dict]], dict | None]


def coordinate(point: dict) -> tuple:
    return point['source_id'], point['sample_id'], point['pressure_kpa']


def index(points: list[dict]) -> dict:
    result = {}
    for point in points:
        key = coordinate(point)
        if key in result:
            message = 'Duplicate prediction coordinate within a registered cohort.'
            raise ValueError(message)
        result[key] = point
    return result


def common(indices: list[dict]) -> list[tuple]:
    keys = sorted(set.intersection(*(set(i) for i in indices))) if indices else []
    for key in keys:
        values = {i[key]['observed'] for i in indices}
        if len(values) != 1:
            message = 'A common-cohort comparison requires identical observed values.'
            raise ValueError(message)
    return keys


def comparative_tables(points: list[dict], metric: Metric) -> list[dict]:
    reports = []
    for scenario, route, pool in sorted(
        {(p['scenario'], p['route'], p['target_pool']) for p in points}
    ):
        selected = [
            p
            for p in points
            if (p['scenario'], p['route'], p['target_pool']) == (scenario, route, pool)
        ]
        roster = sorted({p['function'] for p in selected})
        indices = {fid: index([p for p in selected if p['function'] == fid]) for fid in roster}
        keys = common(list(indices.values()))
        rows = [
            {
                'function': fid,
                'common_points': len(keys),
                'metrics': metric([indices[fid][key] for key in keys]),
            }
            for fid in roster
        ]
        reports.append(
            {
                'scenario': scenario,
                'route': route,
                'target_pool': pool,
                'registered_members': roster,
                'common_points': len(keys),
                'rows': rows,
                'status': 'computed' if keys else 'empty_common_cohort',
                'recommendation': None,
            }
        )
    return reports


def scenario_sensitivity(points: list[dict], scenarios: list[str], metric: Metric) -> dict:
    left, right = scenarios
    paired, rankings = [], []
    for fid, route, pool in sorted({(p['function'], p['route'], p['target_pool']) for p in points}):
        selected = [
            p for p in points if (p['function'], p['route'], p['target_pool']) == (fid, route, pool)
        ]
        indices = {
            scenario: index([p for p in selected if p['scenario'] == scenario])
            for scenario in scenarios
        }
        keys = common(list(indices.values()))
        if not keys:
            continue
        scores = {
            scenario: cast('dict', metric([indices[scenario][key] for key in keys]))
            for scenario in scenarios
        }
        differences = [
            indices[right][key]['predicted'] - indices[left][key]['predicted'] for key in keys
        ]
        paired.append(
            {
                'function': fid,
                'route': route,
                'target_pool': pool,
                'coverage': {scenario: len(indices[scenario]) for scenario in scenarios},
                'common_points': len(keys),
                'metrics': scores,
                'difference_right_minus_left': {
                    name: scores[right][name] - scores[left][name] for name in scores[left]
                },
                'prediction_mean_absolute_difference': math.fsum(abs(d) for d in differences)
                / len(differences),
                'prediction_maximum_absolute_difference': max(abs(d) for d in differences),
            }
        )
    for route, pool in sorted({(p['route'], p['target_pool']) for p in points}):
        selected = [p for p in points if (p['route'], p['target_pool']) == (route, pool)]
        roster = sorted(
            set.intersection(
                *(
                    {p['function'] for p in selected if p['scenario'] == scenario}
                    for scenario in scenarios
                )
            )
        )
        indices = {
            (scenario, fid): index(
                [p for p in selected if p['scenario'] == scenario and p['function'] == fid]
            )
            for scenario in scenarios
            for fid in roster
        }
        if len(roster) < _MINIMUM_MEMBERS:
            rankings.append(
                {
                    'route': route,
                    'target_pool': pool,
                    'status': 'insufficient_candidates',
                    'recommendation': None,
                }
            )
            continue
        keys = common(list(indices.values()))
        if not keys:
            rankings.append(
                {
                    'route': route,
                    'target_pool': pool,
                    'status': 'empty_cross_scenario_common_cohort',
                    'recommendation': None,
                }
            )
            continue
        scores = {
            (scenario, fid): cast('dict', metric([indices[scenario, fid][key] for key in keys]))[
                'rmse'
            ]
            for scenario in scenarios
            for fid in roster
        }
        rank = {
            scenario: sorted(roster, key=lambda fid: (scores[scenario, fid], fid))
            for scenario in scenarios
        }
        reversals = []
        for a, b in combinations(roster, 2):
            differences = [scores[scenario, a] - scores[scenario, b] for scenario in scenarios]
            signs = [
                0 if abs(v) <= _RANK_TIE_TOLERANCE else 1 if v > 0 else -1 for v in differences
            ]
            if signs[0] != signs[1]:
                reversals.append([a, b])
        rankings.append(
            {
                'route': route,
                'target_pool': pool,
                'common_points': len(keys),
                'rankings': rank,
                'unstable': bool(reversals),
                'changed_pair_orderings': reversals,
                'status': 'descriptive_common_cohort_only',
                'recommendation': None,
            }
        )
    return {'paired': paired, 'rankings': rankings}


def ensembles(points: list[dict], metric: Metric) -> list[dict]:
    """Use existing fixed means and grouped convex learning only on exact common cohorts."""
    reports = []
    for scenario, route, pool in sorted(
        {(p['scenario'], p['route'], p['target_pool']) for p in points}
    ):
        selected = [
            p
            for p in points
            if (p['scenario'], p['route'], p['target_pool']) == (scenario, route, pool)
        ]
        roster = sorted({p['function'] for p in selected})
        if len(roster) < _MINIMUM_MEMBERS:
            continue
        indices = {fid: index([p for p in selected if p['function'] == fid]) for fid in roster}
        keys = common(list(indices.values()))
        means = []
        for left, right in combinations(roster, 2):
            pair_keys = keys or common([indices[left], indices[right]])
            predictions = [
                {
                    **indices[left][key],
                    'predicted': math.fsum(
                        (indices[left][key]['predicted'] / 2, indices[right][key]['predicted'] / 2)
                    ),
                }
                for key in pair_keys
            ]
            means.append(
                {
                    'members': [left, right],
                    'weights': [0.5, 0.5],
                    'metrics': metric(predictions),
                    'common_points': len(pair_keys),
                    'cohort_scope': 'registered_roster_common' if keys else 'pair_common_only',
                    'comparable_across_pairs': bool(keys),
                    'recommendation_eligible': False,
                }
            )
        sample_index = {(key[0], key[1]): indices[roster[0]][key] for key in keys}
        profiles = {
            (p['source_id'], p['profile_id']) for p in sample_index.values() if p['profile_id']
        }
        learned = {'status': 'insufficient_independent_profile_groups'}
        if (
            len(profiles) >= _MINIMUM_PROFILES
            and all(p['profile_id'] for p in sample_index.values())
            and keys
        ):
            quantity = selected[0]['quantity']
            if quantity in ('volumetric_water_content', 'gravimetric_water_content'):
                target = TargetSpec(
                    quantity=quantity,
                    unit='volume_fraction'
                    if quantity == 'volumetric_water_content'
                    else 'mass_fraction',
                    denominator_basis='bulk_volume'
                    if quantity == 'volumetric_water_content'
                    else 'dry_soil_mass',
                    material_basis='unspecified',
                )
                records = tuple(
                    RetentionCandidateComparisons(
                        candidate_id=fid,
                        dataset_id='catalog-campaign',
                        protocol_id=scenario + ':' + route + ':' + pool,
                        target=target,
                        comparisons=tuple(
                            RetentionComparison(
                                source_id=key[0],
                                sample_id=key[1],
                                suction_kpa=key[2],
                                observed=indices[fid][key]['observed'],
                                predicted=indices[fid][key]['predicted'],
                                profile_id=indices[fid][key]['profile_id'],
                                water_quantity=quantity,
                            )
                            for key in keys
                        ),
                    )
                    for fid in roster
                )
                samples = tuple(
                    GroupedSample(p['source_id'], p['sample_id'], p['profile_id'])
                    for p in sample_index.values()
                )
                learned = grouped_compare(records, samples)
                learned.pop('predictions', None)
        reports.append(
            {
                'scenario': scenario,
                'route': route,
                'target_pool': pool,
                'common_points': len(keys),
                'registered_members': roster,
                'equal_means': means,
                'member_tiers': {
                    fid: sorted({indices[fid][key]['minimum_tier'] for key in keys})
                    for fid in roster
                },
                'training_observation_tiers': sorted(
                    {indices[fid][key]['target_evidence']['tier'] for fid in roster for key in keys}
                ),
                'learned': learned,
                'recommendation': None,
                'recommendation_eligible': False,
            }
        )
    return reports
