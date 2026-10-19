from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module

import pytest

from ptfkit import get_manifest


def test_manifest_is_packaged_read_only_and_matches_public_callables():
    manifest = get_manifest()

    assert manifest['schema_version'] == 1
    coverage = manifest['coverage']
    assert isinstance(coverage, Mapping)
    assert coverage['implemented_functions'] == (
        coverage['manifest_functions'] + len(coverage['omitted_functions'])
    )
    assert coverage['manifest_functions'] > 0

    functions = manifest['functions']
    assert len(functions) == coverage['manifest_functions']
    for function in functions:
        module = import_module(function['module'])
        assert callable(getattr(module, function['callable']))

    with pytest.raises(TypeError):
        manifest['schema_version'] = 2
    with pytest.raises(TypeError):
        manifest['coverage']['manifest_functions'] = 0
