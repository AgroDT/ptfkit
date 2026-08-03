---
name: ptf-review
description: Review ptfkit PTF implementations against validated MD specs, golden tests, units, numeric policy, documentation, Rust core behavior, PyO3/maturin bindings, and public Python API compatibility. Use for code review before merging PTF implementation PRs.
---

# PTF Review

## Workflow

1. Read the validated spec, implementation diff, golden tests, and relevant public wrapper.
2. Load `references/implementation-review-checklist.md`.
3. Check front matter validation, native ufunc presence, Rust/spec signature agreement,
   output order, broadcasting, `out`, `NamedTuple` compatibility, docstring fidelity,
   and public API compatibility. Check that any manual module decision is justified
   and consistently applied to the entire module.
4. Run or request the project checks appropriate to the changed files.
5. Report findings first, ordered by severity, with file and line references where available.

## Output

- Blocking findings.
- Non-blocking findings.
- Test and docs status.
- Approval only if implementation matches the spec and quality gates pass.

## Hard Rules

- Review against the MD spec, not guessed article intent.
- Treat missing golden tests, ambiguous units, and public API breaks as blocking unless explicitly approved.
- Do not rewrite the implementation while acting as reviewer unless the user asks for fixes.
