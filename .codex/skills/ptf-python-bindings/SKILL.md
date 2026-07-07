---
name: ptf-python-bindings
description: Expose ptfkit Rust core PTF functions to Python through PyO3, maturin, and NumPy-compatible wrappers. Use when a Rust PTF kernel exists and Codex must preserve ptfkit public Python API behavior, including scalar inputs, vectorized NumPy inputs, broadcasting, out handling, typing, and NamedTuple results.
---

# PTF Python Bindings

## Workflow

1. Confirm the Rust core function exists and golden scalar tests pass.
2. Read the function spec and `references/python-bindings-contract.md`.
3. Add PyO3/maturin bindings without changing the public wrapper name or module unless the spec explicitly requires a new API.
4. Preserve keyword-only Python wrappers, overloads, `NamedTuple` result classes, scalar behavior, ndarray behavior, broadcasting, and `out` semantics.
5. Add public wrapper tests for scalar, ndarray, broadcasting, multi-output field order, and `out`.
6. Stop if the Rust output order, units, or shape contract conflicts with the spec.

## Output

- Binding files changed.
- Public wrapper behavior preserved or intentionally introduced.
- Tests added or updated.
- Compatibility risks.

## Hard Rules

- Public Python API compatibility is the default.
- Do not expose raw Rust tuples directly when existing API expects a `NamedTuple`.
- Do not drop NumPy vectorized support.
