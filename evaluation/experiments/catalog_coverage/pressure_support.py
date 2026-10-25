"""Count exact observed pressure support without granting scientific eligibility."""

# ruff: noqa: INP001, T201 - Standalone count-only audit.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, cast

from ptfkit import get_manifest
from ptfkit_eval import load_retention_dataset
from ptfkit_eval.documents import canonical_json, document_hash, object_mapping, object_records
from ptfkit_eval.execution import convert_value


if TYPE_CHECKING:
    from collections.abc import Mapping

    from ptfkit_eval import CanonicalRetentionDataset


def count_pressure_support(
    dataset: CanonicalRetentionDataset, manifest: Mapping[str, object]
) -> dict:
    """Use the same exact converted-pressure equality as native fixed-output scoring."""
    points = object_records(dataset.document['observations'])
    outputs = []
    for function in object_records(manifest['functions']):
        for binding in object_records(function['outputs']):
            measurement = object_mapping(binding['measurement'])
            if (
                measurement['quantity'] != dataset.target.quantity
                or measurement['role'] != 'prediction'
            ):
                continue
            conditions = object_records(measurement.get('conditions', ()))
            supported = len(conditions) == 1 and (
                conditions[0]['quantity'] == 'matric_potential'
                and conditions[0]['convention'] == 'magnitude'
            )
            pressure = (
                convert_value(
                    cast('float', conditions[0]['value']),
                    cast('str', conditions[0]['unit']),
                    'kilopascal',
                    manifest=manifest,
                )
                if supported
                else None
            )
            matching = [
                point
                for point in points
                if pressure is not None and point['suction_kpa'] == pressure
            ]
            outputs.append(
                {
                    'function': function['id'],
                    'output': binding['name'],
                    'status': 'fixed_pressure'
                    if supported
                    else 'no_supported_fixed_pressure_condition',
                    'suction_kpa': pressure,
                    'matching_observation_count': len(matching) if supported else None,
                    'matching_sample_count': len(
                        {(point['source_id'], point['sample_id']) for point in matching}
                    )
                    if supported
                    else None,
                }
            )
    return {
        'dataset_id': dataset.dataset_id,
        'dataset_sha256': dataset.sha256,
        'target': dict(dataset.document['target']),
        'outputs': outputs,
        'scope': 'pressure_support_only_not_predictor_material_method_or_scoring_eligibility',
    }


def main() -> None:
    """Write pressure-support metadata for explicit canonical dataset inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = get_manifest()
    datasets = [
        count_pressure_support(load_retention_dataset(path), manifest) for path in args.dataset
    ]
    report = {
        'schema_version': 1,
        'manifest_sha256': document_hash(manifest),
        'policy': 'exact_converted_suction_equality_no_rounding_tolerance_or_interpolation',
        'datasets': datasets,
    }
    args.output.write_bytes(canonical_json(report))
    for dataset in datasets:
        print(dataset['dataset_id'], 'outputs audited:', len(dataset['outputs']))


if __name__ == '__main__':
    main()
