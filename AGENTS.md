## General instructions

Use **only English** for code, comments, documentation, and commits.
For conversations use the user's preferred language.

When in doubt, stop and ask for clarification. Don't try to act without being
completely sure.

## Project management

- Manage **all** project dependencies exclusively via `uv` commands (e.g.,
  `uv add`, `uv remove`, `uv sync`). Do not mix package managers or install
  dependencies ad hoc.
- Run every development tool (tests, linters, formatters, docs, etc.) through
  `uv run --no-sync <command>` to ensure a consistent environment and avoid
  implicit dependency resolution.

## Implementation details

- Core implementations live in `src/ptfkit/_core.py` (Cython-annotated code in
  pure Python mode).
- Vectorized ufuncs follow the naming convention: `calc_ptf_<first-author><year>[_<extra>]_ufunc`.
- Public Python wrappers are in modules named `<first-author><year>.py` and
  should call the corresponding ufuncs.

## AI agent playbooks

- [`.ai/agents/maintainer.md`](.ai/agents/maintainer.md) — maintainer
  responsibilities covering tooling, documentation alignment, branching
  strategy, and commit rules, while coordinating the work of developers,
  testers, and documentation authors to keep processes, environments, and
  communication synchronized.
- [`.ai/agents/developer.md`](.ai/agents/developer.md) — developer guidance for
  implementing vectorized PTF ufuncs in `_core.py` and public wrappers under
  `src/ptfkit/`.
- [`.ai/agents/tester.md`](.ai/agents/tester.md) — tester workflow describing
  how to structure pytest suites for public wrappers and how to gather coverage.
