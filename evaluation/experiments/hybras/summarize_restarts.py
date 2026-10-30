"""Verify restart-audit objectives with an independent Brooks-Corey equation."""

# ruff: noqa: INP001 - Standalone count-only scientific verification.

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


_OBJECTIVE_TOLERANCE = 1e-12
_POLICIES = {
    'seeded_box_v1',
    'brooks_corey_pressure_partitions_v1',
    'brooks_corey_interval_solves_v1',
}


def independent_objective(values: dict[str, float], observations: list[dict]) -> float:
    """Use the plateau/power equation directly, without the family evaluator."""
    residual, saturated, entry, shape = (
        values[name] for name in ('theta_r', 'theta_s', 'air_entry', 'lambda')
    )
    if not 0 <= residual < saturated <= 1 or entry <= 0 or shape <= 0:
        message = 'Audited Brooks-Corey parameters must remain physical.'
        raise ValueError(message)
    squared_errors = []
    for point in observations:
        pressure = point['suction_kpa']
        predicted = (
            saturated
            if pressure <= entry
            else residual + (saturated - residual) * (entry / pressure) ** shape
        )
        squared_errors.append((predicted - point['water_content']) ** 2)
    return math.fsum(squared_errors)


def verify_attempts(
    attempts: list[dict],
    names: tuple[str, ...],
    observations: list[dict],
    *,
    fixed: dict[str, float] | None = None,
) -> int:
    """Check every converged objective, including nonaccepted numerical fits."""
    checked = 0
    for attempt in attempts:
        if not attempt['converged']:
            continue
        values = dict(zip(names, attempt['values'], strict=True))
        values.update({} if fixed is None else fixed)
        objective = independent_objective(values, observations)
        if not math.isclose(
            objective, attempt['sum_squared_error'], rel_tol=0, abs_tol=_OBJECTIVE_TOLERANCE
        ):
            message = 'Stored objective differs from the independent Brooks-Corey equation.'
            raise ValueError(message)
        checked += 1
    return checked


def summarize(directory: Path) -> dict:
    """Require terminal publication, complete policy rosters and independently checked SSE."""
    metadata = json.loads((directory / 'metadata.json').read_bytes())
    terminal = json.loads((directory / 'summary.json').read_bytes())
    raw = (directory / 'audit.jsonl').read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != terminal['audit_sha256']:
        message = 'Audit stream checksum differs from the terminal summary.'
        raise ValueError(message)
    records = [json.loads(line) for line in raw.splitlines()]
    identities = {(r['source_id'], r['sample_id']) for r in records}
    keys = {(r['source_id'], r['sample_id'], r['policy']) for r in records}
    if (
        len(identities) != metadata['counterexamples']
        or len(keys) != len(records)
        or keys != {(*identity, policy) for identity in identities for policy in _POLICIES}
    ):
        message = 'The audit must retain every counterexample and policy exactly once.'
        raise ValueError(message)
    checked = 0
    profiles = []
    accepted_original = Counter()
    for record in records:
        fit = record['fit']
        if fit['plan']['restart_policy'] != record['policy']:
            message = 'Declared policy must match the executed fit plan.'
            raise ValueError(message)
        names = ('theta_r', 'theta_s', 'air_entry', 'lambda')
        checked += verify_attempts(fit['attempts'], names, fit['observations'])
        if (
            record['policy'] == 'brooks_corey_interval_solves_v1'
            and record['original_status'] == 'fitted'
        ):
            accepted_original[fit['status']] += 1
        for item in record['profiles']:
            profile = item['profile']
            nuisance = tuple(
                name for name in profile['parameter_order'] if name != profile['parameter_name']
            )
            for point in profile['points']:
                checked += verify_attempts(
                    point['attempts'],
                    nuisance,
                    fit['observations'],
                    fixed={profile['parameter_name']: point['fixed_value']},
                )
            profiles.append(item)
    return {
        'schema_version': 1,
        'scope': 'targeted_posthoc_optimizer_audit_not_external_validation',
        'counterexamples': len(identities),
        'refits': len(records),
        'independently_verified_converged_objectives': checked,
        'numerical_outcomes': terminal['summary'],
        'originally_accepted_interval_fit_outcomes': dict(accepted_original),
        'profiles': len(profiles),
        'profile_optimality': dict(Counter(p['optimality']['status'] for p in profiles)),
        'profile_grid_accepted_value_counts': dict(
            sorted(
                Counter(
                    sum(len(run) for run in p['region']['accepted_runs']) for p in profiles
                ).items()
            )
        ),
        'profile_regions_reaching_box_bounds': sum(
            p['region']['reaches_lower_bound'] or p['region']['reaches_upper_bound']
            for p in profiles
        ),
        'uncertainty_qualification': 'insufficient_evidence',
        'qualification_blockers': [
            'coarse_profile_grid_not_continuous_interval',
            'empirical_coverage_not_established',
        ],
        'audit_sha256': digest,
        'baseline_sha256': metadata['baseline_sha256'],
        'ordered_sha256': metadata['ordered_sha256'],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audit_directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = summarize(args.audit_directory)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
