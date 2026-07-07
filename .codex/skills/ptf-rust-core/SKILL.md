---
name: ptf-rust-core
description: Implement validated ptfkit PTF function specs in the pure Rust core crate. Use after ptf-spec-ingest reports Ready for implementation and the task is to translate spec formulas, constants, units, and golden cases into Rust f64 kernels. Do not infer missing spec details.
---

# PTF Rust Core

## Workflow

1. Confirm the spec passed `ptf-spec-ingest` with no blocking issues.
2. Read the validated function spec and `references/rust-core-patterns.md`.
3. Implement pure Rust `f64` scalar kernels only. Keep Python, PyO3, NumPy, and allocation concerns outside the pure core.
4. Map every formula variable and constant back to the spec.
5. Add or update Rust golden tests when the Rust crate exists.
6. If the spec is incomplete, stop and send the issue back to `ptf-spec-ingest`.

## Output

- Rust function names and files changed.
- Spec fields implemented.
- Golden cases covered.
- Any blocked or deferred items.

## Hard Rules

- Do not read papers to resolve missing formulas.
- Do not change the public Python API in this skill.
- Do not silently change units, output order, or numeric policy.
