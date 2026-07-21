## General instructions

Use **only English** for code, comments, documentation, and commits.
For conversations use the user's preferred language.

When in doubt, stop and ask for clarification. Do not act without being
completely sure.

## Project management

- Manage **all** project dependencies exclusively via `uv` commands (e.g.,
  `uv add`, `uv remove`, `uv sync`). Do not mix package managers or install
  dependencies ad hoc.
- Run every development tool (tests, linters, formatters, docs, etc.) through
  `uv run --no-sync <command>` to ensure a consistent environment and avoid
  implicit dependency resolution.

## PTF specification workflow

- Article-level Markdown extracted from papers belongs in `specs/papers/*.md`.
- `specs/papers/*.md` is a transient input area and must not be committed.
- `ptf-spec-ingest` reads article-level Markdown from `specs/papers/*.md`,
  extracts explicitly stated PTF formulas, and prepares function-level specs in
  `specs/functions/*.md`.
- The source of truth for implementation remains the generated function-level
  Markdown spec in `specs/functions/*.md`.
- Function-level specs must use article/APA-style filenames, not public
  function names. Keep public function names inside the spec identity section.
- Codex must not invent, infer, simplify, or complete missing formulas,
  constants, units, expected values, output fields, or API details. If the paper
  extraction is ambiguous or incomplete, preserve the uncertainty as blocking
  issues in the generated spec and ingest report.
- If a generated function-level spec is incomplete or ambiguous, stop
  implementation work and create a review file that lists blocking issues and
  questions for the spec owner.
- Use the project-specific skills in `.codex/skills/` for the PTF workflow:
  - `ptf-spec-ingest` for converting article-level Markdown into function-level
    specs, validating generated specs, and creating developer/tester tasks.
  - `ptf-rust-core` for implementing validated specs in the pure Rust core.
  - `ptf-python-bindings` for exposing Rust functions through the Python API.
  - `ptf-review` for checking implementation quality against the spec and
    golden tests.

## Implementation details and migration

- The current legacy computational core lives in `src/ptfkit/_core.py`
  (Cython-annotated code in pure Python mode).
- The migration target is a pure Rust core crate. Rust core code must not
  depend on Python, PyO3, NumPy, or Python packaging internals.
- Python bindings may use PyO3, maturin, and NumPy-facing adapter code, but
  they must preserve the public Python API unless a breaking change is
  explicitly agreed before implementation.
- Public Python wrappers remain in modules named `<first-author><year>.py`.
- Existing public wrapper names, keyword-only arguments, return units,
  `NamedTuple` result classes, result field order, scalar behavior, vectorized
  NumPy behavior, and `out` behavior are compatibility constraints unless the
  spec and maintainer approval explicitly say otherwise.
- Vectorized function naming should continue to follow the established
  convention when applicable:
  `calc_ptf_<first-author><year>[_<extra>]`.

## Planning and role orchestration

Before writing new code, first switch to the maintainer role to orchestrate
other agents and confirm role handoffs. After maintainer alignment, select
the remaining roles needed for the task (developer, tester, documentation
author, etc.).

### Mandatory role sweep (blocking)

Before proposing any plan, the agent MUST:

1. List all roles referenced in the AI agent playbooks section below.
2. State how each role will be consulted during the task.
3. If any listed role is not applicable, explicitly justify why.

If any role is omitted, STOP and ask for clarification before proceeding.

- [`.ai/agents/maintainer.md`](.ai/agents/maintainer.md) - maintainer
  responsibilities covering tooling, documentation alignment, branching
  strategy, and commit rules, while coordinating the work of developers,
  testers, and documentation authors to keep processes, environments, and
  communication synchronized.
- [`.ai/agents/developer.md`](.ai/agents/developer.md) - developer guidance for
  implementing vectorized PTF ufuncs in `_core.py` and public wrappers under
  `src/ptfkit/`.
- [`.ai/agents/tester.md`](.ai/agents/tester.md) - tester workflow describing
  how to structure pytest suites for public wrappers and how to gather coverage.

## Testing and quality gates

- Every implemented function must have golden tests derived from the validated
  function-level spec.
- Core formula golden tests belong in the Rust core crate near the
  implementation and may embed cases directly in Rust test code.
- Python tests should cover bindings and public API compatibility: scalar
  wrappers, NumPy array inputs, broadcasting, `NamedTuple` results, and `out`.
- Review must verify formula traceability, units, constants, output order,
  edge cases, documentation, and public Python API compatibility.

## Migration strategy

- Migrate in small steps: one function or a small, coherent group of functions
  per PR.
- Before moving many functions, complete one end-to-end pilot:
  spec ingest, Rust core implementation, Python bindings, golden tests,
  documentation alignment, and review.
- Keep each migration PR passing tests before starting the next function group.
- Do not combine broad refactors with formula migrations unless the maintainer
  explicitly approves the scope.
