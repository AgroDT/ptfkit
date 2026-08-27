---
name: ptf-generate
description: Generate and verify all retained ptfkit targets for one reviewed APA-style source slug. Use after human review of a YAML source file in specs/functions to validate, generate, run the complete verification suite, and atomically mark the source implemented.
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

1. Read the selected YAML file and require at least one function with status
   `ready-for-implementation`. Only those functions participate in the status
   transition; leave functions with any other status unchanged.
2. Run `mise run validate`. Treat any structural or semantic validation failure
   as a blocker.
3. Run `mise run generate` to update every codegen-owned target.
4. Run `mise run verify`. Report any generator capability or target failure as
   a blocker; do not hand-write a generated computational target.
5. Only after all verification passes, change the selected source functions
   from `ready-for-implementation` to `implemented`.
6. Run `mise run generate` once more to produce the final implemented state.
   Treat the status update and final generation as one transition: do not leave
   the selected functions marked `implemented` if final generation fails.

## Hard rules

- Never hand-edit marked generated files.
- Do not rewrite formulas, implementation variables, metadata, or other
  scientific content. Human review must complete those changes before this
  skill runs.
- `generation.public_python: manual` permits only a hand-written public wrapper
  that delegates to the generated native ufunc.
- Do not change status unless all required retained targets pass.
- Do not manually audit generated output or prove regeneration idempotence for
  a routine PTF addition. Use those checks when the generator, schema, output
  formatting, or generation infrastructure changes, or when explicitly running
  `ptf-review`.
