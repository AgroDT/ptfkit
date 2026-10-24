"""Conditional profile coverage with all nonlinear retention fit failures retained."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from collections import Counter
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from ptfkit_eval import (
    FitParameterRange,
    RetentionFitPlan,
    RetentionSeriesPoint,
    TargetSpec,
    assess_profile_grid_region,
    fit_retention_family,
    profile_retention_parameter,
)
from ptfkit_eval.artifacts import artifact_value


if TYPE_CHECKING:
    from ptfkit_eval.fitting import RestartPolicy


AXIS = np.array([0, 2, 5, 10, 20, 50, 100, 200, 300, 1000, 3000, 10000])
_AIR_ENTRY = 10


def _plan(family: str) -> RetentionFitPlan:
    saturation = FitParameterRange('theta_s', 0.3, 0.8, 0.45)
    residual = FitParameterRange('theta_r', 0, 0.2, 0.05)
    boxes = {
        'van_genuchten_mualem_v1': (
            residual,
            saturation,
            FitParameterRange('alpha', 0.01, 1, 0.08),
            FitParameterRange('n', 1.1, 4, 1.8),
        ),
        'van_genuchten_m1_v1': (
            residual,
            saturation,
            FitParameterRange('alpha', 0.01, 1, 0.08),
            FitParameterRange('n', 0.2, 4, 1.8),
        ),
        'brooks_corey_v1': (
            residual,
            saturation,
            FitParameterRange('air_entry', 1, 30, 7),
            FitParameterRange('lambda', 0.1, 2, 0.8),
        ),
        'clapp1978_gradual_air_entry_v1': (
            saturation,
            FitParameterRange('saturation_suction', 0.2, 2, 0.8),
            FitParameterRange('b', 2, 6, 3.8),
        ),
    }
    return RetentionFitPlan(
        family_id=family,
        target=TargetSpec(
            'volumetric_water_content', 'volume_fraction', 'synthetic_control', 'bulk_volume'
        ),
        parameters=boxes[family],
        seed=7123,
        minimum_log10_span=2,
    )


def mean_curve(
    family: str, saturation: float, *, axis: np.ndarray = AXIS, air_entry: float = _AIR_ENTRY
) -> np.ndarray:
    """Use explicit published branches as the synthetic generative equations."""
    if family == 'van_genuchten_mualem_v1':
        return 0.1 + (saturation - 0.1) / np.sqrt(1 + (axis / 10) ** 2)
    if family == 'van_genuchten_m1_v1':
        return 0.1 + (saturation - 0.1) / (1 + (axis / 10) ** 2)
    if family == 'brooks_corey_v1':
        return np.array(
            [
                saturation if h <= air_entry else 0.1 + (saturation - 0.1) * (air_entry / h) ** 0.5
                for h in axis
            ]
        )
    if family == 'clapp1978_gradual_air_entry_v1':
        # This grid samples saturation and the dry power branch only (psi_s=1, b=4).
        return np.array([saturation if h == 0 else saturation / h**0.25 for h in axis])
    message = 'Unknown synthetic retention family.'
    raise ValueError(message)


def _restart_policy(*, pressure_restarts: bool, interval_solves: bool) -> RestartPolicy:
    if pressure_restarts and interval_solves:
        message = 'Choose exactly one optional restart policy.'
        raise ValueError(message)
    return (
        'brooks_corey_interval_solves_v1'
        if interval_solves
        else 'brooks_corey_pressure_partitions_v1'
        if pressure_restarts
        else 'seeded_box_v1'
    )


def simulate_scenario(
    *,
    plan: RetentionFitPlan,
    truth: float,
    axis: np.ndarray,
    sigma: float,
    air_entry: float,
    repetitions: int,
    rng: np.random.Generator,
) -> tuple[dict[str, int], list[dict[str, object]]]:
    """Keep every outcome in one explicitly declared generative scenario."""
    family = plan.family_id
    counts: Counter[str] = Counter()
    records: list[dict[str, object]] = []
    for repetition in range(repetitions):
        water = mean_curve(family, truth, axis=axis, air_entry=air_entry) + rng.normal(
            0, sigma, len(axis)
        )
        counts['generated'] += 1
        if np.any(water < 0) or np.any(water > 1):
            counts['invalid_physical_sample'] += 1
            records.append(
                {
                    'family': family,
                    'truth': truth,
                    'repetition': repetition,
                    'status': 'invalid_physical_sample',
                    'water': water.tolist(),
                }
            )
            continue
        points = tuple(
            RetentionSeriesPoint(float(h), float(value), str(index))
            for index, (h, value) in enumerate(zip(axis, water, strict=True))
        )
        fit = fit_retention_family(points, plan=plan)
        counts[fit.status] += 1
        profile, region = None, None
        if fit.status == 'failed':
            counts[str(fit.reason)] += 1
        else:
            estimate = next(item.value for item in fit.parameters if item.name == 'theta_s')
            profile = profile_retention_parameter(
                fit,
                parameter_name='theta_s',
                grid=sorted({0.3, 0.425, 0.55, 0.675, 0.8, truth, estimate}),
            )
            region = assess_profile_grid_region(
                profile,
                confidence_level=0.95,
                absolute_tolerance=1e-10,
                relative_tolerance=0,
            )
            counts[region.status] += 1
            if region.status == 'assessed':
                counts['covered'] += any(truth in run for run in region.accepted_runs)
            else:
                counts[str(region.reason)] += 1
        records.append(
            {
                'family': family,
                'truth': truth,
                'repetition': repetition,
                'fit': artifact_value(fit),
                'profile': artifact_value(profile),
                'region': artifact_value(region),
            }
        )
    return dict(sorted(counts.items())), records


def calibrate(
    *, repetitions: int, seed: int, pressure_restarts: bool = False, interval_solves: bool = False
) -> dict[str, object]:
    if repetitions < 1 or seed < 0:
        message = 'Repetitions must be positive and seed nonnegative.'
        raise ValueError(message)
    rng = np.random.default_rng(seed)
    policy = _restart_policy(pressure_restarts=pressure_restarts, interval_solves=interval_solves)
    summaries, records = [], []
    for family in (
        'van_genuchten_mualem_v1',
        'van_genuchten_m1_v1',
        'brooks_corey_v1',
        'clapp1978_gradual_air_entry_v1',
    ):
        plan = _plan(family)
        if family == 'brooks_corey_v1':
            plan = replace(plan, restart_policy=policy)
        for truth in (0.5, 0.3):
            counts, scenario_records = simulate_scenario(
                plan=plan,
                truth=truth,
                axis=AXIS,
                sigma=0.002,
                air_entry=_AIR_ENTRY,
                repetitions=repetitions,
                rng=rng,
            )
            records.extend(scenario_records)
            summaries.append({'family': family, 'truth': truth, 'counts': counts})
    return {
        'method': 'nonlinear_retention_profile_coverage_pilot_v1',
        'seed': seed,
        'sigma': 0.002,
        'coverage_status': 'pilot_not_qualified',
        'pressure_restarts': pressure_restarts,
        'interval_solves': interval_solves,
        'pressure_kpa': AXIS.tolist(),
        'nominal_confidence': 0.95,
        'environment': {
            'python': platform.python_version(),
            **{name: version(name) for name in ('ptfkit-eval', 'numpy', 'scipy')},
        },
        'summaries': summaries,
        'records': records,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions', type=int, default=50)
    parser.add_argument('--seed', type=int, default=20261024)
    parser.add_argument('--output', type=Path, required=True)
    policies = parser.add_mutually_exclusive_group()
    policies.add_argument('--pressure-restarts', action='store_true')
    policies.add_argument('--interval-solves', action='store_true')
    arguments = parser.parse_args()
    result = calibrate(
        repetitions=arguments.repetitions,
        seed=arguments.seed,
        pressure_restarts=arguments.pressure_restarts,
        interval_solves=arguments.interval_solves,
    )
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with arguments.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
