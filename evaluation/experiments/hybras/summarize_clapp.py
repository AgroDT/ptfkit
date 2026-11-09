"""Verify native Clapp predictions against published Table 2 and summarize the run."""

# ruff: noqa: INP001 - Standalone independent numerical verifier.

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


# Clapp and Hornberger (1978), Table 2: b, saturation suction (cm), saturation.
PUBLISHED = {
    'sand': (4.05, 3.50, 0.395),
    'loamy sand': (4.38, 1.78, 0.410),
    'sandy loam': (4.90, 7.18, 0.435),
    'silt loam': (5.30, 56.6, 0.485),
    'loam': (5.39, 14.6, 0.451),
    'sandy clay loam': (7.12, 8.63, 0.420),
    'silty clay loam': (7.75, 14.6, 0.477),
    'clay loam': (8.52, 36.1, 0.476),
    'sandy clay': (10.4, 6.16, 0.426),
    'silty clay': (10.4, 17.4, 0.492),
    'clay': (11.4, 18.6, 0.482),
}


def published_water(texture: str, head: float) -> float:
    """Invert source equations 1 and 3 using bisection on the wet parabola."""
    b, saturation_head, saturated = PUBLISHED[texture]
    wetness_i = 0.92
    head_i = saturation_head * wetness_i ** (-b)
    if head >= head_i:
        return saturated * (head / saturation_head) ** (-1 / b)
    # In t=(W-W_i)/(1-W_i), fit the quadratic through (0,h_i),(1,0)
    # with dh/dt at t=0 equal to -b*h_i*(1-W_i)/W_i (source equation 1).
    slope = -b * head_i * (1 - wetness_i) / wetness_i
    lower, upper = 0.0, 1.0
    for _ in range(60):
        t = (lower + upper) / 2
        pressure = head_i + slope * t - (head_i + slope) * t * t
        if pressure > head:
            lower = t
        else:
            upper = t
    return saturated * (wetness_i + (1 - wetness_i) * (lower + upper) / 2)


def summarize(run: Path) -> dict:
    """Check persisted artifacts, unchanged targets, all predictions and mean errors."""
    artifacts = run / 'artifacts'
    manifest = json.loads((artifacts / 'run-manifest.json').read_bytes())
    for name, entry in manifest['files'].items():
        raw = (artifacts / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256'] or len(raw) != entry['bytes']:
            message = f'Artifact checksum mismatch: {name}.'
            raise ValueError(message)
    dataset = json.loads((run / 'dataset.json').read_bytes())
    review = json.loads((run / 'review.json').read_bytes())
    decisions = {(s['source_id'], s['sample_id']): s for s in review['selected_samples']}
    observations = {
        (o['source_id'], o['sample_id'], o['suction_kpa']): o['value']
        for o in dataset['observations']
    }
    cohorts = json.loads((artifacts / 'cohorts.json').read_bytes())
    for entry in cohorts:
        points = entry['cohort']['comparisons']
        errors: dict[tuple[str, str], list[float]] = defaultdict(list)
        seen = set()
        for point in points:
            identity = (point['source_id'], point['sample_id'])
            key = (*identity, point['suction_kpa'])
            if key in seen or observations.get(key) != point['observed']:
                message = 'Compared observations differ from unique canonical targets.'
                raise ValueError(message)
            seen.add(key)
            head = point['suction_kpa'] / 0.0980665
            expected = published_water(decisions[identity]['texture'], head)
            if not math.isclose(expected, point['predicted'], abs_tol=2e-14, rel_tol=2e-13):
                message = f'Prediction differs from published Clapp equation: {key}.'
                raise ValueError(message)
            errors[identity].append(expected - point['observed'])
        if seen != observations.keys():
            message = 'The cohort does not cover every reviewed target exactly.'
            raise ValueError(message)
        n = len(errors)
        independent = {
            'mean_error': sum(sum(e) / len(e) for e in errors.values()) / n,
            'mean_absolute_error': sum(sum(map(abs, e)) / len(e) for e in errors.values()) / n,
            'root_mean_squared_error': math.sqrt(
                sum(sum(v * v for v in e) / len(e) for e in errors.values()) / n
            ),
        }
        recorded = entry['confidence']['summary']['metrics']
        for name, value in independent.items():
            if not math.isclose(value, recorded[name], abs_tol=2e-14, rel_tol=2e-13):
                message = f'Sample-balanced metric differs from independent calculation: {name}.'
                raise ValueError(message)
    first = cohorts[0]['confidence']
    return {
        'schema_version': 1,
        'scope': 'fixed_clapp_external_validation_not_best_model_selection',
        'dataset_id': dataset['dataset_id'],
        'samples': review['samples'],
        'profiles': review['profiles'],
        'sources': review['sources'],
        'observations': review['observations'],
        'metrics': first['summary']['metrics'],
        'confidence': {k: v for k, v in first.items() if k != 'summary'},
        'verified_prediction_records': sum(len(e['cohort']['comparisons']) for e in cohorts),
        'verification': 'Published Table 2, parabolic/power curves and independent sample means.',
        'limitations': review['limitations'],
        'review_sha256': hashlib.sha256((run / 'review.json').read_bytes()).hexdigest(),
        'cohorts_sha256': hashlib.sha256((artifacts / 'cohorts.json').read_bytes()).hexdigest(),
        'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = summarize(args.run)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
