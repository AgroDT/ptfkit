"""Auditable candidate execution over a portable canonical retention dataset."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

from .cohorts import RetentionCandidateComparisons, RetentionCohort, build_retention_cohorts
from .conformal import (
    ConformalPrediction,
    ConformalPredictionInterval,
    GroupedConformalCalibration,
    apply_grouped_prediction_intervals,
    calibrate_grouped_prediction_intervals,
)
from .contracts import FixedPointPrediction, FunctionCurveCandidate, RangeGatedCurveCandidate
from .documents import object_mapping, object_records
from .execution import CurveExecutionError, CurvePoint, convert_value, evaluate_candidate
from .fitting import RetentionFitResult, fit_retention_family
from .folds import GroupedSample
from .input_bindings import RunInputTrace, bind_retention_inputs
from .metrics import RetentionComparison
from .quality import RetentionSeriesPoint
from .run_plans import RetentionRunPlan, candidate_atoms
from .selection import FixedNestedSelection, select_fixed_retention_candidates
from .uncertainty import RetentionBootstrapResult, bootstrap_retention_errors


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from .contracts import CurveCandidate
    from .folds import SampleKey


@dataclass(frozen=True)
class RunPointDecision:
    """One candidate/observation eligibility decision with prediction lineage."""

    candidate_id: str
    observation_id: str
    source_id: str
    sample_id: str
    profile_id: str | None
    suction_kpa: float
    observed: float
    reasons: tuple[str, ...]
    input_traces: tuple[RunInputTrace, ...]
    observation_cells: tuple[str, ...]
    prediction: CurvePoint | None
    comparison: RetentionComparison | None
    diagnostics: tuple[str, ...]
    execution_error: str | None
    observation_source_file: str | None = None

    @property
    def eligible(self) -> bool:
        """Return whether this point entered descriptive scoring."""
        return self.comparison is not None


@dataclass(frozen=True)
class RunSampleEligibility:
    """Coverage for every declared candidate and sample, including missing targets."""

    candidate_id: str
    source_id: str
    sample_id: str
    total_observation_count: int
    eligible_point_count: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class RunCohortResult:
    """A labeled comparison cohort and its metric confidence calculation."""

    cohort: RetentionCohort
    confidence: RetentionBootstrapResult


@dataclass(frozen=True)
class RunApproximationFit:
    """One family/sample fit, separate from any PTF candidate error or selection."""

    source_id: str
    sample_id: str
    excluded_observation_ids: tuple[str, ...]
    fit: RetentionFitResult


@dataclass(frozen=True)
class RunFuturePrediction:
    """A target-free canonical forecast and all input/execution eligibility evidence."""

    candidate_id: str
    source_id: str
    sample_id: str
    profile_id: str | None
    suction_kpa: float
    predicted: float | None
    reasons: tuple[str, ...]
    input_traces: tuple[RunInputTrace, ...]
    prediction: CurvePoint | None
    execution_error: str | None


@dataclass(frozen=True)
class RunPredictionIntervals:
    """Calibration and unlabelled test forecasts, separate from metric confidence."""

    calibration: GroupedConformalCalibration
    forecasts: tuple[RunFuturePrediction, ...]
    intervals: tuple[ConformalPredictionInterval, ...]

    @property
    def status(self) -> str:
        """Expose absent interval evidence even when a calibration was attempted."""
        return (
            'computed'
            if any(item.status == 'computed' for item in self.intervals)
            else 'insufficient_evidence'
        )


@dataclass(frozen=True)
class RetentionRunResult:
    """Complete in-memory run, retaining all decisions and declared candidates."""

    plan: RetentionRunPlan
    points: tuple[RunPointDecision, ...]
    sample_eligibility: tuple[RunSampleEligibility, ...]
    cohorts: tuple[RunCohortResult, ...]
    selection: FixedNestedSelection | None = None
    approximations: tuple[RunApproximationFit, ...] = ()
    prediction_intervals: tuple[RunPredictionIntervals, ...] = ()


@dataclass(frozen=True, kw_only=True)
class _InputContext:
    plan: RetentionRunPlan
    candidate: CurveCandidate
    sample: Mapping[str, object]
    functions: Mapping[str, Mapping[str, object]]


@dataclass(frozen=True, kw_only=True)
class _PointContext(_InputContext):
    observation: Mapping[str, object]


def execute_retention_run(plan: RetentionRunPlan) -> RetentionRunResult:
    """Execute fixed candidates without training, target-dependent routing, or ranking."""
    samples = {
        (sample['source_id'], sample['sample_id']): sample
        for sample in object_records(plan.dataset.document['samples'])
    }
    functions = {
        cast('str', function['id']): function
        for function in object_records(plan.manifest['functions'])
    }
    observations = sorted(
        object_records(plan.dataset.document['observations']),
        key=lambda item: (
            cast('str', item['source_id']),
            cast('str', item['sample_id']),
            cast('float', item['suction_kpa']),
        ),
    )
    decisions: list[RunPointDecision] = []
    candidates: list[RetentionCandidateComparisons] = []
    for candidate in sorted(plan.evaluation.candidates, key=lambda item: item.id):
        candidate_points = tuple(
            _evaluate_point(
                _PointContext(
                    plan=plan,
                    candidate=candidate,
                    observation=observation,
                    sample=samples[observation['source_id'], observation['sample_id']],
                    functions=functions,
                )
            )
            for observation in observations
        )
        decisions.extend(candidate_points)
        candidates.append(
            RetentionCandidateComparisons(
                candidate_id=candidate.id,
                dataset_id=plan.dataset.dataset_id,
                protocol_id=cast('str', object_mapping(plan.document['protocol'])['id']),
                target=plan.dataset.target,
                comparisons=tuple(
                    point.comparison for point in candidate_points if point.comparison is not None
                ),
            )
        )
    cohorts = build_retention_cohorts(candidates)
    requested = object_mapping(plan.document['protocol'])['cohorts']
    results = tuple(
        RunCohortResult(cohort, bootstrap_retention_errors(cohort.comparisons, plan=plan.bootstrap))
        for cohort in (*cohorts.maximal, *cohorts.common)
        if cohort.kind in cast('tuple[str, ...]', requested)
    )
    result = RetentionRunResult(
        plan,
        tuple(decisions),
        _sample_matrix(plan, decisions),
        results,
        approximations=_fit_reference_curves(plan),
    )
    result = (
        result
        if plan.selection is None
        else replace(
            result, selection=select_fixed_retention_candidates(result, plan=plan.selection)
        )
    )
    return (
        replace(result, prediction_intervals=_prediction_intervals(result))
        if plan.prediction_intervals
        else result
    )


def predict_retention_grid(
    plan: RetentionRunPlan,
    *,
    candidate_id: str,
    sample_keys: Iterable[SampleKey],
    pressure_grid_kpa: Sequence[float],
) -> tuple[RunFuturePrediction, ...]:
    """Predict explicit sample/pressure points using features only, with no target access."""
    candidates = {candidate.id: candidate for candidate in plan.evaluation.candidates}
    if candidate_id not in candidates:
        message = 'Target-free prediction references an unregistered candidate.'
        raise CurveExecutionError(message)
    samples = {
        (cast('str', sample['source_id']), cast('str', sample['sample_id'])): sample
        for sample in object_records(plan.dataset.document['samples'])
    }
    keys = tuple(sample_keys)
    if len(set(keys)) != len(keys) or set(keys) - set(samples):
        message = 'Target-free prediction requires unique declared sample identities.'
        raise CurveExecutionError(message)
    grid = tuple(pressure_grid_kpa)
    if len(set(grid)) != len(grid) or any(
        isinstance(value, bool) or not math.isfinite(value) or value < 0 for value in grid
    ):
        message = 'Target-free prediction requires distinct finite nonnegative pressures.'
        raise CurveExecutionError(message)
    functions = {
        cast('str', function['id']): function
        for function in object_records(plan.manifest['functions'])
    }
    return tuple(
        _future_prediction(
            _InputContext(
                plan=plan,
                candidate=candidates[candidate_id],
                sample=samples[key],
                functions=functions,
            ),
            pressure,
        )
        for key in sorted(keys)
        for pressure in sorted(grid)
    )


def _future_prediction(context: _InputContext, pressure: float) -> RunFuturePrediction:
    reasons: list[str] = []
    traces: tuple[RunInputTrace, ...] = ()
    prediction: CurvePoint | None = None
    value: float | None = None
    error: str | None = None
    try:
        axis = convert_value(
            pressure, 'kilopascal', context.candidate.axis.unit, manifest=context.plan.manifest
        )
        traces, inputs = _point_inputs(context, axis)
        reasons.extend(sorted({reason for trace in traces for reason in trace.reasons}))
        if not reasons:
            prediction = _predict(context, axis, inputs)
            value = convert_value(
                prediction.value,
                context.candidate.target.unit,
                'volume_fraction',
                manifest=context.plan.manifest,
            )
            if not math.isfinite(value):
                reasons.append('nonfinite_prediction')
                error = f'Nonfinite prediction: {prediction!r}'
                prediction = None
                value = None
    except (ValueError, ArithmeticError) as failure:
        reasons.append('execution_failed')
        error = f'{type(failure).__name__}: {failure}'
    return RunFuturePrediction(
        context.candidate.id,
        cast('str', context.sample['source_id']),
        cast('str', context.sample['sample_id']),
        cast('str | None', context.sample['profile_id']),
        pressure,
        value,
        tuple(reasons),
        traces,
        prediction,
        error,
    )


def _prediction_intervals(result: RetentionRunResult) -> tuple[RunPredictionIntervals, ...]:
    samples = tuple(
        GroupedSample(
            cast('str', sample['source_id']),
            cast('str', sample['sample_id']),
            cast('str | None', sample['profile_id']),
        )
        for sample in object_records(result.plan.dataset.document['samples'])
    )
    outputs: list[RunPredictionIntervals] = []
    for policy in result.plan.prediction_intervals:
        calibration_samples = {
            (sample.source_id, sample.sample_id)
            for sample in samples
            if _interval_group(sample, policy.grouping) in policy.calibration_groups
        }
        comparisons = tuple(
            point.comparison
            for point in result.points
            if point.candidate_id == policy.candidate_id
            and (point.source_id, point.sample_id) in calibration_samples
            and point.suction_kpa in policy.pressure_grid_kpa
            and point.comparison is not None
        )
        calibration = calibrate_grouped_prediction_intervals(
            comparisons, samples=samples, plan=policy
        )
        test_samples = tuple(
            (sample.source_id, sample.sample_id)
            for sample in samples
            if _interval_group(sample, policy.grouping) in policy.test_groups
        )
        forecasts = predict_retention_grid(
            result.plan,
            candidate_id=policy.candidate_id,
            sample_keys=test_samples,
            pressure_grid_kpa=policy.pressure_grid_kpa,
        )
        intervals = apply_grouped_prediction_intervals(
            calibration,
            (
                ConformalPrediction(
                    point.source_id,
                    point.sample_id,
                    point.profile_id,
                    point.suction_kpa,
                    point.predicted,
                )
                for point in forecasts
                if point.predicted is not None
            ),
        )
        outputs.append(RunPredictionIntervals(calibration, forecasts, intervals))
    return tuple(outputs)


def _interval_group(sample: GroupedSample, grouping: str) -> tuple[str, str]:
    return (
        sample.source_id,
        sample.profile_id if grouping == 'profile' and sample.profile_id is not None else '',
    )


def _fit_reference_curves(plan: RetentionRunPlan) -> tuple[RunApproximationFit, ...]:
    if not plan.approximations:
        return ()
    protocol = object_mapping(plan.document['protocol'])
    observations = object_records(plan.dataset.document['observations'])
    fits: list[RunApproximationFit] = []
    for sample in object_records(plan.dataset.document['samples']):
        records = [
            observation
            for observation in observations
            if (observation['source_id'], observation['sample_id'])
            == (sample['source_id'], sample['sample_id'])
        ]
        points = tuple(
            RetentionSeriesPoint(
                cast('float', item['suction_kpa']),
                cast('float', item['value']),
                cast('str', item['id']),
            )
            for item in records
            if not _target_reasons(item, protocol)
        )
        excluded = tuple(
            cast('str', item['id']) for item in records if _target_reasons(item, protocol)
        )
        fits.extend(
            RunApproximationFit(
                cast('str', sample['source_id']),
                cast('str', sample['sample_id']),
                excluded,
                fit_retention_family(points, plan=fit_plan),
            )
            for fit_plan in plan.approximations
        )
    return tuple(fits)


def _evaluate_point(context: _PointContext) -> RunPointDecision:
    observation = context.observation
    source = cast('str', observation['source_id'])
    sample = cast('str', observation['sample_id'])
    profile = cast('str | None', context.sample['profile_id'])
    suction = cast('float', observation['suction_kpa'])
    observed = cast('float', observation['value'])
    protocol = object_mapping(context.plan.document['protocol'])
    reasons = _target_reasons(observation, protocol)
    if isinstance(context.candidate, FunctionCurveCandidate):
        binding = context.candidate.curve.prediction
        if isinstance(binding, FixedPointPrediction):
            required = convert_value(
                binding.axis_value, binding.axis_unit, 'kilopascal', manifest=context.plan.manifest
            )
            if suction != required:
                reasons.append('pressure_condition_mismatch')
    traces: tuple[RunInputTrace, ...] = ()
    prediction: CurvePoint | None = None
    comparison: RetentionComparison | None = None
    diagnostics: list[str] = []
    execution_error: str | None = None
    if not reasons:
        try:
            axis = convert_value(
                suction, 'kilopascal', context.candidate.axis.unit, manifest=context.plan.manifest
            )
            traces, inputs = _point_inputs(context, axis)
            reasons.extend(sorted({reason for trace in traces for reason in trace.reasons}))
            if not reasons:
                prediction = _predict(context, axis, inputs)
                canonical_value = convert_value(
                    prediction.value,
                    context.candidate.target.unit,
                    'volume_fraction',
                    manifest=context.plan.manifest,
                )
                if not math.isfinite(canonical_value) or not math.isfinite(
                    (canonical_value - observed) ** 2
                ):
                    reasons.append('nonfinite_prediction_error')
                    execution_error = f'Nonfinite prediction or squared error: {prediction!r}'
                    prediction = None
                else:
                    comparison = RetentionComparison(
                        source, sample, suction, observed, canonical_value, profile
                    )
                    if not 0 <= canonical_value <= 1:
                        diagnostics.append('prediction_outside_physical_bounds')
        except (ValueError, ArithmeticError) as error:
            reasons.append('execution_failed')
            execution_error = f'{type(error).__name__}: {error}'
    return RunPointDecision(
        context.candidate.id,
        cast('str', observation['id']),
        source,
        sample,
        profile,
        suction,
        observed,
        tuple(reasons),
        traces,
        cast('tuple[str, ...]', observation['source_cells']),
        prediction,
        comparison,
        tuple(diagnostics),
        execution_error,
        cast('str | None', observation.get('source_file')),
    )


def _target_reasons(observation: Mapping[str, object], protocol: Mapping[str, object]) -> list[str]:
    reasons: list[str] = []
    if observation['review_status'] != 'confirmed':
        reasons.append('unreviewed_target')
    if observation['origin'] not in cast('tuple[str, ...]', protocol['allowed_target_origins']):
        reasons.append('target_origin_not_allowed')
    if observation['origin'] == 'derived':
        reasons.append('unverified_target_derivation')
    if observation['quality_flags'] or not 0 <= cast('float', observation['value']) <= 1:
        reasons.append('failed_quality_control')
    return reasons


def _point_inputs(
    context: _InputContext, axis: float
) -> tuple[tuple[RunInputTrace, ...], dict[str, object]]:
    candidate = context.candidate
    active = (
        {candidate.id}
        if isinstance(candidate, FunctionCurveCandidate)
        else {
            contribution.member_id
            for contribution in candidate.router.route(axis)
            if contribution.weight > 0
        }
    )
    bindings = object_mapping(object_mapping(context.plan.document['protocol'])['bindings'])
    traces: list[RunInputTrace] = []
    inputs: dict[str, object] = {}
    for member_id, atom in candidate_atoms(candidate):
        if member_id not in active:
            continue
        member_traces = bind_retention_inputs(
            context.functions[atom.function],
            context.sample,
            object_mapping(bindings[atom.function]),
            manifest=context.plan.manifest,
        )
        traces.extend(member_traces)
        values = {trace.input: trace.value for trace in member_traces}
        if isinstance(candidate, FunctionCurveCandidate):
            inputs.update(values)
        else:
            inputs[member_id] = values
    return tuple(traces), inputs


def _predict(context: _InputContext, axis: float, inputs: Mapping[str, object]) -> CurvePoint:
    if isinstance(context.candidate, RangeGatedCurveCandidate):
        return evaluate_candidate(
            context.candidate,
            [axis],
            cast('Mapping[str, Mapping[str, object]]', inputs),
            manifest=context.plan.manifest,
        ).points[0]
    return evaluate_candidate(
        context.candidate, [axis], inputs, manifest=context.plan.manifest
    ).points[0]


def _sample_matrix(
    plan: RetentionRunPlan, decisions: list[RunPointDecision]
) -> tuple[RunSampleEligibility, ...]:
    groups: dict[tuple[str, str, str], list[RunPointDecision]] = defaultdict(list)
    for decision in decisions:
        groups[decision.candidate_id, decision.source_id, decision.sample_id].append(decision)
    result: list[RunSampleEligibility] = []
    for candidate in sorted(plan.evaluation.candidates, key=lambda item: item.id):
        for sample in sorted(
            object_records(plan.dataset.document['samples']),
            key=lambda item: (cast('str', item['source_id']), cast('str', item['sample_id'])),
        ):
            source, sample_id = cast('str', sample['source_id']), cast('str', sample['sample_id'])
            points = groups[candidate.id, source, sample_id]
            reasons = (
                tuple(sorted({reason for point in points for reason in point.reasons}))
                if points
                else ('missing_target',)
            )
            result.append(
                RunSampleEligibility(
                    candidate.id,
                    source,
                    sample_id,
                    len(points),
                    sum(point.eligible for point in points),
                    reasons,
                )
            )
    return tuple(result)
