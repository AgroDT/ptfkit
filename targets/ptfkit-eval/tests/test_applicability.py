import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    EmpiricalDomainPlan,
    EvaluationDocumentError,
    RetentionRunPlan,
    assess_retention_applicability,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


EXAMPLES = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_retention'


def _numeric_plan(
    directory: Path, *, test_sand: float = 70, missing_training: bool = False
) -> RetentionRunPlan:
    dataset = json.loads((EXAMPLES / 'dataset.json').read_text('utf-8'))
    evaluation = json.loads((EXAMPLES / 'evaluation_plan.json').read_text('utf-8'))
    evaluation['candidates'] = [evaluation['candidates'][1]]
    template = dataset['samples'][0]
    dataset['samples'] = []
    dataset['observations'] = []
    for source, sand in (('a', 40), ('b', 60), ('test', test_sand)):
        sample = copy.deepcopy(template)
        sample.update(source_id=source, sample_id='one')
        for feature in sample['features']:
            if feature['id'] == 'sand':
                feature['value'] = sand / 100
                feature['measurement']['unit'] = 'mass_fraction'
            if feature['id'] == 'carbon' and source == 'b' and missing_training:
                feature['value'] = None
        dataset['samples'].append(sample)
    path = write_run_fixture(directory, dataset=dataset, evaluation=evaluation)
    document = json.loads(path.read_text('utf-8'))
    document['protocol']['bindings'] = {
        'calc_ptf_vereecken1989': {
            'sand': 'sand',
            'clay': 'clay',
            'carbon': 'carbon',
            'bulk_density': 'bulk_density',
        }
    }
    document['empirical_domains'] = [
        {
            'method': 'training_input_envelope_v1',
            'candidate_id': 'vereecken',
            'training_groups': [['a', ''], ['b', '']],
            'test_groups': [['test', '']],
            'grouping': 'source',
            'minimum_training_groups': 2,
        }
    ]
    return load_retention_run_plan(document, base_directory=directory)


@pytest.mark.parametrize(
    ('test_sand', 'expected'), [(40, 'inside'), (60, 'inside'), (70, 'outside')]
)
def test_numeric_domain_uses_converted_training_inputs_and_inclusive_bounds(
    tmp_path: Path, test_sand: float, expected: str
):
    plan = _numeric_plan(tmp_path, test_sand=test_sand)
    result = assess_retention_applicability(plan, policy=plan.empirical_domains[0])
    member = result.members[0]
    sand = next(bound for bound in member.bounds if bound.input == 'sand')

    assert (sand.unit, sand.lower, sand.upper) == ('mass_percent', 40, 60)
    assert member.training_group_count == 2
    assert member.test_samples[0].status == expected
    assert member.test_samples[0].input_traces[0].compatibility == 'unit_converted'
    assert member.test_samples[0].reasons == (
        ('outside_empirical_input:sand',) if expected == 'outside' else ()
    )
    # Other predictors are constant and remain valid at both equal bounds.
    assert all(bound.lower == bound.upper for bound in member.bounds if bound.input != 'sand')


def test_incomplete_training_vectors_cannot_supply_partial_bounds(tmp_path: Path):
    plan = _numeric_plan(tmp_path, missing_training=True)
    member = assess_retention_applicability(plan, policy=plan.empirical_domains[0]).members[0]

    assert member.status == 'insufficient_evidence'
    assert member.reason == 'too_few_training_groups'
    assert member.training_group_count == 1
    assert member.bounds == ()
    assert member.training_samples[1].reasons == ('missing_input',)
    assert member.test_samples[0].status == 'insufficient_evidence'


def test_test_inputs_cannot_change_training_bounds(tmp_path: Path):
    first = _numeric_plan(tmp_path / 'first', test_sand=50)
    changed = _numeric_plan(tmp_path / 'changed', test_sand=80)
    one = assess_retention_applicability(first, policy=first.empirical_domains[0]).members[0]
    two = assess_retention_applicability(changed, policy=changed.empirical_domains[0]).members[0]
    assert one.bounds == two.bounds
    assert (one.test_samples[0].status, two.test_samples[0].status) == ('inside', 'outside')


def test_categorical_domain_and_target_independence_are_preserved_in_run(tmp_path: Path):
    dataset = json.loads(json.dumps(dataset_document()))
    dataset['samples'][1]['features'][0]['value'] = 'clay'
    plan = load_retention_run_plan(write_run_fixture(tmp_path / 'inputs', dataset=dataset))
    policy = EmpiricalDomainPlan(
        candidate_id='sand_a',
        training_groups=(('a', ''),),
        test_groups=(('b', ''),),
        minimum_training_groups=1,
    )
    domain = assess_retention_applicability(plan, policy=policy)
    assert domain.members[0].bounds[0].categories == ('sand',)
    assert domain.members[0].test_samples[0].status == 'outside'
    changed = copy.deepcopy(dataset)
    changed['observations'] = []
    changed_plan = load_retention_run_plan(write_run_fixture(tmp_path / 'changed', dataset=changed))
    assert assess_retention_applicability(changed_plan, policy=policy) == domain


def test_profiles_are_source_local_and_sample_multiplicity_does_not_inflate_groups(tmp_path: Path):
    dataset = json.loads(json.dumps(dataset_document()))
    extra = copy.deepcopy(dataset['samples'][0])
    extra['sample_id'] = 'two'
    dataset['samples'].append(extra)
    dataset['samples'][1]['features'][0]['value'] = 'clay'
    plan = load_retention_run_plan(write_run_fixture(tmp_path / 'first', dataset=dataset))
    policy = EmpiricalDomainPlan(
        candidate_id='sand_a',
        training_groups=(('a', 'profile_one'),),
        test_groups=(('b', 'profile_one'),),
        grouping='profile',
        minimum_training_groups=2,
    )
    domain = assess_retention_applicability(plan, policy=policy)
    member = domain.members[0]
    assert len(member.training_samples) == 2
    assert member.training_group_count == 1
    assert member.status == 'insufficient_evidence'
    assert len(member.test_samples) == 1
    assessed = assess_retention_applicability(
        plan, policy=replace(policy, minimum_training_groups=1)
    )
    assert assessed.members[0].test_samples[0].status == 'outside'
    dataset['samples'].reverse()
    reordered = load_retention_run_plan(write_run_fixture(tmp_path / 'reordered', dataset=dataset))
    assert assess_retention_applicability(reordered, policy=policy) == domain


def test_missing_profile_has_no_implicit_source_fallback(tmp_path: Path):
    dataset = json.loads(json.dumps(dataset_document()))
    dataset['samples'][0]['profile_id'] = None
    plan = load_retention_run_plan(write_run_fixture(tmp_path, dataset=dataset))
    policy = EmpiricalDomainPlan(
        candidate_id='sand_a',
        training_groups=(('a', 'profile_one'),),
        test_groups=(('b', 'profile_one'),),
        grouping='profile',
        minimum_training_groups=1,
    )
    with pytest.raises(EvaluationDocumentError, match='complete profile identifiers'):
        assess_retention_applicability(plan, policy=policy)


def test_run_retains_domain_artifact_without_changing_scoring_and_replays(tmp_path: Path):
    plan = _numeric_plan(tmp_path / 'input')
    result = execute_retention_run(plan)
    baseline = execute_retention_run(replace(plan, empirical_domains=()))
    assert result.points == baseline.points
    assert result.cohorts == baseline.cohorts
    assert result.empirical_domains[0].members[0].test_samples[0].status == 'outside'
    output = write_retention_run(result, tmp_path / 'run')
    assert 'Empirical input domains' in read_retention_run_report(output)
    artifact = json.loads((output / 'empirical-domains.json').read_text('utf-8'))
    assert artifact[0]['members'][0]['bounds'][0]['upper'] == 60
    replay = execute_retention_run(load_retention_run_plan(output / 'run-plan.json'))
    assert replay.empirical_domains == result.empirical_domains


def test_composite_example_retains_separate_member_domains():
    plan = load_retention_run_plan(EXAMPLES / 'run.json')
    policy = next(
        policy for policy in plan.empirical_domains if policy.candidate_id == 'fixed_blend'
    )
    result = assess_retention_applicability(plan, policy=policy)
    wet, dry = result.members
    assert (wet.member_id, dry.member_id) == ('wet', 'dry')
    assert len(wet.bounds) == 1
    assert len(dry.bounds) == 4
    assert wet.training_group_count == dry.training_group_count == 4
    assert len(wet.training_samples) == len(dry.training_samples) == 8
    sand = next(bound for bound in dry.bounds if bound.input == 'sand')
    assert (sand.lower, sand.upper) == (55, 59)
    assert [sample.status for sample in wet.test_samples] == ['inside'] * 4
    assert [sample.status for sample in dry.test_samples] == [
        'inside',
        'outside',
        'outside',
        'outside',
    ]


@pytest.mark.parametrize(
    'change', ['overlap', 'duplicate', 'unknown', 'profile', 'candidate', 'gate']
)
def test_domain_registration_rejects_invalid_roles(tmp_path: Path, change: str):
    plan = _numeric_plan(tmp_path)
    document = json.loads(canonical_json(plan.document))
    policy = document['empirical_domains'][0]
    if change == 'overlap':
        policy['test_groups'] = [['a', '']]
    elif change == 'duplicate':
        policy['training_groups'].append(['a', ''])
    elif change == 'unknown':
        policy['training_groups'] = [['absent', '']]
    elif change == 'profile':
        policy['grouping'] = 'profile'
    elif change == 'candidate':
        policy['candidate_id'] = 'absent'
    else:
        policy['minimum_training_groups'] = 0
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(document, base_directory=tmp_path)
