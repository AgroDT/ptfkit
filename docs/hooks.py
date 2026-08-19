from __future__ import annotations

import re
from pathlib import Path

from mkdocs.structure.files import File, Files, InclusionLevel


TYPE_CHECKING = False
if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page


def _normalize_root_links(path: Path) -> str:
    docs_re = re.compile(r'https:\/\/agrodt\.github\.io\/ptfkit\/(.+)\/')
    content = (
        path.read_text()
        .replace('(./', '(https://github.com/AgroDT/ptfkit/tree/main/')
        .replace(
            'https://agrodt.github.io/ptfkit/contributing/development/',
            'contributing/development.md',
        )
    )
    return docs_re.sub(r'\1/index.md', content)


GENERATED_PAGES = (
    ('README.md', 'index.md', _normalize_root_links),
    ('CONTRIBUTING.md', 'contributing/index.md', Path.read_bytes),
    ('targets/ptfkit-native/README.md', 'targets/native.md', Path.read_bytes),
    ('targets/ptfkit-py/README.md', 'targets/python.md', Path.read_bytes),
    ('targets/ptfkit-rs/README.md', 'targets/rust.md', Path.read_bytes),
)


def on_files(files: Files, /, *, config: MkDocsConfig) -> Files | None:
    root = Path(__file__).joinpath('../..').resolve()
    for source, destination, get_content in GENERATED_PAGES:
        files.append(
            File.generated(
                config,
                destination,
                content=get_content(root / source),
                inclusion=InclusionLevel.INCLUDED,
            )
        )

    return files


def on_page_markdown(
    markdown: str,
    *,
    page: Page,
    **_kwargs,  # noqa: ANN003
) -> str:
    nav_title = page.meta.get('nav-title')

    if isinstance(nav_title, str):
        page.title = nav_title

    return markdown
