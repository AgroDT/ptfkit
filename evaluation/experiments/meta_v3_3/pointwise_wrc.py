"""Experimental-point WRC scoring and source-held-out available-member ensembles."""

# ruff: noqa: INP001 - Repository experiment entry points.

from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean, median


BASES = ('volumetric_water_content', 'gravimetric_water_content')
ENSEMBLES = ('top_3', 'top_5', 'median', 'all_available_mean')


def identity(point: dict) -> tuple:
    return point['basis'], point['source_id'], point['sample_id'], point['pressure_kpa']


def sample_key(point: dict) -> tuple:
    return point['source_id'], point['sample_id']


def score(points: list[dict], ledger: list[dict]) -> dict:
    """Equal sample weights apply to squared errors before taking the square root."""
    total_samples = len({sample_key(p) for p in ledger})
    groups = defaultdict(list)
    for point in points:
        groups[sample_key(point)].append(point['predicted'] - point['observed'])
    errors = [p['predicted'] - p['observed'] for p in points]
    observed = [p['observed'] for p in points]
    squares = sum(e * e for e in errors)
    average = mean(observed) if points else 0
    variance = sum((v - average) ** 2 for v in observed)
    return {
        'n_predicted_points': len(points),
        'n_total_points': len(ledger),
        'point_coverage': len(points) / len(ledger) if ledger else 0,
        'n_predicted_samples': len(groups),
        'n_total_samples': total_samples,
        'sample_coverage': len(groups) / total_samples if total_samples else 0,
        'sample_balanced_rmse': math.sqrt(mean(mean(e * e for e in g) for g in groups.values()))
        if groups
        else None,
        'sample_balanced_mae': mean(mean(abs(e) for e in g) for g in groups.values())
        if groups
        else None,
        'sample_balanced_bias': mean(mean(g) for g in groups.values()) if groups else None,
        'rmse': math.sqrt(squares / len(points)) if points else None,
        'mae': mean(abs(e) for e in errors) if points else None,
        'bias': mean(errors) if points else None,
        'median_absolute_error': median(abs(e) for e in errors) if points else None,
        'r_squared_descriptive': 1 - squares / variance if variance > 0 else None,
        'pressure_min_kpa': min(p['pressure_kpa'] for p in points) if points else None,
        'pressure_max_kpa': max(p['pressure_kpa'] for p in points) if points else None,
    }


def align_predictions(predictions: list[dict], ledger: list[dict]) -> list[dict]:
    """Require actual measured coordinates; never promote interpolated targets."""
    observations = {identity(p): p for p in ledger}
    if len(observations) != len(ledger):
        msg = 'Experimental ledger has duplicate sample/basis/pressure coordinates.'
        raise ValueError(msg)
    result, seen = [], set()
    for point in predictions:
        if point['basis'] not in BASES or point.get('water_conditioned'):
            continue
        if point.get('target_reconstruction'):
            msg = 'Interpolated targets cannot enter the experimental ledger benchmark.'
            raise ValueError(msg)
        key = identity(point)
        if key not in observations:
            msg = f'Prediction has no experimental observation: {key!r}'
            raise ValueError(msg)
        original = observations[key]
        if not math.isclose(point['observed'], original['observed'], rel_tol=1e-12, abs_tol=1e-14):
            msg = 'Prediction observation differs from the experimental ledger.'
            raise ValueError(msg)
        unique = point['function'], key
        if unique in seen:
            msg = f'Duplicate model prediction: {unique!r}'
            raise ValueError(msg)
        seen.add(unique)
        if not math.isfinite(point['predicted']):
            msg = 'Nonfinite WRC prediction.'
            raise ValueError(msg)
        result.append(
            {**point, **original, 'function': point['function'], 'predicted': point['predicted']}
        )
    return result


def ranking(points: list[dict], ledger: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for point in points:
        groups[point['function']].append(point)
    return sorted(
        [{'model': name, **score(group, ledger)} for name, group in groups.items()],
        key=lambda r: (r['sample_balanced_rmse'], abs(r['sample_balanced_bias']), r['model']),
    )


def held_out_ensembles(points: list[dict], ledger: list[dict]) -> tuple[list[dict], list[dict]]:
    """Leave an entire source out; select members using training observations only."""
    output, folds = [], []
    ledger_index = {identity(p): p for p in ledger}
    for source in sorted({p['source_id'] for p in ledger}):
        training = [p for p in points if p['source_id'] != source]
        train_ledger = [p for p in ledger if p['source_id'] != source]
        ordered = [r['model'] for r in ranking(training, train_ledger)]
        selections = {
            'top_3': ordered[:3],
            'top_5': ordered[:5],
            'median': ordered,
            'all_available_mean': ordered,
        }
        held = defaultdict(dict)
        for point in points:
            if point['source_id'] == source:
                held[identity(point)][point['function']] = point
        folds.append({'held_out_source': source, 'training_rank': ordered, 'selected': selections})
        for kind, members in selections.items():
            for available in held.values():
                used = [m for m in members if m in available]
                if not used:
                    continue
                values = [available[m]['predicted'] for m in used]
                point = available[used[0]]
                output.append(
                    {
                        **ledger_index[identity(point)],
                        'function': 'ensemble:' + kind,
                        'predicted': median(values) if kind == 'median' else mean(values),
                        'route_type': 'ensemble',
                        'held_out_source': source,
                        'ensemble_members': used,
                        'n_members': len(used),
                        'member_predictor_evidence': {
                            m: available[m].get('predictor_evidence', {}) for m in used
                        },
                    }
                )
    return output, folds


def nominations(rows: list[dict]) -> dict:
    """Expose thresholds and a deterministic, explicitly heuristic Pareto compromise."""
    ordered = sorted(rows, key=lambda r: (r['sample_balanced_rmse'], r['model']))
    if not ordered:
        return {'best_accuracy': None, 'high_coverage': {}, 'pareto': [], 'compromise': None}
    frontier = [
        r
        for r in ordered
        if not any(
            other['point_coverage'] >= r['point_coverage']
            and other['sample_balanced_rmse'] <= r['sample_balanced_rmse']
            and (
                other['point_coverage'] > r['point_coverage']
                or other['sample_balanced_rmse'] < r['sample_balanced_rmse']
            )
            for other in ordered
        )
    ]
    threshold = next(
        (t for t in (75, 50, 25) if any(r['point_coverage'] >= t / 100 for r in frontier)),
        None,
    )
    candidates = (
        [r for r in frontier if r['point_coverage'] >= threshold / 100]
        if threshold
        else [
            r for r in frontier if r['point_coverage'] == max(p['point_coverage'] for p in frontier)
        ]
    )
    compromise = min(
        candidates,
        key=lambda r: (r['sample_balanced_rmse'], r['model']),
    )
    return {
        'best_accuracy': ordered[0],
        'high_coverage': {
            str(t): next((r for r in ordered if r['point_coverage'] >= t / 100), None)
            for t in (25, 50, 75)
        },
        'pareto': [r['model'] for r in frontier],
        'compromise': compromise,
        'compromise_policy': (
            'Minimum RMSE on the Pareto frontier at the highest attainable '
            'coverage threshold among 75%, 50%, 25%; if none, maximum frontier coverage. '
            'Descriptive practical choice, not a uniquely optimal model.'
        ),
    }


def analyze(points: list[dict], ledger: list[dict]) -> dict:
    individual = ranking(points, ledger)
    ensemble_points, folds = held_out_ensembles(points, ledger)
    ensemble = ranking(ensemble_points, ledger)
    threshold = next(
        (t for t in (75, 50, 25) if any(r['point_coverage'] >= t / 100 for r in individual)),
        None,
    )
    reference = next(
        (r for r in individual if threshold is not None and r['point_coverage'] >= threshold / 100),
        None,
    )
    if reference is None and individual:
        maximum = max(r['point_coverage'] for r in individual)
        reference = next(r for r in individual if r['point_coverage'] == maximum)
    comparisons = []
    if reference:
        atomic = {identity(p): p for p in points if p['function'] == reference['model']}
        for row in ensemble:
            index = {identity(p): p for p in ensemble_points if p['function'] == row['model']}
            common = sorted(atomic.keys() & index.keys())
            a = score([atomic[k] for k in common], ledger)
            e = score([index[k] for k in common], ledger)
            comparisons.append(
                {
                    'ensemble': row['model'],
                    'individual': reference['model'],
                    'n_common_points': len(common),
                    'individual_common': a,
                    'ensemble_common': e,
                    'coverage_at_least_individual': row['point_coverage']
                    >= reference['point_coverage'],
                    'lower_common_error': bool(common)
                    and e['sample_balanced_rmse'] < a['sample_balanced_rmse'],
                }
            )
    return {
        'individual': individual,
        'ensembles': ensemble,
        'folds': folds,
        'nominations': nominations(individual),
        'ensemble_nominations': nominations(ensemble),
        'combined_nominations': nominations(individual + ensemble),
        'high_coverage_comparison_threshold_percent': threshold,
        'ensemble_comparisons': comparisons,
        'ensemble_predictions': ensemble_points,
    }
