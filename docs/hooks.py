from __future__ import annotations

import re
from pathlib import Path

from mkdocs.structure.files import File, Files, InclusionLevel


TYPE_CHECKING = False
if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


MD_LINK_RE = re.compile(r'\[(.+)\]\(.+\)', re.MULTILINE)


def on_files(files: Files, /, *, config: MkDocsConfig) -> Files | None:
    content = Path(__file__, '../../README.md').resolve().read_text('utf-8')
    content = MD_LINK_RE.sub(r'\1', content)
    index_file = File.generated(
        config,
        'index.md',
        content=content,
        inclusion=InclusionLevel.INCLUDED,
    )
    files.append(index_file)

    return files
