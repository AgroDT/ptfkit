"""Checksum-bound retention run plans joining portable data and candidate contracts."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from ptfkit import get_manifest

from .canonical import CanonicalRetentionDataset, load_retention_dataset
from .conformal import GroupedConformalPlan, validate_prediction_interval_roster
from .contracts import (
    EvaluationPlan,
    FixedPointPrediction,
    FunctionCurveCandidate,
    OutputPrediction,
    RangeGatedCurveCandidate,
    load_evaluation_plan,
)
from .documents import (
    EvaluationDocumentError,
    document_hash,
    freeze,
    load_document,
    object_mapping,
    object_records,
    parse_document,
    validate_document,
)
from .fitting import FitParameterRange, RetentionFitPlan
from .folds import GroupedSample, NestedGroupPlan
from .losses import LogPressureLossPlan
from .selection import FixedSelectionPlan
from .uncertainty import ClusterBootstrapPlan


if TYPE_CHECKING:
    from .contracts import AtomicCurve, CurveCandidate


@dataclass(frozen=True)
class RetentionRunPlan:
    """Immutable execution contract and exact content used for resolution."""

    document: Mapping[str, object]
    evaluation_document: Mapping[str, object]
    evaluation: EvaluationPlan
    dataset: CanonicalRetentionDataset
    manifest: Mapping[str, object]
    bootstrap: ClusterBootstrapPlan
    input_hashes: Mapping[str, object]
    selection: FixedSelectionPlan | None = None
    approximations: tuple[RetentionFitPlan, ...] = ()
    prediction_intervals: tuple[GroupedConformalPlan, ...] = ()


def load_retention_run_plan(
    source: str | Path | Mapping[str, object],
    *,
    base_directory: str | Path | None = None,
    manifest: Mapping[str, object] | None = None,
) -> RetentionRunPlan:
    """Validate a run and resolve local dependencies relative to the run file.

    File references bind exact file bytes; semantic JSON hashes additionally
    record resolved content. Mapping inputs resolve paths against the supplied
    base directory, or the current directory when it is omitted.
    """
    document = load_document(source)
    validate_document(document, 'retention-run.schema.json')
    base = (
        Path(base_directory)
        if base_directory is not None
        else (Path.cwd() if isinstance(source, Mapping) else Path(source).resolve().parent)
    )
    evaluation_document = _read_bound_document(object_mapping(document['evaluation_plan']), base)
    dataset_document = _read_bound_document(object_mapping(document['dataset']), base)
    manifest_document = object_mapping(
        freeze(load_document(get_manifest() if manifest is None else manifest))
    )
    evaluation = load_evaluation_plan(evaluation_document, manifest=manifest_document)
    dataset = load_retention_dataset(dataset_document)
    protocol = object_mapping(document['protocol'])
    _validate_run_candidates(evaluation, dataset, protocol, manifest_document)
    bootstrap_document = object_mapping(document['bootstrap'])
    bootstrap = ClusterBootstrapPlan(
        seed=cast('int', bootstrap_document['seed']),
        minimum_groups=cast('int', bootstrap_document['minimum_groups']),
        grouping=cast("Literal['source', 'profile']", bootstrap_document['grouping']),
        missing_profiles=cast(
            "Literal['reject', 'source']", bootstrap_document['missing_profiles']
        ),
        confidence_level=cast('float', bootstrap_document['confidence_level']),
        n_resamples=cast('int', bootstrap_document['n_resamples']),
    )
    hashes = {
        'run_plan': document_hash(document),
        'evaluation_plan': document_hash(evaluation_document),
        'dataset': dataset.sha256,
        'ptfkit_manifest': document_hash(manifest_document),
    }
    selection = _selection_plan(document.get('selection'))
    if selection is not None and set(selection.candidate_ids) - {
        candidate.id for candidate in evaluation.candidates
    }:
        message = 'Selection roster contains candidates absent from the evaluation plan.'
        raise EvaluationDocumentError(message)
    return RetentionRunPlan(
        object_mapping(freeze(document)),
        object_mapping(freeze(evaluation_document)),
        evaluation,
        dataset,
        manifest_document,
        bootstrap,
        object_mapping(freeze(hashes)),
        selection,
        _approximation_plans(document.get('approximations', ()), dataset),
        _prediction_interval_plans(document, dataset, evaluation),
    )


def _prediction_interval_plans(
    root: Mapping[str, object],
    dataset: CanonicalRetentionDataset,
    evaluation: EvaluationPlan,
) -> tuple[GroupedConformalPlan, ...]:
    plans: list[GroupedConformalPlan] = []
    samples = tuple(
        GroupedSample(
            cast('str', item['source_id']),
            cast('str', item['sample_id']),
            cast('str | None', item['profile_id']),
        )
        for item in object_records(dataset.document['samples'])
    )
    identifiers = {candidate.id for candidate in evaluation.candidates}
    for document in object_records(root.get('prediction_intervals', ())):
        plan = GroupedConformalPlan(
            candidate_id=cast('str', document['candidate_id']),
            protocol_id=cast('str', object_mapping(root['protocol'])['id']),
            target=dataset.target,
            calibration_groups=_group_roles(document, 'calibration_groups'),
            training_groups=_group_roles(document, 'training_groups'),
            test_groups=_group_roles(document, 'test_groups'),
            pressure_grid_kpa=tuple(cast('list[float]', document['pressure_grid_kpa'])),
            confidence_level=cast('float', document['confidence_level']),
            minimum_calibration_groups=cast('int', document['minimum_calibration_groups']),
            grouping=cast("Literal['source', 'profile']", document['grouping']),
        )
        if plan.candidate_id not in identifiers:
            message = 'Prediction intervals reference a candidate absent from the evaluation plan.'
            raise EvaluationDocumentError(message)
        validate_prediction_interval_roster(samples, plan=plan)
        plans.append(plan)
    if len({plan.candidate_id for plan in plans}) != len(plans):
        message = 'Each candidate may have only one prediction-interval registration per run.'
        raise EvaluationDocumentError(message)
    return tuple(plans)


def _group_roles(document: Mapping[str, object], name: str) -> tuple[tuple[str, str], ...]:
    return tuple((group[0], group[1]) for group in cast('list[list[str]]', document[name]))


def _approximation_plans(
    value: object, dataset: CanonicalRetentionDataset
) -> tuple[RetentionFitPlan, ...]:
    plans = [
        RetentionFitPlan(
            family_id=cast('str', document['family_id']),
            target=dataset.target,
            parameters=tuple(
                FitParameterRange(
                    cast('str', parameter['name']),
                    cast('float', parameter['lower']),
                    cast('float', parameter['upper']),
                    cast('float', parameter['initial']),
                )
                for parameter in object_records(document['parameters'])
            ),
            seed=cast('int', document['seed']),
            minimum_log10_span=cast('float', document['minimum_log10_span']),
            n_starts=cast('int', document['n_starts']),
            max_evaluations=cast('int', document['max_evaluations']),
            optimizer_tolerance=cast('float', document['optimizer_tolerance']),
            boundary_tolerance=cast('float', document['boundary_tolerance']),
            rank_tolerance=cast('float', document['rank_tolerance']),
            maximum_condition_number=cast('float', document['maximum_condition_number']),
            objective_agreement_tolerance=cast('float', document['objective_agreement_tolerance']),
            parameter_agreement_tolerance=cast('float', document['parameter_agreement_tolerance']),
            confidence_level=cast('float', document['confidence_level']),
        )
        for document in object_records(value)
    ]
    if len({plan.family_id for plan in plans}) != len(plans):
        message = 'Approximation family registrations must be unique within a run.'
        raise EvaluationDocumentError(message)
    return tuple(plans)


def _selection_plan(value: object) -> FixedSelectionPlan | None:
    if value is None:
        return None
    document = object_mapping(value)
    folds = object_mapping(document['folds'])
    loss = object_mapping(document['loss'])
    return FixedSelectionPlan(
        candidate_ids=tuple(cast('tuple[str, ...]', document['candidate_ids'])),
        minimum_coverage=cast('float', document['minimum_coverage']),
        folds=NestedGroupPlan(
            seed=cast('int', folds['seed']),
            outer_folds=cast('int', folds['outer_folds']),
            inner_folds=cast('int', folds['inner_folds']),
            grouping=cast("Literal['source', 'profile']", folds['grouping']),
            missing_profiles=cast("Literal['reject', 'source']", folds['missing_profiles']),
            minimum_training_groups=cast('int', folds['minimum_training_groups']),
            minimum_validation_groups=cast('int', folds['minimum_validation_groups']),
        ),
        loss=LogPressureLossPlan(
            lower_suction_kpa=cast('float', loss['lower_suction_kpa']),
            upper_suction_kpa=cast('float', loss['upper_suction_kpa']),
            minimum_points=cast('int', loss['minimum_points']),
        ),
    )


def candidate_atoms(candidate: CurveCandidate) -> tuple[tuple[str, AtomicCurve], ...]:
    """Enumerate the stable member identifiers and atomic functions of a candidate."""
    if isinstance(candidate, FunctionCurveCandidate):
        return ((candidate.id, candidate.curve),)
    return tuple((member.id, member.curve) for member in candidate.members)


def _read_bound_document(reference: Mapping[str, object], base: Path) -> dict[str, object]:
    path = base / cast('str', reference['path'])
    try:
        contents = path.read_bytes()
    except OSError as error:
        message = f'Cannot read checksum-bound input {path}.'
        raise EvaluationDocumentError(message) from error
    if hashlib.sha256(contents).hexdigest() != reference['sha256']:
        message = f'Checksum mismatch for input {path.name}.'
        raise EvaluationDocumentError(message)
    try:
        text = contents.decode('utf-8')
        return parse_document(text, path.suffix.lower())
    except (UnicodeError, ValueError) as error:
        message = f'Cannot parse checksum-bound input {path.name}.'
        raise EvaluationDocumentError(message) from error


def _validate_run_candidates(
    evaluation: EvaluationPlan,
    dataset: CanonicalRetentionDataset,
    protocol: Mapping[str, object],
    manifest: Mapping[str, object],
) -> None:
    if protocol['observation_method'] != dataset.document['method']:
        message = 'Run protocol and dataset observation methods must agree explicitly.'
        raise EvaluationDocumentError(message)
    bindings = object_mapping(protocol['bindings'])
    functions = {function['id']: function for function in object_records(manifest['functions'])}
    used: set[str] = set()
    for candidate in evaluation.candidates:
        if (
            (
                candidate.target.quantity,
                candidate.target.material_basis,
                candidate.target.denominator_basis,
            )
            != (
                dataset.target.quantity,
                dataset.target.material_basis,
                dataset.target.denominator_basis,
            )
            or candidate.axis.quantity != 'matric_potential'
            or candidate.axis.convention != 'magnitude'
        ):
            message = 'Run candidates must match the canonical target and suction-magnitude axis.'
            raise EvaluationDocumentError(message)
        if isinstance(candidate, RangeGatedCurveCandidate) and candidate.provenance.kind != 'fixed':
            message = (
                'Learned composites require nested training and cannot run as fixed candidates.'
            )
            raise EvaluationDocumentError(message)
        for _, atom in candidate_atoms(candidate):
            if (
                isinstance(atom.prediction, FixedPointPrediction)
                and atom.prediction.method is not None
                and atom.prediction.method != protocol['observation_method']
            ):
                message = 'Fixed-output observation method does not match the manifest contract.'
                raise EvaluationDocumentError(message)
            used.add(atom.function)
            supplied = object_mapping(bindings.get(atom.function, {}))
            expected = {
                binding['name'] for binding in object_records(functions[atom.function]['inputs'])
            }
            if isinstance(atom.prediction, OutputPrediction):
                expected.discard(atom.prediction.axis_input)
            if set(supplied) != expected:
                message = (
                    f'Run input bindings must exactly cover external inputs of {atom.function!r}.'
                )
                raise EvaluationDocumentError(message)
    if set(bindings) != used:
        message = 'Run bindings must name exactly the atomic functions used by its candidates.'
        raise EvaluationDocumentError(message)
