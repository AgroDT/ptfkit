---
name: ptf-python-bindings
description: Expose ptfkit Rust core PTF functions to Python through PyO3, maturin, and NumPy-compatible wrappers. Use when a Rust PTF kernel exists and the agent must preserve ptfkit public Python API behavior, including scalar inputs, vectorized NumPy inputs, broadcasting, out handling, typing, and NamedTuple results.
---

# PTF Python Bindings

## Workflow

1. Confirm the Rust core function exists and golden scalar tests pass.
2. Read the function spec and `references/python-bindings-contract.md`.
3. Run `just generate`; a spec generates `ptfkit.<source.key>` unless its
   top-level `python_generation` is `manual`, and generated ufuncs are the only
   native binding implementation.
4. Review generated keyword-only wrappers, overloads, `NamedTuple` result classes,
   scalar behavior, ndarray behavior, broadcasting, and `out` semantics.
5. Never edit an automatically generated Python module. If review shows a genuine
   exception, set top-level `python_generation: manual`, validate, regenerate,
   remove the generated marker, and then implement the public module manually
   using the native generated ufunc.
6. Add public wrapper tests for scalar, ndarray, broadcasting, multi-output field order, and `out`.
7. Stop if the Rust output order, units, or shape contract conflicts with the spec.

## Output

- Binding files changed.
- Public wrapper behavior preserved or intentionally introduced.
- Tests added or updated.
- Compatibility risks.

## Hard Rules

- Public Python API compatibility is the default.
- Do not expose raw Rust tuples directly when existing API expects a `NamedTuple`.
- Do not drop NumPy vectorized support.
- A manual module must not duplicate formulas or array calculations in Python.
- Render the module summary, APA citation, DOI identifier, and DOI URL verbatim
  from `source`; do not derive a summary or synthesize a DOI URL.
- Render module and function territories from their respective scope fields;
  never inherit, override, or combine them.
