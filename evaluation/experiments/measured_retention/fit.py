"""Replay reference-family fits without requiring eligible PTF predictors."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections import Counter
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np
from ptfkit_eval import (
    FitParameterRange,
    RetentionFitPlan,
    RetentionFitResult,
    RetentionParameterProfile,
    RetentionSeriesPoint,
    assess_profile_grid_region,
    assess_profile_optimality,
    diagnose_fit_uncertainty_support,
    diagnose_retention_series,
    fit_retention_family,
    load_retention_dataset,
    profile_retention_parameter,
)
from ptfkit_eval.artifacts import artifact_value
from ptfkit_eval.documents import canonical_json, object_records


if TYPE_CHECKING:
    from ptfkit_eval.fitting import RestartPolicy


_MINIMUM_PROFILE_POINTS = 2


def _profile_start(
    plan: RetentionFitPlan, profile: RetentionParameterProfile, fixed_value: float
) -> RetentionFitPlan | None:
    point = next(point for point in profile.points if point.fixed_value == fixed_value)
    attempt = min(
        (attempt for attempt in point.attempts if attempt.converged),
        key=lambda attempt: cast('float', attempt.sum_squared_error),
    )
    nuisance = tuple(name for name in profile.parameter_order if name != profile.parameter_name)
    initial = dict(zip(nuisance, attempt.values, strict=True))
    initial[profile.parameter_name] = fixed_value
    if not all(item.lower < initial[item.name] < item.upper for item in plan.parameters):
        return None
    return replace(
        plan,
        parameters=tuple(replace(item, initial=initial[item.name]) for item in plan.parameters),
    )


def _audit_refit(result: RetentionFitResult | None, grid_points: int) -> dict[str, object] | None:
    if result is None or result.status != 'fitted':
        return None
    estimates = {item.name: item.value for item in result.parameters}
    profiles = []
    for bounds in result.plan.parameters:
        grid = sorted(
            {*np.linspace(bounds.lower, bounds.upper, grid_points), estimates[bounds.name]}
        )
        profile = profile_retention_parameter(result, parameter_name=bounds.name, grid=grid)
        profiles.append(
            {
                'profile': artifact_value(profile),
                'optimality': artifact_value(
                    assess_profile_optimality(
                        profile,
                        absolute_tolerance=1e-10,
                        relative_tolerance=0,
                    )
                ),
                'approximate_grid_region': artifact_value(
                    assess_profile_grid_region(
                        profile,
                        confidence_level=result.plan.confidence_level,
                        absolute_tolerance=1e-10,
                        relative_tolerance=0,
                    )
                ),
            }
        )
    return {
        'parameter_profiles': profiles,
        'uncertainty_support': artifact_value(diagnose_fit_uncertainty_support(result)),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile-saturation-points', type=int, default=0)
    parser.add_argument(
        '--brooks-corey-policy',
        choices=(
            'seeded_box_v1',
            'brooks_corey_pressure_partitions_v1',
            'brooks_corey_interval_solves_v1',
        ),
        default='seeded_box_v1',
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Write one exclusive, self-contained descriptive fitting artifact."""
    parser = _parser()
    arguments = parser.parse_args(argv)
    if (
        arguments.profile_saturation_points != 0
        and arguments.profile_saturation_points < _MINIMUM_PROFILE_POINTS
    ):
        parser.error('Saturation profiling needs at least two grid points, or zero to disable.')
    if arguments.output.exists():
        parser.error('Output already exists; choose a new artifact path.')
    dataset_bytes = arguments.dataset.read_bytes()
    dataset = load_retention_dataset(json.loads(dataset_bytes))
    observations = object_records(dataset.document['observations'])
    if any(
        item['origin'] != 'measured' or item['review_status'] != 'confirmed'
        for item in observations
    ):
        parser.error('This experiment requires confirmed measured observations.')
    if any(item['quality_flags'] for item in observations):
        parser.error('Resolve flagged observations before running this experiment.')
    residual = FitParameterRange('theta_r', 0, 0.14, 0.05)
    saturation = FitParameterRange('theta_s', 0.25, 0.8, 0.45)
    alpha = FitParameterRange('alpha', 0.001, 10, 0.1)
    boxes = {
        'van_genuchten_mualem_v1': (
            residual,
            saturation,
            alpha,
            FitParameterRange('n', 1.05, 5, 1.8),
        ),
        'van_genuchten_m1_v1': (residual, saturation, alpha, FitParameterRange('n', 0.05, 5, 1.8)),
        'brooks_corey_v1': (
            residual,
            saturation,
            FitParameterRange('air_entry', 0.05, 10, 1),
            FitParameterRange('lambda', 0.05, 2, 0.5),
        ),
        'clapp1978_gradual_air_entry_v1': (
            saturation,
            FitParameterRange('saturation_suction', 0.001, 5, 0.2),
            FitParameterRange('b', 0.5, 11.4, 4.5),
        ),
    }
    plans = tuple(
        RetentionFitPlan(
            family_id=family,
            target=dataset.target,
            parameters=parameters,
            seed=7123,
            minimum_log10_span=2.0,
            restart_policy=(
                cast('RestartPolicy', arguments.brooks_corey_policy)
                if family == 'brooks_corey_v1'
                else 'seeded_box_v1'
            ),
        )
        for family, parameters in boxes.items()
    )
    records = []
    counts: Counter[tuple[str, str, str | None]] = Counter()
    for sample in object_records(dataset.document['samples']):
        points = tuple(
            RetentionSeriesPoint(
                cast('float', item['suction_kpa']),
                cast('float', item['value']),
                cast('str', item['id']),
            )
            for item in observations
            if (item['source_id'], item['sample_id']) == (sample['source_id'], sample['sample_id'])
        )
        quality = diagnose_retention_series(points)
        for plan in plans:
            result = fit_retention_family(points, plan=plan)
            profile, optimality, profile_refit = None, None, None
            profile_refit_status = 'not_requested'
            if arguments.profile_saturation_points and result.status == 'fitted':
                bounds = next(item for item in plan.parameters if item.name == 'theta_s')
                estimate = next(item.value for item in result.parameters if item.name == 'theta_s')
                grid = sorted(
                    {
                        *np.linspace(
                            bounds.lower, bounds.upper, arguments.profile_saturation_points
                        ),
                        estimate,
                    }
                )
                profile = profile_retention_parameter(result, parameter_name='theta_s', grid=grid)
                optimality = assess_profile_optimality(
                    profile,
                    absolute_tolerance=1e-10,
                    relative_tolerance=0,
                )
                profile_refit_status = 'no_improvement_detected'
                if optimality.status == 'lower_objective_found':
                    warm_plan = _profile_start(
                        plan, profile, cast('float', optimality.best_fixed_value)
                    )
                    if warm_plan is not None:
                        profile_refit = fit_retention_family(points, plan=warm_plan)
                        profile_refit_status = 'refitted'
                    else:
                        profile_refit_status = 'profile_start_on_boundary'
            counts[plan.family_id, result.status, result.reason] += 1
            records.append(
                {
                    'source_id': sample['source_id'],
                    'sample_id': sample['sample_id'],
                    'quality': artifact_value(quality),
                    'fit': artifact_value(result),
                    'uncertainty_support': artifact_value(diagnose_fit_uncertainty_support(result)),
                    'saturation_profile': artifact_value(profile),
                    'profile_optimality': artifact_value(optimality),
                    'profile_refit_status': profile_refit_status,
                    'profile_refit': artifact_value(profile_refit),
                    'profile_refit_audit': _audit_refit(
                        profile_refit, arguments.profile_saturation_points
                    ),
                }
            )
    summary = [
        {'family_id': family, 'status': status, 'reason': reason, 'count': count}
        for (family, status, reason), count in sorted(counts.items(), key=lambda item: str(item[0]))
    ]
    artifact = {
        'schema_version': 1,
        'experiment': 'measured_retention_reference_fits_v1',
        'dataset': dataset.document,
        'dataset_sha256': dataset.sha256,
        'dataset_file_sha256': hashlib.sha256(dataset_bytes).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'environment': {
            'python': platform.python_version(),
            **{name: version(name) for name in ('ptfkit-eval', 'numpy', 'scipy')},
        },
        'summary': summary,
        'results': records,
    }
    with arguments.output.open('xb') as stream:
        stream.write(canonical_json(artifact))
    sys.stdout.write(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
