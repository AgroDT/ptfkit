"""Exact finite-population diagnostic; no confidence interval is qualified."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from fractions import Fraction
from itertools import product
from math import factorial
from pathlib import Path

from ptfkit_eval import (
    ConvexPairPlan,
    FixedSelectionPlan,
    GroupedSample,
    GroupMembership,
    GroupMultiplicity,
    LearnedNestedSelection,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    resample_grouped_forecasts,
    select_grouped_forecast_candidates,
)


_HIGH_GROUP_SIZE = 3


PLAN = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('one', 'zero'),
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
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
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')


def population_risk(prediction: float, high_group_size: int) -> float:
    """Independent oracle: E[group error sum] / E[group size]."""
    return (prediction**2 + high_group_size * (1 - prediction) ** 2) / (1 + high_group_size)


def forecasts(
    states: tuple[int, ...], high_group_size: int, *, missing_high_sample: bool = False
) -> tuple[tuple[GroupedSample, ...], tuple[RetentionCandidateComparisons, ...]]:
    """Mathematical constants, not outputs attributed to published PTFs."""
    samples = tuple(
        GroupedSample(f'g{group}', f's{index}', 'profile')
        for group, state in enumerate(states)
        for index in range(high_group_size if state else 1)
    )
    records = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id='mathematical',
            protocol_id='constants',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(
                    sample.source_id,
                    sample.sample_id,
                    pressure,
                    float(states[int(sample.source_id[1:])]),
                    predicted,
                    sample.profile_id,
                )
                for sample in samples
                if not missing_high_sample or sample.sample_id != 's2'
                for pressure in ((1, 10, 100) if states[int(sample.source_id[1:])] else (1, 100))
            ),
        )
        for identifier, predicted in (('one', 1.0), ('zero', 0.0))
    )
    return samples, records


def selection(
    samples: tuple[GroupedSample, ...],
    records: tuple[RetentionCandidateComparisons, ...],
    *,
    plan: LearnedSelectionPlan = PLAN,
) -> LearnedNestedSelection:
    """Run the registered selector without native-function execution."""
    return select_grouped_forecast_candidates(
        records, samples=samples, candidate_kinds={'one': 'atomic', 'zero': 'atomic'}, plan=plan
    )


def materialize(
    samples: tuple[GroupedSample, ...],
    records: tuple[RetentionCandidateComparisons, ...],
    counts: tuple[int, ...],
) -> tuple[tuple[GroupedSample, ...], tuple[RetentionCandidateComparisons, ...]]:
    """Repeat observations while preserving the independent source group."""
    groups = tuple(
        GroupMembership(
            (f'g{group}', ''),
            tuple(
                (sample.source_id, sample.sample_id)
                for sample in samples
                if sample.source_id == f'g{group}'
            ),
        )
        for group in range(len(counts))
    )
    replay = resample_grouped_forecasts(
        records,
        samples=samples,
        groups=groups,
        multiplicities=tuple(
            GroupMultiplicity(group.group_id, count)
            for group, count in zip(groups, counts, strict=True)
        ),
        grouping='source',
    )
    return replay.samples, replay.candidates


def calibrate(high_group_size: int, *, missing_high_sample: bool = False) -> dict[str, object]:
    """Enumerate eight datasets and all ten bootstrap multiplicity vectors."""
    if isinstance(high_group_size, bool) or high_group_size not in (1, 3):
        message = 'The registered group sizes are 1 (control) and 3 (unequal).'
        raise ValueError(message)
    if missing_high_sample and high_group_size != _HIGH_GROUP_SIZE:
        message = 'Missing high targets require the registered three-sample high groups.'
        raise ValueError(message)
    plan = (
        replace(PLAN, fixed=replace(PLAN.fixed, minimum_coverage=2 / 3))
        if missing_high_sample
        else PLAN
    )
    datasets = []
    expected_losses = {'atomic': 0.0, 'ensemble': 0.0}
    expected_risks = {'atomic': 0.0, 'ensemble': 0.0}
    for states in product((0, 1), repeat=3):
        samples, records = forecasts(
            states, high_group_size, missing_high_sample=missing_high_sample
        )
        baseline = selection(samples, records, plan=plan)
        strategies = {}
        for kind in expected_losses:
            protocol = next(item for item in baseline.protocols if item.kind == kind)
            if protocol.status != 'computed':
                message = 'Every original dataset must support the registered procedure.'
                raise RuntimeError(message)
            risks = []
            for fold in baseline.folds:
                locked = getattr(fold, kind)
                prediction = (
                    locked.outer_fit.left_weight
                    if kind == 'ensemble'
                    else float(locked.candidate_id == 'one')
                )
                risks.append(population_risk(prediction, high_group_size))
            # Outer folds each train on two groups. Equal fold weighting here
            # estimates their average conditional risk, not sample-weighted CV.
            conditional_risk = sum(risks) / 3
            strategies[kind] = {
                'sample_weighted_outer_loss': protocol.mean_outer_loss,
                'total_sample_count': protocol.total_sample_count,
                'eligible_sample_count': protocol.eligible_sample_count,
                'equal_fold_mean_conditional_risk': conditional_risk,
            }
            expected_losses[kind] += protocol.mean_outer_loss / 8
            expected_risks[kind] += conditional_risk / 8
        draws = []
        complete_probability = Fraction(0)
        for counts in product(range(4), repeat=3):
            if sum(counts) != len(states):
                continue
            probability = Fraction(
                factorial(3),
                3**3 * factorial(counts[0]) * factorial(counts[1]) * factorial(counts[2]),
            )
            replay = selection(*materialize(samples, records, counts), plan=plan)
            complete = replay.status == 'computed' and all(
                item.status == 'computed' for item in replay.protocols
            )
            if complete:
                complete_probability += probability
            draws.append(
                {
                    'multiplicities': counts,
                    'probability': str(probability),
                    'status': 'complete' if complete else 'insufficient_evidence',
                    'unique_groups': sum(count > 0 for count in counts),
                    'split_failure_reason': replay.splits.reason,
                    'strategies': {item.kind: item.mean_outer_loss for item in replay.protocols},
                }
            )
        datasets.append(
            {
                'group_states': states,
                'probability': '1/8',
                'strategies': strategies,
                'bootstrap_complete_probability': str(complete_probability),
                'draws': draws,
            }
        )
    return {
        'method': 'exhaustive_three_group_constant_forecast_diagnostic_v1',
        'uncertainty_status': 'not_qualified_no_interval',
        'population': {
            'high_state_probability': '1/2',
            'low_group_size': 1,
            'high_group_size': high_group_size,
            'missing_target_policy': 'third_sample_of_each_high_group'
            if missing_high_sample
            else 'none',
        },
        'minimum_coverage': plan.fixed.minimum_coverage,
        'training_groups_per_outer_rule': 2,
        'estimand': 'expected_sample_risk_of_rule_trained_on_two_iid_groups',
        'expected_sample_weighted_outer_loss': expected_losses,
        'expected_equal_fold_conditional_risk': expected_risks,
        'bias_against_two_group_rule_risk': {
            kind: expected_losses[kind] - expected_risks[kind] for kind in expected_losses
        },
        'datasets': datasets,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--high-group-size', type=int, choices=(1, 3), required=True)
    parser.add_argument('--missing-high-sample', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    payload = calibrate(
        arguments.high_group_size, missing_high_sample=arguments.missing_high_sample
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
