import hashlib
import json
import math
from pathlib import Path
from typing import cast

import pytest
from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    CurveEvaluation,
    CurvePoint,
    EvaluationDocumentError,
    FunctionCurveCandidate,
    RangeGatedCurveCandidate,
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.cli import main
from ptfkit_eval.documents import object_records


def test_executes_real_public_ptf_and_preserves_hand_calculated_errors_and_lineage(tmp_path: Path):
    plan = load_retention_run_plan(write_run_fixture(tmp_path))
    result = execute_retention_run(plan)

    assert len(result.points) == 8
    assert all(point.eligible for point in result.points)
    assert [point.prediction.value for point in result.points if point.prediction] == pytest.approx(
        [0.395, 0.1975] * 4
    )
    assert result.points[0].observation_cells == ('a!B1', 'a!C1')
    trace = result.points[0].input_traces[0]
    assert trace.source_cells == ('a!A1',)
    assert (trace.feature_id, trace.input, trace.value, trace.compatibility) == (
        'texture',
        'soil_texture',
        'sand',
        'exact',
    )
    assert result.points[0].prediction is not None
    assert result.points[0].prediction.contributions[0].function == 'calc_ptf_clapp1978'
    assert len(result.cohorts) == 4
    for item in result.cohorts:
        summary = item.cohort.summary
        assert summary is not None
        assert (summary.sample_count, summary.point_count, summary.source_count) == (2, 4, 2)
        assert summary.metrics.mean_error == pytest.approx(0.04625)
        assert summary.metrics.mean_absolute_error == pytest.approx(0.04875)
        assert summary.metrics.root_mean_squared_error == pytest.approx(math.sqrt(0.004515625))
        assert item.confidence.status == 'computed'
    missing = [
        sample for sample in result.sample_eligibility if sample.source_id == 'without_target'
    ]
    assert len(missing) == 2
    assert all(sample.reasons == ('missing_target',) for sample in missing)


def test_blocked_features_and_invalid_targets_remain_visible_exclusions(tmp_path: Path):
    document = json.loads(json.dumps(dataset_document()))
    document['samples'][0]['features'][0]['review_status'] = 'blocked'
    document['samples'][0]['features'][0]['blockers'] = ['texture_review']
    document['observations'][2]['quality_flags'] = ['suspect_scale']
    result = execute_retention_run(
        load_retention_run_plan(write_run_fixture(tmp_path, dataset=document))
    )

    reasons = [point.reasons for point in result.points[:4]]
    assert reasons == [
        ('unreviewed_input',),
        ('unreviewed_input',),
        ('failed_quality_control',),
        (),
    ]
    assert result.points[0].input_traces[0].source_cells == ('a!A1',)
    assert result.points[2].prediction is None
    assert result.cohorts[0].confidence.reason == 'too_few_groups'


def test_artifacts_are_repeatable_complete_and_integrity_checked(tmp_path: Path):
    result = execute_retention_run(load_retention_run_plan(write_run_fixture(tmp_path / 'inputs')))
    first = write_retention_run(result, tmp_path / 'first')
    second = write_retention_run(result, tmp_path / 'second')

    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    manifest = json.loads((first / 'run-manifest.json').read_text('utf-8'))
    assert manifest['run_kind'] == 'synthetic_validation'
    assert len(manifest['input_hashes']['ptfkit_manifest']) == 64
    for name, metadata in manifest['files'].items():
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == metadata['sha256']
    report = read_retention_run_report(first)
    assert 'not external predictive accuracy evidence' in report
    assert 'sand_a' in report
    replay = execute_retention_run(load_retention_run_plan(first / 'run-plan.json'))
    assert replay.points == result.points
    assert replay.cohorts == result.cohorts
    decisions = json.loads((first / 'point-decisions.json').read_text('utf-8'))
    assert decisions[0]['eligible'] is True
    with pytest.raises(FileExistsError):
        write_retention_run(result, first)
    (first / 'point-decisions.json').write_text('[]\n', encoding='utf-8')
    with pytest.raises(EvaluationDocumentError, match='checksum'):
        read_retention_run_report(first)


@pytest.mark.parametrize('system', ['Windows', 'Linux'])
def test_failed_publication_removes_its_staging_without_publishing_partial_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    system: str,
):
    result = execute_retention_run(load_retention_run_plan(write_run_fixture(tmp_path / 'inputs')))
    monkeypatch.setattr('ptfkit_eval.artifacts.platform.system', lambda: system)

    def failed_write(_path: Path, _data: bytes) -> int:
        message = 'Injected publication failure.'
        raise OSError(message)

    monkeypatch.setattr(Path, 'write_bytes', failed_write)
    with pytest.raises(OSError, match='Injected publication failure'):
        write_retention_run(result, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()
    assert list(tmp_path.glob('.output.*')) == []


def test_checksum_drift_is_rejected_before_execution(tmp_path: Path):
    path = write_run_fixture(tmp_path)
    with (tmp_path / 'dataset.json').open('a', encoding='utf-8') as stream:
        stream.write('\n')
    with pytest.raises(EvaluationDocumentError, match='Checksum mismatch'):
        load_retention_run_plan(path)


def test_portable_data_rejects_duplicate_keys_and_orphan_observations():
    document = json.loads(json.dumps(dataset_document()))
    document['observations'][0]['sample_id'] = 'unknown'
    with pytest.raises(EvaluationDocumentError, match='unknown sample'):
        load_retention_dataset(document)
    document = json.loads(json.dumps(dataset_document()))
    document['samples'].append(document['samples'][0])
    with pytest.raises(EvaluationDocumentError, match='Duplicate canonical sample'):
        load_retention_dataset(document)


def test_canonical_data_is_recursively_read_only_and_not_aliased():
    document = json.loads(json.dumps(dataset_document()))
    dataset = load_retention_dataset(document)
    document['samples'][0]['features'][0]['value'] = 'clay'
    assert json.loads(json.dumps(document))['samples'][0]['features'][0]['value'] == 'clay'

    sample = object_records(dataset.document['samples'])[0]
    assert object_records(sample['features'])[0]['value'] == 'sand'
    with pytest.raises(TypeError):
        cast('dict[str, object]', dataset.document)['dataset_id'] = 'changed'


def test_cli_validates_runs_and_reads_reports(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    path = write_run_fixture(tmp_path / 'inputs')
    assert main(['plan', str(path)]) == 0
    assert json.loads(capsys.readouterr().out)['kind'] == 'retention_run'
    destination = tmp_path / 'run'
    assert main(['run', str(path), '--output', str(destination)]) == 0
    capsys.readouterr()
    assert main(['report', str(destination)]) == 0
    assert 'synthetic_retention_v1' in capsys.readouterr().out


def test_cli_reports_input_errors_with_nonzero_status(tmp_path: Path):
    with pytest.raises(SystemExit) as error:
        main(['plan', str(tmp_path / 'missing.json')])
    assert error.value.code == 2


def test_nonfinite_function_results_are_exclusions_that_can_still_be_published(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    def nonfinite(
        candidate: FunctionCurveCandidate | RangeGatedCurveCandidate,
        axes: list[float],
        _inputs: object,
        **_kwargs: object,
    ) -> CurveEvaluation:
        return CurveEvaluation(candidate.id, (CurvePoint(axes[0], math.nan, ()),))

    monkeypatch.setattr('ptfkit_eval.runner.evaluate_candidate', nonfinite)
    result = execute_retention_run(load_retention_run_plan(write_run_fixture(tmp_path / 'inputs')))
    assert len(result.points) == 8
    assert all(point.reasons == ('nonfinite_prediction_error',) for point in result.points)
    assert all(point.prediction is None for point in result.points)
    output = write_retention_run(result, tmp_path / 'output')
    assert 'NaN' not in (output / 'point-decisions.json').read_text('utf-8')
    assert 'excluded_point_count' in read_retention_run_report(output)
