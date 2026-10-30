"""Separate water-content exports from reviewed workbook normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .canonical import CanonicalRetentionDataset, load_retention_dataset
from .documents import EvaluationDocumentError
from .water import canonical_water_contract


if TYPE_CHECKING:
    from .normalization import RetentionNormalizationResult


@dataclass(frozen=True)
class RetentionDatasetExport:
    """One canonical physical target and explicit omitted normalized row identities."""

    dataset: CanonicalRetentionDataset
    omitted_gravimetric_rows: tuple[int, ...]
    omitted_volumetric_rows: tuple[int, ...] = ()


def export_normalized_retention_dataset(
    result: RetentionNormalizationResult,
    *,
    dataset_id: str,
    material_basis: str,
    water_quantity: str = 'volumetric_water_content',
) -> RetentionDatasetExport:
    """Preserve one reviewed water quantity without inferring predictors or profiles.

    The caller declares the target material basis; use ``unspecified`` when it
    has not been reviewed. The other quantity remains explicitly accounted
    for and is never converted using density. Duplicate sample/
    pressure pairs fail canonical validation instead of being averaged.
    """
    water_unit, water_basis = canonical_water_contract(water_quantity)
    if len(result.observations) != result.summary.normalized_observation_count:
        message = 'Export requires consistent normalized observation accounting.'
        raise EvaluationDocumentError(message)
    samples: dict[tuple[str, str], dict[str, object]] = {}
    observations: list[dict[str, object]] = []
    omitted: dict[str, list[int]] = {
        'volumetric_water_content': [],
        'gravimetric_water_content': [],
    }
    for point in result.observations:
        if point.source_filename != result.summary.source_filename:
            message = 'Export observation does not belong to the normalized source file.'
            raise EvaluationDocumentError(message)
        canonical_water_contract(point.water_quantity)
        if point.water_quantity != water_quantity:
            omitted[point.water_quantity].append(point.row)
            continue
        if (
            point.water_unit != water_unit
            or point.pressure_unit != 'kilopascal'
            or point.pressure_convention != 'magnitude'
            or point.pressure_quantity != 'matric_potential'
            or point.water_basis != water_basis
        ):
            message = (
                'Export requires canonical volumetric or gravimetric water '
                'with matching units/basis and suction magnitudes.'
            )
            raise EvaluationDocumentError(message)
        if not isinstance(point.sample_id, str) or not point.sample_id.strip():
            message = 'Export requires a reviewed string sample identity.'
            raise EvaluationDocumentError(message)
        identity = (point.source, point.sample_id)
        samples.setdefault(
            identity,
            {
                'source_id': point.source,
                'sample_id': point.sample_id,
                'profile_id': None,
                'features': [],
            },
        )
        observations.append(
            {
                'id': f'workbook-row-{point.row}',
                'source_id': point.source,
                'sample_id': point.sample_id,
                'suction_kpa': point.pressure_kilopascal,
                'value': point.water_content,
                'origin': 'measured',
                'review_status': 'confirmed',
                'quality_flags': [],
                'source_file': 'workbook',
                'source_cells': list(point.source_cells),
            }
        )
    dataset = load_retention_dataset(
        {
            'schema_version': 1 if water_quantity == 'volumetric_water_content' else 2,
            'dataset_id': dataset_id,
            'kind': 'measured',
            'target': {
                'quantity': water_quantity,
                'unit': water_unit,
                'material_basis': material_basis,
                'denominator_basis': water_basis,
            },
            'method': 'Reviewed workbook normalization; physical quality assessed separately.',
            'source_files': [
                {
                    'id': 'workbook',
                    'filename': result.summary.source_filename,
                    'sha256': result.summary.sha256,
                }
            ],
            'samples': [samples[key] for key in sorted(samples)],
            'observations': observations,
        }
    )
    return RetentionDatasetExport(
        dataset,
        tuple(omitted['gravimetric_water_content']),
        tuple(omitted['volumetric_water_content']),
    )
