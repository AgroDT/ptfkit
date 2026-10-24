"""Count-only exact-identity join of canonical curves and predictor eligibility."""

# ruff: noqa: INP001 - Standalone reproducible dataset audit.

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from ptfkit_eval import audit_predictor_workbook, load_dataset_mapping, load_retention_dataset
from ptfkit_eval.documents import canonical_json, document_hash, object_records

from ptfkit import get_manifest


if TYPE_CHECKING:
    from ptfkit_eval import CanonicalRetentionDataset
    from ptfkit_eval.predictors import FunctionSampleEligibility, PredictorAuditResult


def join_readiness(
    dataset: CanonicalRetentionDataset, predictors: PredictorAuditResult
) -> dict[str, object]:
    """Do not infer identity matches or turn predictor eligibility into scoring permission."""
    source_hashes = {
        item['sha256'] for item in object_records(dataset.document.get('source_files', ()))
    }
    if source_hashes != {predictors.summary.sha256}:
        message = 'Canonical observations and predictor audit must bind the same workbook bytes.'
        raise ValueError(message)
    index: dict[tuple[object, object, str], list[FunctionSampleEligibility]] = defaultdict(list)
    for item in predictors.eligibility:
        index[item.source, item.sample_id, item.function].append(item)
    functions = []
    for function in sorted(item.function for item in predictors.summary.function_audits):
        counts: Counter[str] = Counter()
        reasons: Counter[str] = Counter()
        for sample in object_records(dataset.document['samples']):
            counts['canonical_samples'] += 1
            matches = index[sample['source_id'], sample['sample_id'], function]
            if len(matches) != 1:
                counts['ambiguous_identity' if matches else 'unmatched_identity'] += 1
                continue
            item = matches[0]
            counts['matched_samples'] += 1
            counts['complete_raw_inputs'] += 'missing_input' not in item.reasons
            counts['predictor_eligible' if item.eligible else 'predictor_blocked'] += 1
            reasons.update(set(item.reasons))
        functions.append(
            {
                'function': function,
                'counts': dict(sorted(counts.items())),
                'blockers': dict(sorted(reasons.items())),
            }
        )
    return {
        'schema_version': 1,
        'dataset_id': dataset.dataset_id,
        'dataset_sha256': dataset.sha256,
        'workbook_sha256': predictors.summary.sha256,
        'target_material_basis': dataset.target.material_basis,
        'join_policy': 'exact_source_and_sample_id_unique_master_row',
        'scope': 'predictor_readiness_for_canonical_curve_identities_not_scoring_eligibility',
        'functions': functions,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    mapping = load_dataset_mapping(arguments.mapping)
    manifest = get_manifest()
    audit = audit_predictor_workbook(arguments.workbook, mapping, manifest=manifest)
    payload = join_readiness(load_retention_dataset(arguments.dataset), audit)
    payload['mapping_sha256'] = document_hash(mapping.document)
    payload['manifest_sha256'] = document_hash(manifest)
    with arguments.output.open('xb') as stream:
        stream.write(canonical_json(payload))
