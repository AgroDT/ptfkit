from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from importlib import import_module
from typing import cast

import pytest

from ptfkit import get_manifest


def test_manifest_is_packaged_read_only_and_matches_public_callables():
    manifest = get_manifest()

    assert manifest['schema_version'] == 1
    coverage = manifest['coverage']
    assert isinstance(coverage, Mapping)
    implemented = coverage['implemented_functions']
    included = coverage['manifest_functions']
    omitted = coverage['omitted_functions']
    assert isinstance(implemented, int)
    assert isinstance(included, int)
    assert isinstance(omitted, tuple)
    assert implemented == included + len(omitted)
    assert included > 0

    functions = manifest['functions']
    assert isinstance(functions, tuple)
    assert len(functions) == included
    for function in functions:
        assert isinstance(function, Mapping)
        module_name = function['module']
        callable_name = function['callable']
        assert isinstance(module_name, str)
        assert isinstance(callable_name, str)
        module = import_module(module_name)
        assert callable(getattr(module, callable_name))

    with pytest.raises(TypeError):
        cast('MutableMapping[str, object]', manifest)['schema_version'] = 2
    with pytest.raises(TypeError):
        cast('MutableMapping[str, object]', coverage)['manifest_functions'] = 0
