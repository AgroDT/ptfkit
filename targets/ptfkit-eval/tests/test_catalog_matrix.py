from __future__ import annotations

import runpy
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from _run_fixtures import dataset_document

from ptfkit_eval import load_retention_dataset
from ptfkit_eval.predictors import (
    FunctionPredictorAudit,
    FunctionSampleEligibility,
    PredictorAuditResult,
    PredictorAuditSummary,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from ptfkit_eval import CanonicalRetentionDataset


def _inputs() -> tuple[dict, CanonicalRetentionDataset, PredictorAuditResult]:
    document = dataset_document()
    document['source_files'] = [{'id': 'workbook', 'filename': 'fixture.xlsx', 'sha256': 'a' * 64}]
    coverage = {
        'implemented_functions': 2,
        'manifest_functions': 1,
        'functions': [
            {
                'id': 'complete',
                'manifest_eligible': True,
                'missing_measurement_paths': [],
                'outputs': [{'quantity': 'volumetric_water_content'}],
            },
            {
                'id': 'legacy',
                'manifest_eligible': False,
                'missing_measurement_paths': ['inputs.clay.measurement'],
                'outputs': [{'quantity': 'gravimetric_water_content'}],
            },
        ],
    }
    summary = PredictorAuditSummary(
        schema_version=2,
        source_filename='fixture.xlsx',
        sha256='a' * 64,
        manifest_schema_version=1,
        public_function_count=1,
        candidate_sample_count=3,
        binding_audits=(),
        function_audits=(FunctionPredictorAudit('complete', 1, 3, 1, 1, 2),),
        exclusion_reasons=(),
    )
    rows = (
        FunctionSampleEligibility(
            'master!1',
            'one',
            'a',
            1,
            'complete',
            eligible=False,
            reasons=('missing_input_binding',),
        ),
        FunctionSampleEligibility('master!2', 'one', 'b', 1, 'complete', eligible=True, reasons=()),
        FunctionSampleEligibility(
            'master!3', 'one', 'b', 1, 'complete', eligible=False, reasons=('missing_input',)
        ),
    )
    return coverage, load_retention_dataset(document), PredictorAuditResult(summary, (), rows)


def _builder(monkeypatch: pytest.MonkeyPatch) -> Callable:
    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root))
    return runpy.run_path(str(root / 'evaluation/experiments/catalog_coverage/matrix.py'))[
        'build_matrix'
    ]


def test_matrix_keeps_every_function_and_never_counts_unbound_inputs_as_present(
    monkeypatch: pytest.MonkeyPatch,
):
    report = _builder(monkeypatch)(*_inputs())
    assert (
        report['source_partition_count'],
        report['sample_count'],
        report['observation_count'],
    ) == (
        3,
        3,
        4,
    )
    partitions = {item['source_id']: item for item in report['source_partitions']}
    assert partitions['a']['functions'][0]['predictor_counts'] == {
        'matched_samples': 1,
        'complete_raw_inputs': 0,
        'predictor_blocked': 1,
    }
    assert partitions['a']['functions'][0]['predictor_blockers'] == {'missing_input_binding': 1}
    assert partitions['b']['functions'][0]['predictor_blockers'] == {'ambiguous_identity': 1}
    assert partitions['without_target']['functions'][0]['predictor_blockers'] == {
        'unmatched_identity': 1,
    }
    for partition in partitions.values():
        assert [item['function'] for item in partition['functions']] == ['complete', 'legacy']
        legacy = partition['functions'][1]
        assert legacy['status'] == 'blocked_measurement_contract'
        assert legacy['missing_measurement_paths'] == ['inputs.clay.measurement']
        assert legacy['predictor_counts'] == {}


def test_ready_predictors_do_not_authorize_scoring_or_selection(monkeypatch: pytest.MonkeyPatch):
    coverage, dataset, audit = _inputs()
    ready = replace(audit.eligibility[0], eligible=True, reasons=())
    report = _builder(monkeypatch)(coverage, dataset, replace(audit, eligibility=(ready,)))
    partition = report['source_partitions'][0]
    candidate = partition['functions'][0]
    assert candidate['status'] == 'requires_target_and_protocol_review'
    assert candidate['scoring_permission'] == 'not_established'
    assert partition['selection_status'] == 'not_assessed'


def test_matrix_rejects_workbook_mismatch_and_incomplete_manifest_audits(
    monkeypatch: pytest.MonkeyPatch,
):
    build = _builder(monkeypatch)
    coverage, dataset, audit = _inputs()
    with pytest.raises(ValueError, match='same workbook'):
        build(coverage, dataset, replace(audit, summary=replace(audit.summary, sha256='b' * 64)))
    with pytest.raises(ValueError, match='Every manifest function'):
        build(coverage, dataset, replace(audit, summary=replace(audit.summary, function_audits=())))
