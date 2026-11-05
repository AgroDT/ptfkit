"""Reconcile every implemented function with source partitions of real retention data."""

# ruff: noqa: INP001, T201 - Standalone audit entry point with console summary.

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from evaluation.experiments.catalog_coverage.audit import audit
from ptfkit import get_manifest
from ptfkit_eval import audit_predictor_workbook, load_dataset_mapping, load_retention_dataset
from ptfkit_eval.documents import canonical_json, document_hash, object_records


if TYPE_CHECKING:
    from ptfkit_eval import CanonicalRetentionDataset
    from ptfkit_eval.predictors import FunctionSampleEligibility, PredictorAuditResult


def _count_matches(
    matches: list[FunctionSampleEligibility], counts: Counter[str], reasons: Counter[str]
) -> None:
    if len(matches) != 1:
        reasons['ambiguous_identity' if matches else 'unmatched_identity'] += 1
        return
    match = matches[0]
    counts['matched_samples'] += 1
    counts['complete_raw_inputs'] += not {'missing_input', 'missing_input_binding'}.intersection(
        match.reasons
    )
    counts['predictor_eligible' if match.eligible else 'predictor_blocked'] += 1
    reasons.update(set(match.reasons))


def build_matrix(
    coverage: dict, dataset: CanonicalRetentionDataset, predictors: PredictorAuditResult
) -> dict:
    """Keep metadata, raw predictor readiness and scientific scoring permission separate."""
    workbook_hashes = {item['sha256'] for item in object_records(dataset.document['source_files'])}
    if workbook_hashes != {predictors.summary.sha256}:
        message = 'Dataset and predictors must refer to exactly the same workbook.'
        raise ValueError(message)
    covered = {item['id'] for item in coverage['functions'] if item['manifest_eligible']}
    audited = {item.function for item in predictors.summary.function_audits}
    if covered != audited:
        message = 'Every manifest function must have a predictor audit, with no extras.'
        raise ValueError(message)
    index = defaultdict(list)
    for item in predictors.eligibility:
        index[item.source, item.sample_id, item.function].append(item)
    samples = defaultdict(list)
    points = Counter()
    for sample in object_records(dataset.document['samples']):
        samples[sample['source_id']].append(sample)
    for point in object_records(dataset.document['observations']):
        points[point['source_id']] += 1
    partitions = []
    for source, source_samples in sorted(samples.items()):
        records = []
        for function in coverage['functions']:
            counts, reasons = Counter(), Counter()
            if function['manifest_eligible']:
                for sample in source_samples:
                    matches = index[source, sample['sample_id'], function['id']]
                    _count_matches(matches, counts, reasons)
                status = (
                    'requires_target_and_protocol_review'
                    if counts['predictor_eligible']
                    else 'blocked_predictors_or_identity'
                )
            else:
                status = 'blocked_measurement_contract'
            records.append(
                {
                    'function': function['id'],
                    'status': status,
                    'missing_measurement_paths': function['missing_measurement_paths'],
                    'output_quantities': sorted({item['quantity'] for item in function['outputs']}),
                    'predictor_counts': dict(sorted(counts.items())),
                    'predictor_blockers': dict(sorted(reasons.items())),
                    'scoring_permission': 'not_established',
                }
            )
        partitions.append(
            {
                'source_id': source,
                'sample_count': len(source_samples),
                'observation_count': points[source],
                'samples_without_profile_id': sum(
                    sample['profile_id'] is None for sample in source_samples
                ),
                'selection_status': 'not_assessed',
                'selection_blockers': [
                    'scoring_protocol_not_assessed',
                ],
                'functions': records,
            }
        )
    return {
        'schema_version': 1,
        'scope': 'implemented_catalog_by_source_partition_raw_predictor_readiness_not_scoring',
        'dataset_id': dataset.dataset_id,
        'dataset_sha256': dataset.sha256,
        'workbook_sha256': predictors.summary.sha256,
        'target': dict(dataset.document['target']),
        'coverage_sha256': document_hash(coverage),
        'implemented_functions': coverage['implemented_functions'],
        'manifest_functions': coverage['manifest_functions'],
        'source_partition_count': len(partitions),
        'sample_count': sum(item['sample_count'] for item in partitions),
        'observation_count': sum(points.values()),
        'limitations': [
            'Source partitions do not establish independent datasets or soil groups.',
            'Raw bindings differ from source-reviewed overlays such as the Panina Clapp pilot.',
            'Input readiness does not establish target compatibility, pressure support or scoring.',
            'Omitted functions remain visible; no descriptor is inferred from a name.',
        ],
        'source_partitions': partitions,
    }


def main() -> None:
    """Audit the current sources and workbook rather than reusing stale count summaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    mapping = load_dataset_mapping(args.mapping)
    manifest = get_manifest()
    coverage = audit(root)
    # Check the installed public manifest as well as the generated file used by the inventory.
    current = json.loads((root / 'targets/ptfkit-py/src/ptfkit/_manifest.json').read_bytes())
    if document_hash(manifest) != document_hash(current):
        message = 'Installed and generated manifests differ; use the matching ptfkit environment.'
        raise ValueError(message)
    predictors = audit_predictor_workbook(args.workbook, mapping, manifest=manifest)
    report = build_matrix(coverage, load_retention_dataset(args.dataset), predictors)
    report['mapping_sha256'] = document_hash(mapping.document)
    report['manifest_sha256'] = document_hash(manifest)
    args.output.write_bytes(canonical_json(report))
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    'dataset_id',
                    'implemented_functions',
                    'manifest_functions',
                    'source_partition_count',
                    'sample_count',
                    'observation_count',
                )
            },
            indent=2,
        )
    )


if __name__ == '__main__':
    main()
