from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from mkdocs.structure.files import File, Files, InclusionLevel


TYPE_CHECKING = False
if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


util_spec = spec_from_file_location('util', Path(__file__).with_name('util.py'))
if util_spec is None or util_spec.loader is None:
    raise RuntimeError

util = module_from_spec(util_spec)
util_spec.loader.exec_module(util)


def on_files(files: Files, /, *, config: MkDocsConfig) -> Files | None:
    index_file = File.generated(
        config,
        'index.md',
        content=util.get_normalized_readme(),
        inclusion=InclusionLevel.INCLUDED,
    )
    files.append(index_file)

    return files
