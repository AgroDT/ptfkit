"""Independent linear controls and truth-initialized audits of a flagged profile cell."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import runpy
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import numpy as np
from ptfkit_eval.documents import document_hash
from scipy.optimize import least_squares
from scipy.stats import binomtest, t


_NOMINAL_CONFIDENCE = 0.95


def vg_curve_and_jacobian(
    axis: np.ndarray, parameters: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Independent analytic derivatives in theta_r, theta_s, alpha, n order."""
    residual, saturation, alpha, exponent = parameters
    m = 1 - 1 / exponent
    z = (alpha * axis) ** exponent
    effective = (1 + z) ** -m
    delta = saturation - residual
    jacobian = np.zeros((len(axis), 4))
    jacobian[:, 0], jacobian[:, 1] = 1 - effective, effective
    jacobian[:, 2] = -delta * m * exponent * z * effective / (alpha * (1 + z))
    positive = axis > 0
    jacobian[positive, 3] = (
        delta
        * effective[positive]
        * (
            -np.log1p(z[positive]) / exponent**2
            - m * z[positive] * np.log(alpha * axis[positive]) / (1 + z[positive])
        )
    )
    return residual + delta * effective, jacobian


def linear_control(errors: np.ndarray, design: np.ndarray, level: float) -> dict[str, object]:
    """Exact Gaussian linear-model t control, with no nonlinear solver or F quantile."""
    q, r = np.linalg.qr(design, mode='reduced')
    coefficients = np.linalg.solve(r, q.T @ errors)
    residual = errors - q @ (q.T @ errors)
    variance = float(residual @ residual) / (len(errors) - design.shape[1])
    inverse = np.linalg.solve(r, np.eye(r.shape[0]))
    standard_error = math.sqrt(variance * float(inverse[1] @ inverse[1]))
    critical = float(t.isf((1 - level) / 2, len(errors) - design.shape[1]))
    return {
        'selected': bool(coefficients[1] > 0),
        'covered': bool(abs(coefficients[1]) <= critical * standard_error),
        'saturation_deviation': float(coefficients[1]),
    }


def paired_counts(records: list, axis: np.ndarray, truth: np.ndarray) -> dict[str, int]:
    mean, design = vg_curve_and_jacobian(axis, truth)
    counts: Counter[str] = Counter()
    for record in records:
        fit, region = record.get('fit'), record.get('region')
        water = np.array(
            [point['water_content'] for point in fit['observations']] if fit else record['water']
        )
        control = linear_control(water - mean, design, 0.95)
        assessed = bool(region and region['status'] == 'assessed')
        covered = bool(assessed and any(truth[1] in run for run in region['accepted_runs']))
        counts['generated'] += 1
        counts['nonlinear_assessed'] += assessed
        counts['nonlinear_covered'] += covered
        counts['linear_all_covered'] += bool(control['covered'])
        counts['linear_selected'] += bool(control['selected'])
        counts['linear_selected_covered'] += bool(control['selected'] and control['covered'])
        if assessed and control['selected']:
            counts['joint_selected'] += 1
            counts['joint_linear_covered'] += bool(control['covered'])
            counts['joint_nonlinear_covered'] += covered
            counts['joint_coverage_disagreements'] += covered != control['covered']
    return dict(sorted(counts.items()))


def audit_original(records: list, axis: np.ndarray, truth: np.ndarray) -> dict[str, object]:
    """Known truth initializes diagnostic solves only; it never changes public fits."""
    audits = []
    indices = [0, 2, 3]

    def expanded(values: np.ndarray) -> np.ndarray:
        result = truth.copy()
        result[indices] = values
        return result

    for record in records:
        fit = record['fit']
        water = np.array([point['water_content'] for point in fit['observations']])
        full = least_squares(
            lambda values, observations=water: (
                vg_curve_and_jacobian(axis, values)[0] - observations
            ),
            truth,
            jac=lambda values: vg_curve_and_jacobian(axis, values)[1],
            bounds=([0, 0.3, 0.01, 1.1], [0.2, 0.8, 1, 4]),
            x_scale='jac',
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
            max_nfev=10000,
        )
        fixed = least_squares(
            lambda values, observations=water: (
                vg_curve_and_jacobian(axis, expanded(values))[0] - observations
            ),
            truth[indices],
            jac=lambda values: vg_curve_and_jacobian(axis, expanded(values))[1][:, indices],
            bounds=([0, 0.01, 1.1], [0.2, 1, 4]),
            x_scale='jac',
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
            max_nfev=10000,
        )
        objectives = [
            attempt['sum_squared_error'] for attempt in fit['attempts'] if attempt['converged']
        ]
        profile = record.get('profile')
        public_fixed = (
            next(
                (
                    point['sum_squared_error']
                    for point in profile['points']
                    if point['fixed_value'] == truth[1]
                ),
                None,
            )
            if profile
            else None
        )
        audits.append(
            {
                'repetition': record['repetition'],
                'public_full_sse': min(objectives) if objectives else None,
                'audit_full_sse': float(full.fun @ full.fun),
                'audit_full_converged': bool(full.success),
                'public_fixed_sse': public_fixed,
                'audit_fixed_sse': float(fixed.fun @ fixed.fun),
                'audit_fixed_converged': bool(fixed.success),
            }
        )
    return {'method': 'analytic_jacobian_truth_initialized_audit_v1', 'records': audits}


def _coverage(covered: int, total: int) -> dict[str, object]:
    if not total:
        return {'status': 'no_evidence'}
    estimate = covered / total
    interval = binomtest(covered, total).proportion_ci(confidence_level=0.95, method='exact')
    return {
        'covered': covered,
        'total': total,
        'estimate': estimate,
        'monte_carlo_standard_error': math.sqrt(estimate * (1 - estimate) / total),
        'simulation_probability_interval': [float(interval.low), float(interval.high)],
        'undercoverage_p_value': float(
            binomtest(covered, total, p=0.95, alternative='less').pvalue
        ),
    }


def large_linear_control(
    axis: np.ndarray, truth: np.ndarray, draws: int, seed: int
) -> dict[str, object]:
    """Vectorized exact fixed-design control with a separate random stream."""
    design = vg_curve_and_jacobian(axis, truth)[1]
    q, r = np.linalg.qr(design, mode='reduced')
    errors = np.random.default_rng(np.random.SeedSequence([seed, 999])).normal(
        size=(draws, len(axis))
    )
    projected = errors @ q
    inverse = np.linalg.solve(r, np.eye(r.shape[0]))
    coefficients = projected @ inverse.T
    residuals = errors - projected @ q.T
    variance = np.sum(residuals**2, axis=1) / (len(axis) - design.shape[1])
    critical = float(t.isf(0.025, len(axis) - design.shape[1]))
    covered = np.abs(coefficients[:, 1]) <= critical * np.sqrt(
        variance * float(inverse[1] @ inverse[1])
    )
    selected = coefficients[:, 1] > 0
    return {
        'generated': draws,
        'all_coverage': _coverage(int(np.sum(covered)), draws),
        'selected_coverage': _coverage(int(np.sum(covered & selected)), int(np.sum(selected))),
    }


def run(plan_path: Path, source: Path, output: Path) -> None:
    plan_bytes, source_bytes = plan_path.read_bytes(), source.read_bytes()
    plan, envelope = json.loads(plan_bytes), json.loads(source_bytes)
    payload = envelope['payload']
    if document_hash(payload) != envelope['sha256'] or payload['cell']['id'] != plan['source_cell']:
        message = 'Original study cell binding failed.'
        raise ValueError(message)
    if (
        plan['nominal_confidence'] != _NOMINAL_CONFIDENCE
        or plan['sigma'] != payload['cell']['sigma']
    ):
        message = 'Follow-up requires the fixed nominal level and original noise scale.'
        raise ValueError(message)
    output.mkdir(parents=True, exist_ok=False)
    directory = Path(__file__).parent
    generator = runpy.run_path(str(directory / 'calibrate.py'))
    axis = np.array(payload['cell']['pressure_kpa'])
    truth = np.array([0.1, 0.3, 0.1, 2])
    original = {
        'paired_counts': paired_counts(payload['records'], axis, truth),
        'optimizer_audit': audit_original(payload['records'], axis, truth),
    }
    (output / 'original-audit.json').write_text(json.dumps(original, indent=2) + '\n')
    totals: Counter[str] = Counter()
    blocks = []
    for block in range(plan['blocks']):
        rng = np.random.default_rng(np.random.SeedSequence([plan['seed'], block]))
        counts, records = generator['simulate_scenario'](
            plan=generator['_plan']('van_genuchten_mualem_v1'),
            truth=0.3,
            axis=axis,
            sigma=plan['sigma'],
            air_entry=10,
            repetitions=plan['repetitions_per_block'],
            rng=rng,
        )
        paired = paired_counts(records, axis, truth)
        totals.update(paired)
        blocks.append({'block': block, 'fit_counts': counts, 'paired_counts': paired})
        (output / f'block-{block}.json').write_text(
            json.dumps({'counts': counts, 'records': records, 'paired_counts': paired}) + '\n'
        )
        sys.stdout.write(
            f'Completed independent block {block + 1}/{plan["blocks"]}: {json.dumps(paired)}\n'
        )
        sys.stdout.flush()
    summary = {
        'plan': plan,
        'plan_sha256': hashlib.sha256(plan_bytes).hexdigest(),
        'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'generator_sha256': hashlib.sha256((directory / 'calibrate.py').read_bytes()).hexdigest(),
        'environment': {
            'python': platform.python_version(),
            **{name: version(name) for name in ('ptfkit-eval', 'numpy', 'scipy')},
        },
        'original_paired_counts': original['paired_counts'],
        'blocks': blocks,
        'totals': dict(totals),
        'primary_conditional_coverage': _coverage(
            totals['nonlinear_covered'], totals['nonlinear_assessed']
        ),
        'linear_conditional_coverage': _coverage(
            totals['linear_selected_covered'], totals['linear_selected']
        ),
        'qualification': 'no_global_coverage_qualification',
        'primary_undercoverage_flag': bool(
            binomtest(
                totals['nonlinear_covered'],
                totals['nonlinear_assessed'],
                p=0.95,
                alternative='less',
            ).pvalue
            < plan['primary_alpha']
        )
        if totals['nonlinear_assessed']
        else None,
        'large_linear_control': large_linear_control(
            axis, truth, plan['linear_control_repetitions'], plan['seed']
        ),
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--plan', type=Path, default=Path(__file__).with_name('boundary-followup-plan.json')
    )
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.plan, arguments.source, arguments.output)
