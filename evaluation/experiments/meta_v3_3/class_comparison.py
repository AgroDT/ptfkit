"""Compare reviewed Panina classes using the existing Clapp and Cosby contracts."""

# ruff: noqa: INP001 - Standalone experiment helpers.

from __future__ import annotations

import copy
import hashlib
import json
from typing import TYPE_CHECKING, cast

from ptfkit_eval import (
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json, plain
from ptfkit_eval.input_derivations import COSBY_CLASS_MIDPOINTS, COSBY_MIDPOINT_METHOD

from evaluation.experiments.meta_v3_3.summaries import region_metrics


if TYPE_CHECKING:
    from pathlib import Path
from ptfkit import get_manifest


def add_class_coordinates(dataset: dict) -> dict:
    """Retain reviewed categorical evidence and label Table 2 coordinates as derived."""
    result = copy.deepcopy(dataset)
    function = next(
        f
        for f in cast('dict', plain(get_manifest()))['functions']
        if f['id'] == 'calc_ptf_cosby1984_univariate'
    )
    for sample in result['samples']:
        texture = next(f for f in sample['features'] if f['id'] == 'texture')
        if (
            texture['review_status'] != 'confirmed'
            or texture['origin'] != 'measured'
            or texture['category_system'] != 'clapp1978.UsdaTextureClass'
        ):
            message = 'Cosby coordinates require a reviewed measured USDA class.'
            raise ValueError(message)
        coordinates = COSBY_CLASS_MIDPOINTS[texture['value']]
        for binding, value in zip(function['inputs'], coordinates, strict=True):
            sample['features'].append(
                {
                    'id': binding['name'],
                    'kind': 'numeric',
                    'value': value,
                    'origin': 'derived',
                    'review_status': 'confirmed',
                    'measurement': {
                        key: plain(binding['measurement'][key])
                        for key in (
                            'quantity',
                            'unit',
                            'basis',
                            'method',
                            'particle_size',
                            'conditions',
                        )
                    },
                    'source_file': texture['source_file'],
                    'source_cells': [*texture['source_cells'], 'Cosby1984:Table2'],
                    'derivation': {'method': COSBY_MIDPOINT_METHOD, 'source_feature': 'texture'},
                }
            )
    return cast('dict', plain(load_retention_dataset(result).document))


def run(reference: Path, output: Path) -> tuple[Path, dict]:
    """Reuse the hash-verified pilot and unchanged run, cohort and bootstrap engines."""
    read_retention_run_report(reference / 'artifacts')
    dataset = add_class_coordinates(json.loads((reference / 'dataset.json').read_bytes()))
    evaluation = json.loads((reference / 'evaluation_plan.json').read_bytes())
    cosby = copy.deepcopy(evaluation['candidates'][0])
    cosby.update(
        id='cosby',
        function='calc_ptf_cosby1984_univariate',
        prediction={'id': 'cosby1984_class_midpoint_dry_h_theta', 'kind': 'model_adapter'},
    )
    evaluation['candidates'].append(cosby)
    plan = json.loads((reference / 'run.json').read_bytes())
    plan['protocol']['id'] = 'panina2015_clapp_cosby_reviewed_classes_v1'
    plan['protocol']['bindings']['calc_ptf_cosby1984_univariate'] = {
        component: component for component in ('sand', 'silt', 'clay')
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, document in (('dataset', dataset), ('evaluation_plan', evaluation)):
        raw = canonical_json(document)
        (output / f'{name}.json').write_bytes(raw)
        plan[name] = {'path': f'{name}.json', 'sha256': hashlib.sha256(raw).hexdigest()}
    path = output / 'run.json'
    path.write_bytes(canonical_json(plan))
    artifacts = write_retention_run(
        execute_retention_run(load_retention_run_plan(path)), output / 'artifacts'
    )
    read_retention_run_report(artifacts)
    cohorts = json.loads((artifacts / 'cohorts.json').read_bytes())
    coverage = json.loads((artifacts / 'coverage.json').read_bytes())
    summary = {
        'protocol': plan['protocol']['id'],
        'coverage': coverage,
        'profile_count': len({(s['source_id'], s['profile_id']) for s in dataset['samples']}),
        'source_count': len({s['source_id'] for s in dataset['samples']}),
        'selection': {'status': 'insufficient_evidence', 'reason': 'one_reviewed_profile'},
        'applicability': 'external_evaluation_of_reviewed_classes_not_regional_validation',
        'cohorts': [],
    }
    for record in cohorts:
        cohort = record['cohort']
        points = cohort['comparisons']
        diagnostics = region_metrics(points)
        for region in diagnostics['regions']:
            if region['summary']:
                region['summary'].pop('samples', None)
        summary['cohorts'].append(
            {
                'confidence': {k: v for k, v in record['confidence'].items() if k != 'summary'},
                'candidate_id': cohort['candidate_id'],
                'kind': cohort['kind'],
                'pressure_support_kpa': sorted({p['suction_kpa'] for p in points}),
                'pressure_diagnostics': diagnostics,
                'cohort': {
                    'status': cohort['status'],
                    'summary': {k: v for k, v in cohort['summary'].items() if k != 'samples'},
                },
            }
        )
    (output / 'summary.json').write_bytes(canonical_json(summary))
    return artifacts, summary
