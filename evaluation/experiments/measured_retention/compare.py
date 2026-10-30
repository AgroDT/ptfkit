"""Compare fit policies on exactly matching canonical curves, reporting counts only."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


_IMPROVEMENT_TOLERANCE = 1e-10
_REGRESSION_TOLERANCE = 1e-12


def _objective(fit: dict) -> float | None:
    values = [
        attempt['sum_squared_error']
        for attempt in fit['attempts']
        if attempt['converged'] and attempt['sum_squared_error'] is not None
    ]
    return min(values) if values else None


def _index(document: dict) -> dict:
    records = document['results']
    index = {
        (record['source_id'], record['sample_id'], record['fit']['plan']['family_id']): record
        for record in records
    }
    if len(index) != len(records):
        message = 'Fit comparison requires unique sample/family records.'
        raise ValueError(message)
    return index


def compare(baseline: dict, candidate: dict) -> dict[str, object]:
    left, right = _index(baseline), _index(candidate)
    if baseline['dataset_sha256'] != candidate['dataset_sha256'] or left.keys() != right.keys():
        message = 'Fit comparison requires identical canonical data and sample/family rosters.'
        raise ValueError(message)
    families = []
    for family in sorted({key[2] for key in left}):
        counts: Counter[str] = Counter()
        baseline_reasons: Counter[str] = Counter()
        candidate_reasons: Counter[str] = Counter()
        for key in left:
            if key[2] != family:
                continue
            before, after = left[key]['fit'], right[key]['fit']
            settings = [dict(before['plan']), dict(after['plan'])]
            for plan in settings:
                plan.pop('restart_policy', None)
            if settings[0] != settings[1] or before['observations'] != after['observations']:
                message = 'Fit comparison requires identical observations and non-policy settings.'
                raise ValueError(message)
            counts['samples'] += 1
            counts[f'{before["status"]}_to_{after["status"]}'] += 1
            baseline_reasons[before['reason'] or 'accepted'] += 1
            candidate_reasons[after['reason'] or 'accepted'] += 1
            first, second = _objective(before), _objective(after)
            if first is not None and second is not None:
                counts['comparable_objectives'] += 1
                counts['improved_objectives'] += first - second > _IMPROVEMENT_TOLERANCE
                counts['worsened_objectives'] += second - first > _REGRESSION_TOLERANCE
            for name, records in (('baseline', left), ('candidate', right)):
                optimality = records[key].get('profile_optimality')
                counts[f'{name}_profile_counterexamples'] += bool(
                    optimality and optimality['status'] == 'lower_objective_found'
                )
        families.append(
            {
                'family': family,
                'counts': dict(sorted(counts.items())),
                'baseline_reasons': dict(sorted(baseline_reasons.items())),
                'candidate_reasons': dict(sorted(candidate_reasons.items())),
            }
        )
    return {
        'schema_version': 1,
        'dataset_sha256': baseline['dataset_sha256'],
        'scope': 'descriptive_fit_policy_comparison_not_PTF_prediction_assessment',
        'improvement_tolerance': 1e-10,
        'regression_tolerance': 1e-12,
        'families': families,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    first, second = arguments.baseline.read_bytes(), arguments.candidate.read_bytes()
    result = compare(json.loads(first), json.loads(second))
    result['baseline_artifact_sha256'] = hashlib.sha256(first).hexdigest()
    result['candidate_artifact_sha256'] = hashlib.sha256(second).hexdigest()
    with arguments.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
