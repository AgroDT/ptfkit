from __future__ import annotations

import re
from pathlib import Path


GITHUB_ONLY_RE = re.compile(
    r'<!--\s*github:start\s*-->[\S\s]*<!--\s*github:end\s*-->\n*',
    re.MULTILINE,
)
MD_LINK_RE = re.compile(r'\[(`.+`)\]\(.+\)', re.MULTILINE)


def get_normalized_readme() -> str:
    content = Path(__file__, '../../README.md').resolve().read_text('utf-8')
    content = GITHUB_ONLY_RE.sub('', content)
    return MD_LINK_RE.sub(r'`\1`', content)
