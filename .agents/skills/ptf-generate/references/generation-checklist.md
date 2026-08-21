# Generation checklist

## Preconditions

- The requested APA-style slug identifies
  `specs/functions/<apa_article_key>.yaml`; its filename stem is the sole
  source identity.
- Every selected function is `ready-for-implementation`, has no unresolved
  blocker or `TODO`, and has complete schema-valid semantic implementation and
  matching ordered output metadata.
- Every record `outputs.name` is PascalCase and names generated structures and
  classes.
- Run `cargo run --manifest-path codegen/Cargo.toml -- validate` before
  generation.

## Required commands

Run the relevant project gates after
`cargo run --manifest-path codegen/Cargo.toml -- generate`:

```sh
mise run codegen:format
mise run codegen:lint
mise run codegen:test
mise run rust:format
mise run rust:lint
mise run rust:test
mise run python:format
mise run python:lint
mise run python:test
```

Run `cargo run --manifest-path codegen/Cargo.toml -- generate` a second time and
inspect the diff for idempotence. Once all gates pass, set only the selected
source's functions to `implemented`, then rerun validation, generation, and the
second generation idempotence check. Investigate every unexpected diff.

## Failure classification

- Invalid, incomplete, or ambiguous science: return a spec blocker for the
  user to resolve.
- Valid semantic IR unsupported by Rust or the native NumPy backend: return a
  generator capability blocker. Do not hand-write a retained target.
- A manual public module may only wrap its generated native ufunc; it does not
  disable native generation or allow a duplicate formula.
