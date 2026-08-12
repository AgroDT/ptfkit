---
name: ptf-extract
description: Extract a user-supplied local paper into a validated draft PTF source specification. Use when a paper must become a YAML source file in specs/functions before human review; preserve missing or ambiguous scientific details as blockers and never generate targets.
---

# PTF Extract

## Invocation

Use `$ptf-extract <path-to-local-source-file>`.

Accept exactly one positional argument: a readable local regular file containing
the supplied paper or source material. Reject a missing argument, more than one
argument, a directory, a non-local path, or an unreadable file. Do not create or
change a specification when input validation fails; report `Blocked` and the
input error.

## Procedure

1. Read the supplied local paper, `specs/schema/ptf-spec.schema.json`, and
   `references/extraction-quality-gate.md`.
2. Extract only facts explicitly supported by the paper. Write its standalone
   YAML directly to `specs/functions/<apa_article_key>.yaml`, following
   `references/spec-template.yaml`.
3. Record missing or ambiguous required scientific information as explicit
   blockers and set affected functions to `blocked`; otherwise set reviewed,
   complete functions to `ready-for-implementation`.
4. Run `cargo run -p ptfkit-codegen -- validate` and fix validation errors
   before finishing. Validation never justifies inferred science.

## Output

Return `Ready for user review` with the exact YAML path, or `Blocked` with the
exact YAML path and explicit blockers.

## Hard rules

- Do not set `implemented`, run target generation, or edit generated files.
- Do not invent formulas, units, metadata, golden values, applicability, or
  API details. Keep uncertainty explicit in the YAML.
- Use `generation.public_python: manual` only when the public wrapper cannot
  follow the standard generated API; it never opts the native NumPy ufunc out
  of generation.
