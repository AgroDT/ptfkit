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
- Every categorical input binds a function-local `name` to an enum `$ref`.
  Enum member names and canonical textual values are unique, and categorical
  golden inputs name enum members rather than textual values or ordinals.
- Every lookup references an enum input and record output, covers every enum
  member exactly once, and gives every row exactly the record's fields. Each
  lookup invocation uses an in-scope key of the declared enum type; field
  access and direct record return match the resolved record type.
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
- Valid semantic IR unsupported by any retained Rust, C, C++, or Python path:
  return a generator capability blocker. This includes categorical types, typed
  lookups, and record-field access. Do not hand-write a retained computational
  target.
- A manual public module may only wrap its generated native ufunc; it does not
  disable native generation or allow a duplicate formula.
