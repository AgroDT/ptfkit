"""Exact training-law calibration through the complete finite-grid selector."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import product
from math import factorial
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ptfkit_eval import (
    FixedSelectionPlan,
    GroupedSample,
    GroupMembership,
    HardSwitchGridFit,
    HardSwitchGridPlan,
    IndependentSelectionTrainingRisk,
    IndependentTrainingBlock,
    IndependentTrainingRiskPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    PairedTrainingRiskPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    TrainingRiskTestGroup,
    allocate_independent_training_blocks,
    assess_independent_forecast_training,
    bound_independent_training_risk,
    bound_paired_independent_training_risk,
    pair_selection_training_evidence,
)
from ptfkit_eval.artifacts import artifact_value


if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class PopulationState:
    """A whole-group outcome, with an exact probability and replicated samples."""

    name: str
    size: int
    curve: Literal['early', 'late']
    probability: Fraction


OutcomeKey = tuple[bool, int, Fraction]


@dataclass(frozen=True)
class LocalLaw:
    """Exact sufficient-state law induced by complete selector invocations."""

    keys: tuple[OutcomeKey, ...]
    probabilities: tuple[Fraction, ...]
    representatives: tuple[IndependentTrainingBlock, ...]
    success: Fraction
    mass: Fraction
    conditional: Fraction
    late_fraction: Fraction
    traces: list[dict[str, object]]


POPULATIONS = {
    'equal_binary': (
        PopulationState('early_one', 1, 'early', Fraction(1, 2)),
        PopulationState('late_one', 1, 'late', Fraction(1, 2)),
    ),
    'informative_four': (
        PopulationState('early_one', 1, 'early', Fraction(1, 2)),
        PopulationState('late_one', 1, 'late', Fraction(1, 4)),
        PopulationState('early_three', 3, 'early', Fraction(1, 8)),
        PopulationState('late_three', 3, 'late', Fraction(1, 8)),
    ),
}
LOSS = LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100, minimum_points=3)
EARLY_BOUNDARY = 5
LATE_BOUNDARY = 10
SELECTOR = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('high', 'low'),
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
        loss=LOSS,
    ),
    ensembles=(
        HardSwitchGridPlan(
            id='trained_switch',
            left_candidate_id='high',
            right_candidate_id='low',
            boundary_grid_kpa=(EARLY_BOUNDARY, LATE_BOUNDARY),
            boundary_member='left',
            minimum_training_groups=1,
            minimum_loss_gap=1e-12,
        ),
    ),
    method='nested_two_curve_selection_v1',
)
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')
KINDS: dict[str, Literal['atomic', 'ensemble']] = {'high': 'atomic', 'low': 'atomic'}


def risk_plan(population: str, n_blocks: int) -> IndependentTrainingRiskPlan:
    """Register the exact same two-training-group learner for every block count."""
    return IndependentTrainingRiskPlan(
        population_id=f'mathematical_selector_{population}',
        learner_id='singleton_inner_cv_two_group_hard_switch_v1',
        grouping='source',
        loss=LOSS,
        maximum_sample_loss=1 / 8,
        minimum_group_size=1,
        maximum_group_size=max(s.size for s in POPULATIONS[population]),
        training_groups_per_block=2,
        test_groups_per_block=1,
        n_blocks=n_blocks,
    )


def _execute_case(
    population: str,
    training: tuple[PopulationState, PopulationState],
    test: PopulationState,
    *,
    for_pair: bool = False,
) -> tuple[IndependentSelectionTrainingRisk, dict[str, object]]:
    """Run the actual allocation, inner tuning, outer refit and test-loss adapter."""
    plan = risk_plan(population, 2)
    if for_pair:
        plan = replace(plan, maximum_sample_loss=3 / 16, learner_id='atomic_and_switch_training_v1')
    initial = tuple(GroupedSample(f'original_{i}', 's0') for i in range(6))
    allocated = allocate_independent_training_blocks(initial, plan=plan, seed=71)
    states = {s.source_id: POPULATIONS[population][0] for s in initial}
    first = allocated.blocks[0]
    for group, state in zip(first.training_groups, training, strict=True):
        states[group.group_id[0]] = state
    states[first.test_groups[0].group_id[0]] = test
    samples = tuple(
        GroupedSample(source, f's{i}')
        for source, state in sorted(states.items())
        for i in range(state.size)
    )
    candidates = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id=plan.population_id,
            protocol_id='three_pressure_grid',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(sample.source_id, sample.sample_id, pressure, observed, value)
                for sample in samples
                for pressure, observed in (
                    (1, 0.75),
                    (10, 0.75 if states[sample.source_id].curve == 'late' else 0.25),
                    (100, 0.25),
                )
            ),
        )
        for identifier, value in (('high', 0.75), ('low', 0.25))
    )
    result = assess_independent_forecast_training(
        candidates,
        samples=samples,
        candidate_kinds=KINDS,
        selection_plan=SELECTOR,
        bounds=plan,
        strategy='ensemble',
        seed=71,
    )
    block = result.blocks[0]
    selected = block.selection.folds[0].ensemble
    fit = selected.outer_fit
    if not isinstance(fit, HardSwitchGridFit) or selected.candidate_id != 'trained_switch':
        message = 'Every singleton inner fit must exist and select the registered switch.'
        raise RuntimeError(message)
    # Independent oracle: only the middle pressure differs, with exact weight
    # 1/2 and squared difference 1/4, hence loss 1/8 for a mismatched curve.
    late = sum(s.size for s in training if s.curve == 'late')
    early = sum(s.size for s in training if s.curve == 'early')
    oracle = None if late == early else LATE_BOUNDARY if late > early else EARLY_BOUNDARY
    if fit.switch_suction_kpa != oracle:
        message = 'The actual selector disagrees with the whole-sample majority oracle.'
        raise RuntimeError(message)
    failure = 'unidentifiable_boundary' if oracle is None else None
    expected = (
        None
        if oracle is None
        else (
            float(
                Fraction(oracle != (LATE_BOUNDARY if test.curve == 'late' else EARLY_BOUNDARY), 8)
            ),
        )
        * test.size
    )
    actual = block.evidence.test_groups[0].sample_losses
    if block.evidence.training_failure_reason != failure or actual != expected:
        message = 'Complete training/test evidence disagrees with the independent exact oracle.'
        raise RuntimeError(message)
    return result, {
        'training_states': [s.name for s in training],
        'test_state': test.name,
        'probability': str(training[0].probability * training[1].probability * test.probability),
        'oracle_boundary_kpa': oracle,
        'samples': artifact_value(samples),
        'candidates': artifact_value(candidates),
        'block': artifact_value(block),
    }


def _probe(
    population: str, training: tuple[PopulationState, PopulationState], test: PopulationState
) -> tuple[IndependentTrainingBlock, dict[str, object]]:
    result, trace = _execute_case(population, training, test)
    return result.blocks[0].evidence, trace


def local_law(population: str) -> LocalLaw:
    """Push the exact IID group law through the public complete-selector path."""
    states = POPULATIONS[population]
    probabilities: dict[tuple[bool, int, Fraction], Fraction] = defaultdict(Fraction)
    representatives = {}
    traces = []
    success = Fraction(0)
    mass = Fraction(0)
    mean_size = sum((s.probability * s.size for s in states), Fraction(0))
    late_size = sum((s.probability * s.size for s in states if s.curve == 'late'), Fraction(0))
    late_fraction = late_size / mean_size
    for one, two, test in product(states, repeat=3):
        evidence, trace = _probe(population, (one, two), test)
        traces.append(trace)
        probability = one.probability * two.probability * test.probability
        failed = evidence.training_failure_reason is not None
        losses = evidence.test_groups[0].sample_losses
        key = (failed, test.size, sum((Fraction(x) for x in losses or ()), Fraction(0)))
        probabilities[key] += probability
        representatives.setdefault(key, evidence)
        # Population risk comes from fresh test groups, not this finite test
        # ratio. E[N_late]/E[N] preserves informative group-size weighting.
        if not failed:
            success += probability
            boundary = trace['oracle_boundary_kpa']
            risk = (late_fraction if boundary == EARLY_BOUNDARY else 1 - late_fraction) / 8
            mass += probability * risk
    ordered = tuple(sorted(probabilities))
    return LocalLaw(
        ordered,
        tuple(probabilities[key] for key in ordered),
        tuple(representatives[key] for key in ordered),
        success,
        mass,
        mass / success,
        late_fraction,
        traces,
    )


def count_vectors(total: int, slots: int) -> Iterator[tuple[int, ...]]:
    """Enumerate every sufficient-count vector without random sampling."""
    if slots == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for rest in count_vectors(total - first, slots - 1):
                yield (first, *rest)


def _rename(group: GroupMembership, prefix: str) -> GroupMembership:
    return GroupMembership(
        (prefix, ''), tuple((prefix, f's{i}') for i in range(len(group.samples)))
    )


def _blocks(
    counts: tuple[int, ...], representatives: tuple[IndependentTrainingBlock, ...]
) -> tuple[IndependentTrainingBlock, ...]:
    """Instantiate disjoint representatives with identical sufficient statistics."""
    output = []
    for count, example in zip(counts, representatives, strict=True):
        for _ in range(count):
            prefix = f'original_block_{len(output)}'
            output.append(
                IndependentTrainingBlock(
                    prefix,
                    tuple(
                        _rename(g, f'{prefix}_train_{i}')
                        for i, g in enumerate(example.training_groups)
                    ),
                    tuple(
                        TrainingRiskTestGroup(
                            _rename(g.group, f'{prefix}_test_{i}'), g.sample_losses
                        )
                        for i, g in enumerate(example.test_groups)
                    ),
                    example.training_failure_reason,
                )
            )
    return tuple(output)


def calibrate(*, population: str, n_blocks: int) -> dict[str, object]:
    """Convolve the actual learner's law and check joint unconditional coverage."""
    if population not in POPULATIONS or n_blocks not in (4, 12):
        message = 'Registered calibration uses equal_binary/informative_four and 4/12 blocks.'
        raise ValueError(message)
    law = local_law(population)
    probabilities = law.probabilities
    representatives = law.representatives
    plan = risk_plan(population, n_blocks)
    success = law.success
    mass = law.mass
    conditional = law.conditional
    joint = Fraction(0)
    issued = Fraction(0)
    error_and_issued = Fraction(0)
    cases = []
    for counts in count_vectors(n_blocks, len(probabilities)):
        probability = Fraction(factorial(n_blocks))
        for count, p in zip(counts, probabilities, strict=True):
            probability *= Fraction(p.numerator**count, p.denominator**count * factorial(count))
        bound = bound_independent_training_risk(_blocks(counts, representatives), plan=plan)
        success_ci = bound.training_success_probability_interval
        mass_ci = bound.risk_mass_on_success_interval
        if success_ci is None or mass_ci is None:
            message = 'All exact count states require complete success and risk-mass bounds.'
            raise RuntimeError(message)
        risk_ci = bound.successful_training_mean_risk_interval
        risk_ok = risk_ci is None or risk_ci.lower <= float(conditional) <= risk_ci.upper
        covered = (
            success_ci.lower <= float(success) <= success_ci.upper
            and mass_ci.lower <= float(mass) <= mass_ci.upper
            and risk_ok
        )
        joint += probability * covered
        issued += probability * (risk_ci is not None)
        error_and_issued += probability * (risk_ci is not None and not risk_ok)
        cases.append(
            {
                'sufficient_state_counts': counts,
                'probability': str(probability),
                'jointly_covered': covered,
                'bound': artifact_value(bound),
            }
        )
    return {
        'population': population,
        'plan': artifact_value(plan),
        'selector': artifact_value(SELECTOR),
        'training_success_probability': str(success),
        'risk_mass_on_success': str(mass),
        'successful_training_mean_risk': str(conditional),
        'population_late_sample_fraction': str(law.late_fraction),
        'unconditional_model_risk': None,
        'sufficient_states': [
            {
                'failed_training': k[0],
                'test_size': k[1],
                'loss_sum': str(k[2]),
                'probability': str(p),
            }
            for k, p in zip(law.keys, probabilities, strict=True)
        ],
        'joint_coverage_probability': str(joint),
        'conditional_interval_issue_probability': str(issued),
        'conditional_error_and_issued_probability': str(error_and_issued),
        'local_cases': law.traces,
        'cases': cases,
    }


@dataclass(frozen=True)
class PairedLocalLaw:
    """Actual joint learner outcomes plus independent population risk targets."""

    keys: tuple[tuple[bool, int], ...]
    probabilities: tuple[Fraction, ...]
    left: tuple[IndependentTrainingBlock, ...]
    right: tuple[IndependentTrainingBlock, ...]
    success: Fraction
    marginal_difference: Fraction
    traces: list[dict[str, object]]


def paired_local_law(population: str) -> PairedLocalLaw:
    """Pair the actual inner-selected atomic and learned-switch outputs."""
    states = POPULATIONS[population]
    probabilities: dict[tuple[bool, int], Fraction] = defaultdict(Fraction)
    left, right = {}, {}
    traces = []
    success = Fraction(0)
    atomic_risk = Fraction(0)
    ensemble_mass = Fraction(0)
    mean_size = sum((s.probability * s.size for s in states), Fraction(0))
    late_fraction = (
        sum((s.probability * s.size for s in states if s.curve == 'late'), Fraction(0)) / mean_size
    )
    for one, two, test in product(states, repeat=3):
        result, trace = _execute_case(population, (one, two), test, for_pair=True)
        plan = PairedTrainingRiskPlan(
            bounds=result.allocation.plan,
            left_learner_id='inner_selected_atomic_v1',
            right_learner_id='inner_selected_grid_switch_v1',
        )
        paired = pair_selection_training_evidence(
            result, plan=plan, left_strategy='atomic', right_strategy='ensemble'
        )
        block = paired.blocks[0]
        probability = one.probability * two.probability * test.probability
        failed = block.right.training_failure_reason is not None
        key = (failed, test.size)
        probabilities[key] += probability
        left.setdefault(key, block.left)
        right.setdefault(key, block.right)
        if block.left.training_failure_reason is not None:
            message = 'The fixed atomic strategy must remain defined on all training states.'
            raise RuntimeError(message)
        if not failed:
            a, b = block.left.test_groups[0].sample_losses, block.right.test_groups[0].sample_losses
            if (
                a is None
                or b is None
                or any(
                    Fraction(x) - Fraction(y) != Fraction(1, 16) for x, y in zip(a, b, strict=True)
                )
            ):
                message = (
                    'Actual joint-success loss differences must equal the independent 1/16 oracle.'
                )
                raise RuntimeError(message)
            success += probability
            risk = (
                late_fraction
                if trace['oracle_boundary_kpa'] == EARLY_BOUNDARY
                else 1 - late_fraction
            ) / 8
            ensemble_mass += probability * risk
        late = sum(s.size for s in (one, two) if s.curve == 'late')
        early = sum(s.size for s in (one, two) if s.curve == 'early')
        # A tie selects 'high' lexically. This population calculation includes
        # those atomic models, unlike conditioning on the switch also existing.
        atomic_risk += probability * (
            Fraction(1, 16) + (1 - late_fraction if late >= early else late_fraction) / 8
        )
        traces.append({**trace, 'paired_block': artifact_value(block)})
    keys = tuple(sorted(probabilities))
    return PairedLocalLaw(
        keys,
        tuple(probabilities[k] for k in keys),
        tuple(left[k] for k in keys),
        tuple(right[k] for k in keys),
        success,
        atomic_risk - ensemble_mass / success,
        traces,
    )


def calibrate_pair(*, population: str, n_blocks: int) -> dict[str, object]:
    """Enumerate the joint-success comparison law, not marginal CI subtraction."""
    if population not in POPULATIONS or n_blocks not in (4, 12):
        message = (
            'Registered paired calibration uses equal_binary/informative_four and 4/12 blocks.'
        )
        raise ValueError(message)
    law = paired_local_law(population)
    plan = PairedTrainingRiskPlan(
        bounds=replace(
            risk_plan(population, n_blocks),
            maximum_sample_loss=3 / 16,
            learner_id='atomic_and_switch_training_v1',
        ),
        left_learner_id='inner_selected_atomic_v1',
        right_learner_id='inner_selected_grid_switch_v1',
    )
    mass_truth, conditional_truth = law.success / 16, Fraction(1, 16)
    joint = Fraction(0)
    issued = Fraction(0)
    error_and_issued = Fraction(0)
    cases = []
    for counts in count_vectors(n_blocks, len(law.probabilities)):
        probability = Fraction(factorial(n_blocks))
        for count, p in zip(counts, law.probabilities, strict=True):
            probability *= Fraction(p.numerator**count, p.denominator**count * factorial(count))
        bound = bound_paired_independent_training_risk(
            _blocks(counts, law.left), _blocks(counts, law.right), plan=plan
        )
        p_ci = bound.joint_success_probability_interval
        mass_ci = bound.risk_difference_mass_on_joint_success_interval
        if p_ci is None or mass_ci is None:
            message = 'Complete paired states require joint-success and signed-mass bounds.'
            raise RuntimeError(message)
        conditional = bound.joint_success_mean_risk_difference_interval
        risk_ok = (
            conditional is None
            or conditional.lower <= float(conditional_truth) <= conditional.upper
        )
        covered = (
            p_ci.lower <= float(law.success) <= p_ci.upper
            and mass_ci.lower <= float(mass_truth) <= mass_ci.upper
            and risk_ok
        )
        joint += probability * covered
        issued += probability * (conditional is not None)
        error_and_issued += probability * (conditional is not None and not risk_ok)
        cases.append(
            {
                'sufficient_state_counts': counts,
                'probability': str(probability),
                'jointly_covered': covered,
                'bound': artifact_value(bound),
            }
        )
    return {
        'population': population,
        'plan': artifact_value(plan),
        'comparison': 'atomic_minus_ensemble',
        'joint_training_success_probability': str(law.success),
        'risk_difference_mass_on_joint_success': str(mass_truth),
        'joint_success_mean_risk_difference': str(conditional_truth),
        'difference_of_marginal_successful_training_risks': str(law.marginal_difference),
        'unconditional_model_risk_difference': None,
        'sufficient_states': [
            {'failed_training': k[0], 'test_size': k[1], 'probability': str(p)}
            for k, p in zip(law.keys, law.probabilities, strict=True)
        ],
        'joint_coverage_probability': str(joint),
        'conditional_interval_issue_probability': str(issued),
        'conditional_error_and_issued_probability': str(error_and_issued),
        'local_cases': law.traces,
        'cases': cases,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--population', choices=tuple(POPULATIONS), required=True)
    parser.add_argument('--blocks', type=int, choices=(4, 12), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--paired', action='store_true')
    arguments = parser.parse_args()
    calibrator = calibrate_pair if arguments.paired else calibrate
    result = calibrator(population=arguments.population, n_blocks=arguments.blocks)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
