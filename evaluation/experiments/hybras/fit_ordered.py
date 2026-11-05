"""Descriptive HYBRAS fits with explicit overlapping physical water boxes."""

# ruff: noqa: INP001, T201 - Standalone research experiment with progress reporting.

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path

import ptfkit_eval
from ptfkit_eval import (
    FitParameterRange,
    RetentionFitPlan,
    RetentionSeriesPoint,
    diagnose_fit_uncertainty_support,
    diagnose_retention_series,
    fit_retention_family,
    load_retention_dataset,
)
from ptfkit_eval.artifacts import artifact_value
from ptfkit_eval.documents import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    dataset_bytes = args.dataset.read_bytes()
    document = json.loads(dataset_bytes)
    dataset = load_retention_dataset(document)
    if dataset.sha256 != '7ee2c78e07da2ffe97b987e776620ce275390b1e24939a63552f08f3039fd665':
        parser.error('This protocol requires the exact reviewed HYBRAS positive-head cohort.')
    water = (
        FitParameterRange('theta_r', 0, 0.533, 0.2),
        FitParameterRange('theta_s', 0.1, 0.96, 0.8),
    )
    # VG bounds and initials: HYBRAS manual PDF page 21 (printed page 15).
    # Alpha in cm^-1 is divided by 0.0980665 to obtain kPa^-1.
    boxes = {
        'van_genuchten_mualem_v1': (
            *water,
            FitParameterRange('alpha', 0.00001 / 0.0980665, 0.99999 / 0.0980665, 0.06 / 0.0980665),
            FitParameterRange('n', 1.01, 15, 2),
        ),
        # BC scale/shape boxes are declared computational restrictions, not
        # values attributed to the HYBRAS source or validated soil domains.
        'brooks_corey_v1': (
            *water,
            FitParameterRange('air_entry', 0.001, 1000, 1),
            FitParameterRange('lambda', 0.01, 5, 0.5),
        ),
    }
    plans = [
        RetentionFitPlan(
            family_id=family,
            target=dataset.target,
            parameters=parameters,
            seed=7123,
            minimum_log10_span=2,
            method='bounded_trf_ordered_water_multistart_v1',
        )
        for family, parameters in boxes.items()
    ]
    grouped = defaultdict(list)
    for point in document['observations']:
        if point['review_status'] != 'confirmed' or point['quality_flags']:
            parser.error('Confirmed, unflagged pressure provenance is required.')
        grouped[point['source_id'], point['sample_id']].append(
            RetentionSeriesPoint(point['suction_kpa'], point['value'], point['id'])
        )
    source_root = Path(ptfkit_eval.__file__).parent
    metadata = {
        'experiment': 'hybras_ordered_water_descriptive_fits_v1',
        'dataset_sha256': dataset.sha256,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'environment': {
            'python': platform.python_version(),
            **{name: version(name) for name in ('ptfkit-eval', 'numpy', 'scipy')},
        },
        'implementation_sha256': {
            p.relative_to(source_root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source_root.rglob('*'))
            if p.suffix in {'.py', '.json'}
        },
        'plans': artifact_value(plans),
        'limitations': [
            'Descriptive per-curve fits, not external PTF selection.',
            'No saturation anchors; nonmonotone measured points retained with diagnostics.',
            'VG boxes follow source optimization bounds, not validated applicability ranges.',
            'BC shape/scale bounds are declared computational restrictions.',
            'Local iid Student-t uncertainty is not coverage-qualified for this cohort.',
        ],
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'dataset.json').write_bytes(dataset_bytes)
    (args.output / 'metadata.json').write_bytes(canonical_json(metadata))
    counts = Counter()
    with (args.output / 'fits.jsonl').open('xb') as stream:
        for index, sample in enumerate(document['samples'], start=1):
            points = grouped[sample['source_id'], sample['sample_id']]
            for plan in plans:
                result = fit_retention_family(points, plan=plan)
                record = {
                    'source_id': sample['source_id'],
                    'sample_id': sample['sample_id'],
                    'fit': artifact_value(result),
                    'quality': artifact_value(diagnose_retention_series(points)),
                    'uncertainty_support': artifact_value(diagnose_fit_uncertainty_support(result)),
                }
                stream.write(
                    (
                        json.dumps(
                            record,
                            sort_keys=True,
                            ensure_ascii=False,
                            allow_nan=False,
                            separators=(',', ':'),
                        )
                        + '\n'
                    ).encode('utf-8')
                )
                stream.flush()
                counts[plan.family_id, result.status, result.reason] += 1
            if index % 100 == 0:
                print(f'Completed {index}/{len(document["samples"])} curves', flush=True)
    summary = {
        'dataset_sha256': dataset.sha256,
        'fits': sum(counts.values()),
        'summary': [
            {'family_id': family, 'status': status, 'reason': reason, 'count': count}
            for (family, status, reason), count in sorted(
                counts.items(), key=lambda item: str(item[0])
            )
        ],
        'fits_sha256': hashlib.sha256((args.output / 'fits.jsonl').read_bytes()).hexdigest(),
    }
    (args.output / 'summary.json').write_bytes(canonical_json(summary))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
