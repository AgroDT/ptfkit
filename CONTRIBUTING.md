# Contributing to ptfkit

ptfkit is a Cargo workspace with a pure Rust computational core and a Python
binding package. New PTFs are normally added through the repository's
agent-assisted workflow, with a validated function-level specification as the
contract between stages.

## Project Layout

- `crates/ptfkit-core` contains pure Rust PTF kernels and their golden tests.
- `crates/ptfkit-py` contains the PyO3 bindings, public Python modules, and
  Python package tooling.
- `specs/functions` contains the validated function-level specifications that
  define formulas, units, numeric policy, API contracts, and golden cases.
- `.agents/skills` contains the workflow skills used to add and review PTFs.

## Toolchains and Dependencies

Install the Rust toolchain with [rustup](https://rustup.rs/) and install
[`uv`](https://docs.astral.sh/uv/getting-started/installation/) for the Python
package.

```sh
cargo --version
uv --version
```

Cargo owns the Rust workspace dependencies and `Cargo.lock`. Use Cargo commands
such as `cargo add`, `cargo remove`, and `cargo update` for Rust changes.

`uv` owns Python dependencies, virtual environments, and
`crates/ptfkit-py/uv.lock`. Use `uv add`, `uv remove`, and `uv sync` for Python
package changes. Do not edit either lockfile by hand or use one ecosystem's
package manager for the other.

Synchronize the Python package environment with:

```sh
just python::sync
```

## Everyday Development

Run Rust workspace checks from the repository root:

```sh
cargo fmt --check
cargo clippy --workspace --all-targets
cargo test --workspace
```

Run Python package workflows through the root `Justfile`:

```sh
just python::lint
just python::format
just python::test
just python::docs
```

`just python::test` builds the local bindings before running the public Python
test suite. Use the smallest relevant checks while iterating, then run every
applicable check before submitting a change.

## Adding a PTF

Most new PTF work is agent-assisted. Use the skills in `.agents/skills` in this
order:

1. In one session, give `ptf-extract` a local path to the source material. It
   writes and validates a draft YAML under `specs/functions` using only
   explicitly stated facts, then reports `Ready for user review` or `Blocked`.
2. Review and, if needed, edit the YAML directly. Resolve blockers before
   generation.
3. In a fresh session, use `ptf-generate <apa_article_key>` to validate, generate,
   test, prove idempotence, and mark the reviewed source implemented only after
   all retained targets pass.
4. Optionally use `ptf-review <apa_article_key>` in another fresh session for
   independent, read-only pre-merge review.

The source file is transient input. Do not copy it into the repository or store
its path in generated files. The validated function-level specification is the
only persisted ingest artifact and the source of truth for implementation.

## Change Scope and Quality

Keep formula migrations small: one function or a closely related group per
change. Do not combine a formula migration with an unrelated refactor unless
the scope is explicitly approved.

Every implementation must remain traceable to its YAML source specification.
Generated Rust and native NumPy targets own formula golden tests; the Python package owns public API compatibility
tests. Update documentation when a public API, a specification, or a supported
workflow changes.

## Documentation, Branches, and Commits

Keep `README.md`, `AGENTS.md`, relevant MkDocs content, `Cargo.toml`,
`pyproject.toml`, and `Justfile` aligned with the change. Build Python package
documentation with:

```sh
just python::docs
```

Name branches as `(<type>)/<short-description>`, for example
`feature/add-cosby1984`.

Use English Conventional Commits:

```text
<type>(<scope>): <short summary>
```

Use imperative mood, keep the subject at 50 characters or fewer, wrap body
lines at 72 characters, and avoid emojis.
