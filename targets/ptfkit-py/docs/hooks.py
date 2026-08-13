from __future__ import annotations  # noqa: INP001

from mkdocs.structure.files import File, Files, InclusionLevel


TYPE_CHECKING = False
if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


def on_files(files: Files, /, *, config: MkDocsConfig) -> Files | None:
    index_file = File.generated(
        config,
        'index.md',
        abs_src_path='README.md',
        inclusion=InclusionLevel.INCLUDED,
    )
    files.append(index_file)

    return files
