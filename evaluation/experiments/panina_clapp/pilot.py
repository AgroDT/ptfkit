"""Reproduce the source-reviewed descriptive pilot directly from the private workbook."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import runpy
from pathlib import Path

from ptfkit_eval import (
    export_normalized_retention_dataset,
    load_dataset_mapping,
    normalize_retention_workbook,
    write_retention_normalization_summary,
)
from ptfkit_eval.documents import canonical_json


def pilot(workbook: Path, paper: Path, output: Path) -> None:
    """Reuse normalization, fixed-PTF evaluation and registered reference fitting policies."""
    root = Path(__file__).resolve().parents[3]
    experiment = Path(__file__).resolve().parent
    review = root / 'evaluation/datasets/meta_v3_3.clapp-source-review.json'
    mapping = load_dataset_mapping(root / 'evaluation/datasets/meta_v3_3.yaml')
    normalized = normalize_retention_workbook(workbook, mapping)
    exported = export_normalized_retention_dataset(
        normalized, dataset_id='meta-v3-3-reviewed-volume', material_basis='unspecified'
    )
    output.mkdir(parents=True, exist_ok=False)
    dataset = output / 'canonical.json'
    dataset.write_bytes(canonical_json(exported.dataset.document))
    write_retention_normalization_summary(normalized, output / 'normalization.json')
    artifacts = runpy.run_path(str(experiment / 'run.py'))['run'](
        dataset, review, paper, output / 'clapp'
    )
    fits = output / 'approximation-fits.json'
    runpy.run_path(str(experiment.parent / 'measured_retention/fit.py'))['main'](
        [str(artifacts / 'dataset.json'), '--output', str(fits)]
    )
    runpy.run_path(str(experiment / 'report.py'))['publish'](
        artifacts, review, output / 'decision', fits_path=fits
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--paper', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    pilot(arguments.workbook, arguments.paper, arguments.output)
