import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    EvaluationDocumentError,
    FixedSelectionPlan,
    LogPressureLossPlan,
    NestedDomainPlan,
    NestedGroupPlan,
    RetentionRunResult,
    diagnose_nested_applicability,
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    select_fixed_retention_candidates,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


POLICY = NestedDomainPlan(minimum_training_groups=2)
SELECTION = FixedSelectionPlan(
    candidate_ids=('sand_a', 'sand_b'),
    folds=NestedGroupPlan(seed=27, outer_folds=3, inner_folds=2),
    loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    empirical_domains=POLICY,
)


def _fixture(directory: Path, *, missing_target: bool = False) -> RetentionRunResult:
    dataset = json.loads(json.dumps(dataset_document()))
    template = dataset['samples'][0]
    dataset['samples'] = []
    dataset['observations'] = []
    for index in range(6):
        source = f'source_{index}'
        sample = copy.deepcopy(template)
        sample['source_id'] = source
        sample['features'][0]['value'] = 'clay' if index == 0 else 'sand'
        dataset['samples'].append(sample)
        if missing_target and index == 5:
            continue
        dataset['observations'].extend(
            {
                'id': f'{source}_{pressure}',
                'source_id': source,
                'sample_id': 'one',
                'suction_kpa': pressure,
                'value': value,
                'origin': 'synthetic',
                'review_status': 'confirmed',
                'quality_flags': [],
                'source_cells': [f'{source}!A1'],
            }
            for pressure, value in ((1, 0.5), (100, 0.25))
        )
    plan = load_retention_run_plan(write_run_fixture(directory, dataset=dataset))
    result = execute_retention_run(plan)
    points = []
    for point in result.points:
        assert point.comparison is not None
        delta = 0.125 if point.candidate_id == 'sand_a' else 0.25
        points.append(
            replace(point, comparison=replace(point.comparison, predicted=point.observed + delta))
        )
    result = replace(result, points=tuple(points))
    return replace(result, selection=select_fixed_retention_candidates(result, plan=SELECTION))


def test_all_inner_and_outer_domains_use_exact_training_roles_and_numeric_error_oracles(
    tmp_path: Path,
):
    result = _fixture(tmp_path)
    assert result.selection is not None
    diagnostics = diagnose_nested_applicability(result, policy=POLICY)
    assert diagnostics.status == 'computed'
    assert len(diagnostics.folds) == 18  # 3 outer * (outer + 2 inner) * 2 candidates.
    rare_outer_seen = False
    for diagnostic in diagnostics.folds:
        outer = result.selection.splits.folds[diagnostic.outer_fold_id]
        if diagnostic.inner_fold_id is None:
            training = outer.training_groups
            expected_test = outer.test_groups
        else:
            inner = outer.inner[diagnostic.inner_fold_id]
            training = inner.training_groups
            expected_test = inner.validation_groups
        assert diagnostic.domain.plan.training_groups == training
        assert diagnostic.domain.plan.test_groups == expected_test
        assert set(training).isdisjoint(expected_test)
        categories = diagnostic.domain.members[0].bounds[0].categories
        assert categories == (('clay', 'sand') if ('source_0', '') in training else ('sand',))
        statuses = {sample.source_id: sample.status for sample in diagnostic.samples}
        if diagnostic.inner_fold_id is None and 'source_0' in statuses:
            rare_outer_seen = True
            assert statuses['source_0'] == 'outside'
        assert diagnostic.selected_by_inner_validation == (
            diagnostic.inner_fold_id is None and diagnostic.domain.plan.candidate_id == 'sand_a'
        )
        delta = 0.125 if diagnostic.domain.plan.candidate_id == 'sand_a' else 0.25
        for stratum in diagnostic.strata:
            if not stratum.samples:
                assert stratum.confidence.summary is None
                assert stratum.mean_log_pressure_loss is None
                continue
            assert stratum.mean_log_pressure_loss == pytest.approx(delta**2)
            assert stratum.eligible_loss_sample_count == stratum.total_sample_count
            assert stratum.confidence.summary is not None
            assert stratum.confidence.summary.metrics.mean_error == pytest.approx(delta)
            assert stratum.confidence.summary.metrics.root_mean_squared_error == pytest.approx(
                delta
            )
    assert rare_outer_seen


def test_missing_targets_remain_in_stratum_coverage_denominators(tmp_path: Path):
    result = _fixture(tmp_path, missing_target=True)
    diagnostics = diagnose_nested_applicability(result, policy=POLICY)
    containing = [
        stratum
        for fold in diagnostics.folds
        if fold.partition == 'outer_test'
        for stratum in fold.strata
        if ('source_5', 'one') in stratum.samples
    ]
    assert len(containing) == 2
    for stratum in containing:
        assert stratum.total_sample_count > stratum.eligible_loss_sample_count
        missing = next(sample for sample in stratum.loss_samples if sample.source_id == 'source_5')
        assert missing.loss is None
        assert missing.reason == 'insufficient_points'


def test_outer_inputs_and_targets_cannot_expand_own_training_domain_or_change_choices(
    tmp_path: Path,
):
    result = _fixture(tmp_path)
    assert result.selection is not None
    before = diagnose_nested_applicability(result, policy=POLICY)
    held_out = {group[0] for group in result.selection.splits.folds[0].test_groups}
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    for sample in dataset['samples']:
        if sample['source_id'] in held_out:
            sample['features'][0]['value'] = 'loam'
    for point in dataset['observations']:
        if point['source_id'] in held_out:
            point['value'] = 0.99
    changed = replace(result, plan=replace(result.plan, dataset=load_retention_dataset(dataset)))
    after = diagnose_nested_applicability(changed, policy=POLICY)
    for one, two in zip(before.folds, after.folds, strict=True):
        if one.outer_fold_id == 0:
            assert [member.bounds for member in one.domain.members] == [
                member.bounds for member in two.domain.members
            ]
    assert result.selection == changed.selection
    assert all(
        sample.status == 'outside'
        for fold in after.folds
        if fold.outer_fold_id == 0 and fold.partition == 'outer_test'
        for sample in fold.samples
    )


def test_nested_domain_evidence_gate_never_alters_selection(tmp_path: Path):
    result = _fixture(tmp_path)
    before = result.selection
    diagnostics = diagnose_nested_applicability(
        result, policy=NestedDomainPlan(minimum_training_groups=99)
    )
    assert diagnostics.status == 'computed'
    assert all(
        sample.status == 'insufficient_evidence'
        for fold in diagnostics.folds
        for sample in fold.samples
    )
    assert all(member.bounds == () for fold in diagnostics.folds for member in fold.domain.members)
    assert result.selection == before


def test_nested_domain_pipeline_persists_and_replays(tmp_path: Path):
    result = _fixture(tmp_path / 'inputs')
    plan_document = json.loads(canonical_json(result.plan.document))
    plan_document['selection'] = {
        'method': 'fixed_candidate_nested_selection_v1',
        'candidate_ids': ['sand_a', 'sand_b'],
        'minimum_coverage': 1,
        'tie_breaker': 'candidate_id',
        'failure_policy': 'require_common_cohort',
        'folds': {
            'seed': 27,
            'outer_folds': 3,
            'inner_folds': 2,
            'grouping': 'source',
            'missing_profiles': 'reject',
            'minimum_training_groups': 2,
            'minimum_validation_groups': 1,
        },
        'loss': {
            'method': 'log10_trapezoid_mse_v1',
            'lower_suction_kpa': 1,
            'upper_suction_kpa': 100,
            'minimum_points': 2,
        },
        'empirical_domains': {
            'method': 'nested_training_input_envelope_v1',
            'minimum_training_groups': 2,
            'composite_rule': 'all_registered_members',
        },
    }
    plan = load_retention_run_plan(plan_document, base_directory=tmp_path / 'inputs')
    executed = execute_retention_run(plan)
    assert executed.nested_applicability is not None
    output = write_retention_run(executed, tmp_path / 'output')
    assert 'Nested input-domain diagnostics' in read_retention_run_report(output)
    saved = json.loads((output / 'nested-applicability.json').read_text('utf-8'))
    assert len(saved['folds']) == 18
    assert sum(stratum['total_sample_count'] for stratum in saved['folds'][0]['strata']) == 2
    replay = execute_retention_run(load_retention_run_plan(output / 'run-plan.json'))
    assert replay.nested_applicability == executed.nested_applicability


def test_missing_selection_evidence_is_rejected(tmp_path: Path):
    with pytest.raises(EvaluationDocumentError, match='nested selection'):
        diagnose_nested_applicability(replace(_fixture(tmp_path), selection=None), policy=POLICY)


def test_failed_splits_remain_insufficient_without_partial_domains(tmp_path: Path):
    result = _fixture(tmp_path)
    impossible = replace(SELECTION, folds=replace(SELECTION.folds, minimum_training_groups=99))
    selection = select_fixed_retention_candidates(result, plan=impossible)
    assessment = diagnose_nested_applicability(replace(result, selection=selection), policy=POLICY)
    assert assessment.status == 'insufficient_evidence'
    assert assessment.reason == 'insufficient_groups_for_requested_folds'
    assert assessment.folds == ()


def test_domains_follow_explicit_whole_roster_profile_fallback(tmp_path: Path):
    result = _fixture(tmp_path)
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    for sample in dataset['samples']:
        sample['profile_id'] = None
    result = replace(result, plan=replace(result.plan, dataset=load_retention_dataset(dataset)))
    plan = replace(
        SELECTION, folds=replace(SELECTION.folds, grouping='profile', missing_profiles='source')
    )
    selection = select_fixed_retention_candidates(result, plan=plan)
    assert selection.splits.effective_grouping == 'source'
    diagnostics = diagnose_nested_applicability(replace(result, selection=selection), policy=POLICY)
    assert len(diagnostics.folds) == 18
    assert all(fold.domain.plan.grouping == 'source' for fold in diagnostics.folds)


def test_composite_all_member_rule_and_failed_input_priority():
    path = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_retention/run.json'
    plan = load_retention_run_plan(path)
    dataset = json.loads(canonical_json(plan.dataset.document))
    sample = dataset['samples'][0]
    for feature in sample['features']:
        if feature['id'] == 'carbon':
            feature['value'] = None
    assert plan.selection is not None
    plan = replace(
        plan,
        dataset=load_retention_dataset(dataset),
        approximations=(),
        bootstrap=replace(plan.bootstrap, n_resamples=16),
        selection=replace(plan.selection, empirical_domains=POLICY),
    )
    result = execute_retention_run(plan)
    assert result.nested_applicability is not None
    frames = [
        fold
        for fold in result.nested_applicability.folds
        if fold.domain.plan.candidate_id == 'fixed_blend'
    ]
    assert len(frames) == 9
    failed_seen = False
    for fold in frames:
        for assessment in fold.samples:
            wet, dry = assessment.member_statuses
            assert wet == ('wet', 'inside')
            if (
                assessment.source_id == sample['source_id']
                and assessment.sample_id == sample['sample_id']
            ):
                failed_seen = True
                assert dry == ('dry', 'excluded_input')
                assert assessment.status == 'excluded_input'
            else:
                assert assessment.status == dry[1]
    assert failed_seen
