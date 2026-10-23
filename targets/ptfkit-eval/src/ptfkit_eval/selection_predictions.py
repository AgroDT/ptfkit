"""Explicit held-out prediction frames shared by selection diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .cohorts import build_retention_cohorts, run_candidate_comparisons
from .documents import EvaluationDocumentError


if TYPE_CHECKING:
    from .folds import GroupKey, InnerGroupFold, NestedGroupFolds, OuterGroupFold, SampleKey
    from .metrics import RetentionComparison
    from .runner import RetentionRunResult
    from .selection import ValidationLoss


@dataclass(frozen=True)
class SelectionPredictionFrame:
    """One candidate's prediction records on exactly one declared holdout roster."""

    protocol: Literal['fixed', 'learned']
    selection_method: str
    strategy: Literal['atomic', 'ensemble']
    outer_fold_id: int
    inner_fold_id: int | None
    candidate_id: str | None
    training_groups: tuple[GroupKey, ...]
    held_out_groups: tuple[GroupKey, ...]
    samples: tuple[SampleKey, ...]
    predictions: tuple[RetentionComparison, ...]
    assessment: ValidationLoss | None
    reason: str | None

    @property
    def partition(self) -> str:
        """Only outer frames represent choices already locked by inner validation."""
        return 'outer_test' if self.inner_fold_id is None else 'inner_validation'

    @property
    def status(self) -> str:
        """Partial predictions remain available without implying complete assessment."""
        return (
            'assessed'
            if self.assessment is not None and self.assessment.mean_loss is not None
            else 'insufficient_evidence'
        )


def selection_prediction_frames(result: RetentionRunResult) -> tuple[SelectionPredictionFrame, ...]:
    """Recover held-out predictions without training, selecting, or target lookup.

    Fixed predictions use the exact selection-roster common cohort. Learned
    predictions come directly from retained inner validation/outer assessments.
    Each frame retains the full holdout sample roster, including missing targets
    and failed inputs/fits. Inner frames never imply locked outer choices.
    """
    frames = (*_fixed_frames(result), *_learned_frames(result))
    identities = [
        (
            frame.protocol,
            frame.strategy,
            frame.outer_fold_id,
            frame.inner_fold_id,
            frame.candidate_id,
        )
        for frame in frames
    ]
    if len(set(identities)) != len(identities):
        message = 'Duplicate selection holdout frame identity.'
        raise EvaluationDocumentError(message)
    return tuple(
        sorted(
            frames,
            key=lambda frame: (
                frame.protocol,
                frame.strategy,
                frame.outer_fold_id,
                -1 if frame.inner_fold_id is None else frame.inner_fold_id,
                frame.candidate_id or '',
            ),
        )
    )


def _samples(splits: NestedGroupFolds, groups: tuple[GroupKey, ...]) -> tuple[SampleKey, ...]:
    return tuple(
        sorted(
            sample
            for group in splits.groups
            if group.group_id in groups
            for sample in group.samples
        )
    )


def _frame(
    splits: NestedGroupFolds,
    *,
    protocol: Literal['fixed', 'learned'],
    method: str,
    strategy: Literal['atomic', 'ensemble'],
    outer: OuterGroupFold,
    inner: InnerGroupFold | None,
    identifier: str | None,
    predictions: tuple[RetentionComparison, ...],
    assessment: ValidationLoss | None,
    reason: str | None,
) -> SelectionPredictionFrame:
    training = outer.training_groups if inner is None else inner.training_groups
    held_out = outer.test_groups if inner is None else inner.validation_groups
    samples = _samples(splits, held_out)
    known = set(samples)
    if any((point.source_id, point.sample_id) not in known for point in predictions):
        message = 'Selection predictions include a sample outside their declared holdout roster.'
        raise EvaluationDocumentError(message)
    ordered = tuple(
        sorted(predictions, key=lambda point: (point.source_id, point.sample_id, point.suction_kpa))
    )
    keys = [(point.source_id, point.sample_id, point.suction_kpa) for point in ordered]
    if len(set(keys)) != len(keys):
        message = 'A selection prediction frame contains duplicate sample/pressure keys.'
        raise EvaluationDocumentError(message)
    return SelectionPredictionFrame(
        protocol,
        method,
        strategy,
        outer.fold_id,
        None if inner is None else inner.fold_id,
        identifier,
        training,
        held_out,
        samples,
        ordered,
        assessment,
        reason,
    )


def _fixed_frames(result: RetentionRunResult) -> tuple[SelectionPredictionFrame, ...]:
    selection = result.selection
    if selection is None or selection.splits.status != 'computed':
        return ()
    common = {
        cohort.candidate_id: cohort.comparisons
        for cohort in build_retention_cohorts(
            run_candidate_comparisons(result, selection.plan.candidate_ids)
        ).common
    }
    output = []
    for fold in selection.folds:
        outer = next(item for item in selection.splits.folds if item.fold_id == fold.fold_id)
        for strategy, selected in (('atomic', fold.atomic), ('ensemble', fold.ensemble)):
            candidate = selected.choice.candidate_id
            keys = set(_samples(selection.splits, outer.test_groups))
            output.append(
                _frame(
                    selection.splits,
                    protocol='fixed',
                    method=selection.method,
                    strategy=strategy,
                    outer=outer,
                    inner=None,
                    identifier=candidate,
                    predictions=tuple(
                        point
                        for point in common.get(candidate or '', ())
                        if (point.source_id, point.sample_id) in keys
                    ),
                    assessment=selected.assessment,
                    reason=selected.choice.reason
                    or (selected.assessment.reason if selected.assessment else None),
                )
            )
            for score in selected.choice.inner_scores:
                for evidence in score.folds:
                    inner = next(item for item in outer.inner if item.fold_id == evidence.fold_id)
                    keys = set(_samples(selection.splits, inner.validation_groups))
                    output.append(
                        _frame(
                            selection.splits,
                            protocol='fixed',
                            method=selection.method,
                            strategy=strategy,
                            outer=outer,
                            inner=inner,
                            identifier=score.candidate_id,
                            predictions=tuple(
                                point
                                for point in common[score.candidate_id]
                                if (point.source_id, point.sample_id) in keys
                            ),
                            assessment=evidence,
                            reason=evidence.reason,
                        )
                    )
    return tuple(output)


def _learned_frames(result: RetentionRunResult) -> tuple[SelectionPredictionFrame, ...]:
    selection = result.learned_selection
    if selection is None or selection.splits.status != 'computed':
        return ()
    output = []
    for fold in selection.folds:
        outer = next(item for item in selection.splits.folds if item.fold_id == fold.fold_id)
        for strategy, selected in (('atomic', fold.atomic), ('ensemble', fold.ensemble)):
            if (
                selected.outer_fit is not None
                and selected.outer_fit.training_groups != outer.training_groups
            ):
                message = 'Outer refit provenance differs from the declared outer training groups.'
                raise EvaluationDocumentError(message)
            output.append(
                _frame(
                    selection.splits,
                    protocol='learned',
                    method=selection.method,
                    strategy=strategy,
                    outer=outer,
                    inner=None,
                    identifier=selected.candidate_id,
                    predictions=selected.predictions,
                    assessment=selected.assessment,
                    reason=selected.reason,
                )
            )
            for score in selected.inner_scores:
                for evidence in score.folds:
                    inner = next(item for item in outer.inner if item.fold_id == evidence.fold_id)
                    if (
                        evidence.fit is not None
                        and evidence.fit.training_groups != inner.training_groups
                    ):
                        message = (
                            'Inner fit provenance differs from the declared inner training groups.'
                        )
                        raise EvaluationDocumentError(message)
                    output.append(
                        _frame(
                            selection.splits,
                            protocol='learned',
                            method=selection.method,
                            strategy=strategy,
                            outer=outer,
                            inner=inner,
                            identifier=score.candidate_id,
                            predictions=evidence.predictions,
                            assessment=evidence.assessment,
                            reason=evidence.fit.reason
                            if evidence.fit and evidence.fit.reason
                            else evidence.assessment.reason,
                        )
                    )
    return tuple(output)
