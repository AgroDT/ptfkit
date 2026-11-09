"""Descriptive predictor envelopes fitted only to registered training groups."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal, cast

from .documents import EvaluationDocumentError, object_mapping, object_records
from .input_bindings import RunInputTrace, bind_retention_inputs


if TYPE_CHECKING:
    from collections.abc import Mapping

    from .run_plans import RetentionRunPlan


_GROUP_KEY_SIZE = 2


@dataclass(frozen=True, kw_only=True)
class EmpiricalDomainPlan:
    """Disjoint source/profile roles for a descriptive input envelope."""

    candidate_id: str
    training_groups: tuple[tuple[str, str], ...]
    test_groups: tuple[tuple[str, str], ...]
    minimum_training_groups: int
    grouping: Literal['source', 'profile'] = 'source'
    method: Literal['training_input_envelope_v1'] = 'training_input_envelope_v1'

    def __post_init__(self) -> None:
        """Reject overlapping roles and unsupported protocols before seeing inputs."""
        if (
            not self.candidate_id.strip()
            or self.method != 'training_input_envelope_v1'
            or self.grouping not in ('source', 'profile')
            or isinstance(self.minimum_training_groups, bool)
            or not isinstance(self.minimum_training_groups, int)
            or self.minimum_training_groups < 1
        ):
            message = 'Empirical domains require a supported method and positive group gate.'
            raise EvaluationDocumentError(message)
        roles = (*self.training_groups, *self.test_groups)
        if (
            not self.training_groups
            or not self.test_groups
            or len(set(roles)) != len(roles)
            or any(
                len(group) != _GROUP_KEY_SIZE
                or not group[0].strip()
                or (bool(group[1].strip()) != (self.grouping == 'profile'))
                for group in roles
            )
        ):
            message = 'Empirical domain training/test groups must be valid, unique and disjoint.'
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class EmpiricalInputBound:
    """An inclusive numeric range or observed categorical names in manifest units."""

    input: str
    unit: str | None
    lower: float | None
    upper: float | None
    categories: tuple[str, ...]


@dataclass(frozen=True)
class EmpiricalSampleAssessment:
    """A complete input trace and explicit envelope decision for one sample."""

    source_id: str
    sample_id: str
    profile_id: str | None
    status: str
    reasons: tuple[str, ...]
    input_traces: tuple[RunInputTrace, ...]


@dataclass(frozen=True)
class EmpiricalMemberDomain:
    """One member's training evidence and untouched test-input assessments."""

    member_id: str
    function: str
    status: str
    reason: str | None
    training_group_count: int
    training_samples: tuple[EmpiricalSampleAssessment, ...]
    bounds: tuple[EmpiricalInputBound, ...]
    test_samples: tuple[EmpiricalSampleAssessment, ...]


@dataclass(frozen=True)
class RunEmpiricalDomain:
    """Member-specific envelopes; no joint-support or predictive coverage claim."""

    plan: EmpiricalDomainPlan
    members: tuple[EmpiricalMemberDomain, ...]


def domain_group(sample: Mapping[str, object], grouping: str) -> tuple[str, str]:
    """Resolve an explicit group without implicit missing-profile fallback."""
    profile = cast('str | None', sample['profile_id'])
    if grouping == 'profile' and not profile:
        message = 'Profile empirical domains require complete profile identifiers.'
        raise EvaluationDocumentError(message)
    return cast('str', sample['source_id']), profile if grouping == 'profile' and profile else ''


def validate_empirical_domain_roster(
    dataset: Mapping[str, object], policy: EmpiricalDomainPlan
) -> None:
    """Require every registered role to resolve without accessing observations."""
    groups = {
        domain_group(sample, policy.grouping) for sample in object_records(dataset['samples'])
    }
    if {*policy.training_groups, *policy.test_groups} - groups:
        message = 'Empirical domain roles reference groups absent from the sample roster.'
        raise EvaluationDocumentError(message)


def assess_retention_applicability(
    plan: RetentionRunPlan, *, policy: EmpiricalDomainPlan
) -> RunEmpiricalDomain:
    """Fit complete-case envelopes from training predictors only; assess test inputs.

    Each member has its own complete-case roster and evidence gate. Missing or
    incompatible training vectors are retained as exclusions. Test inputs and
    all targets cannot change the bounds. Numeric bounds include their exact
    endpoints and constant predictors; categories use canonical enum names.
    This diagnostic does not change eligibility, ranking, or prediction values.
    """
    # Local import avoids coupling the plan record to its own loader.
    from .run_plans import candidate_atoms  # noqa: PLC0415

    validate_empirical_domain_roster(plan.dataset.document, policy)
    candidates = {candidate.id: candidate for candidate in plan.evaluation.candidates}
    if policy.candidate_id not in candidates:
        message = 'Empirical domain references an unregistered candidate.'
        raise EvaluationDocumentError(message)
    functions = {item['id']: item for item in object_records(plan.manifest['functions'])}
    bindings = object_mapping(object_mapping(plan.document['protocol'])['bindings'])
    samples = sorted(
        object_records(plan.dataset.document['samples']),
        key=lambda sample: (cast('str', sample['source_id']), cast('str', sample['sample_id'])),
    )
    members = []
    for member_id, atom in candidate_atoms(candidates[policy.candidate_id]):
        function = functions[atom.function]
        registered = object_mapping(bindings[atom.function])
        training = tuple(
            _sample_inputs(plan, function, registered, sample)
            for sample in samples
            if domain_group(sample, policy.grouping) in policy.training_groups
        )
        complete = tuple(sample for sample in training if not sample.reasons)
        group_count = len(
            {
                (sample.source_id, sample.profile_id if policy.grouping == 'profile' else '')
                for sample in complete
            }
        )
        reason = 'too_few_training_groups' if group_count < policy.minimum_training_groups else None
        bounds = _input_bounds(complete) if reason is None else ()
        tests = tuple(
            _assess_sample(_sample_inputs(plan, function, registered, sample), bounds, reason)
            for sample in samples
            if domain_group(sample, policy.grouping) in policy.test_groups
        )
        members.append(
            EmpiricalMemberDomain(
                member_id,
                atom.function,
                'assessed' if reason is None else 'insufficient_evidence',
                reason,
                group_count,
                training,
                bounds,
                tests,
            )
        )
    return RunEmpiricalDomain(policy, tuple(members))


def _sample_inputs(
    plan: RetentionRunPlan,
    function: Mapping[str, object],
    bindings: Mapping[str, object],
    sample: Mapping[str, object],
) -> EmpiricalSampleAssessment:
    traces = bind_retention_inputs(function, sample, bindings, manifest=plan.manifest)
    inputs = {item['name']: item for item in object_records(function['inputs'])}
    normalized = tuple(_canonical_category(trace, inputs[trace.input]) for trace in traces)
    reasons = tuple(sorted({reason for trace in normalized for reason in trace.reasons}))
    return EmpiricalSampleAssessment(
        cast('str', sample['source_id']),
        cast('str', sample['sample_id']),
        cast('str | None', sample['profile_id']),
        'excluded_input' if reasons else 'complete_input',
        reasons,
        normalized,
    )


def _canonical_category(trace: RunInputTrace, binding: Mapping[str, object]) -> RunInputTrace:
    if binding['kind'] == 'categorical' and not trace.reasons:
        values = object_records(object_mapping(binding['enum'])['values'])
        name = next(item['name'] for item in values if trace.value in (item['name'], item['value']))
        return replace(trace, value=name)
    return trace


def _input_bounds(
    samples: tuple[EmpiricalSampleAssessment, ...],
) -> tuple[EmpiricalInputBound, ...]:
    bounds = []
    for index, trace in enumerate(samples[0].input_traces):
        values = [sample.input_traces[index].value for sample in samples]
        if trace.target_unit is None:
            bounds.append(
                EmpiricalInputBound(
                    trace.input, None, None, None, tuple(sorted(set(cast('list[str]', values))))
                )
            )
        else:
            numbers = cast('list[float]', values)
            bounds.append(
                EmpiricalInputBound(
                    trace.input,
                    trace.target_unit,
                    min(numbers),
                    max(numbers),
                    (),
                )
            )
    return tuple(bounds)


def _assess_sample(
    sample: EmpiricalSampleAssessment,
    bounds: tuple[EmpiricalInputBound, ...],
    evidence_reason: str | None,
) -> EmpiricalSampleAssessment:
    if sample.reasons:
        return sample
    if evidence_reason is not None:
        return replace(sample, status='insufficient_evidence', reasons=(evidence_reason,))
    outside = tuple(
        f'outside_empirical_input:{bound.input}'
        for trace, bound in zip(sample.input_traces, bounds, strict=True)
        if (
            trace.value not in bound.categories
            if bound.unit is None
            else not cast('float', bound.lower)
            <= cast('float', trace.value)
            <= cast('float', bound.upper)
        )
    )
    return replace(sample, status='outside' if outside else 'inside', reasons=outside)
