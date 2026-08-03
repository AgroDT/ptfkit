## General instructions

Use **only English** for code, comments, documentation, and commits.
For conversations use the user's preferred language.

When in doubt, stop and ask for clarification. Do not act without being
completely sure.

## Project management

- Manage **all** project dependencies exclusively via `uv` commands (e.g.,
  `uv add`, `uv remove`, `uv sync`). Do not mix package managers or install
  dependencies ad hoc.
- Run Python development workflows through the root `Justfile`; its recipes
  invoke `uv` against `crates/ptfkit-py` without implicit dependency resolution.

## PTF specification workflow

- Use the project-specific skills in `.agents/skills/` in this order:
  - `ptf-spec-ingest` for converting a user-supplied local source file into a
    validated function-level spec under `specs/functions/`.
  - `ptf-rust-core` for implementing validated specs in the pure Rust core.
  - `ptf-python-bindings` for exposing Rust functions through the Python API.
  - `ptf-review` for checking implementation quality against the spec and
    golden tests.

## Implementation details and migration

- The current legacy computational core lives in
  `crates/ptfkit-py/python/ptfkit/_core.py`
  (Cython-annotated code in pure Python mode).
- Maturin configuration belongs to the bindings package, not the repository
  root.
- Public Python wrappers remain in modules named `<first-author><year>.py`
  under `crates/ptfkit-py/python/ptfkit/`.
- Vectorized function naming should continue to follow the established
  convention when applicable:
  `calc_ptf_<first-author><year>[_<extra>]`.

## Migration strategy

- Migrate in small steps: one function or a small, coherent group of functions
  per PR.
- Before moving many functions, complete one end-to-end pilot:
  spec ingest, Rust core implementation, Python bindings, golden tests,
  documentation alignment, and review.
- Keep each migration PR passing tests before starting the next function group.
- Do not combine broad refactors with formula migrations unless the scope is
  explicitly approved.
