"""Target-free member contrasts at registered composite transition boundaries."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from .composites import HardSwitchTransition
from .contracts import FunctionCurveCandidate, RangeGatedCurveCandidate
from .documents import object_mapping, object_records
from .execution import CurvePoint, convert_value, evaluate_candidate
from .input_bindings import RunInputTrace, bind_retention_inputs


if TYPE_CHECKING:
    from collections.abc import Mapping

    from .contracts import CompositeMember
    from .run_plans import RetentionRunPlan


@dataclass(frozen=True)
class SeamMemberValue:
    """An independently evaluated member at the exact boundary, with lineage."""

    member_id: str
    value: float | None
    input_traces: tuple[RunInputTrace, ...]
    prediction: CurvePoint | None
    reasons: tuple[str, ...]
    execution_error: str | None


@dataclass(frozen=True)
class CompositeSeamDiagnostic:
    """A right-minus-left contrast, distinct from a blended curve jump."""

    candidate_id: str
    source_id: str
    sample_id: str
    kind: str
    suction_kpa: float
    left: SeamMemberValue
    right: SeamMemberValue
    right_minus_left: float | None
    status: str
    method: str = 'exact_transition_member_contrast_v1'


def diagnose_composite_seams(plan: RetentionRunPlan) -> tuple[CompositeSeamDiagnostic, ...]:
    """Evaluate every sample's members at switches and blend endpoints.

    No observations are accessed. Both members are evaluated even where a
    routing weight is zero. Blend endpoint differences describe member
    disagreement, not jumps in the blended curve. Hard-switch differences
    describe a jump only when both member curves are continuous there.
    Failed inputs/execution are retained and do not affect scored predictions.
    """
    functions = {item['id']: item for item in object_records(plan.manifest['functions'])}
    bindings = object_mapping(object_mapping(plan.document['protocol'])['bindings'])
    diagnostics = []
    samples = sorted(
        object_records(plan.dataset.document['samples']),
        key=lambda sample: (cast('str', sample['source_id']), cast('str', sample['sample_id'])),
    )
    for candidate in sorted(plan.evaluation.candidates, key=lambda item: item.id):
        if not isinstance(candidate, RangeGatedCurveCandidate):
            continue
        members = {member.id: member for member in candidate.members}
        for transition in candidate.router.transitions:
            boundaries = (
                (('hard_switch', transition.at),)
                if isinstance(transition, HardSwitchTransition)
                else (
                    ('blend_start', transition.interval.lower),
                    ('blend_end', transition.interval.upper),
                )
            )
            for kind, axis_value in boundaries:
                pressure = convert_value(
                    axis_value, candidate.axis.unit, 'kilopascal', manifest=plan.manifest
                )
                for sample in samples:
                    left, right = (
                        _member_value(
                            plan,
                            candidate,
                            members[member_id],
                            sample,
                            function=functions[members[member_id].curve.function],
                            bindings=object_mapping(bindings[members[member_id].curve.function]),
                            axis_value=axis_value,
                        )
                        for member_id in (transition.left_member, transition.right_member)
                    )
                    difference = (
                        right.value - left.value
                        if right.value is not None and left.value is not None
                        else None
                    )
                    status = 'computed' if difference is not None else 'unavailable'
                    if difference is not None and not math.isfinite(difference):
                        difference = None
                        status = 'nonfinite_contrast'
                    diagnostics.append(
                        CompositeSeamDiagnostic(
                            candidate.id,
                            cast('str', sample['source_id']),
                            cast('str', sample['sample_id']),
                            kind,
                            pressure,
                            left,
                            right,
                            difference,
                            status,
                        )
                    )
    return tuple(diagnostics)


def _member_value(
    plan: RetentionRunPlan,
    candidate: RangeGatedCurveCandidate,
    member: CompositeMember,
    sample: Mapping[str, object],
    *,
    function: Mapping[str, object],
    bindings: Mapping[str, object],
    axis_value: float,
) -> SeamMemberValue:
    traces = bind_retention_inputs(function, sample, bindings, manifest=plan.manifest)
    reasons = tuple(sorted({reason for trace in traces for reason in trace.reasons}))
    prediction = None
    value = None
    error = None
    if not reasons:
        atom = FunctionCurveCandidate(member.id, candidate.axis, candidate.target, member.curve)
        try:
            prediction = evaluate_candidate(
                atom,
                [axis_value],
                {trace.input: trace.value for trace in traces},
                manifest=plan.manifest,
            ).points[0]
            value = convert_value(
                prediction.value,
                candidate.target.unit,
                plan.dataset.target.unit,
                manifest=plan.manifest,
            )
            if not math.isfinite(value):
                reasons = ('nonfinite_prediction',)
                error = f'Nonfinite seam prediction: {prediction!r}'
                value = None
                prediction = None
        except (ValueError, ArithmeticError) as failure:
            reasons = ('execution_failed',)
            error = f'{type(failure).__name__}: {failure}'
    return SeamMemberValue(member.id, value, traces, prediction, reasons, error)
