"""Descriptive catalog comparisons on explicitly retained exact common cohorts."""

# ruff: noqa: INP001 - Repository experiment shared by the benchmark command.

from __future__ import annotations

import math
from collections import defaultdict
from itertools import combinations
from statistics import median

from evaluation.experiments.meta_v3_3.campaign_comparisons import common, index


MINIMUM_CANDIDATES = 2
MINIMUM_CORRELATION_POINTS = 3
CORRELATION_LIMIT = 0.8
RELATIVE_ERROR_TOLERANCE = 0.01
RANK_TOLERANCE = 1e-12


def describe(points: list[dict]) -> dict | None:
    """Equal sample weighting for mean losses; pointwise median absolute error."""
    if not points:
        return None
    index(points)
    groups = defaultdict(list)
    for p in points:
        groups[p['source_id'], p['sample_id']].append(p['predicted'] - p['observed'])
    errors = [e for group in groups.values() for e in group]
    return {
        'rmse': math.sqrt(
            sum(sum(e * e for e in g) / len(g) for g in groups.values()) / len(groups)
        ),
        'mae': sum(sum(abs(e) for e in g) / len(g) for g in groups.values()) / len(groups),
        'bias': sum(sum(g) / len(g) for g in groups.values()) / len(groups),
        'median_absolute_error': median(abs(e) for e in errors),
    }


def correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < MINIMUM_CORRELATION_POINTS:
        return None
    a = [v - sum(left) / len(left) for v in left]
    b = [v - sum(right) / len(right) for v in right]
    denominator = math.sqrt(sum(v * v for v in a) * sum(v * v for v in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / denominator if denominator else None


def counts(points: list[dict]) -> dict:
    return {
        'points': len(points),
        'samples': len({(p['source_id'], p['sample_id']) for p in points}),
        'profiles': len({(p['source_id'], p['profile_id']) for p in points if p.get('profile_id')}),
        'sources': len({p['source_id'] for p in points}),
        'samples_without_profile': len(
            {(p['source_id'], p['sample_id']) for p in points if not p.get('profile_id')}
        ),
    }


def _dominates(left: dict, right: dict) -> bool:
    # A 1% relative improvement is required to trade away coverage or evidence.
    a = (left['metrics']['rmse'], abs(left['metrics']['bias']))
    b = (right['metrics']['rmse'], abs(right['metrics']['bias']))
    no_worse = all(
        x <= y * (1 + RELATIVE_ERROR_TOLERANCE) + 1e-12 for x, y in zip(a, b, strict=True)
    )
    burden = left['required_tier'] <= right['required_tier']
    coverage = left['coverage'] >= right['coverage']
    better = (
        any(x < y * (1 - RELATIVE_ERROR_TOLERANCE) - 1e-12 for x, y in zip(a, b, strict=True))
        or left['required_tier'] < right['required_tier']
        or left['coverage'] > right['coverage']
    )
    return no_worse and burden and coverage and better


def pool_analysis(points: list[dict]) -> dict:
    roster = sorted({p['function'] for p in points})
    indices = {f: index([p for p in points if p['function'] == f]) for f in roster}
    keys = common(list(indices.values()))
    union = set.union(*(set(i) for i in indices.values()))
    result: dict = {
        'members': roster,
        'cohort': [list(k) for k in keys],
        'coverage_denominator': 'union_of_executable_candidate_coordinates_in_this_pool',
        'available_points': len(union),
        'status': 'computed' if keys else 'empty_common_cohort',
        'recommendation': None,
    }
    if not keys:
        # Every pair still receives a comparison, without mixing pair cohorts.
        result['pairwise_cohorts'] = (
            [
                {
                    'members': [a, b],
                    'comparison': pool_analysis([p for p in points if p['function'] in (a, b)]),
                }
                for a, b in combinations(roster, 2)
            ]
            if len(roster) > MINIMUM_CANDIDATES
            else []
        )
        return result
    selected = {f: [indices[f][k] for k in keys] for f in roster}
    result.update(counts(selected[roster[0]]))
    rows = [
        {
            'function': f,
            'metrics': describe(selected[f]),
            'coverage': len(indices[f]) / len(union),
            'available': counts(list(indices[f].values())),
            'minimum_tier': min(p['minimum_tier'] for p in selected[f]),
            'required_tier': max(p['minimum_tier'] for p in selected[f]),
        }
        for f in roster
    ]
    rows.sort(key=lambda r: (r['metrics']['rmse'], r['required_tier'], r['function']))
    result['ranking'] = rows
    residuals = {f: [p['predicted'] - p['observed'] for p in selected[f]] for f in roster}
    correlations = [
        {'left': a, 'right': b, 'correlation': correlation(residuals[a], residuals[b])}
        for a, b in combinations(roster, 2)
    ]
    result['residual_correlations'] = correlations
    result['correlation_weighting'] = 'pointwise Pearson; descriptive, no independence inference'
    result['pareto'] = [
        row['function'] for row in rows if not any(_dominates(other, row) for other in rows)
    ]
    result['pareto_relative_error_tolerance'] = RELATIVE_ERROR_TOLERANCE
    fixed = []

    def ensemble(name: str, members: list[str], *, use_median: bool = False) -> None:
        predictions = [
            {
                **indices[members[0]][k],
                'predicted': (
                    median(indices[f][k]['predicted'] for f in members)
                    if use_median
                    else math.fsum(indices[f][k]['predicted'] / len(members) for f in members)
                ),
            }
            for k in keys
        ]
        fixed.append({'algorithm': name, 'members': members, 'metrics': describe(predictions)})

    if len(roster) >= MINIMUM_CANDIDATES:
        ensemble('equal_weight_mean', roster)
        ensemble('median', roster, use_median=True)
        for a, b in combinations(roster, 2):
            ensemble('equal_weight_pair', [a, b])
        good = {
            r['function']
            for r in rows
            if r['metrics']['rmse'] <= median(row['metrics']['rmse'] for row in rows)
        }
        reduced = [rows[0]['function']]
        lookup = {frozenset((r['left'], r['right'])): r['correlation'] for r in correlations}
        for row in rows[1:]:
            f = row['function']
            if f in good and all(
                lookup[frozenset((f, g))] is not None
                and abs(lookup[frozenset((f, g))]) < CORRELATION_LIMIT
                for g in reduced
            ):
                reduced.append(f)
        if len(reduced) >= MINIMUM_CANDIDATES:
            ensemble('reduced_equal_weight_mean', reduced)
        result['reduced_ensemble'] = {
            'members': reduced,
            'status': 'computed'
            if len(reduced) >= MINIMUM_CANDIDATES
            else 'insufficient_complementary_candidates',
            'rule': 'RMSE <= atomic median; absolute residual correlation < 0.8',
            'selection': 'in_sample_descriptive_only',
        }
        best = min(fixed, key=lambda r: r['metrics']['rmse'])
        result['best_atomic_vs_ensemble'] = {
            'atomic': rows[0],
            'ensemble': best,
            'delta_rmse_ensemble_minus_atomic': best['metrics']['rmse']
            - rows[0]['metrics']['rmse'],
            'status': 'descriptive_in_sample_selection; not validated generalization',
        }
    result['fixed_ensembles'] = fixed
    return result


def analyze(points: list[dict], *, dataset_samples: int | None = None) -> list[dict]:
    groups = defaultdict(list)
    for p in points:
        groups[p['scenario'], p['route'], p['target_pool']].append(p)
    reports = [
        {'scenario': scenario, 'route': route, 'target_pool': pool, **pool_analysis(group)}
        for (scenario, route, pool), group in sorted(groups.items())
        if len({p['function'] for p in group}) >= MINIMUM_CANDIDATES
    ]
    for report in reports:
        _dataset_coverage(report, dataset_samples)
    return reports


def _dataset_coverage(report: dict, denominator: int | None) -> None:
    report['dataset_sample_denominator'] = denominator
    for row in report.get('ranking', []):
        row['dataset_sample_coverage'] = (
            row['available']['samples'] / denominator if denominator else None
        )
    for pair in report.get('pairwise_cohorts', []):
        _dataset_coverage(pair['comparison'], denominator)


def robustness(points: list[dict], *, dimension: str) -> list[dict]:
    """Compare ranks on coordinates common to every candidate and both variants.

    Across target routes, observed values intentionally differ. Each variant is
    validated internally; its loss is evaluated against its own declared target.
    """
    fixed_dimension = 'route' if dimension == 'scenario' else 'scenario'
    groups = defaultdict(list)
    for p in points:
        groups[p[fixed_dimension], p['target_pool']].append(p)
    reports = []
    for (fixed, pool), group in sorted(groups.items()):
        variants = sorted({p[dimension] for p in group})
        for left, right in combinations(variants, 2):
            sets = {v: {p['function'] for p in group if p[dimension] == v} for v in (left, right)}
            roster = sorted(sets[left] & sets[right])
            indices = {
                (v, f): index([p for p in group if p[dimension] == v and p['function'] == f])
                for v in (left, right)
                for f in roster
            }
            for v in (left, right):
                common([indices[v, f] for f in roster])
            if dimension == 'scenario':
                common(list(indices.values()))
            keys = sorted(set.intersection(*(set(i) for i in indices.values()))) if indices else []
            report = {
                fixed_dimension: fixed,
                'target_pool': pool,
                'dimension': dimension,
                'variants': [left, right],
                'members': roster,
                'common_points': len(keys),
                'status': 'computed'
                if len(roster) >= MINIMUM_CANDIDATES and keys
                else 'insufficient_common_evidence',
            }
            if report['status'] == 'computed':
                scores = {
                    v: {f: describe([indices[v, f][k] for k in keys])['rmse'] for f in roster}
                    for v in (left, right)
                }
                rankings = {
                    v: sorted(roster, key=lambda f: (scores[v][f], f)) for v in (left, right)
                }
                report.update(
                    {
                        'rankings': rankings,
                        'rmse': scores,
                        'rank_changes': {
                            f: rankings[right].index(f) - rankings[left].index(f) for f in roster
                        },
                        'changed_pair_orderings': [
                            [a, b]
                            for a, b in combinations(roster, 2)
                            if _sign(scores[left][a] - scores[left][b])
                            != _sign(scores[right][a] - scores[right][b])
                        ],
                        'cohort': [list(k) for k in keys],
                        'interpretation': 'target sensitivity'
                        if dimension == 'route'
                        else 'predictor scenario sensitivity',
                    }
                )
            reports.append(report)
    return reports


def _sign(value: float) -> int:
    return 0 if abs(value) <= RANK_TOLERANCE else 1 if value > 0 else -1
