---
name: ptf-review
description: Independently review a generated ptfkit PTF source against its YAML specification, semantic IR, retained targets, generation policy, and public API parity. Use for read-only pre-merge review after $ptf-generate.
---

# PTF Review

## Invocation

Use `$ptf-review <apa_article_key>`.

Accept exactly one positional argument: an APA-style source slug such as
`cosby1984`. It identifies `specs/functions/<apa_article_key>.yaml`; the
filename stem is the sole source identity. Reject a missing argument, more than
one argument, a path, or an unknown slug. Report the input error without
modifying repository state.

## Procedure

1. Read `specs/schema/ptf-spec.schema.json`, the selected YAML specification,
   implementation diff, generated Rust, C, C++, and native NumPy targets,
   golden tests, and relevant public wrapper.
2. Load `references/implementation-review-checklist.md`.
3. Check schema and semantic IR fidelity, all retained targets, deterministic
   regeneration, status transition evidence, categorical type and lookup
   fidelity, output order, NumPy broadcasting, `out`, enum-array typing,
   `NamedTuple` compatibility, docstring fidelity, and public API parity.
4. Run or request the project checks appropriate to the changed files.
5. Report findings first, ordered by severity, with file and line references.

## Output

- Blocking findings.
- Non-blocking findings.
- Test and documentation status.
- Approval only when the implementation matches the YAML specification and
  quality gates pass.

## Hard rules

- Treat the YAML specification and semantic implementation as the sole
  numerical source of truth, not guessed article intent.
- Treat missing golden tests, ambiguous units, and public API breaks as
  blocking unless explicitly approved.
- Verify that each record `outputs.name` is PascalCase and names generated
  structures and classes.
- Treat repository-only specification paths in production Rust, native extension
  comments, public Python docstrings, or package metadata as blocking.
- Remain read-only by default and never own the transition to `implemented`.
