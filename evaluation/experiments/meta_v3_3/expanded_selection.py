"""Exact-cohort rankings and training-only enlarged ensemble validation."""

# ruff: noqa: INP001, E501, C901, PLR0912, PLR0915, PLR0917, PLR2004 - Scientific selection protocol.

from __future__ import annotations

import math
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np

from evaluation.experiments.meta_v3_3 import model_selection as original
from evaluation.experiments.meta_v3_3.expanded_participation import BASES, OUTPUT, read
from evaluation.experiments.meta_v3_3.final_approximation import json_write


ENSEMBLES = ('mean', 'median', 'reduced', 'top_2', 'top_3', 'top_5')


def sample_errors(
    errors: np.ndarray, group_indices: list[np.ndarray]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Columns are models; rows are observations; samples have equal total weight."""
    results = tuple(
        np.stack([np.mean(transform(errors[g]), axis=0) for g in group_indices])
        for transform in (np.square, np.abs, lambda x: x)
    )
    return results[0], results[1], results[2]


def correlation_matrix(residuals: np.ndarray) -> tuple[np.ndarray, float]:
    """Participation ratio of the residual correlation spectrum; undefined columns excluded."""
    centered = residuals - residuals.mean(axis=0)
    norms = np.sqrt(np.sum(centered * centered, axis=0))
    denominator = np.outer(norms, norms)
    matrix = np.divide(
        centered.T @ centered,
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 1e-24,
    )
    valid = norms > 1e-12
    trace = float(np.trace(matrix))
    effective = trace * trace / float(np.sum(matrix * matrix)) if np.any(valid) else 0.0
    return matrix, effective


def choose_members(
    residuals: np.ndarray,
    sample_mse: np.ndarray,
    sample_bias: np.ndarray,
    weights: np.ndarray,
    names: list[str],
    point_mask: np.ndarray,
) -> dict[str, list[int]]:
    """Every performance rank and complementarity decision uses training data only."""
    loss = np.average(sample_mse, axis=0, weights=weights)
    bias = np.average(sample_bias, axis=0, weights=weights)
    ordered = sorted(range(len(names)), key=lambda i: (loss[i], abs(bias[i]), names[i]))
    selected = ordered[:2]
    matrix, _ = correlation_matrix(residuals[point_mask])
    norms = np.std(residuals[point_mask], axis=0)
    best = ordered[0]
    for i in ordered[1:5]:
        if min(norms[best], norms[i]) > 1e-12 and matrix[best, i] < 0.95:
            selected = [best, i]
            break
    return {
        'mean': list(range(len(names))),
        'median': list(range(len(names))),
        'reduced': selected,
        **{f'top_{n}': ordered[:n] for n in (2, 3, 5)},
    }


def ensemble_assessment(indices: dict, members: list[str], keys: list) -> dict:
    if len(members) < 2:
        return {'status': 'insufficient_members'}
    points = [indices[members[0]][k] for k in keys]
    observed = np.array([p['observed'] for p in points])
    forecasts = np.array([[indices[f][k]['predicted'] for f in members] for k in keys])
    residuals = forecasts - observed[:, None]
    identities = sorted({(p['source_id'], p['sample_id']) for p in points})
    group_indices = [
        np.array(
            [i for i, p in enumerate(points) if (p['source_id'], p['sample_id']) == key], dtype=int
        )
        for key in identities
    ]
    squared, _absolute, biases = sample_errors(residuals, group_indices)
    membership = choose_members(
        residuals,
        squared,
        biases,
        np.ones(len(identities)),
        members,
        np.ones(len(points), dtype=bool),
    )

    def prediction(kind: str, selection: dict) -> np.ndarray:
        values = forecasts[:, selection[kind]]
        return np.median(values, axis=1) if kind == 'median' else values.mean(axis=1)

    def score(values: np.ndarray, sample_weights: np.ndarray) -> dict:
        errors = values - observed
        s, a, b = sample_errors(errors[:, None], group_indices)
        return {
            'rmse': math.sqrt(float(np.average(s[:, 0], weights=sample_weights))),
            'mae': float(np.average(a[:, 0], weights=sample_weights)),
            'bias': float(np.average(b[:, 0], weights=sample_weights)),
            'samples': int(np.count_nonzero(sample_weights)),
            'observations': sum(len(group_indices[i]) for i in np.flatnonzero(sample_weights)),
        }

    pooled: dict[str, dict] = {
        kind: {
            **score(prediction(kind, membership), np.ones(len(identities))),
            'members': [members[i] for i in membership[kind]],
        }
        for kind in ENSEMBLES
    }
    sources = {p['source_id'] for p in points}
    profiles = {p.get('profile_id') for p in points}
    if len(sources) >= 2:
        dimension = 'source_id'
    elif None not in profiles and len(profiles) >= 2:
        dimension = 'profile_id'
    else:
        dimension = 'sample_bootstrap'
    splits = []
    if dimension != 'sample_bootstrap':
        labels = [points[g[0]].get(dimension) for g in group_indices]
        for label in sorted(set(labels)):
            test = np.array([v == label for v in labels], dtype=float)
            splits.append((1 - test, test, str(label)))
    else:
        rng = np.random.default_rng(20261026)
        for i in range(500):
            weights = np.bincount(
                rng.integers(0, len(identities), len(identities)), minlength=len(identities)
            ).astype(float)
            test = (weights == 0).astype(float)
            if test.any():
                splits.append((weights, test, str(i)))
    pooled_best = min(
        range(len(members)),
        key=lambda i: (float(squared[:, i].mean()), abs(float(biases[:, i].mean())), members[i]),
    )
    folds, frequencies, deltas, deltas_pooled = (
        [],
        defaultdict(Counter),
        defaultdict(list),
        defaultdict(list),
    )
    effective_counts = defaultdict(list)
    oof = []
    for train, test, label in splits:
        mask = np.zeros(len(points), dtype=bool)
        for i in np.flatnonzero(train):
            mask[group_indices[i]] = True
        selected = choose_members(residuals, squared, biases, train, members, mask)
        training_best = min(
            range(len(members)),
            key=lambda i: (
                float(np.average(squared[:, i], weights=train)),
                abs(float(np.average(biases[:, i], weights=train))),
                members[i],
            ),
        )
        atomic = score(forecasts[:, training_best], test)
        fixed = score(forecasts[:, pooled_best], test)
        record = {
            'omitted_group': label,
            'training_best_atomic': members[training_best],
            'held_out_training_best_atomic': atomic,
            'held_out_pooled_best_atomic': fixed,
            'held_out_ensembles': {},
            'selected_members': {},
        }
        for kind in ENSEMBLES:
            chosen = selected[kind]
            values = prediction(kind, selected)
            result = score(values, test)
            record['held_out_ensembles'][kind] = result
            record['selected_members'][kind] = [members[i] for i in chosen]
            frequencies[kind].update(members[i] for i in chosen)
            deltas[kind].append(result['rmse'] - atomic['rmse'])
            deltas_pooled[kind].append(result['rmse'] - fixed['rmse'])
            _, effective = correlation_matrix(residuals[mask][:, chosen])
            effective_counts[kind].append(effective)
            if kind == 'reduced' and dimension != 'sample_bootstrap':
                for sample_index in np.flatnonzero(test):
                    oof.extend(
                        {**points[i], 'predicted': float(values[i])}
                        for i in group_indices[sample_index]
                    )
        folds.append(record)
    matrix, effective = correlation_matrix(residuals)
    atomic_pooled_rmse = math.sqrt(float(squared[:, pooled_best].mean()))
    conclusion = {
        kind: {
            'relative_rmse_change': pooled[kind]['rmse'] / atomic_pooled_rmse - 1,
            'meaningful_and_robust': bool(
                pooled[kind]['rmse'] <= 0.99 * atomic_pooled_rmse
                and deltas[kind]
                and all(d < 0 for d in deltas[kind])
                and all(d < 0 for d in deltas_pooled[kind])
            ),
            'evaluations': len(deltas[kind]),
            'fraction_better_than_training_atomic': float(np.mean(np.array(deltas[kind]) < 0))
            if deltas[kind]
            else None,
            'fraction_better_than_pooled_atomic': float(np.mean(np.array(deltas_pooled[kind]) < 0))
            if deltas_pooled[kind]
            else None,
            'delta_quantiles_training': np.quantile(
                deltas[kind], [0, 0.025, 0.5, 0.975, 1]
            ).tolist()
            if deltas[kind]
            else [],
            'delta_quantiles_pooled': np.quantile(
                deltas_pooled[kind], [0, 0.025, 0.5, 0.975, 1]
            ).tolist()
            if deltas_pooled[kind]
            else [],
        }
        for kind in ENSEMBLES
    }
    return {
        'status': 'computed',
        'ensembles': pooled,
        'ensemble_conclusion': conclusion,
        'dimension': dimension,
        'folds': folds,
        'reduced_nested_oof': original.metrics(oof),
        'diversity': {
            'members': members,
            'residual_correlation_matrix': matrix.tolist(),
            'undefined_constant_residual_columns': [
                members[i] for i in range(len(members)) if np.std(residuals[:, i]) <= 1e-12
            ],
            'effective_member_count': effective,
            'definition': '(trace(R))^2 / sum(R^2), undefined constant-residual columns excluded; descriptive, not independent model count',
            'membership_frequencies': {
                kind: {f: n / len(folds) for f, n in counts.items()}
                for kind, counts in frequencies.items()
            },
            'effective_selected_members_median': {
                kind: float(np.median(v)) for kind, v in effective_counts.items()
            },
        },
        'bootstrap_training': 'Atomic and top-N performance ranks weight in-bag multiplicity; residual correlation uses unique in-bag points. Every selection excludes out-of-bag outcomes.',
    }


def analyze(points: list[dict], *, ksat: bool = False) -> dict:
    indices = defaultdict(dict)
    for p in points:
        if p['id'] in indices[p['function']]:
            message = 'Duplicate function/observation coordinate in expanded predictions.'
            raise ValueError(message)
        indices[p['function']][p['id']] = p
    if not ksat:
        indices = {
            f: {k: i[k] for k in original.eligible_keys(set(i), i, ksat=False)}
            for f, i in indices.items()
        }
    indices = {f: i for f, i in indices.items() if i}
    cohorts = original.common_cohorts(indices, ksat=ksat)
    if not cohorts:
        return {
            'status': 'no_common_cohort',
            'coverage': {f: original.inventory(list(i.values())) for f, i in indices.items()},
            'compatible_cohorts': [],
        }
    maximum = max(original.inventory(list(i.values()))['samples'] for i in indices.values())
    viable = [c for c in cohorts if c['samples'] >= maximum / 2]
    primary = min(
        viable or cohorts,
        key=lambda c: (-len(c['members']), -c['samples'], -c['observations'], c['members']),
    )
    for number, cohort in enumerate(cohorts, 1):
        cohort['cohort_id'] = f'compatible_{number:03d}'
        cohort['ranking'] = original.rank(indices, cohort['members'], cohort['keys'], ksat=ksat)
        if not ksat:
            cohort['ensemble_analysis'] = ensemble_assessment(
                indices, cohort['members'], cohort['keys']
            )
            cohort['ensembles'] = cohort['ensemble_analysis']['ensembles']
        else:
            cohort['robustness'] = original.robustness(
                indices, cohort['members'], cohort['keys'], ksat=True
            )
            cohort['block_metrics'] = {
                block: original.rank(
                    indices,
                    cohort['members'],
                    [
                        k
                        for k in cohort['keys']
                        if indices[cohort['members'][0]][k]['block'] == block
                    ],
                    ksat=True,
                )
                for block in sorted(
                    {indices[cohort['members'][0]][k]['block'] for k in cohort['keys']}
                )
            }
    result = {
        'status': 'expanded_exploratory_E5',
        'coverage': {f: original.inventory(list(i.values())) for f, i in sorted(indices.items())},
        'primary': primary,
        'compatible_cohorts': cohorts,
        'pairwise': [],
        'maximal_metrics': {
            f: original.scored(list(i.values()), ksat=ksat) for f, i in indices.items()
        },
    }
    for left, right in combinations(sorted(indices), 2):
        shared = original.eligible_keys(
            set(indices[left]) & set(indices[right]), indices[left], ksat=ksat
        )
        if shared:
            result['pairwise'].append(
                {
                    'members': [left, right],
                    'ranking': original.rank(indices, [left, right], sorted(shared), ksat=ksat),
                }
            )
    result['regions'] = (
        {}
        if ksat
        else {
            region: {
                f: original.metrics(
                    [
                        p
                        for p in i.values()
                        if low <= p['pressure_kpa'] < (high if high is not None else math.inf)
                    ]
                )
                for f, i in indices.items()
            }
            for region, (low, high) in original.POLICY['pressure_regions_kpa'].items()
        }
    )
    if ksat:
        result['widest_cohort'] = cohorts[0]
    else:
        result['ensembles'] = primary['ensembles']
        result['ensemble_conclusion'] = primary['ensemble_analysis']['ensemble_conclusion']
    return result


def main() -> None:
    points = read(OUTPUT / 'predictions.json')
    analyses = {}
    for basis in BASES:
        analyses[basis] = analyze([p for p in points if p['basis'] == basis], ksat=basis == 'ksat')
        json_write(OUTPUT / f'analysis-{basis}.json', analyses[basis])
        print(  # noqa: T201 - Command result.
            f'{basis}: {len(analyses[basis]["coverage"])} candidates; {len(analyses[basis]["compatible_cohorts"])} cohorts.',
            flush=True,
        )
    json_write(OUTPUT / 'analyses.json', analyses)


if __name__ == '__main__':
    main()
