"""Summarize independently fitted curves after pressure-provenance exclusions."""

# ruff: noqa: INP001 - Standalone count-only experiment review.

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from ptfkit_eval import load_retention_dataset


def review_fits(parent: dict, dataset_document: dict) -> dict:
    """Reuse no fit unless its complete observation series matches exactly."""
    dataset = load_retention_dataset(dataset_document)
    if (
        parent['experiment'] != 'measured_retention_reference_fits_v1'
        or load_retention_dataset(parent['dataset']).sha256 != parent['dataset_sha256']
        or parent['dataset']['target'] != dataset_document['target']
    ):
        message = 'Expected a consistent independent descriptive fitting artifact and target.'
        raise ValueError(message)
    expected = defaultdict(list)
    for point in dataset_document['observations']:
        if point['review_status'] != 'confirmed' or point['quality_flags']:
            message = 'Reviewed fit summary requires confirmed unflagged observations.'
            raise ValueError(message)
        expected[point['source_id'], point['sample_id']].append(
            {
                'reference': point['id'],
                'suction_kpa': point['suction_kpa'],
                'water_content': point['value'],
            }
        )
    for points in expected.values():
        points.sort(key=lambda point: point['suction_kpa'])
    families = {
        'van_genuchten_mualem_v1',
        'van_genuchten_m1_v1',
        'brooks_corey_v1',
        'clapp1978_gradual_air_entry_v1',
    }
    seen = set()
    counts = Counter()
    for record in parent['results']:
        identity = (record['source_id'], record['sample_id'])
        if identity not in expected:
            continue
        fit = record['fit']
        key = (*identity, fit['plan']['family_id'])
        if key in seen or fit['observations'] != expected[identity]:
            message = 'Duplicate fit or changed observation series; refit instead of reusing.'
            raise ValueError(message)
        seen.add(key)
        counts[fit['plan']['family_id'], fit['status'], fit['reason']] += 1
    if seen != {(*identity, family) for identity in expected for family in families}:
        message = 'Reviewed cohort must have exactly one fit per sample and required family.'
        raise ValueError(message)
    return {
        'schema_version': 1,
        'scope': 'descriptive_fixed_box_fits_not_native_PTF_ranking_or_coverage_qualification',
        'dataset_sha256': dataset.sha256,
        'parent_dataset_sha256': parent['dataset_sha256'],
        'samples': len(expected),
        'observations': len(dataset_document['observations']),
        'fits': len(seen),
        'reuse_policy': (
            'Exact unchanged per-curve observations; exclusions based only on pressure provenance.'
        ),
        'summary': [
            {'family_id': family, 'status': status, 'reason': reason, 'count': count}
            for (family, status, reason), count in sorted(
                counts.items(), key=lambda item: str(item[0])
            )
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent_fits', type=Path)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    parent_bytes = args.parent_fits.read_bytes()
    summary = review_fits(json.loads(parent_bytes), json.loads(args.dataset.read_bytes()))
    summary['parent_artifact_sha256'] = hashlib.sha256(parent_bytes).hexdigest()
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
