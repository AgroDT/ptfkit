# Development guide

ptfkit is specification-driven. YAML files describe source publications and
function contracts; the code generator validates those files and writes the
language targets, tests, and PTF catalog. Generated files are committed so that
package builds and documentation builds do not depend on running codegen first.

## Repository layout

- `specs/functions/` contains one YAML specification per source publication.
- `specs/schema/` defines the specification format.
- `codegen/` contains validation and generation code.
- `targets/ptfkit-native/` contains the C11 headers and C++20 modules.
- `targets/ptfkit-py/` contains the Python package and its native extension.
- `targets/ptfkit-rs/` contains the Rust crate.
- `docs/mkdocs.yml` configures the documentation site.
- `docs/src/` contains published Markdown, navigation, and static assets
  including generated files.
- `.agents/skills/` contains the assisted extraction, generation, and review
  workflows.

For the specification format and its cross-target contracts, see
the [PTF source specification guide](../ptf-catalog/index.md).

## Toolchains and dependencies

Install Rust using your preferred method or via [rustup](https://rustup.rs/),
and install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
We also recommend to install [`just`](https://just.systems/) for running
repository commands. The native target also requires CMake and a
C11/C++20 compiler.

Use `cargo` to manage dependencies for the codegen and Rust target, and use `uv`
to manage the Python environment. Add, update, or remove dependencies through
these tools instead of manually editing dependency lists in `pyproject.toml` or
`Cargo.toml`.

Prepare the Python environment with:

```sh
just python::sync
```

## Specifications and generated targets

The [PTF source specification guide](../ptf-catalog/index.md) explains the
scientific information represented by each YAML file. The JSON Schema and
`just validate` define the complete structural and semantic contract.

Do not edit generated target sources, tests, the PTF catalog, or generated API
reference pages directly. Regenerate every target and the PTF catalog with:

```sh
just generate
```

A second generation run must leave the working tree unchanged.

### Generation conventions

The specification filename stem is the APA-style source slug. Codegen uses it
for Rust, Python, and C++ modules, C headers, tests, and documentation. Generated
function names follow `calc_ptf_<first-author><year>[_<extra>]` where applicable.

Each source has one public Python module, `ptfkit.<apa_article_key>`. Codegen
creates it by default. Set `generation.public_python: manual` only when the
public wrapper must be maintained manually; the wrapper must still delegate to
the generated native ufuncs rather than duplicate formulas.

Codegen compiles each `implementation` into a shared semantic model and renders
the Rust, C, C++, and native NumPy implementations independently. Documentation
is generated from the same validated specification. Put target-independent
summaries, parameter descriptions, return descriptions, notes, and warnings in
the YAML rather than adding them to generated files.

### Adding a PTF

The assisted workflow uses the skills in `.agents/skills/`:

1. Give `ptf-extract` a readable local source paper. It writes a blocked or
   review-ready draft under `specs/functions/` using only information supported
   by that source.
2. Review the YAML and resolve every blocker, including missing metadata.
3. Run `ptf-generate <apa_article_key>` to validate, generate, test, prove
   idempotence, and mark the reviewed source implemented.
4. Optionally run `ptf-review <apa_article_key>` for an independent, read-only
   pre-merge review.

The source paper is transient input. The reviewed specification is the
persisted record and the source of truth for generated implementations.

## Checks

Use the smallest relevant checks while iterating. Before submitting changes that
affect multiple targets, run the complete target verification suite:

```sh
just verify
```

For a narrower change, run the component verification suite:

```sh
just codegen::verify
just rust::verify
just native::verify
just python::verify
```

Each component `verify` runs all of its format, lint, type-checking, and test
checks. `just test` runs only the target test suites together. Python tests
build the local native extension before exercising the public API.

## Documentation

Build or serve the site through the locked MkDocs environment:

```sh
just docs build
just docs serve
```

Run `just generate` before building documentation if specifications or codegen
changed.

The MkDocs configuration is `docs/mkdocs.yml`; it renders `docs/src/` into
`docs/dist/`. Handwritten pages are maintained under `docs/src/`. The PTF
catalog and API reference pages are generated from reviewed specifications and
the compiled semantic model. C reference Markdown is generated under
`docs/src/reference/c/`; C++ reference Markdown is generated under
`docs/src/reference/cpp/`; Python module pages are generated under
`docs/src/reference/python/` and render public docstrings through
`mkdocstrings`. Rust API documentation is published by
[docs.rs](https://docs.rs/ptfkit/).

## Change scope and commits

Follow [Adding a PTF](#adding-a-ptf) for new functions. Keep the extraction,
review, generation, and other changes for one source publication in a single
commit. Keep formula changes limited to one function or a closely related
group, and do not combine them with an unrelated refactor.

Use English Conventional Commits:

```text
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

Use imperative mood, keep the subject to 50 characters or fewer, and avoid
emojis. If a body is needed, wrap it at 72 characters.
