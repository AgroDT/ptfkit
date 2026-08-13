# Contributing to ptfkit

ptfkit is a spec-driven project that generates independent Rust and Python
targets from machine-readable PTF specifications. New PTFs are normally added
through the repository's agent-assisted workflow, with a validated
function-level specification as the contract between stages.

## Project Layout

- `specs/` contains the machine-readable PTF specifications and their schema.
- `codegen/` contains the specification validator and code generator.
- `targets/ptfkit-rs/` contains the generated idiomatic Rust target and its
  golden tests.
- `targets/ptfkit-py/` contains the generated Python target: public modules,
  direct-CPython extension sources, tests, and Python package tooling.
- `.agents/skills` contains the workflow skills used to add and review PTFs.

## Toolchains and Dependencies

Install the Rust toolchain with [rustup](https://rustup.rs/) and install
[`uv`](https://docs.astral.sh/uv/getting-started/installation/) for the Python
package.

```sh
cargo --version
uv --version
```

Rust dependencies are managed independently by the code generator and Rust
target Cargo projects. Run Cargo dependency commands against the relevant
project manifest, and do not edit either project's `Cargo.lock` by hand.

`uv` owns Python dependencies, virtual environments, and
`targets/ptfkit-py/uv.lock`. Use `uv add`, `uv remove`, and `uv sync` for Python
package changes. Do not edit either lockfile by hand or use one ecosystem's
package manager for the other.

Synchronize the Python package environment with:

```sh
just python::sync
```

## Everyday Development

Use the root `Justfile` to check the independent code generator and Rust target:

```sh
just codegen::format
just codegen::lint
just codegen::test
just rust::format
just rust::lint
just rust::test
```

The equivalent low-level Rust target commands are:

```sh
cargo fmt --manifest-path targets/ptfkit-rs/Cargo.toml --all --check
cargo clippy --manifest-path targets/ptfkit-rs/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path targets/ptfkit-rs/Cargo.toml
```

Validate or regenerate specifications directly with:

```sh
cargo run --manifest-path codegen/Cargo.toml -- validate
cargo run --manifest-path codegen/Cargo.toml -- generate
```

Run Python package workflows through the root `Justfile`:

```sh
just python::lint
just python::format
just python::test
just python::docs
```

`just python::test` builds the local native extension before running the public
Python test suite. Use the smallest relevant checks while iterating, then run
every applicable check before submitting a change.

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
