"""Local document loading and deterministic JSON for evaluation artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import cast

import yaml
from jsonschema import Draft202012Validator


class EvaluationDocumentError(ValueError):
    """Raised when a local evaluation document violates its persisted contract."""


def plain(value: object) -> object:
    """Copy JSON-compatible structures without retaining mutable aliases."""
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            message = 'Evaluation document keys must be strings.'
            raise EvaluationDocumentError(message)
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [plain(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    message = f'Unsupported or nonfinite evaluation document value: {type(value).__name__}.'
    raise EvaluationDocumentError(message)


def canonical_json(value: object) -> bytes:
    """Encode portable JSON with stable keys, Unicode, and a final newline."""
    return (
        json.dumps(plain(value), sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
        + '\n'
    ).encode('utf-8')


def document_hash(value: object) -> str:
    """Hash the canonical semantic JSON representation of a document."""
    return hashlib.sha256(canonical_json(value)).hexdigest()


def freeze(value: object) -> object:
    """Recursively freeze a validated JSON document."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze(item) for item in value)
    return value


def load_document(source: str | Path | Mapping[str, object]) -> dict[str, object]:
    """Load strict JSON data from a mapping or a local JSON/YAML file."""
    if isinstance(source, Mapping):
        value = plain(source)
    else:
        path = Path(source)
        try:
            contents = path.read_text(encoding='utf-8')
            return parse_document(contents, path.suffix.lower())
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
            message = f'Cannot read evaluation document {path}.'
            raise EvaluationDocumentError(message) from error
        value = plain(value)
    if not isinstance(value, dict):
        message = 'An evaluation document must be a JSON object.'
        raise EvaluationDocumentError(message)
    return cast('dict[str, object]', value)


def parse_document(contents: str, suffix: str) -> dict[str, object]:
    """Parse JSON/YAML with string keys, unique fields, and no cyclic aliases."""
    try:
        if suffix in ('.yaml', '.yml'):
            node = yaml.compose(contents, Loader=yaml.SafeLoader)
            if node is not None:
                _check_yaml_node(node, set())
            value = yaml.safe_load(contents)
        else:
            value = json.loads(contents, object_pairs_hook=_unique_object)
    except (ValueError, yaml.YAMLError) as error:
        if isinstance(error, EvaluationDocumentError):
            raise
        message = 'Cannot parse evaluation document.'
        raise EvaluationDocumentError(message) from error
    return load_document(object_mapping(value))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            message = f'Duplicate evaluation document field: {key!r}.'
            raise EvaluationDocumentError(message)
        result[key] = value
    return result


def _check_yaml_node(node: yaml.Node, active: set[int]) -> None:
    if id(node) in active:
        message = 'Cyclic YAML aliases are not permitted in evaluation documents.'
        raise EvaluationDocumentError(message)
    active.add(id(node))
    if isinstance(node, yaml.MappingNode):
        seen: set[str] = set()
        for key, value in node.value:
            if not isinstance(key, yaml.ScalarNode) or key.tag != 'tag:yaml.org,2002:str':
                message = (
                    'YAML evaluation object keys must be literal strings; merges are unsupported.'
                )
                raise EvaluationDocumentError(message)
            if key.value in seen:
                message = f'Duplicate YAML evaluation field: {key.value!r}.'
                raise EvaluationDocumentError(message)
            seen.add(key.value)
            _check_yaml_node(value, active)
    elif isinstance(node, yaml.SequenceNode):
        for value in node.value:
            _check_yaml_node(value, active)
    active.remove(id(node))


def validate_document(document: Mapping[str, object], schema_name: str) -> None:
    """Validate against a packaged schema without fetching remote resources."""
    schema = json.loads(files('ptfkit_eval').joinpath('schemas', schema_name).read_text('utf-8'))
    diagnostics = sorted(
        Draft202012Validator(schema).iter_errors(plain(document)),
        key=lambda error: str(list(error.absolute_path)),
    )
    if diagnostics:
        details = '; '.join(
            f'{list(error.absolute_path)}: {error.message}' for error in diagnostics
        )
        raise EvaluationDocumentError(details)


def object_mapping(value: object) -> Mapping[str, object]:
    """Require a string-keyed object at a validated document boundary."""
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        message = 'Expected an evaluation document object.'
        raise EvaluationDocumentError(message)
    return cast('Mapping[str, object]', value)


def object_records(value: object) -> tuple[Mapping[str, object], ...]:
    """Require an array of document objects."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        message = 'Expected an evaluation document array.'
        raise EvaluationDocumentError(message)
    return tuple(object_mapping(item) for item in value)
