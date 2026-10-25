"""Coarsen HYBRAS source groups by exact shared primary-reference connectivity."""

# ruff: noqa: INP001 - Standalone provenance-preserving data adapter.

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

from ptfkit_eval import (
    GroupedSample,
    NestedGroupPlan,
    build_nested_group_folds,
    load_retention_dataset,
)
from ptfkit_eval.documents import canonical_json


ARCHIVE_SHA256 = 'e9164c2f74e9ad75033b99248b0eee7ba426230150a499a6e6b3a285eebcf618'
WORKBOOK_SHA256 = 'a185fc02e5a46d46bfaeea705c2e37a0f4459278819b72ccbef3955c0874f4c9'


def reference_components(references: dict[str, tuple]) -> dict[str, str]:
    """Connect exact nonempty references transitively before selecting dataset rows."""
    parent = {source: source for source in references}

    def root(source: str) -> str:
        while parent[source] != source:
            source = parent[source]
        return source

    owners: dict[str, str] = {}
    for source, citations in sorted(references.items()):
        for citation in citations:
            if not isinstance(citation, str) or not citation.strip():
                continue
            if citation in owners:
                one, two = sorted((root(source), root(owners[citation])))
                parent[two] = one
            else:
                owners[citation] = source
    components: dict[str, list[str]] = defaultdict(list)
    for source in sorted(references):
        components[root(source)].append(source)
    mapping = {}
    for members in components.values():
        group = (
            members[0]
            if len(members) == 1
            else 'hybras-linked-study-' + hashlib.sha256(canonical_json(members)).hexdigest()[:16]
        )
        mapping.update(dict.fromkeys(members, group))
    return mapping


def apply_groups(document: dict, mapping: dict[str, str]) -> tuple[dict, list[dict]]:
    """Change only source-group keys, retaining identities in an explicit sidecar."""
    updated = json.loads(canonical_json(document))
    lineage = []
    for sample in updated['samples']:
        original = sample['source_id']
        if original not in mapping:
            message = f'Canonical source is absent from the reviewed workbook: {original}.'
            raise ValueError(message)
        sample['source_id'] = mapping[original]
        lineage.append(
            {
                'sample_id': sample['sample_id'],
                'profile_id': sample['profile_id'],
                'original_source_id': original,
                'source_group_id': mapping[original],
            }
        )
    for point in updated['observations']:
        if point['source_id'] not in mapping:
            message = 'An observation source is absent from the reviewed workbook.'
            raise ValueError(message)
        point['source_id'] = mapping[point['source_id']]
    return updated, lineage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.archive.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        message = 'The reviewed HYBRAS archive checksum is required.'
        raise ValueError(message)
    dataset = load_retention_dataset(args.dataset)
    if not any(
        item['id'] == 'hybras-workbook' and item['sha256'] == WORKBOOK_SHA256
        for item in dataset.document['source_files']
    ):
        message = 'The canonical parent must bind the reviewed HYBRAS workbook.'
        raise ValueError(message)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        workbook_bytes = archive.read('HYBRAS_COMPLETE_V1.xlsx')
    if hashlib.sha256(workbook_bytes).hexdigest() != WORKBOOK_SHA256:
        message = 'The reviewed workbook checksum is required.'
        raise ValueError(message)
    workbook = openpyxl.load_workbook(io.BytesIO(workbook_bytes), read_only=True, data_only=True)
    references = {}
    horizon_sources = {}
    try:
        for row in workbook['HYBRAS'].iter_rows(min_row=4, values_only=True):
            pair = (row[36], row[37])
            source = 'hybras-study-' + hashlib.sha256(canonical_json(pair)).hexdigest()[:16]
            references[source] = pair
            horizon_sources[f'hybras-horizon-{row[0]}'] = (source, f'hybras-profile-{row[5]}')
    finally:
        workbook.close()
    document = json.loads(args.dataset.read_bytes())
    for sample in document['samples']:
        if horizon_sources.get(sample['sample_id']) != (sample['source_id'], sample['profile_id']):
            message = 'Canonical sample source/profile identity differs from the workbook.'
            raise ValueError(message)
    mapping = reference_components(references)
    updated, lineage = apply_groups(document, mapping)
    review = {
        'schema_version': 1,
        'method': 'exact_shared_primary_reference_components_v1',
        'parent_dataset_sha256': dataset.sha256,
        'archive_sha256': ARCHIVE_SHA256,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'reference_inventory': references,
        'source_mapping': mapping,
        'samples': lineage,
        'limitations': [
            'Connections are built on the full workbook, including sources absent from the subset.',
            'Only exact nonempty citation strings connect groups; no fuzzy bibliographic matching.',
            'Source groups are conservative blocking units, not proven independent populations.',
            'Use source grouping; profile grouping does not preserve these citation blocks.',
            'No measurement method, target material or predictor eligibility is changed.',
            'Original source/sample keys remain recoverable from this checksum-bound sidecar.',
        ],
    }
    review_bytes = canonical_json(review)
    updated['dataset_id'] += '-linked-source-groups'
    updated['method'] += ' Source IDs coarsened by exact shared primary-reference connectivity.'
    updated['source_files'].append(
        {
            'id': 'hybras-source-group-review',
            'filename': 'source-group-review.json',
            'sha256': hashlib.sha256(review_bytes).hexdigest(),
        }
    )
    result = load_retention_dataset(updated)
    counts = Counter(s['source_id'] for s in updated['samples'])
    split_plan = NestedGroupPlan(
        seed=20261025,
        outer_folds=3,
        inner_folds=2,
        grouping='source',
        minimum_training_groups=2,
        minimum_validation_groups=1,
    )
    splits = build_nested_group_folds(
        [
            GroupedSample(s['source_id'], s['sample_id'], s['profile_id'])
            for s in updated['samples']
        ],
        plan=split_plan,
    )
    summary = {
        'schema_version': 1,
        'method': review['method'],
        'parent_dataset_sha256': dataset.sha256,
        'dataset_sha256': result.sha256,
        'review_sha256': hashlib.sha256(review_bytes).hexdigest(),
        'script_sha256': review['script_sha256'],
        'original_source_groups': len({s['source_id'] for s in document['samples']}),
        'linked_source_groups': len(counts),
        'source_group_sample_counts': dict(sorted(counts.items())),
        'samples': len(updated['samples']),
        'observations': len(updated['observations']),
        'eligibility': 'unchanged_not_granted_by_grouping',
        'independence': 'not_established_by_reference_connectivity',
        'required_validation_grouping': 'source',
        'split_feasibility': {
            'outer_folds': split_plan.outer_folds,
            'inner_folds': split_plan.inner_folds,
            'minimum_training_groups': split_plan.minimum_training_groups,
            'minimum_validation_groups': split_plan.minimum_validation_groups,
            'status': splits.status,
            'reason': splits.reason,
            'scope': 'identity_only_split_feasibility_not_model_selection_or_independence_proof',
        },
    }
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in (('dataset', updated), ('summary', summary)):
        (args.output / f'{name}.json').write_bytes(canonical_json(value))
    (args.output / 'source-group-review.json').write_bytes(review_bytes)


if __name__ == '__main__':
    main()
