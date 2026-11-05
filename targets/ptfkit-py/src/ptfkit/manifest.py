"""Read-only access to the generated ptfkit function manifest."""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import cache
from importlib.resources import files
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias, cast


if TYPE_CHECKING:
    from importlib.abc import Traversable

JsonScalar: TypeAlias = bool | int | float | str | None
JsonValue: TypeAlias = JsonScalar | list['JsonValue'] | dict[str, 'JsonValue']
FrozenJsonValue: TypeAlias = (
    JsonScalar | tuple['FrozenJsonValue', ...] | Mapping[str, 'FrozenJsonValue']
)


def _freeze(value: JsonValue) -> FrozenJsonValue:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@cache
def get_manifest() -> Mapping[str, FrozenJsonValue]:
    """Return the packaged function manifest as recursively immutable data."""
    resource: Traversable = files('ptfkit').joinpath('_manifest.json')
    parsed = cast('JsonValue', json.loads(resource.read_text(encoding='utf-8')))
    frozen = _freeze(parsed)
    if not isinstance(frozen, Mapping):
        message = 'The packaged ptfkit manifest must contain a JSON object.'
        raise TypeError(message)
    return frozen
