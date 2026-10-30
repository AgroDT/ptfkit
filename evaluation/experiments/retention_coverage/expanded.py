"""Execute and resume a checksum-bound, prespecified nonlinear coverage study."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import runpy
import sys
from dataclasses import replace
from importlib.metadata import version
from itertools import pairwise
from pathlib import Path

import numpy as np
import ptfkit_eval
from ptfkit_eval.documents import canonical_json, document_hash
from scipy.stats import binomtest


_SATURATION_BOUNDS = (0.3, 0.8)
_AIR_ENTRY_BOUNDS = (1, 30)
_MINIMUM_POINTS = 5


def _implementation_hash() -> str:
    root = Path(ptfkit_eval.__file__).parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*.py')):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def coverage_statistics(covered: int, assessed: int, comparisons: int) -> dict[str, object]:
    """Inference concerns the simulation probability, conditional on assessment."""
    if not 0 <= covered <= assessed or comparisons < 1:
        message = 'Coverage counts and comparison count are invalid.'
        raise ValueError(message)
    if not assessed:
        return {'status': 'no_assessed_regions'}
    test = binomtest(covered, assessed, p=0.95, alternative='less')
    interval = binomtest(covered, assessed).proportion_ci(confidence_level=0.95, method='exact')
    rate = covered / assessed
    return {
        'status': 'estimated',
        'covered': covered,
        'assessed': assessed,
        'conditional_coverage': rate,
        'monte_carlo_standard_error': math.sqrt(rate * (1 - rate) / assessed),
        'simulation_probability_interval': [float(interval.low), float(interval.high)],
        'undercoverage_p_value': float(test.pvalue),
        'familywise_test_threshold': 0.05 / comparisons,
        'undercoverage_flag': bool(test.pvalue < 0.05 / comparisons),
        'adequacy_established': False,
    }


def _write_immutable(path: Path, document: object) -> None:
    raw = canonical_json(document)
    if path.exists():
        if path.read_bytes() != raw:
            message = f'Existing artifact differs: {path.name}.'
            raise ValueError(message)
    else:
        with path.open('xb') as stream:
            stream.write(raw)


def _validate_plan(plan: dict) -> None:
    if (
        plan['schema_version'],
        plan['nominal_confidence'],
        plan['familywise_alpha'],
        plan['brooks_corey_policy'],
    ) != (1, 0.95, 0.05, 'brooks_corey_interval_solves_v1'):
        message = 'Unsupported study protocol.'
        raise ValueError(message)
    cells = plan['cells']
    if (
        not cells
        or len({cell['id'] for cell in cells}) != len(cells)
        or plan['comparison_count'] != len(cells)
    ):
        message = 'Study cells must have unique identifiers and a fixed comparison count.'
        raise ValueError(message)
    for cell in cells:
        axis = cell['pressure_kpa']
        if (
            Path(cell['id']).name != cell['id']
            or '/' in cell['id']
            or '\\' in cell['id']
            or not isinstance(cell['repetitions'], int)
            or isinstance(cell['repetitions'], bool)
            or cell['repetitions'] < 1
            or not _SATURATION_BOUNDS[0] <= cell['truth'] <= _SATURATION_BOUNDS[1]
            or not _AIR_ENTRY_BOUNDS[0] <= cell['air_entry'] <= _AIR_ENTRY_BOUNDS[1]
            or not math.isfinite(cell['sigma'])
            or cell['sigma'] <= 0
            or len(axis) < _MINIMUM_POINTS
            or any(not math.isfinite(value) or value < 0 for value in axis)
            or any(left >= right for left, right in pairwise(axis))
        ):
            message = 'Invalid study cell.'
            raise ValueError(message)


def run_study(plan_path: Path, output: Path) -> dict[str, object]:
    """Resume only complete cells matching the exact protocol and implementation."""
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    _validate_plan(plan)
    generator_path = Path(__file__).with_name('calibrate.py')
    namespace = runpy.run_path(str(generator_path))
    for cell in plan['cells']:
        namespace['_plan'](cell['family'])
    context = {
        'study_sha256': hashlib.sha256(plan_bytes).hexdigest(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'generator_sha256': hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        'evaluation_implementation_sha256': _implementation_hash(),
        'python': platform.python_version(),
        **{name: version(name) for name in ('ptfkit-eval', 'numpy', 'scipy')},
    }
    output.mkdir(parents=True, exist_ok=True)
    _write_immutable(output / 'study-plan.json', plan)
    _write_immutable(output / 'context.json', context)
    summaries = []
    for index, cell in enumerate(plan['cells']):
        path = output / f'{cell["id"]}.json'
        if path.exists():
            payload = _read_cell(path, cell, context)
        else:
            payload = _run_cell(cell, context, plan['seed'], namespace)
            _write_immutable(path, {'payload': payload, 'sha256': document_hash(payload)})
        counts = payload['counts']
        summaries.append(
            {
                'cell': cell,
                'counts': counts,
                'coverage': coverage_statistics(
                    counts.get('covered', 0), counts.get('assessed', 0), plan['comparison_count']
                ),
            }
        )
        sys.stdout.write(f'{index + 1}/{len(plan["cells"])} {cell["id"]} {json.dumps(counts)}\n')
        sys.stdout.flush()
    summary = {'context': context, 'study_id': plan['study_id'], 'summaries': summaries}
    _write_immutable(output / 'summary.json', summary)
    return summary


def _read_cell(path: Path, cell: dict, context: dict) -> dict:
    envelope = json.loads(path.read_bytes())
    payload = envelope['payload']
    if (
        document_hash(payload) != envelope['sha256']
        or payload['context'] != context
        or payload['cell'] != cell
        or payload['counts']['generated'] != cell['repetitions']
        or len(payload['records']) != cell['repetitions']
    ):
        message = f'Invalid or incompatible resumed cell: {path.name}.'
        raise ValueError(message)
    return payload


def _run_cell(cell: dict, context: dict, seed: int, namespace: dict) -> dict:
    cell_seed = int.from_bytes(hashlib.sha256(cell['id'].encode()).digest()[:8], 'big')
    rng = np.random.default_rng(np.random.SeedSequence([seed, cell_seed]))
    plan = namespace['_plan'](cell['family'])
    if cell['family'] == 'brooks_corey_v1':
        plan = replace(plan, restart_policy='brooks_corey_interval_solves_v1')
    counts, records = namespace['simulate_scenario'](
        plan=plan,
        truth=cell['truth'],
        axis=np.array(cell['pressure_kpa']),
        sigma=cell['sigma'],
        air_entry=cell['air_entry'],
        repetitions=cell['repetitions'],
        rng=rng,
    )
    return {'cell': cell, 'context': context, 'counts': counts, 'records': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=Path(__file__).with_name('expanded-plan.json'))
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    run_study(arguments.plan, arguments.output)
