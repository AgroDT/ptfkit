# Generation checklist

## Preconditions

- The requested APA-style slug identifies
  `specs/functions/<apa_article_key>.yaml`; its filename stem is the sole
  source identity.
- Every selected function is `ready-for-implementation`, has no unresolved
  blocker or `TODO`, and has complete schema-valid semantic implementation and
  matching ordered output metadata.
- Run `cargo run -p ptfkit-codegen -- validate` before generation.

## Required commands

Run the relevant project gates after `cargo run -p ptfkit-codegen -- generate`:

```sh
cargo test --workspace
just python::test
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
just python::lint
just python::format
```

Run `cargo run -p ptfkit-codegen -- generate` a second time and inspect the
diff for idempotence. Once all gates pass, set only the selected source's
functions to `implemented`, then rerun validation, generation, and the second
generation idempotence check. Investigate every unexpected diff.

## Failure classification

- Invalid, incomplete, or ambiguous science: return a spec blocker for the
  user to resolve.
- Valid semantic IR unsupported by Rust or the native NumPy backend: return a
  generator capability blocker. Do not hand-write a retained target.
- A manual public module may only wrap its generated native ufunc; it does not
  disable native generation or allow a duplicate formula.
