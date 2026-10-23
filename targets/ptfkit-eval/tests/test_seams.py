import json
from pathlib import Path

import pytest
from _run_fixtures import write_run_fixture

from ptfkit_eval import (
    RetentionRunPlan,
    diagnose_composite_seams,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)


EXAMPLES = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_retention'


def _plan(
    directory: Path, *, blend: bool = False, missing_dry_input: bool = False
) -> RetentionRunPlan:
    dataset = json.loads((EXAMPLES / 'dataset.json').read_text('utf-8'))
    evaluation = json.loads((EXAMPLES / 'evaluation_plan.json').read_text('utf-8'))
    dataset['samples'] = dataset['samples'][:1]
    dataset['observations'] = []
    values = {
        'texture': 'sand',
        'sand': 52.14,
        'clay': 10.93,
        'carbon': 1.03,
        'bulk_density': 1.466,
    }
    for feature in dataset['samples'][0]['features']:
        feature['value'] = values[feature['id']]
        if missing_dry_input and feature['id'] == 'carbon':
            feature['value'] = None
    candidate = evaluation['candidates'][2]
    candidate['members'][0]['interval']['upper']['value'] = 10
    candidate['members'][1]['interval']['lower']['value'] = 1
    transition = candidate['routing']['transitions'][0]
    transition['interval']['lower']['value'] = 1
    transition['interval']['upper']['value'] = 10
    if not blend:
        candidate['routing']['transitions'] = [
            {
                'kind': 'hard_switch',
                'at': 1,
                'boundary_member': 'left',
                'left_member': 'wet',
                'right_member': 'dry',
            }
        ]
    evaluation['candidates'] = [candidate]
    path = write_run_fixture(directory, dataset=dataset, evaluation=evaluation)
    document = json.loads(path.read_text('utf-8'))
    document['protocol']['bindings']['calc_ptf_vereecken1989'] = {
        'sand': 'sand',
        'clay': 'clay',
        'carbon': 'carbon',
        'bulk_density': 'bulk_density',
    }
    return load_retention_run_plan(document, base_directory=directory)


@pytest.mark.parametrize('blend', [False, True])
def test_seams_evaluate_both_members_without_observations(tmp_path: Path, *, blend: bool):
    plan = _plan(tmp_path, blend=blend)
    diagnostics = diagnose_composite_seams(plan)
    assert [item.suction_kpa for item in diagnostics] == ([1, 10] if blend else [1])
    assert [item.kind for item in diagnostics] == (
        ['blend_start', 'blend_end'] if blend else ['hard_switch']
    )
    for item in diagnostics:
        pressure = item.suction_kpa
        # Specification verification parameters at the published mean inputs,
        # combined with the reduced m=1 equation and cm-water conversion.
        vereecken = 0.08407 + (0.406052 - 0.08407) / (
            1 + (0.003581613076579849 * pressure / 0.0980665) ** 0.8602234826041976
        )
        clapp = 0.395 * (3.5 * 0.0980665 / pressure) ** (1 / 4.05)
        assert item.status == 'computed'
        assert item.left.value == pytest.approx(clapp)
        assert item.right.value == pytest.approx(vereecken)
        assert item.right_minus_left == pytest.approx(vereecken - clapp)
        assert item.left.input_traces[0].source_cells
        assert item.left.prediction is not None
        assert item.right.prediction is not None
        assert item.left.prediction.contributions[0].function == 'calc_ptf_clapp1978'
        assert item.right.prediction.contributions[0].function == 'calc_ptf_vereecken1989'


def test_zero_weight_member_failure_is_visible_without_hiding_the_other_member(tmp_path: Path):
    plan = _plan(tmp_path, blend=True, missing_dry_input=True)
    diagnostics = diagnose_composite_seams(plan)
    assert len(diagnostics) == 2
    for item in diagnostics:
        assert item.status == 'unavailable'
        assert item.left.value is not None
        assert item.right.value is None
        assert item.right.reasons == ('missing_input',)
        assert item.right_minus_left is None


def test_run_writes_seam_evidence_for_samples_without_targets_and_replays(tmp_path: Path):
    plan = _plan(tmp_path / 'input')
    result = execute_retention_run(plan)
    assert result.points == ()
    assert len(result.seam_diagnostics) == 1
    output = write_retention_run(result, tmp_path / 'run')
    assert 'Composite transition diagnostics' in read_retention_run_report(output)
    artifact = json.loads((output / 'composite-seams.json').read_text('utf-8'))
    assert artifact[0]['suction_kpa'] == 1
    replay = execute_retention_run(load_retention_run_plan(output / 'run-plan.json'))
    assert replay.seam_diagnostics == result.seam_diagnostics
