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

1. Read the supplied local paper, `specs/schema/ptf-spec.schema.json`,
   `specs/quantities.yaml`, and
   `references/extraction-quality-gate.md`.
   If the source defines a finite categorical input or a table selected by that
   input, also read `references/categorical-lookups.md`.
2. Resolve every scalar output and record field to a stable quantity identifier
   and exact unit in `specs/quantities.yaml`. If either is absent, stop and ask
   the user to review a proposed identifier or unit entry, absolute tolerance,
   optional relative tolerance, and concise rationale. Include the output
   description and nearest analogous entries. Add the policy only after the
   user accepts or edits it; never silently invent a registry entry.
3. Extract only facts explicitly supported by the paper. Write its standalone
   YAML directly to `specs/functions/<apa_article_key>.yaml`, following
   `references/spec-template.yaml`.
4. Add every source-published input-output example as a `published`
   `verification_cases` entry. If none exists, select physically meaningful
   inputs and calculate the expected outputs with simple reference code as
   described in `references/extraction-quality-gate.md`.
5. If the publication explicitly states an applicable output accuracy or
   resolution, optionally propose a function-level `verification_tolerances`
   override keyed by output name and cite its exact `source_location`. Do not
   search indefinitely for one, put an override in a verification case, or use
   model-performance statistics such as RMSE as implementation tolerances.
6. Record missing or ambiguous computational-contract information as explicit
   blockers and set affected functions to `blocked`; otherwise set reviewed,
   complete functions to `ready-for-implementation`.
7. Run `cargo run --manifest-path codegen/Cargo.toml -- validate` and fix
   validation errors before finishing. When a nontrivial formula expression is
   repeated within one implementation, declare it once as an earlier local
   implementation variable and reference that variable; retain the published
   numeric lexemes and do not assign extra scientific semantics. Validation
   never justifies inferred science.

## Output

Return `Ready for user review` with the exact YAML path, or `Blocked` with the
exact YAML path and explicit blockers.

## Hard rules

- Do not set `implemented`, run target generation, or edit generated files.
- Do not invent formulas, units, published examples, applicability, or API
  details. Calculated verification inputs must satisfy the documented domain
  and physical constraints; fix independently calculated expected values in
  YAML and explain the choice in `rationale`.
- Do not call a calculated case independent, source-native, artifact-native,
  external validation, or evidence of model accuracy.
- Do not normalize, alias, abbreviate, or otherwise broaden source-defined
  categorical values. Keep enum member names, canonical textual values, lookup
  rows, and their evidence distinct.
- Give every `type: record` output a PascalCase `name`, whether it is inline or
  declared in `$defs`. It names generated structures and classes; `$defs` keys
  only resolve local `$ref` targets.
- Give every scalar output and record field a reviewed `quantity`. Unit matching
  is exact and textual; do not create a second quantity merely for another unit.
- Use `generation.public_python: manual` only when the public wrapper cannot
  follow the standard generated API; it never opts the native NumPy ufunc out
  of generation.
