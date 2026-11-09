"""Source-reviewed Clapp benchmark for the Panina gray forest profile."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ptfkit_eval import (
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json, object_mapping, object_records, plain

from ptfkit import get_manifest


_MASTER_SHEET = '\u0414\u0430\u043d\u043d\u044b\u0435'


def build_subset(document: dict, review_bytes: bytes, paper_bytes: bytes) -> dict:
    """Apply only exact, source-reviewed identities; preserve every selected target."""
    dataset = load_retention_dataset(document)
    review = json.loads(review_bytes)
    files = {item['sha256'] for item in document['source_files']}
    if (
        dataset.sha256 != review['canonical_dataset_sha256']
        or files != {review['workbook_sha256']}
        or hashlib.sha256(paper_bytes).hexdigest() != review['paper']['sha256']
    ):
        message = 'Reviewed subset requires the exact canonical dataset, workbook and source PDF.'
        raise ValueError(message)
    selection = {
        (item['source_id'], item['sample_id']): item for item in review['selected_samples']
    }
    if (
        len(selection) != len(review['selected_samples'])
        or len(selection) != review['eligible_count']
    ):
        message = 'Reviewed selection must have unique identities and consistent counts.'
        raise ValueError(message)
    function = next(
        item
        for item in object_records(get_manifest()['functions'])
        if item['id'] == 'calc_ptf_clapp1978'
    )
    enum = object_mapping(object_records(function['inputs'])[0]['enum'])
    allowed = {item['value'] for item in object_records(enum['values'])}
    subset = json.loads(json.dumps(plain(dataset.document)))
    subset['samples'] = []
    for sample in document['samples']:
        identity = (sample['source_id'], sample['sample_id'])
        if identity not in selection:
            continue
        decision = selection[identity]
        if decision['texture'] not in allowed or decision['material_basis'] != 'mineral_soil':
            message = 'Reviewed class or material is unsupported by the Clapp contract.'
            raise ValueError(message)
        updated = dict(sample)
        updated['profile_id'] = decision['profile_id']
        updated['features'] = [
            {
                'id': 'texture',
                'kind': 'categorical',
                'value': decision['texture'],
                'review_status': 'confirmed',
                'origin': 'measured',
                'category_system': decision['category_system'],
                'source_file': review['paper']['id'],
                'source_cells': decision['source_locations'],
            }
        ]
        subset['samples'].append(updated)
    if len(subset['samples']) != len(selection):
        message = 'Every reviewed identity must exist exactly in the canonical dataset.'
        raise ValueError(message)
    subset['observations'] = [
        item
        for item in document['observations']
        if (item['source_id'], item['sample_id']) in selection
    ]
    for identity, decision in selection.items():
        evidence = f'{_MASTER_SHEET}!A{decision["master_row"]}:C{decision["master_row"]}'
        if not any(
            (item['source_id'], item['sample_id']) == identity and evidence in item['source_cells']
            for item in subset['observations']
        ):
            message = 'Reviewed identity lacks its expected master-row lineage.'
            raise ValueError(message)
    subset['dataset_id'] = 'meta-v3-3-panina-gray-forest-clapp-reviewed'
    subset['target']['material_basis'] = 'mineral_soil'
    subset['method'] = 'Reviewed Panina 2015 mineral gray forest profile; Table 17 texture classes.'
    subset['source_files'].extend(
        [
            {key: review['paper'][key] for key in ('id', 'filename', 'sha256')},
            {
                'id': 'clapp_source_review',
                'filename': 'meta_v3_3.clapp-source-review.json',
                'sha256': hashlib.sha256(review_bytes).hexdigest(),
            },
        ]
    )
    return json.loads(canonical_json(load_retention_dataset(subset).document))


def run(dataset_path: Path, review_path: Path, paper_path: Path, output: Path) -> Path:
    subset = build_subset(
        json.loads(dataset_path.read_bytes()), review_path.read_bytes(), paper_path.read_bytes()
    )
    output.mkdir(parents=True, exist_ok=False)
    evaluation = {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'clapp',
                'kind': 'function_curve',
                'function': 'calc_ptf_clapp1978',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'log10',
                },
                'target': subset['target'],
                'prediction': {'id': 'clapp1978_h_theta', 'kind': 'model_adapter'},
            }
        ],
    }
    references = {}
    for name, value in (('dataset', subset), ('evaluation_plan', evaluation)):
        raw = canonical_json(value)
        filename = f'{name}.json'
        with (output / filename).open('xb') as stream:
            stream.write(raw)
        references[name] = {'path': filename, 'sha256': hashlib.sha256(raw).hexdigest()}
    plan = {
        'schema_version': 1,
        **references,
        'protocol': {
            'id': 'panina2015_clapp_source_review_v1',
            'observation_method': subset['method'],
            'allowed_target_origins': ['measured'],
            'cohorts': ['maximal', 'common'],
            'bindings': {'calc_ptf_clapp1978': {'soil_texture': 'texture'}},
        },
        'bootstrap': {
            'method': 'cluster_percentile_linear_v1',
            'seed': 20261024,
            'minimum_groups': 5,
            'grouping': 'profile',
            'missing_profiles': 'reject',
            'confidence_level': 0.95,
            'n_resamples': 2000,
        },
    }
    path = output / 'run.json'
    with path.open('xb') as stream:
        stream.write(canonical_json(plan))
    return write_retention_run(
        execute_retention_run(load_retention_run_plan(path)), output / 'artifacts'
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument(
        '--review',
        type=Path,
        default=Path('evaluation/datasets/meta_v3_3.clapp-source-review.json'),
    )
    parser.add_argument('--paper', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.dataset, arguments.review, arguments.paper, arguments.output)
