"""Evaluate Clapp on source-reviewed HYBRAS mineral horizons and reported classes."""

# ruff: noqa: INP001 - Standalone reviewed-data experiment.

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import openpyxl

from ptfkit_eval import (
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


ARCHIVE_SHA256 = 'e9164c2f74e9ad75033b99248b0eee7ba426230150a499a6e6b3a285eebcf618'
DATASET_SHA256 = '7ee2c78e07da2ffe97b987e776620ce275390b1e24939a63552f08f3039fd665'
MANUAL_SHA256 = '0d1ae08d0962fa1157b8b1f3af71e539220fa99f77675984fd81096ecfcc81e0'
WORKBOOK_SHA256 = 'a185fc02e5a46d46bfaeea705c2e37a0f4459278819b72ccbef3955c0874f4c9'

# HYBRAS manual Figure 3, printed page 10: paired class labels and abbreviations.
TEXTURE_CLASSES = {
    'areia': 'sand',
    'areia franca': 'loamy sand',
    'franco arenoso': 'sandy loam',
    'franco siltoso': 'silt loam',
    'franco': 'loam',
    'franco argilo-arenosa': 'sandy clay loam',
    'franco argilo-siltoso': 'silty clay loam',
    'franco argiloso': 'clay loam',
    'argila arenosa': 'sandy clay',
    'argila siltosa': 'silty clay',
    'argila': 'clay',
}


def overlay(document: dict, rows: dict[int, tuple[int, tuple]]) -> tuple[dict, dict]:
    """Join exact source identities and preserve selected observations unchanged."""
    subset = json.loads(canonical_json(document))
    selected = []
    decisions = []
    exclusions: Counter[str] = Counter()
    for sample in document['samples']:
        code = int(sample['sample_id'].removeprefix('hybras-horizon-'))
        number, row = rows[code]
        expected_source = (
            'hybras-study-' + hashlib.sha256(canonical_json([row[36], row[37]])).hexdigest()[:16]
        )
        if (
            sample['sample_id'] != f'hybras-horizon-{row[0]}'
            or sample['source_id'] != expected_source
            or sample['profile_id'] != f'hybras-profile-{row[5]}'
            or row[5] is None
        ):
            message = 'Canonical sample identity does not match the source workbook.'
            raise ValueError(message)
        horizon = row[7]
        if not isinstance(horizon, str) or not re.fullmatch(r'[ABE][a-z]*[0-9]*', horizon):
            exclusions['horizon_not_in_reviewed_single_master_subset'] += 1
            continue
        if row[11] not in TEXTURE_CLASSES:
            exclusions['unreviewed_texture_label'] += 1
            continue
        updated = json.loads(canonical_json(sample))
        updated['features'] = [
            {
                'id': 'texture',
                'kind': 'categorical',
                'value': TEXTURE_CLASSES[row[11]],
                'review_status': 'confirmed',
                'origin': 'measured',
                'category_system': 'clapp1978.UsdaTextureClass',
                'source_file': 'hybras-workbook',
                'source_cells': [f'HYBRAS!L{number}'],
            }
        ]
        selected.append(updated)
        decisions.append(
            {
                'source_id': sample['source_id'],
                'sample_id': sample['sample_id'],
                'profile_id': sample['profile_id'],
                'horizon': horizon,
                'horizon_source_cell': f'HYBRAS!H{number}',
                'reported_texture': row[11],
                'texture': TEXTURE_CLASSES[row[11]],
                'texture_source_cell': f'HYBRAS!L{number}',
            }
        )
    identities = {(s['source_id'], s['sample_id']) for s in selected}
    subset['samples'] = selected
    subset['observations'] = [
        o for o in subset['observations'] if (o['source_id'], o['sample_id']) in identities
    ]
    subset['dataset_id'] = 'hybras-v1-clapp-reviewed-mineral-positive-head'
    subset['target']['material_basis'] = 'mineral_soil'
    subset['method'] = (
        'HYBRAS reviewed positive-head drying observations; reported USDA texture classes '
        'and single A/B/E mineral horizon labels. Rounded source heads preserved.'
    )
    report = {
        'schema_version': 1,
        'scope': 'source_reviewed_clapp_subset_not_global_function_selection',
        'samples': len(selected),
        'profiles': len({s['profile_id'] for s in selected}),
        'sources': len({s['source_id'] for s in selected}),
        'observations': len(subset['observations']),
        'exclusions': dict(exclusions),
        'selected_samples': decisions,
        'limitations': [
            'No fine-earth preparation or zero-gravel assumption is inferred.',
            'Unknown, compound, transitional and annotated horizon labels remain excluded.',
            (
                'Bootstrap intervals describe mean prediction error under profile resampling, '
                'not prediction intervals for individual water contents.'
            ),
            'Profiles can share a study; profile bootstrap is conditional on represented studies.',
            'Only one native function is evaluated; no best-function or ensemble claim follows.',
        ],
    }
    return subset, report


def review_source_bootstrap(subset: dict, report: dict, group_review_bytes: bytes) -> None:
    """Bind the exact cohort to reviewed source blocks before source resampling."""
    group_review = json.loads(group_review_bytes)
    selected = {(s['source_id'], s['sample_id'], s['profile_id']) for s in subset['samples']}
    reviewed = {
        (s['original_source_id'], s['sample_id'], s['profile_id']) for s in group_review['samples']
    }
    if (
        group_review['archive_sha256'] != ARCHIVE_SHA256
        or group_review['method'] != 'exact_shared_primary_reference_components_v1'
        or selected != reviewed
        or len(reviewed) != len(group_review['samples'])
        or any(group_review['source_mapping'].get(source) != source for source, _, _ in selected)
    ):
        message = 'This Clapp replay requires the exact subset with no unresolved source merges.'
        raise ValueError(message)
    report['limitations'] = [
        item
        for item in report['limitations']
        if not item.startswith(('Bootstrap intervals', 'Profiles can share'))
    ] + [
        'Bootstrap intervals describe aggregate error under whole-source-group resampling.',
        'Distinct reference components do not prove independent study populations.',
    ]
    report['source_group_review_sha256'] = hashlib.sha256(group_review_bytes).hexdigest()
    subset['source_files'].append(
        {
            'id': 'hybras-source-group-review',
            'filename': 'source-group-review.json',
            'sha256': report['source_group_review_sha256'],
        }
    )


def parse_arguments() -> argparse.Namespace:
    """Parse source paths and the declared resampling unit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('manual', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--bootstrap-grouping', choices=('profile', 'source'), default='profile')
    parser.add_argument('--source-group-review', type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    archive_bytes = args.archive.read_bytes()
    if (
        hashlib.sha256(archive_bytes).hexdigest() != ARCHIVE_SHA256
        or hashlib.sha256(args.manual.read_bytes()).hexdigest() != MANUAL_SHA256
    ):
        message = 'Reviewed archive and manual checksums are required.'
        raise ValueError(message)
    dataset = load_retention_dataset(args.dataset)
    if dataset.sha256 != DATASET_SHA256:
        message = 'The reviewed positive-head canonical dataset checksum is required.'
        raise ValueError(message)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        raw = archive.read('HYBRAS_COMPLETE_V1.xlsx')
    if hashlib.sha256(raw).hexdigest() != WORKBOOK_SHA256:
        message = 'The reviewed workbook checksum is required.'
        raise ValueError(message)
    workbook = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        rows = {
            row[0]: (number, row)
            for number, row in enumerate(
                workbook['HYBRAS'].iter_rows(min_row=4, values_only=True), start=4
            )
        }
    finally:
        workbook.close()
    subset, report = overlay(json.loads(args.dataset.read_bytes()), rows)
    group_review_bytes = None
    if args.bootstrap_grouping == 'source':
        if args.source_group_review is None:
            message = 'Source bootstrap requires the reviewed reference-connectivity sidecar.'
            raise ValueError(message)
        group_review_bytes = args.source_group_review.read_bytes()
        review_source_bootstrap(subset, report, group_review_bytes)
    report['bootstrap_grouping'] = args.bootstrap_grouping
    report.update(
        {
            'archive_sha256': ARCHIVE_SHA256,
            'parent_dataset_sha256': DATASET_SHA256,
            'manual_sha256': MANUAL_SHA256,
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'material_reference': 'https://www.nrcs.usda.gov/sites/default/files/2022-09/SSM-ch3.pdf',
            'texture_reference': 'HYBRAS manual Figure 3, PDF p16, printed p10; visually reviewed.',
            'texture_crosswalk': TEXTURE_CLASSES,
            'calibration_independence_review': (
                'Clapp calibration uses United States soils; HYBRAS contains Brazilian samples. '
                'No HYBRAS water observations are used to estimate Clapp parameters here.'
            ),
        }
    )
    subset['source_files'].append(
        {'id': 'hybras-manual', 'filename': 'manual.pdf', 'sha256': MANUAL_SHA256}
    )
    subset['source_files'].append(
        {
            'id': 'hybras-clapp-binding-review',
            'filename': 'review.json',
            'sha256': hashlib.sha256(canonical_json(report)).hexdigest(),
        }
    )
    load_retention_dataset(subset)
    args.output.mkdir(parents=True, exist_ok=False)
    if group_review_bytes is not None:
        (args.output / 'source-group-review.json').write_bytes(group_review_bytes)
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
    for name, value in (('dataset', subset), ('evaluation_plan', evaluation), ('review', report)):
        raw = canonical_json(value)
        (args.output / f'{name}.json').write_bytes(raw)
        references[name] = {'path': f'{name}.json', 'sha256': hashlib.sha256(raw).hexdigest()}
    run = {
        'schema_version': 1,
        'dataset': references['dataset'],
        'evaluation_plan': references['evaluation_plan'],
        'protocol': {
            'id': 'hybras_clapp_reviewed_mineral_v1',
            'observation_method': subset['method'],
            'allowed_target_origins': ['measured'],
            'cohorts': ['maximal', 'common'],
            'bindings': {'calc_ptf_clapp1978': {'soil_texture': 'texture'}},
        },
        'bootstrap': {
            'method': 'cluster_percentile_linear_v1',
            'seed': 20261025,
            'minimum_groups': 5,
            'grouping': args.bootstrap_grouping,
            'missing_profiles': 'reject',
            'confidence_level': 0.95,
            'n_resamples': 2000,
        },
    }
    path = args.output / 'run.json'
    path.write_bytes(canonical_json(run))
    write_retention_run(
        execute_retention_run(load_retention_run_plan(path)), args.output / 'artifacts'
    )


if __name__ == '__main__':
    main()
