"""Regenerate count-only physical diagnostics from reviewed workbook observations."""

# ruff: noqa: INP001 - Standalone reproducible dataset audit.

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from ptfkit_eval import load_dataset_mapping, normalize_retention_workbook
from ptfkit_eval.documents import document_hash
from ptfkit_eval.quality import RetentionSeriesPoint, diagnose_retention_series


if TYPE_CHECKING:
    from ptfkit_eval.normalization import NormalizedRetentionObservation


def audit(workbook: Path, mapping_path: Path) -> dict[str, object]:
    """Report source counts without exporting values or changing observations."""
    mapping = load_dataset_mapping(mapping_path)
    result = normalize_retention_workbook(workbook, mapping)
    groups: dict[tuple[object, ...], list[NormalizedRetentionObservation]] = defaultdict(list)
    for observation in result.observations:
        groups[observation.source, observation.sample_id, observation.sample_number].append(
            observation
        )
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    for observations in groups.values():
        counts = by_source[observations[0].source]
        counts['normalized_sample_count'] += 1
        counts['normalized_observation_count'] += len(observations)
        semantics = {(p.water_quantity, p.water_unit, p.water_basis) for p in observations}
        if semantics == {('gravimetric_water_content', 'mass_fraction', 'dry_soil_mass')}:
            counts['gravimetric_sample_count'] += 1
            continue
        if semantics != {('volumetric_water_content', 'volume_fraction', 'bulk_volume')}:
            counts['unsupported_semantics_sample_count'] += 1
            continue
        counts['volumetric_sample_count'] += 1
        if len({p.pressure_kilopascal for p in observations}) != len(observations):
            counts['duplicate_pressure_sample_count'] += 1
            continue
        quality = diagnose_retention_series(
            [
                RetentionSeriesPoint(
                    p.pressure_kilopascal, p.water_content, f'{p.sheet_name}!{p.row}'
                )
                for p in observations
            ],
            monotonicity_tolerance=0,
        )
        counts['diagnosed_volumetric_sample_count'] += 1
        codes = Counter(item.code for item in quality.diagnostics)
        counts['increasing_water_sample_count'] += bool(codes['increasing_water_with_suction'])
        counts['increasing_water_adjacent_pair_count'] += codes['increasing_water_with_suction']
        counts['outside_volume_bounds_sample_count'] += bool(codes['water_outside_physical_bounds'])
    return {
        'schema_version': 1,
        'dataset_id': mapping.dataset_id,
        'source_filename': mapping.source_filename,
        'workbook_sha256': mapping.source_sha256,
        'mapping_sha256': document_hash(mapping.document),
        'normalized_observation_count': len(result.observations),
        'normalized_sample_count': len(groups),
        'monotonicity_tolerance_volume_fraction': 0,
        'scope': 'noncorrecting_diagnostics_of_reviewed_volumetric_observations',
        'scoring_eligibility': 'not_established_by_this_report',
        'sources': [
            {'source': source, **dict(sorted(counts.items()))}
            for source, counts in sorted(by_source.items())
        ],
    }


def main() -> None:
    """Write metadata and counts only; keep workbook values outside version control."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', required=True, type=Path)
    parser.add_argument('--mapping', type=Path, default=Path(__file__).with_name('meta_v3_3.yaml'))
    parser.add_argument(
        '--output', type=Path, default=Path(__file__).with_name('meta_v3_3.quality-summary.json')
    )
    args = parser.parse_args()
    summary = audit(args.workbook, args.mapping)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )


if __name__ == '__main__':
    main()
