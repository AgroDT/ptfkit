"""Gaussian bounded-mean control for profile-grid coverage and fit selection."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from importlib.metadata import version
from pathlib import Path

import numpy as np
from ptfkit_eval import assess_profile_grid_region
from ptfkit_eval.fit_profiles import ParameterProfilePoint, RetentionParameterProfile
from scipy.stats import t


def assess_sample(sample: np.ndarray, truth: float, level: float) -> dict[str, bool]:
    """Classify the exact mean-model SSE profile; observations are latent Gaussian."""
    mean = float(np.mean(sample))
    estimate = min(1.0, max(0.0, mean))
    residual = float(np.sum((sample - mean) ** 2))
    baseline = float(np.sum((sample - estimate) ** 2))
    grid = sorted({0.0, 1.0, truth, estimate})
    profile = RetentionParameterProfile(
        'mean',
        ('mean',),
        baseline,
        tuple(
            ParameterProfilePoint(value, float(np.sum((sample - value) ** 2)), ()) for value in grid
        ),
        residual_degrees_of_freedom=len(sample) - 1,
        parameter_bounds=(0, 1),
    )
    region = assess_profile_grid_region(
        profile,
        confidence_level=level,
        absolute_tolerance=1e-12,
        relative_tolerance=0,
    )
    critical = float(t.ppf((1 + level) / 2, len(sample) - 1))
    return {
        'available': region.status == 'assessed',
        'covered': any(truth in run for run in region.accepted_runs),
        'interior_fit': 0 < mean < 1,
        'upper_boundary_fit': mean >= 1,
        'lower_boundary_fit': mean <= 0,
        'unconstrained_t_covered': abs(mean - truth)
        <= critical * math.sqrt(residual / ((len(sample) - 1) * len(sample))),
    }


def calibrate(*, repetitions: int, seed: int) -> dict[str, object]:
    """Keep availability and coverage denominators explicit; no retention claim."""
    if repetitions < 1 or seed < 0:
        message = 'Repetitions must be positive and seed nonnegative.'
        raise ValueError(message)
    rng = np.random.default_rng(seed)
    scenarios = []
    for truth in (0.0, 0.02, 0.5, 1.0):
        outcomes = [
            assess_sample(sample, truth, 0.95)
            for sample in rng.normal(truth, 0.1, (repetitions, 8))
        ]
        available = [item for item in outcomes if item['available']]
        interior = [item for item in available if item['interior_fit']]
        scenarios.append(
            {
                'truth': truth,
                'generated': repetitions,
                'available': len(available),
                'covered': sum(item['covered'] for item in available),
                'interior_available': len(interior),
                'interior_covered': sum(item['covered'] for item in interior),
                'lower_boundary_fits': sum(item['lower_boundary_fit'] for item in outcomes),
                'upper_boundary_fits': sum(item['upper_boundary_fit'] for item in outcomes),
                'unconstrained_t_covered': sum(
                    item['unconstrained_t_covered'] for item in outcomes
                ),
            }
        )
    return {
        'method': 'gaussian_bounded_mean_profile_control_v1',
        'seed': seed,
        'observations_per_sample': 8,
        'noise_standard_deviation': 0.1,
        'nominal_confidence': 0.95,
        'bounds': [0, 1],
        'unconstrained_reference_coverage': 0.95,
        'single_boundary_reference_coverage': 0.975,
        'single_boundary_reference_scope': 'half_line_limit_not_exact_finite_box_coverage',
        'noise_model': 'iid_gaussian_latent_response_not_truncated',
        'retention_coverage_status': 'not_qualified_control_model_only',
        'environment': {
            'python': platform.python_version(),
            **{name: version(name) for name in ('ptfkit-eval', 'numpy', 'scipy')},
        },
        'scenarios': scenarios,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions', type=int, default=4000)
    parser.add_argument('--seed', type=int, default=20261024)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = calibrate(repetitions=arguments.repetitions, seed=arguments.seed)
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with arguments.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
