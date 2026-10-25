"""Compare descriptive HYBRAS fit policies on exactly unchanged curves."""

# ruff: noqa: INP001 - Standalone count-only paired audit.

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from ptfkit_eval import load_retention_dataset


_IMPROVEMENT_TOLERANCE = 1e-10
_REGRESSION_TOLERANCE = 1e-12


def _baseline_index(parent: dict) -> dict:
    baseline = {
        (r['source_id'], r['sample_id'], r['fit']['plan']['family_id']): r
        for r in parent['results']
    }
    if len(baseline) != len(parent['results']):
        message = 'Baseline fits must have unique identities.'
        raise ValueError(message)
    return baseline


def _expected_series(dataset_document: dict) -> dict:
    expected = defaultdict(list)
    for point in dataset_document['observations']:
        expected[point['source_id'], point['sample_id']].append(
            {
                'reference': point['id'],
                'suction_kpa': point['suction_kpa'],
                'water_content': point['value'],
            }
        )
    for points in expected.values():
        points.sort(key=lambda point: point['suction_kpa'])
    return expected


def _validate_nested_boxes(before: dict, after: dict) -> None:
    old = {p['name']: p for p in before['plan']['parameters']}
    new = {p['name']: p for p in after['plan']['parameters']}
    if old.keys() != new.keys() or any(
        new[name]['lower'] > bounds['lower'] or new[name]['upper'] < bounds['upper']
        for name, bounds in old.items()
    ):
        message = 'Optimizer counterexample audit requires nested physical boxes.'
        raise ValueError(message)


def compare(parent: dict, records: list[dict], dataset_document: dict) -> dict:
    """Count outcomes without treating changed boxes as a controlled solver comparison."""
    baseline = _baseline_index(parent)
    families = {}
    seen = set()
    dataset = load_retention_dataset(dataset_document)
    required = {
        (sample['source_id'], sample['sample_id'], family)
        for sample in dataset_document['samples']
        for family in ('van_genuchten_mualem_v1', 'brooks_corey_v1')
    }
    expected = _expected_series(dataset_document)
    for record in records:
        fit = record['fit']
        family = fit['plan']['family_id']
        key = record['source_id'], record['sample_id'], family
        if key in seen or key not in baseline:
            message = 'Duplicate or unmatched ordered fit.'
            raise ValueError(message)
        seen.add(key)
        before = baseline[key]['fit']
        _validate_nested_boxes(before, fit)
        if (
            fit['observations'] != expected[key[:2]]
            or fit['plan']['target'] != dataset_document['target']
        ):
            message = 'Ordered fit must match the declared canonical dataset.'
            raise ValueError(message)
        if (
            before['observations'] != fit['observations']
            or before['plan']['target'] != fit['plan']['target']
        ):
            message = 'Paired policy comparison requires exactly unchanged observations and target.'
            raise ValueError(message)
        counts = families.setdefault(family, Counter())
        counts['samples'] += 1
        counts[f'{before["status"]}_to_{fit["status"]}'] += 1
        for label, value in [('before', before), ('after', fit)]:
            counts[f'accepted_{label}'] += value['status'] == 'fitted'
        objectives = [
            min(
                (
                    attempt['sum_squared_error']
                    for attempt in item['attempts']
                    if attempt['converged'] and attempt['sum_squared_error'] is not None
                ),
                default=None,
            )
            for item in [before, fit]
        ]
        if all(value is not None for value in objectives):
            counts['comparable_objectives'] += 1
            counts['objective_improved_gt_1e_10'] += (
                objectives[0] - objectives[1] > _IMPROVEMENT_TOLERANCE
            )
            counts['objective_worsened_gt_1e_12'] += (
                objectives[1] - objectives[0] > _REGRESSION_TOLERANCE
            )
            counts['accepted_with_optimizer_counterexample'] += (
                fit['status'] == 'fitted' and objectives[1] - objectives[0] > _REGRESSION_TOLERANCE
            )
        if fit['status'] == 'fitted':
            support = record['uncertainty_support']
            for field in [
                'parameter_intervals_outside_bounds',
                'mean_intervals_outside_physical_bounds',
                'prediction_intervals_outside_physical_bounds',
            ]:
                counts[field] += bool(support[field])
            counts['accepted_with_physical_curve_diagnostics'] += bool(
                record['quality']['diagnostics']
            )
            parameters = {p['name']: p for p in fit['parameters']}
            counts['marginal_water_intervals_overlap'] += (
                parameters['theta_r']['parameter_interval']['upper']
                >= parameters['theta_s']['parameter_interval']['lower']
            )
    if seen != required:
        message = 'The complete reviewed sample/family roster is required.'
        raise ValueError(message)
    return {
        'schema_version': 1,
        'scope': 'descriptive_changed_boxes_and_coordinates_not_external_validation',
        'dataset_sha256': dataset.sha256,
        'uncertainty_qualification': 'insufficient_evidence',
        'qualification_blockers': [
            'empirical_coverage_not_established',
            'optimizer_counterexamples_pending',
        ],
        'records': len(records),
        'families': {
            family: dict(sorted(counts.items())) for family, counts in sorted(families.items())
        },
        'limitations': [
            'Bounds, initials and coordinates changed together; no isolated solver-effect claim.',
            'More accepted fits do not establish coverage or external PTF skill.',
            'Marginal water interval overlap is not a joint confidence-region test.',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('ordered', type=Path)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    baseline_bytes, ordered_bytes = args.baseline.read_bytes(), args.ordered.read_bytes()
    result = compare(
        json.loads(baseline_bytes),
        [json.loads(line) for line in ordered_bytes.splitlines()],
        json.loads(args.dataset.read_bytes()),
    )
    result['baseline_sha256'] = hashlib.sha256(baseline_bytes).hexdigest()
    result['ordered_sha256'] = hashlib.sha256(ordered_bytes).hexdigest()
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
