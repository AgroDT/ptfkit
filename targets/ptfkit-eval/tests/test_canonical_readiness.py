import runpy
from dataclasses import replace
from pathlib import Path

import pytest
from _run_fixtures import dataset_document

from ptfkit_eval import load_retention_dataset
from ptfkit_eval.predictors import (
    FunctionPredictorAudit,
    FunctionSampleEligibility,
    PredictorAuditResult,
    PredictorAuditSummary,
)


def test_readiness_requires_exact_unique_identity_and_same_workbook():
    script = (
        Path(__file__).resolve().parents[3] / 'evaluation/datasets/audit_meta_v3_3_readiness.py'
    )
    join = runpy.run_path(str(script))['join_readiness']
    document = dataset_document()
    document['source_files'] = [{'id': 'workbook', 'filename': 'fixture.xlsx', 'sha256': 'a' * 64}]
    dataset = load_retention_dataset(document)
    summary = PredictorAuditSummary(
        schema_version=2,
        source_filename='fixture.xlsx',
        sha256='a' * 64,
        manifest_schema_version=1,
        public_function_count=1,
        candidate_sample_count=3,
        binding_audits=(),
        function_audits=(FunctionPredictorAudit('ptf', 1, 3, 3, 1, 2),),
        exclusion_reasons=(),
    )
    audit = PredictorAuditResult(
        summary,
        (),
        (
            FunctionSampleEligibility(
                'master!1', 'one', 'a', 1, 'ptf', eligible=False, reasons=('particle_size_schemes',)
            ),
            FunctionSampleEligibility('master!2', 'one', 'b', 1, 'ptf', eligible=True, reasons=()),
            FunctionSampleEligibility(
                'master!3', 'one', 'b', 1, 'ptf', eligible=False, reasons=('missing_input',)
            ),
        ),
    )
    function = join(dataset, audit)['functions'][0]
    assert function['counts'] == {
        'canonical_samples': 3,
        'matched_samples': 1,
        'complete_raw_inputs': 1,
        'predictor_blocked': 1,
        'ambiguous_identity': 1,
        'unmatched_identity': 1,
    }
    assert function['blockers'] == {'particle_size_schemes': 1}
    with pytest.raises(ValueError, match='same workbook'):
        join(dataset, replace(audit, summary=replace(summary, sha256='b' * 64)))
