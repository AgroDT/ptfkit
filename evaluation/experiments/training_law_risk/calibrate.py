"""Exact independent-training-block coverage with a separate failure law."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from math import factorial
from pathlib import Path

from ptfkit_eval import (
    GroupMembership,
    IndependentTrainingBlock,
    IndependentTrainingRiskPlan,
    LogPressureLossPlan,
    TrainingRiskTestGroup,
    bound_independent_training_risk,
)
from ptfkit_eval.artifacts import artifact_value


def group(source: str, size: int) -> GroupMembership:
    """Create a source-local complete group roster."""
    return GroupMembership((source, ''), tuple((source, f's{index}') for index in range(size)))


def evidence(
    counts: tuple[int, ...],
    *,
    high_group_size: int,
    total_learner: bool,
) -> tuple[IndependentTrainingBlock, ...]:
    """Canonical representatives of the four IID train/test state pairs."""
    blocks = []
    for count, (training_state, test_state) in zip(
        counts, ((0, 0), (0, 1), (1, 0), (1, 1)), strict=True
    ):
        for _ in range(count):
            index = len(blocks)
            training = group(f'b{index}_train', high_group_size if training_state else 1)
            test = group(f'b{index}_test', high_group_size if test_state else 1)
            failed = bool(training_state and not total_learner)
            losses = (
                None if failed else (float((test_state - training_state) ** 2),) * len(test.samples)
            )
            blocks.append(
                IndependentTrainingBlock(
                    f'b{index}',
                    (training,),
                    (TrainingRiskTestGroup(test, losses),),
                    'training_state_not_supported' if failed else None,
                )
            )
    return tuple(blocks)


def calibrate(*, n_blocks: int, high_group_size: int, total_learner: bool) -> dict[str, object]:
    """Enumerate every multinomial sufficient-count state, without success filtering."""
    if n_blocks not in (4, 12) or high_group_size not in (1, 3):
        message = 'Registered experiments use 4/12 blocks and high-group size 1/3.'
        raise ValueError(message)
    plan = IndependentTrainingRiskPlan(
        population_id='mathematical_iid_binary_train_test_groups',
        learner_id='state_mean_constant_v1'
        if total_learner
        else 'state_mean_with_state_one_failure_v1',
        grouping='source',
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
        maximum_sample_loss=1,
        minimum_group_size=1,
        maximum_group_size=high_group_size,
        training_groups_per_block=1,
        test_groups_per_block=1,
        n_blocks=n_blocks,
        total_learner=total_learner,
    )
    success_truth = Fraction(1) if total_learner else Fraction(1, 2)
    mass_truth = (
        Fraction(1, 2) if total_learner else Fraction(high_group_size, 2 * (1 + high_group_size))
    )
    risk_truth = mass_truth / success_truth
    joint_coverage = Fraction(0)
    issued = Fraction(0)
    error_and_issued = Fraction(0)
    cases = []
    for first in range(n_blocks + 1):
        for second in range(n_blocks - first + 1):
            for third in range(n_blocks - first - second + 1):
                fourth = n_blocks - first - second - third
                counts = (first, second, third, fourth)
                probability = Fraction(
                    factorial(n_blocks),
                    4**n_blocks
                    * factorial(first)
                    * factorial(second)
                    * factorial(third)
                    * factorial(fourth),
                )
                result = bound_independent_training_risk(
                    evidence(counts, high_group_size=high_group_size, total_learner=total_learner),
                    plan=plan,
                )
                success = result.training_success_probability_interval
                mass = result.risk_mass_on_success_interval
                if success is None or mass is None:
                    message = (
                        'Complete experimental blocks must produce success and risk-mass bounds.'
                    )
                    raise RuntimeError(message)
                conditional = result.successful_training_mean_risk_interval
                conditional_ok = (
                    conditional is None
                    or conditional.lower <= float(risk_truth) <= conditional.upper
                )
                covered = (
                    success.lower <= float(success_truth) <= success.upper
                    and mass.lower <= float(mass_truth) <= mass.upper
                    and conditional_ok
                )
                joint_coverage += probability * covered
                issued += probability * (conditional is not None)
                error_and_issued += probability * (conditional is not None and not conditional_ok)
                cases.append(
                    {
                        'state_pair_counts': counts,
                        'probability': str(probability),
                        'jointly_covered': covered,
                        'bound': artifact_value(result),
                    }
                )
    return {
        'method': plan.method,
        'plan': artifact_value(plan),
        'training_success_probability': str(success_truth),
        'risk_mass_on_success': str(mass_truth),
        'successful_training_mean_risk': str(risk_truth),
        'unconditional_model_risk': str(risk_truth) if total_learner else None,
        'joint_coverage_probability': str(joint_coverage),
        'conditional_interval_issue_probability': str(issued),
        'conditional_error_and_issued_probability': str(error_and_issued),
        'cases': cases,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blocks', type=int, choices=(4, 12), required=True)
    parser.add_argument('--high-group-size', type=int, choices=(1, 3), required=True)
    parser.add_argument('--total-learner', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = calibrate(
        n_blocks=arguments.blocks,
        high_group_size=arguments.high_group_size,
        total_learner=arguments.total_learner,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
