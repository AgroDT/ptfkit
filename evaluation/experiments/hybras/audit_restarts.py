"""Audit all 27 HYBRAS Brooks-Corey optimizer counterexamples without changing targets."""

# ruff: noqa: INP001, T201 - Standalone source-pinned numerical audit.

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from collections import Counter
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np

import ptfkit_eval
from ptfkit_eval import (
    FitParameterRange,
    RetentionFitPlan,
    RetentionSeriesPoint,
    TargetSpec,
    assess_profile_grid_region,
    assess_profile_optimality,
    diagnose_fit_uncertainty_support,
    fit_retention_family,
    profile_retention_parameter,
)
from ptfkit_eval.artifacts import artifact_value
from ptfkit_eval.documents import canonical_json


if TYPE_CHECKING:
    from ptfkit_eval import RetentionFitResult
    from ptfkit_eval.fitting import RestartPolicy


BASELINE_SHA256 = '9e6e9cbd27ee7d83bd9572de60a81a48acf3ecb37ee45b10d93b2e8a9af27b34'
ORDERED_SHA256 = '7b08df058a8983a68cbc9aff1cf2a1354a341e025e7a297778f856fe4093b17f'
REGRESSION_TOLERANCE = 1e-12
EXPECTED_COUNTEREXAMPLES = 27


def best_attempt(fit: dict) -> dict | None:
    """Keep converged numerical solutions separate from evidence acceptance."""
    return min(
        (
            attempt
            for attempt in fit['attempts']
            if attempt['converged'] and attempt['sum_squared_error'] is not None
        ),
        key=lambda attempt: attempt['sum_squared_error'],
        default=None,
    )


def profile_audit(result: RetentionFitResult) -> list[dict]:
    """Use five fixed box grid values plus the estimate; do not tune the grid."""
    estimates = {p.name: p.value for p in result.parameters}
    profiles = []
    for bounds in result.plan.parameters:
        grid = sorted({*np.linspace(bounds.lower, bounds.upper, 5), estimates[bounds.name]})
        profile = profile_retention_parameter(result, parameter_name=bounds.name, grid=grid)
        profiles.append(
            {
                'profile': artifact_value(profile),
                'optimality': artifact_value(
                    assess_profile_optimality(
                        profile, absolute_tolerance=1e-10, relative_tolerance=0
                    )
                ),
                'region': artifact_value(
                    assess_profile_grid_region(
                        profile,
                        confidence_level=result.plan.confidence_level,
                        absolute_tolerance=1e-10,
                        relative_tolerance=0,
                    )
                ),
            }
        )
    return profiles


def select_counterexamples(baseline: dict, ordered: list[dict]) -> list[tuple[dict, dict]]:
    """Select by the predeclared objective discrepancy, retaining every such curve."""
    index = {
        (r['source_id'], r['sample_id'], r['fit']['plan']['family_id']): r
        for r in baseline['results']
    }
    selected = []
    for record in ordered:
        fit = record['fit']
        if fit['plan']['family_id'] != 'brooks_corey_v1':
            continue
        before = index[record['source_id'], record['sample_id'], 'brooks_corey_v1']['fit']
        if before['observations'] != fit['observations']:
            message = 'Counterexample audit requires exactly unchanged observations.'
            raise ValueError(message)
        first, second = best_attempt(before), best_attempt(fit)
        if (
            first is not None
            and second is not None
            and (second['sum_squared_error'] - first['sum_squared_error'] > REGRESSION_TOLERANCE)
        ):
            selected.append((record, first))
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('ordered', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    baseline_bytes, ordered_bytes = args.baseline.read_bytes(), args.ordered.read_bytes()
    if (
        hashlib.sha256(baseline_bytes).hexdigest() != BASELINE_SHA256
        or hashlib.sha256(ordered_bytes).hexdigest() != ORDERED_SHA256
    ):
        parser.error('This audit requires the exact archived baseline and ordered fit records.')
    selected = select_counterexamples(
        json.loads(baseline_bytes), [json.loads(line) for line in ordered_bytes.splitlines()]
    )
    if len(selected) != EXPECTED_COUNTEREXAMPLES:
        parser.error('The complete archived counterexample roster must be retained.')
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(ptfkit_eval.__file__).parent
    metadata = {
        'experiment': 'hybras_brooks_corey_counterexample_restart_audit_v1',
        'baseline_sha256': BASELINE_SHA256,
        'ordered_sha256': ORDERED_SHA256,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'implementation_sha256': {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*'))
            if p.suffix in {'.py', '.json'}
        },
        'counterexamples': len(selected),
        'profile_policy': (
            'Interval-solve results for all six originally locally accepted counterexamples; '
            'five fixed box grid values plus estimate for every parameter.'
        ),
        'environment': {
            'python': platform.python_version(),
            **{name: version(name) for name in ('ptfkit-eval', 'numpy', 'scipy')},
        },
        'uncertainty_qualification': 'insufficient_evidence',
    }
    (args.output / 'metadata.json').write_bytes(canonical_json(metadata))
    counts = Counter()
    with (args.output / 'audit.jsonl').open('xb') as stream:
        for index, (record, baseline_start) in enumerate(selected, start=1):
            original = record['fit']
            settings = dict(original['plan'])
            settings['target'] = TargetSpec(**settings['target'])
            settings['parameters'] = tuple(FitParameterRange(**p) for p in settings['parameters'])
            settings['additional_starts'] = (tuple(baseline_start['values']),)
            plan = RetentionFitPlan(**settings)
            points = tuple(RetentionSeriesPoint(**p) for p in original['observations'])
            for policy in [
                'seeded_box_v1',
                'brooks_corey_pressure_partitions_v1',
                'brooks_corey_interval_solves_v1',
            ]:
                result = fit_retention_family(
                    points, plan=replace(plan, restart_policy=cast('RestartPolicy', policy))
                )
                if artifact_value(result.attempts[: plan.n_starts]) != original['attempts']:
                    message = 'Original seeded solves must remain unchanged in every audit variant.'
                    raise ValueError(message)
                fitted = artifact_value(result)
                best = best_attempt(fitted)
                resolved = (
                    best is not None
                    and best['sum_squared_error'] - baseline_start['sum_squared_error']
                    <= REGRESSION_TOLERANCE
                )
                profiles = (
                    profile_audit(result)
                    if policy == 'brooks_corey_interval_solves_v1'
                    and original['status'] == 'fitted'
                    and result.status == 'fitted'
                    else []
                )
                output = {
                    'source_id': record['source_id'],
                    'sample_id': record['sample_id'],
                    'original_status': original['status'],
                    'policy': policy,
                    'baseline_sum_squared_error': baseline_start['sum_squared_error'],
                    'regression_resolved': resolved,
                    'fit': fitted,
                    'uncertainty_support': artifact_value(diagnose_fit_uncertainty_support(result)),
                    'profiles': profiles,
                }
                stream.write(
                    (
                        json.dumps(output, sort_keys=True, allow_nan=False, separators=(',', ':'))
                        + '\n'
                    ).encode('utf-8')
                )
                stream.flush()
                counts[policy, result.status, result.reason, resolved] += 1
            print(f'Completed {index}/{len(selected)} counterexamples', flush=True)
    summary = {
        'counterexamples': len(selected),
        'refits': sum(counts.values()),
        'uncertainty_qualification': 'insufficient_evidence',
        'summary': [
            {'policy': p, 'status': s, 'reason': r, 'regression_resolved': resolved, 'count': n}
            for (p, s, r, resolved), n in sorted(counts.items(), key=lambda item: str(item[0]))
        ],
        'audit_sha256': hashlib.sha256((args.output / 'audit.jsonl').read_bytes()).hexdigest(),
    }
    (args.output / 'summary.json').write_bytes(canonical_json(summary))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
