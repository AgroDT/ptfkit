"""Checksum-bound dataset mapping contracts."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import TypeAlias, TypeGuard, cast

import yaml
from jsonschema import Draft202012Validator


JsonScalar: TypeAlias = bool | int | float | str | None
JsonValue: TypeAlias = JsonScalar | list['JsonValue'] | dict[str, 'JsonValue']


class DatasetMappingLoadError(ValueError):
    """Raised when a dataset mapping or its inventory cannot be read."""


@dataclass(frozen=True)
class DatasetMappingDiagnostic:
    """One independently actionable dataset-mapping problem."""

    path: str
    code: str
    message: str


class DatasetMappingValidationError(ValueError):
    """Raised when a dataset mapping violates its structural or inventory contract."""

    def __init__(self, diagnostics: Sequence[DatasetMappingDiagnostic]) -> None:
        """Preserve all independent diagnostics and render a compact summary."""
        self.diagnostics = tuple(diagnostics)
        summary = '; '.join(
            f'{diagnostic.path}: {diagnostic.message}' for diagnostic in self.diagnostics
        )
        super().__init__(summary)


@dataclass(frozen=True)
class DatasetMapping:
    """Validated mapping bound to one exact workbook inventory."""

    dataset_id: str
    status: str
    source_filename: str
    source_sha256: str
    document: Mapping[str, object]
    inventory: Mapping[str, object]
    retention_profile: Mapping[str, object]


def load_dataset_mapping(
    source: str | Path | Mapping[str, object],
    *,
    inventory: str | Path | Mapping[str, object] | None = None,
    retention_profile: str | Path | Mapping[str, object] | None = None,
) -> DatasetMapping:
    """Load a mapping and verify its claims against a structural inventory."""
    document, mapping_path = _load_mapping_document(source)
    diagnostics = _schema_diagnostics(document)
    if diagnostics:
        raise DatasetMappingValidationError(diagnostics)

    root = _mapping(document)
    source_contract = _mapping(root['source'])
    inventory_document = _load_inventory_document(
        inventory,
        mapping_path=mapping_path,
        inventory_reference=_string(source_contract['inventory']),
    )
    profile_document = _load_retention_profile_document(
        retention_profile,
        mapping_path=mapping_path,
        profile_reference=_string(source_contract['retention_profile']),
    )
    diagnostics.extend(_inventory_diagnostics(root, inventory_document))
    diagnostics.extend(_retention_profile_diagnostics(root, profile_document))
    diagnostics.extend(_semantic_diagnostics(root))
    if diagnostics:
        raise DatasetMappingValidationError(diagnostics)

    dataset = _mapping(root['dataset'])
    return DatasetMapping(
        dataset_id=_string(dataset['id']),
        status=_string(dataset['status']),
        source_filename=_string(source_contract['filename']),
        source_sha256=_string(source_contract['sha256']),
        document=cast('Mapping[str, object]', _freeze(root)),
        inventory=cast('Mapping[str, object]', _freeze(inventory_document)),
        retention_profile=cast('Mapping[str, object]', _freeze(profile_document)),
    )


def _load_mapping_document(
    source: str | Path | Mapping[str, object],
) -> tuple[JsonValue, Path | None]:
    if isinstance(source, Mapping):
        return _to_json(source, label='Dataset mapping'), None
    path = Path(source)
    return _load_serialized(path, label='dataset mapping'), path


def _load_inventory_document(
    source: str | Path | Mapping[str, object] | None,
    *,
    mapping_path: Path | None,
    inventory_reference: str,
) -> Mapping[str, object]:
    if source is None:
        if mapping_path is None:
            message = 'An inventory must be supplied when loading a mapping object.'
            raise DatasetMappingLoadError(message)
        source = mapping_path.parent / inventory_reference
    if isinstance(source, Mapping):
        value = _to_json(source, label='Workbook inventory')
    else:
        value = _load_serialized(Path(source), label='workbook inventory')
    if not isinstance(value, Mapping):
        message = 'Workbook inventory must contain a JSON object.'
        raise DatasetMappingLoadError(message)
    return cast('Mapping[str, object]', value)


def _load_retention_profile_document(
    source: str | Path | Mapping[str, object] | None,
    *,
    mapping_path: Path | None,
    profile_reference: str,
) -> Mapping[str, object]:
    if source is None:
        if mapping_path is None:
            message = 'A retention profile must be supplied when loading a mapping object.'
            raise DatasetMappingLoadError(message)
        source = mapping_path.parent / profile_reference
    if isinstance(source, Mapping):
        value = _to_json(source, label='Retention profile')
    else:
        value = _load_serialized(Path(source), label='retention profile')
    if not isinstance(value, Mapping):
        message = 'Retention profile must contain a JSON object.'
        raise DatasetMappingLoadError(message)
    return cast('Mapping[str, object]', value)


def _load_serialized(path: Path, *, label: str) -> JsonValue:
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as error:
        message = f'Cannot read {label} {path}: {error}'
        raise DatasetMappingLoadError(message) from error
    try:
        if path.suffix.casefold() == '.json':
            loaded: object = json.loads(text)
        elif path.suffix.casefold() in ('.yaml', '.yml'):
            loaded = yaml.safe_load(text)
        else:
            message = f'Unsupported {label} extension {path.suffix!r}; use JSON or YAML.'
            raise DatasetMappingLoadError(message)
    except (json.JSONDecodeError, yaml.YAMLError) as error:
        message = f'Cannot parse {label} {path}: {error}'
        raise DatasetMappingLoadError(message) from error
    return _to_json(loaded, label=label.title())


def _to_json(value: object, *, label: str) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                message = f'{label} object keys must be strings.'
                raise DatasetMappingLoadError(message)
            result[key] = _to_json(item, label=label)
        return result
    if _is_sequence(value):
        return [_to_json(item, label=label) for item in value]
    message = f'Unsupported {label.lower()} value type: {type(value).__name__}.'
    raise DatasetMappingLoadError(message)


@cache
def _schema() -> Mapping[str, object]:
    resource = files('ptfkit_eval').joinpath('schemas/dataset-mapping.schema.json')
    loaded: object = json.loads(resource.read_text(encoding='utf-8'))
    return _mapping(_to_json(loaded, label='Dataset mapping schema'))


def _schema_diagnostics(document: JsonValue) -> list[DatasetMappingDiagnostic]:
    validator = Draft202012Validator(_schema())
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    return [
        DatasetMappingDiagnostic(
            _json_path(tuple(error.absolute_path)),
            f'schema.{error.validator}',
            error.message,
        )
        for error in errors
    ]


def _inventory_diagnostics(
    mapping: Mapping[str, object], inventory: Mapping[str, object]
) -> list[DatasetMappingDiagnostic]:
    diagnostics = _inventory_source_diagnostics(mapping, inventory)
    diagnostics.extend(_worksheet_inventory_diagnostics(mapping, inventory))
    return diagnostics


def _inventory_source_diagnostics(
    mapping: Mapping[str, object], inventory: Mapping[str, object]
) -> list[DatasetMappingDiagnostic]:
    diagnostics: list[DatasetMappingDiagnostic] = []
    source = _mapping(mapping['source'])
    for field in ('filename', 'sha256', 'size_bytes'):
        inventory_field = 'source_filename' if field == 'filename' else field
        if source[field] != inventory.get(inventory_field):
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'$.source.{field}',
                    'inventory.source_mismatch',
                    f'Mapping value does not match inventory field {inventory_field!r}.',
                )
            )
    return diagnostics


def _worksheet_inventory_diagnostics(
    mapping: Mapping[str, object], inventory: Mapping[str, object]
) -> list[DatasetMappingDiagnostic]:
    diagnostics: list[DatasetMappingDiagnostic] = []

    inventory_sheets_value = inventory.get('sheets')
    if not _is_sequence(inventory_sheets_value):
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$inventory.sheets',
                'inventory.invalid',
                'Inventory sheets must be an array.',
            )
        )
        return diagnostics
    inventory_sheets = {
        str(sheet.get('title')): sheet
        for value in inventory_sheets_value
        if isinstance(value, Mapping)
        for sheet in [cast('Mapping[str, object]', value)]
    }
    mapped_sheets = _sequence(mapping['worksheets'])
    mapped_names = {
        _string(_mapping(value)['name']) for value in mapped_sheets if isinstance(value, Mapping)
    }
    missing = sorted(set(inventory_sheets) - mapped_names)
    extra = sorted(mapped_names - set(inventory_sheets))
    diagnostics.extend(
        DatasetMappingDiagnostic(
            '$.worksheets',
            'inventory.unmapped_sheet',
            f'Inventory worksheet {name!r} has no mapping.',
        )
        for name in missing
    )
    diagnostics.extend(
        DatasetMappingDiagnostic(
            '$.worksheets',
            'inventory.unknown_sheet',
            f'Mapped worksheet {name!r} is absent from the inventory.',
        )
        for name in extra
    )

    for index, value in enumerate(mapped_sheets):
        worksheet = _mapping(value)
        name = _string(worksheet['name'])
        inventory_sheet = inventory_sheets.get(name)
        if inventory_sheet is None:
            continue
        if worksheet['dimension'] != inventory_sheet.get('declared_dimension'):
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'$.worksheets[{index}].dimension',
                    'inventory.dimension_mismatch',
                    'Declared dimension does not match the workbook inventory.',
                )
            )
        expected_headers = tuple(
            tuple(_integer(row) for row in _sequence(block))
            for block in _sequence(worksheet['header_rows'])
        )
        actual_headers = tuple(
            tuple(_integer(row) for row in _sequence(_mapping(block)['rows']))
            for block in _sequence(inventory_sheet.get('header_blocks', []))
        )
        if expected_headers != actual_headers:
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'$.worksheets[{index}].header_rows',
                    'inventory.header_mismatch',
                    'Header blocks do not match the workbook inventory.',
                )
            )
        data_rows = _mapping(worksheet['data_rows'])
        max_row = inventory_sheet.get('max_row')
        if isinstance(max_row, int) and _integer(data_rows['last']) > max_row:
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'$.worksheets[{index}].data_rows.last',
                    'inventory.row_out_of_bounds',
                    f'Data row exceeds inventory maximum {max_row}.',
                )
            )
    return diagnostics


def _retention_profile_diagnostics(
    mapping: Mapping[str, object], profile: Mapping[str, object]
) -> list[DatasetMappingDiagnostic]:
    diagnostics = _retention_profile_contract_diagnostics(mapping, profile)
    diagnostics.extend(_retention_profile_count_diagnostics(profile))
    return diagnostics


def _retention_profile_contract_diagnostics(
    mapping: Mapping[str, object], profile: Mapping[str, object]
) -> list[DatasetMappingDiagnostic]:
    diagnostics: list[DatasetMappingDiagnostic] = []
    source = _mapping(mapping['source'])
    for field in ('source_filename', 'sha256'):
        mapping_field = 'filename' if field == 'source_filename' else field
        if profile.get(field) != source[mapping_field]:
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'$retention_profile.{field}',
                    'profile.source_mismatch',
                    f'Profile value does not match mapping source field {mapping_field!r}.',
                )
            )
    if profile.get('schema_version') != 1:
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$retention_profile.schema_version',
                'profile.unsupported_schema',
                'Retention profile schema_version must be 1.',
            )
        )

    retention_sheets = {
        _string(worksheet['name'])
        for value in _sequence(mapping['worksheets'])
        for worksheet in [_mapping(value)]
        if worksheet['kind'] == 'long_retention_and_parameters'
    }
    if profile.get('sheet_name') not in retention_sheets:
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$retention_profile.sheet_name',
                'profile.unknown_sheet',
                'Profile sheet is not the mapped long-retention worksheet.',
            )
        )
    return diagnostics


def _retention_profile_count_diagnostics(
    profile: Mapping[str, object],
) -> list[DatasetMappingDiagnostic]:
    diagnostics: list[DatasetMappingDiagnostic] = []

    sources_value = profile.get('sources')
    if not _is_sequence(sources_value):
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$retention_profile.sources',
                'profile.invalid',
                'Retention profile sources must be an array.',
            )
        )
        return diagnostics
    sources = tuple(value for value in sources_value if isinstance(value, Mapping))
    if len(sources) != len(sources_value):
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$retention_profile.sources',
                'profile.invalid',
                'Every retention profile source must be an object.',
            )
        )
        return diagnostics
    if profile.get('source_count') != len(sources):
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$retention_profile.source_count',
                'profile.count_mismatch',
                'source_count does not equal the number of source profiles.',
            )
        )

    labels = [value.get('source') for value in sources]
    if len(labels) != len({_hashable_label(value) for value in labels}):
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$retention_profile.sources',
                'profile.duplicate_source',
                'Retention profile contains duplicate source labels.',
            )
        )
    for field in ('observation_count', 'fitted_parameter_count', 'unclassified_count'):
        total = _sum_integer_field(sources, field)
        if total is None or profile.get(field) != total:
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'$retention_profile.{field}',
                    'profile.count_mismatch',
                    f'{field} does not equal the sum of source profiles.',
                )
            )
    component_counts = (
        profile.get('observation_count'),
        profile.get('fitted_parameter_count'),
        profile.get('unclassified_count'),
        profile.get('missing_source_count'),
    )
    if all(isinstance(value, int) and not isinstance(value, bool) for value in component_counts):
        total_data_rows = sum(cast('tuple[int, int, int, int]', component_counts))
        if profile.get('total_data_rows') != total_data_rows:
            diagnostics.append(
                DatasetMappingDiagnostic(
                    '$retention_profile.total_data_rows',
                    'profile.count_mismatch',
                    'total_data_rows does not equal classified and missing-source rows.',
                )
            )
    else:
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$retention_profile.total_data_rows',
                'profile.invalid',
                'Retention profile counts must be integers.',
            )
        )
    return diagnostics


def _sum_integer_field(values: Sequence[Mapping[object, object]], field: str) -> int | None:
    selected = [value.get(field) for value in values]
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in selected):
        return None
    return sum(cast('list[int]', selected))


def _hashable_label(value: object) -> str:
    return f'{type(value).__name__}:{value!r}'


def _semantic_diagnostics(mapping: Mapping[str, object]) -> list[DatasetMappingDiagnostic]:
    diagnostics: list[DatasetMappingDiagnostic] = []
    worksheets = _sequence(mapping['worksheets'])
    _duplicates(
        diagnostics,
        (_string(_mapping(value)['id']) for value in worksheets),
        '$.worksheets',
        'mapping.duplicate_worksheet_id',
        'worksheet id',
    )
    _duplicates(
        diagnostics,
        (_string(_mapping(value)['name']) for value in worksheets),
        '$.worksheets',
        'mapping.duplicate_worksheet_name',
        'worksheet name',
    )
    blockers = _sequence(mapping['blockers'])
    _duplicates(
        diagnostics,
        (_string(_mapping(value)['id']) for value in blockers),
        '$.blockers',
        'mapping.duplicate_blocker_id',
        'blocker id',
    )
    encodings = _sequence(mapping['encodings'])
    _duplicates(
        diagnostics,
        (_string(_mapping(value)['id']) for value in encodings),
        '$.encodings',
        'mapping.duplicate_encoding_id',
        'encoding id',
    )
    diagnostics.extend(_reference_diagnostics(mapping))
    dataset = _mapping(mapping['dataset'])
    status = _string(dataset['status'])
    if status == 'draft_blocked' and not blockers:
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$.blockers',
                'mapping.missing_blockers',
                'A draft_blocked mapping must declare at least one blocker.',
            )
        )
    if status == 'active' and blockers:
        diagnostics.append(
            DatasetMappingDiagnostic(
                '$.blockers',
                'mapping.active_with_blockers',
                'An active mapping cannot retain blockers.',
            )
        )
    return diagnostics


def _reference_diagnostics(
    mapping: Mapping[str, object],
) -> list[DatasetMappingDiagnostic]:
    diagnostics: list[DatasetMappingDiagnostic] = []
    worksheets = _sequence(mapping['worksheets'])
    worksheet_names = {_string(_mapping(value)['name']) for value in worksheets}
    for index, value in enumerate(worksheets):
        worksheet = _mapping(value)
        data_rows = _mapping(worksheet['data_rows'])
        if _integer(data_rows['first']) > _integer(data_rows['last']):
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'$.worksheets[{index}].data_rows',
                    'mapping.invalid_row_range',
                    'Data-row range starts after it ends.',
                )
            )

    identity = _mapping(mapping['identity'])
    _check_worksheet_references(
        diagnostics,
        _sequence(identity['source_aliases']),
        '$.identity.source_aliases',
        worksheet_names,
    )
    _check_worksheet_references(
        diagnostics,
        _sequence(mapping['encodings']),
        '$.encodings',
        worksheet_names,
    )
    formula_policy = _mapping(mapping['formula_policy'])
    _check_worksheet_references(
        diagnostics,
        _sequence(formula_policy['derived_columns']),
        '$.formula_policy.derived_columns',
        worksheet_names,
    )

    blocker_ids = {_string(_mapping(value)['id']) for value in _sequence(mapping['blockers'])}
    for index, value in enumerate(_sequence(mapping['encodings'])):
        encoding = _mapping(value)
        for blocker in _sequence(encoding.get('blockers', [])):
            blocker_id = _string(blocker)
            if blocker_id not in blocker_ids:
                diagnostics.append(
                    DatasetMappingDiagnostic(
                        f'$.encodings[{index}].blockers',
                        'mapping.unknown_blocker',
                        f'Encoding references unknown blocker {blocker_id!r}.',
                    )
                )
    return diagnostics


def _check_worksheet_references(
    diagnostics: list[DatasetMappingDiagnostic],
    values: Sequence[object],
    path: str,
    worksheet_names: set[str],
) -> None:
    for index, value in enumerate(values):
        worksheet = _string(_mapping(value)['worksheet'])
        if worksheet not in worksheet_names:
            diagnostics.append(
                DatasetMappingDiagnostic(
                    f'{path}[{index}].worksheet',
                    'mapping.unknown_worksheet',
                    f'Reference names unknown worksheet {worksheet!r}.',
                )
            )


def _duplicates(
    diagnostics: list[DatasetMappingDiagnostic],
    values: Iterable[str],
    path: str,
    code: str,
    label: str,
) -> None:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    diagnostics.extend(
        DatasetMappingDiagnostic(path, code, f'Duplicate {label} {value!r}.')
        for value in sorted(repeated)
    )


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if _is_sequence(value):
        return tuple(_freeze(item) for item in value)
    return value


def _json_path(parts: Sequence[object]) -> str:
    path = '$'
    for part in parts:
        path += f'[{part}]' if isinstance(part, int) else f'.{part}'
    return path


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        message = f'Expected an object after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return cast('Mapping[str, object]', value)


def _sequence(value: object) -> Sequence[object]:
    if not _is_sequence(value):
        message = f'Expected an array after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return value


def _is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _string(value: object) -> str:
    if not isinstance(value, str):
        message = f'Expected a string after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return value


def _integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        message = f'Expected an integer after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return value
