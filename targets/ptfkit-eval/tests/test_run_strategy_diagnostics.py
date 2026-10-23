import json
from dataclasses import replace
from pathlib import Path

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    RetentionRunResult,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


EXAMPLE = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_hard_switch/run.json'


@pytest.fixture(scope='module')
def diagnostic_run() -> RetentionRunResult:
    source = load_retention_run_plan(EXAMPLE)
    document = json.loads(canonical_json(source.document))
    document['bootstrap']['n_resamples'] = 16
    return execute_retention_run(load_retention_run_plan(document, base_directory=EXAMPLE.parent))


def test_public_pipeline_persists_quality_and_locked_strategy_metrics_with_replay(
    tmp_path: Path, diagnostic_run: RetentionRunResult
):
    result = diagnostic_run
    assert len(result.selection_quality) == 96
    assert len(result.strategy_assessments) == 1
    assessment = result.strategy_assessments[0]
    assert assessment.protocol == 'learned'
    assert assessment.status == 'computed'
    assert [
        (item.total_sample_count, item.eligible_loss_sample_count) for item in assessment.strategies
    ] == [(12, 12), (12, 12)]
    assert result.learned_selection is not None
    for summary, original in zip(
        assessment.strategies, result.learned_selection.protocols, strict=True
    ):
        assert summary.selected_counts == original.selected_counts
        assert summary.mean_outer_loss == original.mean_outer_loss
    output = write_retention_run(result, tmp_path / 'run')
    report = read_retention_run_report(output)
    assert 'Held-out curve physical diagnostics' in report
    assert 'Locked outer strategy descriptive assessment' in report
    assert 'loss coverage=12/12' in report
    assert 'not_estimated_crossfit_dependency' in report
    quality = json.loads((output / 'selection-curve-quality.json').read_text('utf-8'))
    assert sum(curve['partition'] == 'outer_test' for curve in quality) == 24
    saved = json.loads((output / 'strategy-assessment.json').read_text('utf-8'))
    assert saved[0]['strategies'][0]['total_sample_count'] == 12
    assert saved[0]['cohorts']['common'][0]['summary']['point_count'] == 60
    replay = execute_retention_run(load_retention_run_plan(output / 'run-plan.json'))
    assert replay.selection_quality == result.selection_quality
    assert replay.strategy_assessments == result.strategy_assessments


def test_new_diagnostics_do_not_modify_ordinary_candidate_predictions(
    diagnostic_run: RetentionRunResult,
):
    result = diagnostic_run
    baseline = execute_retention_run(replace(result.plan, learned_selection=None))
    assert result.points == baseline.points
    assert result.cohorts == baseline.cohorts
    assert baseline.selection_quality == ()
    assert baseline.strategy_assessments == ()


def test_new_strategy_artifact_is_covered_by_integrity_verification(
    tmp_path: Path, diagnostic_run: RetentionRunResult
):
    output = write_retention_run(diagnostic_run, tmp_path / 'run')
    artifact = output / 'strategy-assessment.json'
    document = json.loads(artifact.read_text('utf-8'))
    document[0]['strategies'][0]['total_sample_count'] = 999
    artifact.write_text(json.dumps(document), encoding='utf-8')
    with pytest.raises(EvaluationDocumentError, match='checksum mismatch'):
        read_retention_run_report(output)
