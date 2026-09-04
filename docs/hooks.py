from __future__ import annotations

from pathlib import Path

from mkdocs.structure.files import File, Files, InclusionLevel


TYPE_CHECKING = False
if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page


GENERATED_PAGES = (
    ('CONTRIBUTING.md', 'contributing/index.md'),
    ('targets/ptfkit-native/README.md', 'targets/native.md'),
    ('targets/ptfkit-py/README.md', 'targets/python.md'),
    ('targets/ptfkit-rs/README.md', 'targets/rust.md'),
)


def on_files(files: Files, /, *, config: MkDocsConfig) -> Files | None:
    root = Path(__file__).joinpath('../..').resolve()
    for source, destination in GENERATED_PAGES:
        files.append(
            File.generated(
                config,
                destination,
                content=(root / source).read_bytes(),
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
