"""Fixed means and existing nested convex learning on reviewed atomic forecasts."""

# ruff: noqa: INP001 - Standalone experiment helpers.

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from itertools import combinations
from typing import TYPE_CHECKING, cast

from ptfkit_eval import read_retention_run_report
from ptfkit_eval.artifacts import artifact_value
from ptfkit_eval.cohorts import RetentionCandidateComparisons, build_retention_cohorts
from ptfkit_eval.contracts import TargetSpec
from ptfkit_eval.documents import canonical_json
from ptfkit_eval.folds import GroupedSample, NestedGroupPlan
from ptfkit_eval.learned import (
    ConvexPairPlan,
    LearnedSelectionPlan,
    select_grouped_forecast_candidates,
)
from ptfkit_eval.losses import LogPressureLossPlan, SinglePressureLossPlan
from ptfkit_eval.metrics import RetentionComparison, summarize_retention_errors
from ptfkit_eval.selection import FixedSelectionPlan


if TYPE_CHECKING:
    from pathlib import Path


_MINIMUM_MEMBERS = 2


def compare(
    records: tuple[RetentionCandidateComparisons, ...], samples: tuple[GroupedSample, ...]
) -> dict:
    """Register every pair before scoring; never tune fixed weights to observations.

    Each call is one target/pressure pool. The standard cohort builder validates
    contracts, duplicate keys, observations and profile identities before means.
    """
    if len(records) < _MINIMUM_MEMBERS:
        message = 'An ensemble comparison requires at least two atomic candidates.'
        raise ValueError(message)
    cohorts = build_retention_cohorts(records)
    common = {c.candidate_id: c.comparisons for c in cohorts.common}
    roster = tuple(sorted(common))
    registration: list[dict] = [
        {'id': f'mean_{left}_{right}', 'members': [left, right], 'weights': [0.5, 0.5]}
        for left, right in combinations(roster, 2)
    ]
    if not all(common.values()):
        return {'status': 'empty_common_cohort', 'registration': registration, 'candidates': []}
    forecasts = list(records)
    for item in registration:
        left, right = (common[name] for name in item['members'])
        points = tuple(
            replace(a, predicted=math.fsum((a.predicted / 2, b.predicted / 2)))
            for a, b in zip(left, right, strict=True)
        )
        forecasts.append(replace(records[0], candidate_id=item['id'], comparisons=points))
    # Rebuild so all atomic and mean metrics use exactly the same coordinates.
    compared = build_retention_cohorts(forecasts)
    results = []
    for cohort in compared.common:
        summary = cast('dict', artifact_value(summarize_retention_errors(cohort.comparisons)))
        summary.pop('samples')
        results.append(
            {
                'id': cohort.candidate_id,
                'kind': 'atomic' if cohort.candidate_id in roster else 'ensemble',
                'common_n': summary['sample_count'],
                'coverage': summary['sample_count'] / len(samples),
                'point_count': summary['point_count'],
                'metrics': summary['metrics'],
                'status': 'descriptive',
            }
        )
    pressures = sorted({p.suction_kpa for p in next(iter(common.values()))})
    learned = select_grouped_forecast_candidates(
        forecasts,
        samples=samples,
        candidate_kinds={
            r.candidate_id: 'atomic' if r.candidate_id in roster else 'ensemble' for r in forecasts
        },
        plan=LearnedSelectionPlan(
            fixed=FixedSelectionPlan(
                candidate_ids=tuple(r['id'] for r in results),
                folds=NestedGroupPlan(
                    seed=20261025,
                    outer_folds=3,
                    inner_folds=2,
                    grouping='profile',
                    missing_profiles='reject',
                ),
                loss=SinglePressureLossPlan(suction_kpa=pressures[0])
                if len(pressures) == 1
                else LogPressureLossPlan(
                    lower_suction_kpa=pressures[0], upper_suction_kpa=pressures[-1]
                ),
            ),
            ensembles=tuple(
                ConvexPairPlan(
                    id=f'convex_{left}_{right}',
                    left_candidate_id=left,
                    right_candidate_id=right,
                    minimum_training_groups=2,
                    minimum_mean_squared_contrast=1e-12,
                    method='constant_convex_pair_single_pressure_v1'
                    if len(pressures) == 1
                    else 'constant_convex_pair_log_pressure_v1',
                )
                for left, right in combinations(roster, 2)
            ),
        ),
    )

    def rmse(row: dict) -> float:
        return row['metrics']['root_mean_squared_error']

    atomic = min((r for r in results if r['kind'] == 'atomic'), key=rmse)
    mean = min((r for r in results if r['kind'] == 'ensemble'), key=rmse)
    return {
        'status': 'descriptive',
        'target': artifact_value(cohorts.target),
        'pressure_support_kpa': pressures,
        'registration': registration,
        'candidates': results,
        'best_atomic': atomic['id'],
        'best_ensemble': mean['id'],
        'delta_rmse_ensemble_minus_atomic': rmse(mean) - rmse(atomic),
        'evidence_status': 'insufficient_evidence'
        if learned.status != 'computed'
        else 'nested_assessment_available',
        'recommendation': None,
        'learned_selection': artifact_value(learned),
        'predictions': {c.candidate_id: artifact_value(c.comparisons) for c in compared.common},
    }


def run(reference: Path, output: Path) -> dict:
    """Use only hash-verified eligible forecasts, preserving the complete input roster."""
    artifacts = reference / 'artifacts'
    read_retention_run_report(artifacts)
    evaluation = json.loads((artifacts / 'evaluation-plan.json').read_bytes())
    dataset = json.loads((artifacts / 'dataset.json').read_bytes())
    plan = json.loads((artifacts / 'run-plan.json').read_bytes())
    candidates = {r['id']: r for r in evaluation['candidates']}
    records = tuple(
        RetentionCandidateComparisons(
            candidate_id=row['cohort']['candidate_id'],
            dataset_id=dataset['dataset_id'],
            protocol_id=plan['protocol']['id'],
            target=TargetSpec(**candidates[row['cohort']['candidate_id']]['target']),
            comparisons=tuple(RetentionComparison(**p) for p in row['cohort']['comparisons']),
        )
        for row in json.loads((artifacts / 'cohorts.json').read_bytes())
        if row['cohort']['kind'] == 'maximal'
    )
    samples = tuple(
        GroupedSample(s['source_id'], s['sample_id'], s.get('profile_id'))
        for s in dataset['samples']
    )
    summary = compare(records, samples)
    summary['input_sha256'] = {
        name: hashlib.sha256((artifacts / name).read_bytes()).hexdigest()
        for name in ('cohorts.json', 'evaluation-plan.json', 'dataset.json')
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / 'predictions.json').write_bytes(canonical_json(summary.pop('predictions', {})))
    (output / 'summary.json').write_bytes(canonical_json(summary))
    return summary
