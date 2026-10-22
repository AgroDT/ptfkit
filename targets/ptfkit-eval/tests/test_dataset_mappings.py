import copy
import json
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
import yaml
from jsonschema import Draft202012Validator

from ptfkit_eval import DatasetMappingValidationError, load_dataset_mapping


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MAPPING_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.yaml'
INVENTORY_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.inventory.json'
PROFILE_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.retention-profile.json'


def _mapping_document() -> dict[str, object]:
    loaded = yaml.safe_load(MAPPING_PATH.read_text(encoding='utf-8'))
    assert isinstance(loaded, dict)
    return loaded


def _inventory_document() -> dict[str, object]:
    loaded = json.loads(INVENTORY_PATH.read_text(encoding='utf-8'))
    assert isinstance(loaded, dict)
    return loaded


def _profile_document() -> dict[str, object]:
    loaded = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
    assert isinstance(loaded, dict)
    return loaded


def test_dataset_mapping_schema_is_valid():
    resource = files('ptfkit_eval').joinpath('schemas/dataset-mapping.schema.json')
    schema = json.loads(resource.read_text(encoding='utf-8'))

    Draft202012Validator.check_schema(schema)


def test_meta_mapping_is_inventory_bound_and_keeps_ambiguities_explicit():
    mapping = load_dataset_mapping(MAPPING_PATH)

    assert mapping.dataset_id == 'meta_v3_3'
    assert mapping.status == 'draft_blocked'
    assert mapping.source_sha256 == (
        '1322bf65b1ca0130085015209858a443d1ee82a7e2ae69232321cd8ede361e68'
    )

    encoding_values = cast('Sequence[Mapping[str, object]]', mapping.document['encodings'])
    encodings = {str(encoding['id']): encoding for encoding in encoding_values}
    assert encodings['water_w']['status'] == 'blocked'
    water_measurement = cast('Mapping[str, object]', encodings['water_w']['measurement'])
    assert water_measurement['unit'] is None
    assert encodings['pressure_mpa_label']['status'] == 'blocked'
    assert encodings['fitted_vgn']['status'] == 'confirmed'
    assert mapping.document['reviewed_corrections'] == ()

    with pytest.raises(TypeError):
        cast('dict[str, object]', mapping.document)['dataset'] = {}


def test_rejects_checksum_drift_in_the_inventory():
    mapping = _mapping_document()
    inventory = _inventory_document()
    inventory['sha256'] = '0' * 64

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(mapping, inventory=inventory, retention_profile=_profile_document())

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        ('$.source.sha256', 'inventory.source_mismatch')
    ]


def test_rejects_an_unmapped_workbook_sheet():
    mapping = _mapping_document()
    worksheets = mapping['worksheets']
    assert isinstance(worksheets, list)
    mapping['worksheets'] = worksheets[:-1]

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert any(
        item.code == 'inventory.unmapped_sheet' and 'диссертации_ссылки' in item.message
        for item in captured.value.diagnostics
    )


def test_active_mapping_cannot_retain_scientific_blockers():
    mapping = copy.deepcopy(_mapping_document())
    dataset = mapping['dataset']
    assert isinstance(dataset, dict)
    dataset['status'] = 'active'

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert any(item.code == 'mapping.active_with_blockers' for item in captured.value.diagnostics)


def test_rejects_an_encoding_reference_to_an_unknown_blocker():
    mapping = _mapping_document()
    encodings = mapping['encodings']
    assert isinstance(encodings, list)
    first = encodings[0]
    assert isinstance(first, dict)
    first['blockers'] = ['invented_blocker']

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        ('$.encodings[0].blockers', 'mapping.unknown_blocker')
    ]


def test_rejects_retention_profile_checksum_drift():
    profile = _profile_document()
    profile['sha256'] = '0' * 64

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            _mapping_document(),
            inventory=_inventory_document(),
            retention_profile=profile,
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        ('$retention_profile.sha256', 'profile.source_mismatch')
    ]
