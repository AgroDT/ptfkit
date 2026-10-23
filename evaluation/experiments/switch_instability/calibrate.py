"""Exhaustive hard-switch identification diagnostic; no interval is qualified."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from itertools import product
from math import factorial
from pathlib import Path

from ptfkit_eval import (
    FixedSelectionPlan,
    GroupedSample,
    GroupMembership,
    GroupMultiplicity,
    HardSwitchGridPlan,
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
from ptfkit_eval.artifacts import artifact_value


GROUP_COUNT = 3
MIDDLE_PRESSURE_KPA = 10
PLAN = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('left', 'right'),
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    ),
    ensembles=(
        HardSwitchGridPlan(
            id='switch',
            left_candidate_id='left',
            right_candidate_id='right',
            boundary_grid_kpa=(5, 10),
            boundary_member='left',
            minimum_training_groups=1,
            minimum_loss_gap=1e-12,
        ),
    ),
    method='nested_two_curve_selection_v1',
)
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')


def forecasts(
    states: tuple[int, ...],
    high_group_size: int,
) -> tuple[tuple[GroupedSample, ...], tuple[RetentionCandidateComparisons, ...]]:
    """Two monotone mathematical target curves, differing only at 10 kPa."""
    samples = tuple(
        GroupedSample(f'g{group}', f's{index}', 'profile')
        for group, state in enumerate(states)
        for index in range(high_group_size if state else 1)
    )
    records = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id='mathematical_switch',
            protocol_id='three_pressure_switch',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(
                    sample.source_id,
                    sample.sample_id,
                    pressure,
                    0.25
                    + 0.5
                    * (
                        pressure == 1
                        or (pressure == MIDDLE_PRESSURE_KPA and states[int(sample.source_id[1:])])
                    ),
                    prediction,
                    sample.profile_id,
                )
                for sample in samples
                for pressure in (1, 10, 100)
            ),
        )
        for identifier, prediction in (('left', 0.75), ('right', 0.25))
    )
    return samples, records


def select(
    samples: tuple[GroupedSample, ...],
    records: tuple[RetentionCandidateComparisons, ...],
) -> LearnedNestedSelection:
    """Run the same nested procedure as native PTF selection."""
    return select_grouped_forecast_candidates(
        records, samples=samples, candidate_kinds={'left': 'atomic', 'right': 'atomic'}, plan=PLAN
    )


def training_law_oracle(high_group_size: int) -> dict[str, object]:
    """Exact four-state oracle, independent of fitted selection evidence."""
    atomic_risk = Fraction(0)
    switch_risk_mass = Fraction(0)
    switch_success = Fraction(0)
    for first, second in product((0, 1), repeat=2):
        high = (first + second) * high_group_size
        low = 2 - first - second
        # Constant curves incur 1/16 at the distant endpoint and an additional
        # 1/8 when their middle-pressure value differs from the target state.
        atomic_left = high >= low
        atomic_risk += (
            Fraction(1, 16)
            + Fraction(1 if atomic_left else high_group_size, 8 * (1 + high_group_size))
        ) / 4
        if high == low:
            continue
        switch_success += Fraction(1, 4)
        switch_risk_mass += (
            Fraction(1 if high > low else high_group_size, 8 * (1 + high_group_size)) / 4
        )
    return {
        'atomic': {
            'failure_probability': '0',
            'risk_mass_on_success': str(atomic_risk),
            'conditional_mean_risk': str(atomic_risk),
            'unconditional_mean_risk': str(atomic_risk),
        },
        'ensemble': {
            'failure_probability': str(1 - switch_success),
            'risk_mass_on_success': str(switch_risk_mass),
            'conditional_mean_risk': str(switch_risk_mass / switch_success),
            'unconditional_mean_risk': str(switch_risk_mass) if switch_success == 1 else None,
        },
    }


def bootstrap_draws(
    samples: tuple[GroupedSample, ...],
    records: tuple[RetentionCandidateComparisons, ...],
) -> tuple[dict[str, object], ...]:
    """Enumerate the exact original-group bootstrap law without retries."""
    groups = tuple(
        GroupMembership(
            (f'g{group}', ''),
            tuple(
                (sample.source_id, sample.sample_id)
                for sample in samples
                if sample.source_id == f'g{group}'
            ),
        )
        for group in range(GROUP_COUNT)
    )
    draws = []
    for counts in product(range(GROUP_COUNT + 1), repeat=GROUP_COUNT):
        if sum(counts) != GROUP_COUNT:
            continue
        probability = Fraction(
            factorial(GROUP_COUNT),
            GROUP_COUNT**GROUP_COUNT
            * factorial(counts[0])
            * factorial(counts[1])
            * factorial(counts[2]),
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
        selected = select(replay.samples, replay.candidates)
        statuses = {item.kind: item.status for item in selected.protocols}
        draws.append(
            {
                'multiplicities': counts,
                'probability': str(probability),
                'strategy_status': {
                    kind: statuses.get(kind, 'insufficient_evidence')
                    for kind in ('atomic', 'ensemble')
                },
                'sample_map': artifact_value(replay.sample_map),
                'selection': artifact_value(selected),
            }
        )
    return tuple(draws)


def calibrate(high_group_size: int) -> dict[str, object]:
    """Enumerate every original dataset, fit failure, and bootstrap trajectory."""
    if isinstance(high_group_size, bool) or high_group_size not in (1, GROUP_COUNT):
        message = 'The registered high-group sizes are 1 and 3.'
        raise ValueError(message)
    datasets = []
    complete = {'atomic': Fraction(0), 'ensemble': Fraction(0)}
    loss_mass = {'atomic': 0.0, 'ensemble': 0.0}
    for states in product((0, 1), repeat=GROUP_COUNT):
        samples, records = forecasts(states, high_group_size)
        baseline = select(samples, records)
        for protocol in baseline.protocols:
            if protocol.mean_outer_loss is not None:
                complete[protocol.kind] += Fraction(1, 8)
                loss_mass[protocol.kind] += protocol.mean_outer_loss / 8
        draws = bootstrap_draws(samples, records)
        datasets.append(
            {
                'group_states': states,
                'probability': '1/8',
                'selection': artifact_value(baseline),
                'bootstrap_complete_probability': {
                    kind: str(
                        sum(
                            (
                                Fraction(draw['probability'])
                                for draw in draws
                                if draw['strategy_status'][kind] == 'computed'
                            ),
                            Fraction(0),
                        )
                    )
                    for kind in complete
                },
                'draws': draws,
            }
        )
    return {
        'method': 'exhaustive_three_group_switch_identification_diagnostic_v1',
        'uncertainty_status': 'not_qualified_no_interval',
        'population': {
            'high_state_probability': '1/2',
            'low_group_size': 1,
            'high_group_size': high_group_size,
        },
        'estimand': 'sample_risk_of_rule_trained_on_two_iid_groups_with_explicit_fit_failure',
        'training_law_oracle': training_law_oracle(high_group_size),
        'crossfit_strategy': {
            kind: {
                'complete_dataset_probability': str(complete[kind]),
                'conditional_mean_complete_dataset_loss': loss_mass[kind] / float(complete[kind]),
                'unconditional_mean_loss': loss_mass[kind] if complete[kind] == 1 else None,
            }
            for kind in complete
        },
        'datasets': datasets,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--high-group-size', type=int, choices=(1, 3), required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(calibrate(arguments.high_group_size), indent=2) + '\n', encoding='utf-8'
    )
