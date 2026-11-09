"""Descriptive assessment of locked outer selection strategies, without refitting."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .cohorts import RetentionCandidateComparisons, RetentionCohortSet, build_retention_cohorts
from .documents import EvaluationDocumentError, object_mapping, object_records
from .losses import (
    SampleCurveLoss,
    SelectionLossPlan,
    evaluate_selection_loss,
    mean_finite_losses,
)
from .paired import RetentionMetricDifferences
from .selection_predictions import SelectionPredictionFrame, selection_prediction_frames


if TYPE_CHECKING:
    from .folds import SampleKey
    from .metrics import RetentionComparison
    from .runner import RetentionRunResult


@dataclass(frozen=True)
class OuterStrategySummary:
    """Full holdout coverage, retained predictions, and complete/partial evidence."""

    strategy: Literal['atomic', 'ensemble']
    folds: tuple[SelectionPredictionFrame, ...]
    total_sample_count: int
    eligible_loss_sample_count: int
    selected_counts: tuple[tuple[str, int], ...]
    failed_fold_count: int
    excluded_pressure_point_count: int
    comparisons: tuple[RetentionComparison, ...]
    loss_samples: tuple[SampleCurveLoss, ...]
    mean_outer_loss: float | None
    reason: str | None

    @property
    def status(self) -> str:
        """Partial descriptive rows cannot certify a complete strategy assessment."""
        return (
            'computed'
            if self.reason is None and self.mean_outer_loss is not None
            else 'insufficient_evidence'
        )


@dataclass(frozen=True)
class SelectionStrategyAssessment:
    """One protocol's maximal/common strategy cohorts on its registered loss domain."""

    protocol: Literal['fixed', 'learned']
    selection_method: str
    loss_plan: SelectionLossPlan
    strategies: tuple[OuterStrategySummary, ...]
    cohorts: RetentionCohortSet
    atomic_minus_ensemble: RetentionMetricDifferences | None
    reason: str | None
    uncertainty_status: str = 'not_estimated_crossfit_dependency'
    method: str = 'locked_outer_strategy_descriptive_v1'

    @property
    def status(self) -> str:
        """Require all declared strategies to have complete outer evidence."""
        return 'computed' if self.reason is None else 'insufficient_evidence'


def assess_selection_strategies(
    result: RetentionRunResult,
) -> tuple[SelectionStrategyAssessment, ...]:
    """Score only locked outer forecasts; inner predictions never enter metrics.

    Each sample belongs to exactly one outer fold per strategy. Predictions are
    restricted to that protocol's registered selection-loss support. Atomic
    and ensemble strategies retain maximal and exact common point cohorts;
    incomplete folds remain explicit, with partial descriptive data labeled.
    No confidence intervals are estimated: overlapping training sets and model
    selection are not accounted for by resampling fixed cross-fit predictions.
    """
    frames = selection_prediction_frames(result)
    output = []
    if result.selection is not None:
        selection = result.selection
        output.append(
            _protocol(
                result,
                protocol='fixed',
                method=selection.method,
                loss=selection.plan.loss,
                frames=frames,
                split_reason=selection.splits.reason,
            )
        )
    if result.learned_selection is not None:
        learned = result.learned_selection
        output.append(
            _protocol(
                result,
                protocol='learned',
                method=learned.method,
                loss=learned.plan.fixed.loss,
                frames=frames,
                split_reason=learned.splits.reason,
            )
        )
    return tuple(output)


def _protocol(
    result: RetentionRunResult,
    *,
    protocol: Literal['fixed', 'learned'],
    method: str,
    loss: SelectionLossPlan,
    frames: tuple[SelectionPredictionFrame, ...],
    split_reason: str | None,
) -> SelectionStrategyAssessment:
    roster = tuple(
        sorted(
            (str(sample['source_id']), str(sample['sample_id']))
            for sample in object_records(result.plan.dataset.document['samples'])
        )
    )
    strategies = tuple(
        _strategy(
            kind,
            tuple(
                frame
                for frame in frames
                if frame.protocol == protocol
                and frame.strategy == kind
                and frame.inner_fold_id is None
            ),
            roster,
            loss,
            split_reason,
        )
        for kind in ('atomic', 'ensemble')
    )
    records = tuple(
        RetentionCandidateComparisons(
            candidate_id=item.strategy,
            dataset_id=result.plan.dataset.dataset_id,
            protocol_id=f'{object_mapping(result.plan.document["protocol"])["id"]}:{protocol}:locked_outer_domain_v1',
            target=result.plan.dataset.target,
            comparisons=item.comparisons,
        )
        for item in strategies
    )
    cohorts = build_retention_cohorts(records)
    common = {cohort.candidate_id: cohort.summary for cohort in cohorts.common}
    left, right = common['atomic'], common['ensemble']
    difference = None
    if left is not None and right is not None:
        one, two = left.metrics, right.metrics
        difference = RetentionMetricDifferences(
            one.mean_error - two.mean_error,
            one.mean_absolute_error - two.mean_absolute_error,
            one.root_mean_squared_error - two.root_mean_squared_error,
            one.median_absolute_error - two.median_absolute_error,
        )
    reason = split_reason or (
        'incomplete_outer_strategy_evidence'
        if any(item.status != 'computed' for item in strategies)
        else None
    )
    return SelectionStrategyAssessment(
        protocol, method, loss, strategies, cohorts, difference, reason
    )


def _strategy(
    kind: Literal['atomic', 'ensemble'],
    frames: tuple[SelectionPredictionFrame, ...],
    roster: tuple[SampleKey, ...],
    loss: SelectionLossPlan,
    split_reason: str | None,
) -> OuterStrategySummary:
    if split_reason is not None:
        return OuterStrategySummary(kind, (), len(roster), 0, (), 0, 0, (), (), None, split_reason)
    assigned = [sample for frame in frames for sample in frame.samples]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(roster):
        message = 'Outer strategy partitions must cover every declared sample exactly once.'
        raise EvaluationDocumentError(message)
    points = []
    records = []
    excluded = 0
    for frame in frames:
        domain = tuple(
            point
            for point in frame.predictions
            if loss.lower_suction_kpa <= point.suction_kpa <= loss.upper_suction_kpa
        )
        excluded += len(frame.predictions) - len(domain)
        evaluated = {
            (sample.source_id, sample.sample_id): sample
            for sample in evaluate_selection_loss(domain, plan=loss)
        }
        frame_losses = tuple(
            evaluated.get(sample, SampleCurveLoss(*sample, 0, None, 'insufficient_points'))
            for sample in frame.samples
        )
        if frame.assessment is not None and frame_losses != frame.assessment.samples:
            message = 'Outer prediction rows do not reproduce stored per-sample validation losses.'
            raise EvaluationDocumentError(message)
        points.extend(domain)
        records.extend(frame_losses)
    failed = sum(frame.status != 'assessed' for frame in frames)
    values = [record.loss for record in records if record.loss is not None]
    mean = mean_finite_losses(values) if values and not failed else None
    counts = Counter(frame.candidate_id for frame in frames if frame.candidate_id is not None)
    comparisons = tuple(
        sorted(points, key=lambda point: (point.source_id, point.sample_id, point.suction_kpa))
    )
    return OuterStrategySummary(
        kind,
        frames,
        len(roster),
        len(values),
        tuple(sorted(counts.items())),
        failed,
        excluded,
        comparisons,
        tuple(sorted(records, key=lambda sample: (sample.source_id, sample.sample_id))),
        mean,
        'incomplete_outer_folds' if failed else None,
    )
