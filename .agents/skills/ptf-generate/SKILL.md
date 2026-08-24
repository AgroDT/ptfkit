---
name: ptf-generate
description: Generate and verify all retained ptfkit targets for one reviewed APA-style source slug. Use after human review of a YAML source file in specs/functions to validate, generate, test, prove idempotence, and atomically mark the source implemented.
---

# PTF Generate

## Invocation

Use `$ptf-generate <apa_article_key>`.

Accept exactly one positional argument: an APA-style source slug such as
`cosby1984`. It identifies `specs/functions/<apa_article_key>.yaml`; the
filename stem is the sole source identity. Reject a missing argument, more than
one argument, a path, or an unknown slug. Do not generate targets or change
status when input validation fails; report the blocking input error.

## Procedure

1. Treat the argument as the source under review. Read
   `specs/schema/ptf-spec.schema.json`, its selected YAML file,
   and `references/generation-checklist.md`.
2. Reject unresolved blockers, `TODO` values, schema or semantic failures, and
   output-metadata mismatches. Record `outputs.name` is PascalCase and names
   generated structures and classes; `$defs` keys only resolve local references.
   For categorical inputs and lookups, verify the named enum binding, exact
   member names and canonical values, complete enum-to-record mapping, lookup
   key type, row fields, and categorical golden inputs. Do not infer missing
   science.
3. Validate, generate all retained targets, and run the required verification
   gates. Before validation, extract each repeated nontrivial formula
   expression within a function into one earlier local implementation variable
   and reference it thereafter; retain published numeric lexemes and do not
   invent scientific semantics for the calculation intermediate. A generator
   capability gap is a blocker, never an invitation to hand-write that
   computational target.
4. After every required check passes, change the selected source functions from
   `ready-for-implementation` to `implemented`, then revalidate, regenerate,
   and prove the second generation pass is idempotent.

## Hard rules

- Never hand-edit marked generated files.
- `generation.public_python: manual` permits only a hand-written public wrapper
  that delegates to the generated native ufunc.
- Do not change status unless all required retained targets pass.
