"""Validated portable canonical retention datasets with explicit provenance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from .contracts import TargetSpec
from .documents import (
    EvaluationDocumentError,
    document_hash,
    freeze,
    load_document,
    object_mapping,
    object_records,
    validate_document,
)


if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


@dataclass(frozen=True)
class CanonicalRetentionDataset:
    """Read-only canonical dataset and its semantic-content checksum."""

    document: Mapping[str, object]
    sha256: str

    @property
    def dataset_id(self) -> str:
        """Return the declared dataset identity."""
        return cast('str', self.document['dataset_id'])

    @property
    def target(self) -> TargetSpec:
        """Return the canonical physical target contract."""
        target = object_mapping(self.document['target'])
        return TargetSpec(
            *(
                cast('str', target[key])
                for key in ('quantity', 'unit', 'material_basis', 'denominator_basis')
            )
        )


def load_retention_dataset(
    source: str | Path | Mapping[str, object],
) -> CanonicalRetentionDataset:
    """Validate canonical records without inferring missing scientific semantics."""
    document = load_document(source)
    validate_document(document, 'retention-dataset.schema.json')
    source_files = object_records(document.get('source_files', ()))
    file_ids = {record['id'] for record in source_files}
    if len(file_ids) != len(source_files):
        message = 'Canonical source-file identifiers must be unique.'
        raise EvaluationDocumentError(message)
    samples: set[tuple[object, object]] = set()
    for sample in object_records(document['samples']):
        identity = (sample['source_id'], sample['sample_id'])
        if identity in samples:
            message = f'Duplicate canonical sample: {identity!r}.'
            raise EvaluationDocumentError(message)
        samples.add(identity)
        features: set[object] = set()
        for feature in object_records(sample['features']):
            if feature['id'] in features:
                message = f'Duplicate feature {feature["id"]!r} for sample {identity!r}.'
                raise EvaluationDocumentError(message)
            features.add(feature['id'])
            _validate_origin(feature, document)
            if feature['review_status'] == 'confirmed' and feature.get('blockers'):
                message = 'A confirmed canonical feature cannot retain unresolved blockers.'
                raise EvaluationDocumentError(message)
    identifiers: set[object] = set()
    pressures: set[tuple[object, object, object]] = set()
    for observation in object_records(document['observations']):
        identity = (observation['source_id'], observation['sample_id'])
        point = (*identity, observation['suction_kpa'])
        if identity not in samples:
            message = f'Observation references an unknown sample: {identity!r}.'
            raise EvaluationDocumentError(message)
        if observation['id'] in identifiers or point in pressures:
            message = f'Duplicate canonical observation identity: {observation["id"]!r}.'
            raise EvaluationDocumentError(message)
        identifiers.add(observation['id'])
        pressures.add(point)
        _validate_origin(observation, document)
    return CanonicalRetentionDataset(object_mapping(freeze(document)), document_hash(document))


def _validate_origin(record: Mapping[str, object], document: Mapping[str, object]) -> None:
    if record['origin'] == 'synthetic' and document['kind'] != 'synthetic':
        message = 'Synthetic records cannot be declared as a measured dataset.'
        raise EvaluationDocumentError(message)
    if record['origin'] != 'synthetic':
        file_ids = {source['id'] for source in object_records(document.get('source_files', ()))}
        if record.get('source_file') not in file_ids:
            message = 'Nonsynthetic records require a known checksum-bound source_file identifier.'
            raise EvaluationDocumentError(message)
