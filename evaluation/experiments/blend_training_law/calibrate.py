"""Exact blend learner law with separate curve and point-error risk assessment."""

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
from typing import Literal

from ptfkit_eval import (
    BlendGridFit,
    BlendGridPlan,
    FixedSelectionPlan,
    GroupedSample,
    IndependentTrainingBlock,
    IndependentTrainingRiskBound,
    IndependentTrainingRiskPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    PointErrorLossPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    allocate_independent_training_blocks,
    assess_independent_forecast_training,
    bound_independent_training_risk,
)
from ptfkit_eval.artifacts import artifact_value


ROOT = Path(__file__).resolve().parent
LOSS = LogPressureLossPlan(lower_suction_kpa=0.1, upper_suction_kpa=1000, minimum_points=5)
SELECTOR = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('high', 'low'),
        loss=LOSS,
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
    ),
    ensembles=(
        BlendGridPlan(
            id='trained_blend',
            left_candidate_id='high',
            right_candidate_id='low',
            interval_grid_kpa=((1, 100), (10, 100)),
            transform='log10',
            weighting='linear',
            minimum_training_groups=1,
            minimum_loss_gap=1e-12,
        ),
    ),
    method='nested_two_curve_selection_v1',
)
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')
KINDS: dict[str, Literal['atomic', 'ensemble']] = {'high': 'atomic', 'low': 'atomic'}


@dataclass(frozen=True)
class State:
    """An IID whole-group curve and its prior probability."""

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


def risk_plan(
    population: str, n_blocks: int, metric: Literal['mae', 'mse'] | None = None
) -> IndependentTrainingRiskPlan:
    """Register the complete learner and prior score bound on its finite support."""
    return IndependentTrainingRiskPlan(
        population_id=f'mathematical_blend_curves_{population}',
        learner_id='singleton_inner_cv_two_group_blend_interval_v1',
        grouping='source',
        loss=PointErrorLossPlan(selection_loss=LOSS, metric=metric) if metric else LOSS,
        maximum_sample_loss=float(point_scale(metric)),
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
    metric: Literal['mae', 'mse'] | None = None,
) -> tuple[IndependentTrainingBlock, dict[str, object]]:
    """Run every target-dependent training step and check a separate curve oracle."""
    plan = risk_plan(population, 2, metric)
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
            candidate_id=identifier,
            dataset_id=plan.population_id,
            protocol_id='five_pressure_blends',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(s.source_id, s.sample_id, pressure, observed, value)
                for s in samples
                for pressure, observed in (
                    (0.1, 0.75),
                    (1, 0.75),
                    (10, 0.75 if states[s.source_id].late else 0.5),
                    (100, 0.25),
                    (1000, 0.25),
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
    fit = block.selection.folds[0].ensemble.outer_fit
    if (
        not isinstance(fit, BlendGridFit)
        or block.selection.folds[0].ensemble.candidate_id != 'trained_blend'
    ):
        message = 'Every singleton inner fit must permit a full-training blend refit.'
        raise RuntimeError(message)
    late = sum(s.size for s in (one, two) if s.late)
    early = sum(s.size for s in (one, two) if not s.late)
    expected = None if late == early else (10, 100) if late > early else (1, 100)
    failure = 'unidentifiable_blend_interval' if expected is None else None
    losses = (
        None
        if expected is None
        else (float(point_scale(metric) * ((late > early) != test.late)),) * test.size
    )
    if (
        fit.interval_kpa != expected
        or block.evidence.training_failure_reason != failure
        or block.evidence.test_groups[0].sample_losses != losses
    ):
        message = 'Actual blend fitting disagrees with the independent 1/64 sample-majority oracle.'
        raise RuntimeError(message)
    return block.evidence, {
        'training_states': [one.name, two.name],
        'test_state': test.name,
        'probability': str(one.probability * two.probability * test.probability),
        'oracle_interval_kpa': expected,
        'samples': artifact_value(samples),
        'candidates': artifact_value(candidates),
        'block': artifact_value(block),
    }


def calibrate(
    *, population: str, n_blocks: int, metric: Literal['mae', 'mse'] | None = None
) -> dict[str, object]:
    """Verify the exact local law and every independently rescaled count state."""
    if population not in POPULATIONS or n_blocks not in (4, 12):
        message = 'Registered blend calibration uses equal_binary/informative_four and 4/12 blocks.'
        raise ValueError(message)
    probabilities: dict[tuple[bool, int, Fraction], Fraction] = defaultdict(Fraction)
    representatives = {}
    local_cases = []
    for one, two, test in product(POPULATIONS[population], repeat=3):
        evidence, trace = probe(population, one, two, test, metric)
        local_cases.append(trace)
        values = evidence.test_groups[0].sample_losses
        key = (
            evidence.training_failure_reason is not None,
            test.size,
            Fraction(round(sum(values or ()) / float(point_scale(metric)))),
        )
        probabilities[key] += one.probability * two.probability * test.probability
        representatives.setdefault(key, evidence)
    keys = tuple(sorted(probabilities))
    reference = runpy.run_path(str(ROOT / '../selector_training_law/calibrate.py'))
    baseline = reference['calibrate'](population=population, n_blocks=n_blocks)
    expected_law = {
        (s['failed_training'], s['test_size'], Fraction(s['loss_sum']) / Fraction(1, 8)): Fraction(
            s['probability']
        )
        for s in baseline['sufficient_states']
    }
    if dict(probabilities) != expected_law:
        message = 'Normalized blend and switch sufficient-state laws must agree exactly.'
        raise RuntimeError(message)
    plan = risk_plan(population, n_blocks, metric)
    truths = (
        (Fraction(1, 2), Fraction(1, 256), Fraction(1, 128))
        if population == 'equal_binary'
        else (Fraction(23, 32), Fraction(11, 2048), Fraction(11, 1472))
    )
    success, mass, conditional = truths
    scale = point_scale(metric) / Fraction(1, 64)
    mass *= scale
    conditional *= scale
    coverage = Fraction(0)
    issued = Fraction(0)
    error_and_issued = Fraction(0)
    cases = []
    for old in baseline['cases']:
        counts = old['sufficient_state_counts']
        probability = Fraction(old['probability'])
        evidence = reference['_blocks'](counts, tuple(representatives[k] for k in keys))
        bound = bound_independent_training_risk(evidence, plan=plan)
        _check_scaled_bound(bound, old['bound'], point_scale(metric) / Fraction(1, 8))
        p_ci, mass_ci = (
            bound.training_success_probability_interval,
            bound.risk_mass_on_success_interval,
        )
        if p_ci is None or mass_ci is None:
            message = 'Every exact blend state needs complete success and risk-mass bounds.'
            raise RuntimeError(message)
        risk_ci = bound.successful_training_mean_risk_interval
        risk_ok = risk_ci is None or risk_ci.lower <= float(conditional) <= risk_ci.upper
        covered = (
            p_ci.lower <= float(success) <= p_ci.upper
            and mass_ci.lower <= float(mass) <= mass_ci.upper
            and risk_ok
        )
        coverage += probability * covered
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
        'unconditional_model_risk': None,
        'switch_risk_scale': str(point_scale(metric) / Fraction(1, 8)),
        'point_metric': metric,
        'joint_coverage_probability': str(coverage),
        'conditional_interval_issue_probability': str(issued),
        'conditional_error_and_issued_probability': str(error_and_issued),
        'normalized_sufficient_states': [
            {
                'failed_training': k[0],
                'test_size': k[1],
                'normalized_loss_sum': str(k[2]),
                'probability': str(probabilities[k]),
            }
            for k in keys
        ],
        'local_cases': local_cases,
        'cases': cases,
    }


def point_scale(metric: Literal['mae', 'mse'] | None) -> Fraction:
    """One mismatched interior prediction differs by 1/4 on five equal points."""
    return (
        Fraction(1, 20)
        if metric == 'mae'
        else Fraction(1, 80)
        if metric == 'mse'
        else Fraction(1, 64)
    )


def _check_scaled_bound(bound: IndependentTrainingRiskBound, old: dict, scale: Fraction) -> None:
    """Check normalized moments and every rescaled risk interval independently."""
    moments = artifact_value(bound.moments)
    if not isinstance(moments, dict) or any(
        not math.isclose(value, old['moments'][key], rel_tol=1e-14, abs_tol=1e-15)
        for key, value in moments.items()
    ):
        message = 'Normalized statistics changed under a pure loss-scale transformation.'
        raise RuntimeError(message)
    if (
        artifact_value(bound.training_success_probability_interval)
        != old['training_success_probability_interval']
    ):
        message = 'A point assessment must not change training success.'
        raise RuntimeError(message)
    for field in ('risk_mass_on_success_interval', 'successful_training_mean_risk_interval'):
        expected = old[field]
        actual = getattr(bound, field)
        if expected is None:
            valid = actual is None
        else:
            valid = actual is not None and all(
                math.isclose(
                    getattr(actual, side), endpoint * float(scale), rel_tol=1e-14, abs_tol=1e-15
                )
                for side, endpoint in expected.items()
            )
        if not valid:
            message = 'A risk interval disagrees with independently scaled switch risk.'
            raise RuntimeError(message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--population', choices=tuple(POPULATIONS), required=True)
    parser.add_argument('--blocks', type=int, choices=(4, 12), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--point-metric', choices=('mae', 'mse'))
    arguments = parser.parse_args()
    result = calibrate(
        population=arguments.population, n_blocks=arguments.blocks, metric=arguments.point_metric
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
