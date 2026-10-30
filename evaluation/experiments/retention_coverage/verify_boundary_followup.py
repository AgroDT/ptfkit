"""Verify follow-up inputs and numerical replay, then emit the count-only report."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import Counter
from pathlib import Path

import numpy as np


def _verify_blocks(
    *,
    directory: Path,
    plan: dict,
    summary: dict,
    generator: dict,
    followup: dict,
    axis: np.ndarray,
    truth: np.ndarray,
) -> None:
    totals: Counter[str] = Counter()
    for block in range(plan['blocks']):
        old = json.loads((directory / f'block-{block}.json').read_bytes())
        rng = np.random.default_rng(np.random.SeedSequence([plan['seed'], block]))
        expected = generator['mean_curve']('van_genuchten_mualem_v1', 0.3, axis=axis) + rng.normal(
            0, plan['sigma'], (plan['repetitions_per_block'], len(axis))
        )
        observed = np.array(
            [
                [point['water_content'] for point in record['fit']['observations']]
                for record in old['records']
            ]
        )
        if not np.array_equal(expected, observed):
            message = 'Independent block noise replay failed.'
            raise ValueError(message)
        paired = followup['paired_counts'](old['records'], axis, truth)
        if paired != old['paired_counts'] or paired != summary['blocks'][block]['paired_counts']:
            message = 'Paired coverage counts do not match saved records.'
            raise ValueError(message)
        totals.update(paired)
    if dict(totals) != summary['totals']:
        message = 'Pooled follow-up counts do not match saved records.'
        raise ValueError(message)
    primary = followup['_coverage'](totals['nonlinear_covered'], totals['nonlinear_assessed'])
    if primary != summary['primary_conditional_coverage']:
        message = 'Primary follow-up inference does not match saved records.'
        raise ValueError(message)


def verify(directory: Path, source: Path) -> dict:
    summary = json.loads((directory / 'summary.json').read_bytes())
    plan = summary['plan']
    scripts = Path(__file__).parent
    plan_bytes = (scripts / 'boundary-followup-plan.json').read_bytes()
    if (
        hashlib.sha256(plan_bytes).hexdigest() != summary['plan_sha256']
        or json.loads(plan_bytes) != plan
    ):
        message = 'Prespecified follow-up plan binding failed.'
        raise ValueError(message)
    for name, key in (
        ('calibrate.py', 'generator_sha256'),
        ('boundary_followup.py', 'script_sha256'),
    ):
        if hashlib.sha256((scripts / name).read_bytes()).hexdigest() != summary[key]:
            message = 'Follow-up implementation binding failed.'
            raise ValueError(message)
    if hashlib.sha256(source.read_bytes()).hexdigest() != summary['source_sha256']:
        message = 'Follow-up source binding failed.'
        raise ValueError(message)
    original = json.loads(source.read_bytes())['payload']
    implementation = runpy.run_path(str(scripts / 'expanded.py'))['_implementation_hash']()
    if implementation != original['context']['evaluation_implementation_sha256']:
        message = 'Public fitting implementation differs from the original study.'
        raise ValueError(message)
    generator = runpy.run_path(str(scripts / 'calibrate.py'))
    followup = runpy.run_path(str(scripts / 'boundary_followup.py'))
    axis = np.array(original['cell']['pressure_kpa'])
    truth = np.array([0.1, 0.3, 0.1, 2])
    control = followup['large_linear_control'](
        axis, truth, plan['linear_control_repetitions'], plan['seed']
    )
    if control != summary['large_linear_control']:
        message = 'Large linear control replay failed.'
        raise ValueError(message)
    _verify_blocks(
        directory=directory,
        plan=plan,
        summary=summary,
        generator=generator,
        followup=followup,
        axis=axis,
        truth=truth,
    )
    counts, records = generator['simulate_scenario'](
        plan=generator['_plan']('van_genuchten_mualem_v1'),
        truth=0.3,
        axis=axis,
        sigma=plan['sigma'],
        air_entry=10,
        repetitions=plan['repetitions_per_block'],
        rng=np.random.default_rng(np.random.SeedSequence([plan['seed'], 0])),
    )
    replay = {
        'counts': counts,
        'records': records,
        'paired_counts': followup['paired_counts'](records, axis, truth),
    }
    if json.loads(json.dumps(replay)) != json.loads((directory / 'block-0.json').read_bytes()):
        message = 'Complete fit/profile block replay failed.'
        raise ValueError(message)
    audit = json.loads((directory / 'original-audit.json').read_bytes())['optimizer_audit'][
        'records'
    ]
    summary['evaluation_implementation_sha256'] = implementation
    summary['optimizer_audit_summary'] = {
        'cases': len(audit),
        'solve_failures': sum(
            not row['audit_full_converged'] or not row['audit_fixed_converged'] for row in audit
        ),
        'full_objective_improvements': sum(
            row['public_full_sse'] is not None
            and row['public_full_sse'] - row['audit_full_sse'] > plan['objective_tolerance']
            for row in audit
        ),
        'profile_objective_improvements': sum(
            row['public_fixed_sse'] is not None
            and row['public_fixed_sse'] - row['audit_fixed_sse'] > plan['objective_tolerance']
            for row in audit
        ),
        'profile_comparisons': sum(row['public_fixed_sse'] is not None for row in audit),
    }
    summary['verification'] = {
        'all_2000_generated_noise_vectors_replayed': True,
        'first_400_full_fit_profile_records_replayed': True,
        'all_100000_linear_control_results_replayed': True,
        'public_implementation_matches_original_study': True,
    }
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = verify(arguments.directory, arguments.source)
    with arguments.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
