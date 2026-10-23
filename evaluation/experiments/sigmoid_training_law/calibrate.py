"""Finite-population coverage of complete sigmoid-steepness selection with failed fits."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import json
import math
import runpy
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from pathlib import Path

from ptfkit_eval import (
    FixedSelectionPlan,
    GroupedSample,
    IndependentTrainingBlock,
    IndependentTrainingRiskPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    SigmoidGridFit,
    SigmoidGridPlan,
    TargetSpec,
    allocate_independent_training_blocks,
    assess_independent_forecast_training,
    bound_independent_training_risk,
)
from ptfkit_eval.artifacts import artifact_value


ROOT = Path(__file__).resolve().parent
REFERENCE = runpy.run_path(str(ROOT / '../selector_training_law/calibrate.py'))


@dataclass(frozen=True)
class State:
    """An independently declared original-group curve and exact probability."""

    name: str
    size: int
    late: bool
    probability: Fraction


POPULATIONS = {
    'equal_binary': (
        State('early_one', 1, late=False, probability=Fraction(1, 2)),
        State('late_one', 1, late=True, probability=Fraction(1, 2)),
    ),
    'informative_four': (
        State('early_one', 1, late=False, probability=Fraction(1, 2)),
        State('late_one', 1, late=True, probability=Fraction(1, 4)),
        State('early_three', 3, late=False, probability=Fraction(1, 8)),
        State('late_three', 3, late=True, probability=Fraction(1, 8)),
    ),
}
LOSS = LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100, minimum_points=3)
SLOPE = math.log(2)
MISMATCH = Fraction(2, 225)
SELECTOR = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('one', 'zero'),
        loss=LOSS,
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
    ),
    ensembles=(
        SigmoidGridPlan(
            id='gate',
            left_candidate_id='one',
            right_candidate_id='zero',
            parameter_grid=((10, SLOPE), (10, 2 * SLOPE)),
            minimum_training_groups=1,
            minimum_loss_gap=1e-12,
        ),
    ),
    method='nested_two_curve_selection_v1',
)


def risk_plan(population: str, n_blocks: int) -> IndependentTrainingRiskPlan:
    """Use a binary prior bound strictly larger than every support loss."""
    return IndependentTrainingRiskPlan(
        population_id=f'mathematical_sigmoid_steepness_{population}',
        learner_id='singleton_inner_cv_two_group_sigmoid_v1',
        grouping='source',
        loss=LOSS,
        maximum_sample_loss=1 / 64,
        minimum_group_size=1,
        maximum_group_size=max(s.size for s in POPULATIONS[population]),
        training_groups_per_block=2,
        test_groups_per_block=1,
        n_blocks=n_blocks,
    )


def probe(
    population: str,
    one: State,
    two: State,
    test: State,
) -> tuple[IndependentTrainingBlock, dict[str, object]]:
    """Fit the real public selector and check an independent rational curve oracle."""
    plan = risk_plan(population, 2)
    original = tuple(GroupedSample(f'original_{i}', 's0') for i in range(6))
    allocation = allocate_independent_training_blocks(original, plan=plan, seed=71)
    roles = allocation.blocks[0]
    states = {s.source_id: POPULATIONS[population][0] for s in original}
    for group, state in zip(roles.training_groups, (one, two), strict=True):
        states[group.group_id[0]] = state
    states[roles.test_groups[0].group_id[0]] = test
    samples = tuple(
        GroupedSample(source, f's{i}')
        for source, state in sorted(states.items())
        for i in range(state.size)
    )
    candidates = tuple(
        RetentionCandidateComparisons(
            candidate_id=name,
            dataset_id=plan.population_id,
            protocol_id='three_pressure_sigmoids',
            target=TargetSpec(
                'volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume'
            ),
            comparisons=tuple(
                RetentionComparison(s.source_id, s.sample_id, pressure, float(observed), prediction)
                for s in samples
                for pressure, observed in zip(
                    (1, 10, 100),
                    (Fraction(4, 5), Fraction(1, 2), Fraction(1, 5))
                    if states[s.source_id].late
                    else (Fraction(2, 3), Fraction(1, 2), Fraction(1, 3)),
                    strict=True,
                )
            ),
        )
        for name, prediction in (('one', 1), ('zero', 0))
    )
    result = assess_independent_forecast_training(
        candidates,
        samples=samples,
        candidate_kinds={'one': 'atomic', 'zero': 'atomic'},
        selection_plan=SELECTOR,
        bounds=plan,
        strategy='ensemble',
        seed=71,
    )
    block = result.blocks[0]
    fit = block.selection.folds[0].ensemble.outer_fit
    late = sum(s.size for s in (one, two) if s.late)
    early = sum(s.size for s in (one, two) if not s.late)
    expected = None if late == early else (10, 2 * SLOPE if late > early else SLOPE)
    failure = 'unidentifiable_sigmoid_parameters' if expected is None else None
    values = block.evidence.test_groups[0].sample_losses
    expected_loss = float(MISMATCH * ((late > early) != test.late))
    if (
        not isinstance(fit, SigmoidGridFit)
        or fit.parameters != expected
        or block.evidence.training_failure_reason != failure
    ):
        message = 'Actual sigmoid fitting disagrees with the sample-majority oracle.'
        raise RuntimeError(message)
    if expected is None:
        if values is not None:
            message = 'Failed sigmoid training invented sample losses.'
            raise RuntimeError(message)
    elif (
        values is None
        or len(values) != test.size
        or any(not math.isclose(v, expected_loss, rel_tol=1e-14, abs_tol=1e-30) for v in values)
    ):
        message = 'Actual sigmoid losses disagree with rational 2/225 mismatch loss.'
        raise RuntimeError(message)
    return block.evidence, {
        'training_states': [one.name, two.name],
        'test_state': test.name,
        'probability': str(one.probability * two.probability * test.probability),
        'oracle_parameters': expected,
        'samples': artifact_value(samples),
        'candidates': artifact_value(candidates),
        'block': artifact_value(block),
    }


def calibrate(*, population: str, n_blocks: int) -> dict[str, object]:
    """Enumerate exact probabilities and actual complete-selector sufficient states."""
    if population not in POPULATIONS or n_blocks not in (4, 12):
        message = 'Calibration requires a registered population and 4/12 blocks.'
        raise ValueError(message)
    probabilities = defaultdict(Fraction)
    representatives = {}
    traces = []
    for one, two, test in product(POPULATIONS[population], repeat=3):
        evidence, trace = probe(population, one, two, test)
        traces.append(trace)
        key = (
            evidence.training_failure_reason is not None,
            test.size,
            Fraction(round(sum(evidence.test_groups[0].sample_losses or ()) / float(MISMATCH))),
        )
        probabilities[key] += one.probability * two.probability * test.probability
        representatives.setdefault(key, evidence)
    baseline = REFERENCE['calibrate'](population=population, n_blocks=n_blocks)
    expected_law = {
        (s['failed_training'], s['test_size'], Fraction(s['loss_sum']) / Fraction(1, 8)): Fraction(
            s['probability']
        )
        for s in baseline['sufficient_states']
    }
    if dict(probabilities) != expected_law:
        message = 'Sigmoid learner law disagrees with the independent sample-majority law.'
        raise RuntimeError(message)
    keys = tuple(sorted(probabilities))
    plan = risk_plan(population, n_blocks)
    success = Fraction(1, 2) if population == 'equal_binary' else Fraction(23, 32)
    mass = MISMATCH * (Fraction(1, 4) if population == 'equal_binary' else Fraction(11, 32))
    conditional = mass / success
    coverage = Fraction(0)
    issuance = Fraction(0)
    error_and_issued = Fraction(0)
    cases = []
    for old in baseline['cases']:
        counts = old['sufficient_state_counts']
        probability = Fraction(old['probability'])
        evidence = REFERENCE['_blocks'](counts, tuple(representatives[k] for k in keys))
        bound = bound_independent_training_risk(evidence, plan=plan)
        p_ci, mass_ci = (
            bound.training_success_probability_interval,
            bound.risk_mass_on_success_interval,
        )
        if p_ci is None or mass_ci is None:
            message = 'Complete finite states must produce success and risk-mass bounds.'
            raise RuntimeError(message)
        risk_ci = bound.successful_training_mean_risk_interval
        risk_ok = risk_ci is None or risk_ci.lower <= float(conditional) <= risk_ci.upper
        covered = (
            p_ci.lower <= float(success) <= p_ci.upper
            and mass_ci.lower <= float(mass) <= mass_ci.upper
            and risk_ok
        )
        coverage += probability * covered
        issuance += probability * (risk_ci is not None)
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
        'rational_mismatch_loss': str(MISMATCH),
        'training_success_probability': str(success),
        'risk_mass_on_success': str(mass),
        'successful_training_mean_risk': str(conditional),
        'unconditional_model_risk': None,
        'joint_coverage_probability': str(coverage),
        'conditional_interval_issue_probability': str(issuance),
        'conditional_error_and_issued_probability': str(error_and_issued),
        'local_cases': traces,
        'cases': cases,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--population', choices=tuple(POPULATIONS), required=True)
    parser.add_argument('--blocks', type=int, choices=(4, 12), required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = calibrate(population=arguments.population, n_blocks=arguments.blocks)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
