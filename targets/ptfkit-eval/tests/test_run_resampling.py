import json
from dataclasses import replace
from pathlib import Path

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


EXAMPLE = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_retraining/run.json'


def _document() -> dict[str, object]:
    source = load_retention_run_plan(EXAMPLE)
    document = json.loads(canonical_json(source.document))
    document['bootstrap']['n_resamples'] = 16
    document['selection_resampling'][0]['n_resamples'] = 2
    return document


def test_public_run_refits_complete_selection_procedures_with_portable_audit_and_replay(
    tmp_path: Path,
):
    plan = load_retention_run_plan(_document(), base_directory=EXAMPLE.parent)
    result = execute_retention_run(plan)
    assert len(result.selection_resampling) == 1
    output = result.selection_resampling[0]
    assert output.status == 'completed'
    assert output.complete_replicate_count == 2
    assert [replicate.unique_group_count for replicate in output.replicates] == [8, 6]
    assert [
        sum(item.count for item in replicate.multiplicities) for replicate in output.replicates
    ] == [12, 12]
    assert [len(replicate.samples) for replicate in output.replicates] == [24, 24]
    baseline = execute_retention_run(replace(plan, selection_resampling=()))
    assert baseline.points == result.points
    assert baseline.learned_selection == result.learned_selection
    assert baseline.strategy_assessments == result.strategy_assessments
    destination = write_retention_run(result, tmp_path / 'run')
    report = read_retention_run_report(destination)
    assert 'Whole-group selection retraining sensitivity' in report
    assert 'not_estimated_retraining_sensitivity_only' in report
    artifact = json.loads((destination / 'selection-resampling.json').read_text('utf-8'))
    assert artifact[0]['complete_replicate_count'] == 2
    assert artifact[0]['replicates'][0]['unique_group_count'] == 8
    assert len(artifact[0]['replicates'][0]['multiplicities']) == 12
    replay = execute_retention_run(load_retention_run_plan(destination / 'run-plan.json'))
    assert replay.selection_resampling == result.selection_resampling


@pytest.mark.parametrize(
    'change', ['missing_protocol', 'duplicate', 'confidence_level', 'method', 'seed']
)
def test_invalid_resampling_run_registrations_are_rejected(change: str):
    document = json.loads(json.dumps(_document()))
    policy = document['selection_resampling'][0]
    if change == 'missing_protocol':
        policy['protocol'] = 'fixed'
    elif change == 'duplicate':
        document['selection_resampling'].append(dict(policy))
    elif change == 'confidence_level':
        policy['confidence_level'] = 0.95
    elif change == 'method':
        policy['method'] = 'naive_crossfit_confidence'
    else:
        policy['seed'] = None
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(document, base_directory=EXAMPLE.parent)
