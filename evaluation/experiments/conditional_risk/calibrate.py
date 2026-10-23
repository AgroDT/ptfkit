"""Exact coverage of bounded conditional fold-risk bands for fitted constants."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from itertools import product
from math import comb
from pathlib import Path

from ptfkit_eval import (
    BoundedGroupLoss,
    ConditionalOuterFoldLoss,
    ConditionalOuterRiskPlan,
    LogPressureLossPlan,
    bound_conditional_outer_risks,
)
from ptfkit_eval.artifacts import artifact_value


def population_risk(prediction: Fraction, high_group_size: int) -> Fraction:
    """Exact fresh-sample risk, including informative population group sizes."""
    return (prediction**2 + high_group_size * (1 - prediction) ** 2) / (1 + high_group_size)


def fitted_constant(high_count: int, groups: int, high_group_size: int) -> Fraction:
    """Independent closed-form sample-balanced squared-loss fit on training only."""
    high_samples = high_count * high_group_size
    return Fraction(high_samples, high_samples + groups - high_count)


def losses(
    counts: tuple[int, int],
    groups_per_fold: int,
    high_group_size: int,
) -> tuple[ConditionalOuterFoldLoss, ...]:
    """Each fold's constant is fitted exclusively on the opposite fold."""
    predictions = tuple(
        fitted_constant(count, groups_per_fold, high_group_size) for count in reversed(counts)
    )
    groups = tuple(
        tuple(
            BoundedGroupLoss(
                (f'fold{fold}_group{index}', ''),
                (float((int(index < count) - prediction) ** 2),)
                * (high_group_size if index < count else 1),
            )
            for index in range(groups_per_fold)
        )
        for fold, (count, prediction) in enumerate(zip(counts, predictions, strict=True))
    )
    return tuple(
        ConditionalOuterFoldLoss(
            fold,
            tuple(group.group_id for group in groups[1 - fold]),
            groups[fold],
        )
        for fold in (0, 1)
    )


def calibrate(*, groups_per_fold: int, high_group_size: int) -> dict[str, object]:
    """Enumerate sufficient group-state counts with exact binomial probabilities."""
    if groups_per_fold not in (4, 20) or high_group_size not in (1, 3):
        message = 'Registered designs use 4 or 20 groups per fold and high-group size 1 or 3.'
        raise ValueError(message)
    plan = ConditionalOuterRiskPlan(
        population_id='mathematical_independent_binary_groups',
        grouping='source',
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
        maximum_sample_loss=1,
        maximum_group_size=high_group_size,
    )
    simultaneous_coverage = Fraction(0)
    mixture_coverage = Fraction(0)
    nonvacuous = Fraction(0)
    cases = []
    for first, second in product(range(groups_per_fold + 1), repeat=2):
        counts = (first, second)
        probability = Fraction(
            comb(groups_per_fold, first) * comb(groups_per_fold, second), 2 ** (2 * groups_per_fold)
        )
        result = bound_conditional_outer_risks(
            losses(counts, groups_per_fold, high_group_size), plan=plan
        )
        risks = tuple(
            population_risk(
                fitted_constant(count, groups_per_fold, high_group_size), high_group_size
            )
            for count in reversed(counts)
        )
        mixture_risk = sum(risks) / 2
        covered = all(
            bound.risk_interval.lower <= float(risk) <= bound.risk_interval.upper
            for bound, risk in zip(result.folds, risks, strict=True)
        )
        interval = result.equal_fold_mean_risk_interval
        mixture_covered = interval.lower <= float(mixture_risk) <= interval.upper
        informative = interval.upper - interval.lower < plan.maximum_sample_loss
        simultaneous_coverage += probability * covered
        mixture_coverage += probability * mixture_covered
        nonvacuous += probability * informative
        cases.append(
            {
                'high_group_counts': counts,
                'probability': str(probability),
                'conditional_fold_risks': [str(risk) for risk in risks],
                'true_equal_fold_mean_risk': str(mixture_risk),
                'simultaneously_covered': covered,
                'mixture_covered': mixture_covered,
                'mixture_interval': {'lower': interval.lower, 'upper': interval.upper},
                'bound': artifact_value(result),
            }
        )
    return {
        'method': plan.method,
        'plan': artifact_value(plan),
        'target': 'equal_fold_mean_conditional_sample_risk',
        'groups_per_fold': groups_per_fold,
        'high_group_size': high_group_size,
        'confidence_level': plan.confidence_level,
        'maximum_sample_loss': plan.maximum_sample_loss,
        'training_group_count_per_rule': groups_per_fold,
        'simultaneous_coverage_probability': str(simultaneous_coverage),
        'mixture_coverage_probability': str(mixture_coverage),
        'nonvacuous_interval_probability': str(nonvacuous),
        'cases': cases,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups-per-fold', type=int, choices=(4, 20), required=True)
    parser.add_argument('--high-group-size', type=int, choices=(1, 3), required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    payload = calibrate(
        groups_per_fold=arguments.groups_per_fold, high_group_size=arguments.high_group_size
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
