"""Checksum-bound retention run plans joining portable data and candidate contracts."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from ptfkit import get_manifest

from .applicability import EmpiricalDomainPlan, validate_empirical_domain_roster
from .blend_grid import BlendGridPlan
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
from .folds import GroupedSample, NestedGroupPlan, build_nested_group_folds
from .hard_switch import HardSwitchGridPlan
from .learned import ConvexPairPlan, LearnedSelectionPlan, validate_learned_selection_candidates
from .losses import LogPressureLossPlan
from .nested_applicability import NestedDomainPlan
from .paired import PairedComparisonPlan
from .point_losses import PointErrorLossPlan
from .resampling import SelectionResamplingPlan
from .risk_bounds import ConditionalOuterRiskPlan
from .selection import FixedSelectionPlan
from .selection_risk import SelectionRiskPlan, validate_selection_risk_policies
from .sigmoid_grid import SigmoidGridPlan
from .training_blocks import allocate_independent_training_blocks
from .training_pairs import PairedTrainingRiskPlan
from .training_risk import IndependentTrainingRiskPlan
from .training_selection import (
    SelectionPairedTrainingRiskPlan,
    SelectionTrainingRiskPlan,
    validate_independent_selection_policies,
    validate_point_training_policies,
)
from .uncertainty import ClusterBootstrapPlan


if TYPE_CHECKING:
    from .contracts import AtomicCurve, CurveCandidate
    from .fitting import RestartPolicy


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
    empirical_domains: tuple[EmpiricalDomainPlan, ...] = ()
    paired_comparisons: tuple[PairedComparisonPlan, ...] = ()
    learned_selection: LearnedSelectionPlan | None = None
    selection_resampling: tuple[SelectionResamplingPlan, ...] = ()
    conditional_outer_risk: tuple[SelectionRiskPlan, ...] = ()
    independent_training_risk: tuple[SelectionTrainingRiskPlan, ...] = ()
    paired_training_risk: SelectionPairedTrainingRiskPlan | None = None
    point_training_risk: tuple[SelectionTrainingRiskPlan, ...] = ()


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
    learned_selection = _learned_selection_plan(document.get('learned_selection'), evaluation)
    result = RetentionRunPlan(
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
        _empirical_domain_plans(document, dataset, evaluation),
        _paired_comparison_plans(document, evaluation),
        learned_selection,
        _selection_resampling_plans(document),
        _conditional_risk_plans(document, selection, learned_selection, dataset),
        _training_risk_plans(document, learned_selection, dataset),
        _paired_training_risk_plan(document, learned_selection, dataset),
        _point_training_risk_plans(document, learned_selection, dataset),
    )
    for policy in result.selection_resampling:
        if (policy.protocol == 'fixed' and result.selection is None) or (
            policy.protocol == 'learned' and result.learned_selection is None
        ):
            message = (
                'Selection resampling requires its registered fixed/learned selection protocol.'
            )
            raise EvaluationDocumentError(message)
    return result


def _point_training_risk_plans(
    root: Mapping[str, object],
    learned: LearnedSelectionPlan | None,
    dataset: CanonicalRetentionDataset,
) -> tuple[SelectionTrainingRiskPlan, ...]:
    policies = tuple(
        SelectionTrainingRiskPlan(
            strategy=cast("Literal['atomic', 'ensemble']", item['strategy']),
            seed=cast('int', item['seed']),
            bounds=_assessment_risk_bounds(item, learned, dataset),
        )
        for item in object_records(root.get('point_training_risk', ()))
    )
    validate_point_training_policies(policies)
    return policies


def _assessment_risk_bounds(
    item: Mapping[str, object],
    learned: LearnedSelectionPlan | None,
    dataset: CanonicalRetentionDataset,
) -> IndependentTrainingRiskPlan:
    bounds = _training_risk_bounds(item, learned, dataset)
    return (
        replace(
            bounds,
            loss=PointErrorLossPlan(
                selection_loss=cast('LogPressureLossPlan', bounds.loss),
                metric=cast("Literal['mae', 'mse']", item['point_metric']),
            ),
        )
        if 'point_metric' in item
        else bounds
    )


def _training_risk_plans(
    root: Mapping[str, object],
    learned: LearnedSelectionPlan | None,
    dataset: CanonicalRetentionDataset,
) -> tuple[SelectionTrainingRiskPlan, ...]:
    policies = []
    for item in object_records(root.get('independent_training_risk', ())):
        bounds = _training_risk_bounds(item, learned, dataset)
        policy = SelectionTrainingRiskPlan(
            strategy=cast("Literal['atomic', 'ensemble']", item['strategy']),
            seed=cast('int', item['seed']),
            bounds=bounds,
        )
        policies.append(policy)
    result = tuple(policies)
    validate_independent_selection_policies(result)
    return result


def _training_risk_bounds(
    item: Mapping[str, object],
    learned: LearnedSelectionPlan | None,
    dataset: CanonicalRetentionDataset,
) -> IndependentTrainingRiskPlan:
    if learned is None:
        message = 'Independent training risk requires its registered learned selector.'
        raise EvaluationDocumentError(message)
    roster = tuple(
        GroupedSample(str(s['source_id']), str(s['sample_id']), cast('str | None', s['profile_id']))
        for s in object_records(dataset.document['samples'])
    )
    resolved = build_nested_group_folds(roster, plan=learned.fixed.folds).effective_grouping
    if item['grouping'] != resolved:
        message = 'Independent training risk must use the resolved original grouping.'
        raise EvaluationDocumentError(message)
    bounds = IndependentTrainingRiskPlan(
        population_id=cast('str', item['population_id']),
        learner_id=cast('str', item['learner_id']),
        grouping=cast("Literal['source', 'profile']", item['grouping']),
        loss=learned.fixed.loss,
        maximum_sample_loss=cast('float', item['maximum_sample_loss']),
        minimum_group_size=cast('int', item['minimum_group_size']),
        maximum_group_size=cast('int', item['maximum_group_size']),
        training_groups_per_block=cast('int', item['training_groups_per_block']),
        test_groups_per_block=cast('int', item['test_groups_per_block']),
        n_blocks=cast('int', item['n_blocks']),
        total_learner=cast('bool', item['total_learner']),
        confidence_level=cast('float', item['confidence_level']),
    )
    allocate_independent_training_blocks(roster, plan=bounds, seed=cast('int', item['seed']))
    return bounds


def _paired_training_risk_plan(
    root: Mapping[str, object],
    learned: LearnedSelectionPlan | None,
    dataset: CanonicalRetentionDataset,
) -> SelectionPairedTrainingRiskPlan | None:
    value = root.get('paired_training_risk')
    if value is None:
        return None
    item = object_mapping(value)
    return SelectionPairedTrainingRiskPlan(
        bounds=PairedTrainingRiskPlan(
            bounds=_assessment_risk_bounds(item, learned, dataset),
            left_learner_id=cast('str', item['left_learner_id']),
            right_learner_id=cast('str', item['right_learner_id']),
        ),
        left_strategy=cast("Literal['atomic', 'ensemble']", item['left_strategy']),
        right_strategy=cast("Literal['atomic', 'ensemble']", item['right_strategy']),
        seed=cast('int', item['seed']),
    )


def _conditional_risk_plans(
    root: Mapping[str, object],
    fixed: FixedSelectionPlan | None,
    learned: LearnedSelectionPlan | None,
    dataset: CanonicalRetentionDataset,
) -> tuple[SelectionRiskPlan, ...]:
    policies = []
    for item in object_records(root.get('conditional_outer_risk', ())):
        protocol = cast("Literal['fixed', 'learned']", item['protocol'])
        selection = fixed if protocol == 'fixed' else learned.fixed if learned is not None else None
        if selection is None:
            message = 'Conditional risk requires its registered fixed/learned selection protocol.'
            raise EvaluationDocumentError(message)
        roster = tuple(
            GroupedSample(
                str(sample['source_id']),
                str(sample['sample_id']),
                cast('str | None', sample['profile_id']),
            )
            for sample in object_records(dataset.document['samples'])
        )
        resolved = build_nested_group_folds(roster, plan=selection.folds).effective_grouping
        if item['grouping'] != resolved:
            message = 'Conditional risk grouping must match the resolved selection grouping.'
            raise EvaluationDocumentError(message)
        policies.append(
            SelectionRiskPlan(
                protocol=protocol,
                strategy=cast("Literal['atomic', 'ensemble']", item['strategy']),
                bounds=ConditionalOuterRiskPlan(
                    population_id=cast('str', item['population_id']),
                    grouping=cast("Literal['source', 'profile']", item['grouping']),
                    loss=selection.loss,
                    maximum_sample_loss=cast('float', item['maximum_sample_loss']),
                    maximum_group_size=cast('int', item['maximum_group_size']),
                    minimum_group_size=cast('int', item['minimum_group_size']),
                    confidence_level=cast('float', item['confidence_level']),
                ),
            )
        )
    result = tuple(policies)
    validate_selection_risk_policies(result)
    return result


def _selection_resampling_plans(root: Mapping[str, object]) -> tuple[SelectionResamplingPlan, ...]:
    plans = tuple(
        SelectionResamplingPlan(
            protocol=cast("Literal['fixed', 'learned']", item['protocol']),
            seed=cast('int', item['seed']),
            n_resamples=cast('int', item['n_resamples']),
            minimum_groups=cast('int', item['minimum_groups']),
        )
        for item in object_records(root.get('selection_resampling', ()))
    )
    if len({policy.protocol for policy in plans}) != len(plans):
        message = 'Each selection protocol may have only one retraining resampling registration.'
        raise EvaluationDocumentError(message)
    return plans


def _learned_selection_plan(
    value: object, evaluation: EvaluationPlan
) -> LearnedSelectionPlan | None:
    if value is None:
        return None
    document = object_mapping(value)
    fixed = _selection_plan(document['fixed_selection'])
    if fixed is None:
        message = 'Learned selection requires a complete fixed candidate/fold/loss contract.'
        raise EvaluationDocumentError(message)
    identifiers = {candidate.id for candidate in evaluation.candidates}
    if set(fixed.candidate_ids) - identifiers:
        message = 'Learned selection fixed roster references absent evaluation candidates.'
        raise EvaluationDocumentError(message)
    plan = LearnedSelectionPlan(
        fixed=fixed,
        method=cast(
            "Literal['nested_convex_pair_selection_v1', 'nested_two_curve_selection_v1']",
            document['method'],
        ),
        empirical_domains=(
            NestedDomainPlan(
                minimum_training_groups=cast(
                    'int', object_mapping(document['empirical_domains'])['minimum_training_groups']
                )
            )
            if 'empirical_domains' in document
            else None
        ),
        ensembles=tuple(
            _trainable_ensemble(item) for item in object_records(document['ensembles'])
        ),
    )
    validate_learned_selection_candidates(plan, evaluation)
    return plan


def _trainable_ensemble(
    item: Mapping[str, object],
) -> ConvexPairPlan | HardSwitchGridPlan | BlendGridPlan | SigmoidGridPlan:
    if item['method'] == 'training_grid_log_pressure_sigmoid_v1':
        return SigmoidGridPlan(
            id=cast('str', item['id']),
            left_candidate_id=cast('str', item['left_candidate_id']),
            right_candidate_id=cast('str', item['right_candidate_id']),
            parameter_grid=tuple(
                (pair[0], pair[1]) for pair in cast('list[list[float]]', item['parameter_grid'])
            ),
            minimum_training_groups=cast('int', item['minimum_training_groups']),
            minimum_loss_gap=cast('float', item['minimum_loss_gap']),
        )
    if item['method'] == 'training_grid_blend_interval_v1':
        return BlendGridPlan(
            id=cast('str', item['id']),
            left_candidate_id=cast('str', item['left_candidate_id']),
            right_candidate_id=cast('str', item['right_candidate_id']),
            interval_grid_kpa=tuple(
                (bounds[0], bounds[1])
                for bounds in cast('list[list[float]]', item['interval_grid_kpa'])
            ),
            transform=cast("Literal['linear', 'log10']", item['transform']),
            weighting=cast("Literal['linear', 'smoothstep']", item['weighting']),
            minimum_training_groups=cast('int', item['minimum_training_groups']),
            minimum_loss_gap=cast('float', item['minimum_loss_gap']),
        )
    if item['method'] == 'training_grid_hard_switch_v1':
        return HardSwitchGridPlan(
            id=cast('str', item['id']),
            left_candidate_id=cast('str', item['left_candidate_id']),
            right_candidate_id=cast('str', item['right_candidate_id']),
            minimum_training_groups=cast('int', item['minimum_training_groups']),
            boundary_grid_kpa=tuple(cast('list[float]', item['boundary_grid_kpa'])),
            boundary_member=cast("Literal['left', 'right']", item['boundary_member']),
            minimum_loss_gap=cast('float', item['minimum_loss_gap']),
        )
    return ConvexPairPlan(
        id=cast('str', item['id']),
        left_candidate_id=cast('str', item['left_candidate_id']),
        right_candidate_id=cast('str', item['right_candidate_id']),
        minimum_training_groups=cast('int', item['minimum_training_groups']),
        minimum_mean_squared_contrast=cast('float', item['minimum_mean_squared_contrast']),
    )


def _paired_comparison_plans(
    root: Mapping[str, object], evaluation: EvaluationPlan
) -> tuple[PairedComparisonPlan, ...]:
    plans = tuple(
        PairedComparisonPlan(
            left_candidate_id=cast('str', document['left_candidate_id']),
            right_candidate_id=cast('str', document['right_candidate_id']),
        )
        for document in object_records(root.get('paired_comparisons', ()))
    )
    identifiers = {candidate.id for candidate in evaluation.candidates}
    seen: set[frozenset[str]] = set()
    for policy in plans:
        pair = frozenset((policy.left_candidate_id, policy.right_candidate_id))
        if pair - identifiers or pair in seen:
            message = 'Paired comparisons require known candidates and unique unordered pairs.'
            raise EvaluationDocumentError(message)
        seen.add(pair)
    return plans


def _empirical_domain_plans(
    root: Mapping[str, object], dataset: CanonicalRetentionDataset, evaluation: EvaluationPlan
) -> tuple[EmpiricalDomainPlan, ...]:
    plans = tuple(
        EmpiricalDomainPlan(
            candidate_id=cast('str', document['candidate_id']),
            training_groups=_group_roles(document, 'training_groups'),
            test_groups=_group_roles(document, 'test_groups'),
            minimum_training_groups=cast('int', document['minimum_training_groups']),
            grouping=cast("Literal['source', 'profile']", document['grouping']),
        )
        for document in object_records(root.get('empirical_domains', ()))
    )
    identifiers = {candidate.id for candidate in evaluation.candidates}
    if len({plan.candidate_id for plan in plans}) != len(plans):
        message = 'Each candidate may have only one empirical domain registration per run.'
        raise EvaluationDocumentError(message)
    for plan in plans:
        if plan.candidate_id not in identifiers:
            message = 'Empirical domain references a candidate absent from the evaluation plan.'
            raise EvaluationDocumentError(message)
        validate_empirical_domain_roster(dataset.document, plan)
    return plans


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
            restart_policy=cast(
                'RestartPolicy',
                document.get('restart_policy', 'seeded_box_v1'),
            ),
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
        empirical_domains=(
            NestedDomainPlan(
                minimum_training_groups=cast(
                    'int', object_mapping(document['empirical_domains'])['minimum_training_groups']
                )
            )
            if 'empirical_domains' in document
            else None
        ),
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
