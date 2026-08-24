# Implementation review checklist

## Specification and IR

- [ ] YAML validates against the active unversioned schema and semantic checks.
- [ ] Every record `outputs.name` is PascalCase and names generated structures
  and classes; `$defs` keys only resolve local references.
- [ ] Every public function name, argument, output, unit, and IR expression
  matches the YAML specification.
- [ ] Every categorical argument binds its function-local name to the intended
  enum type; type and optional binding descriptions retain their separate roles.
- [ ] Enum member names, exact canonical textual values, order, and optional
  descriptions match the source-supported specification. Golden inputs use
  member names, never textual values or generated ordinals.
- [ ] Every lookup maps the declared enum to the declared record, covers each
  member exactly once, and gives each row exactly the record fields. Lookup
  invocation keys have the declared enum type, and record-field access resolves
  to real fields.
- [ ] No scientific assumption is present only in generated code.

## Formula and units

- [ ] Formula terms, constants, unit conversions, output order, and numeric
  policy match the YAML specification.

## Retained targets

- [ ] Generated Rust, C, and C++ preserve enum types, member identity, typed
  lookup conversion, record shape, and numeric computation from the semantic IR.
- [ ] Generated native NumPy ufuncs use the same IR and private ordinal encoding
  only as a target implementation detail.
- [ ] Generated target tests cover every structured golden case.
- [ ] Valid IR unsupported by a retained target is reported as a generator
  capability blocker, not replaced with hand-written computation.

## Python API

- [ ] Public module and function names, keyword-only inputs, scalar/array
  behavior, broadcasting, `out`, and `NamedTuple` output match the contract.
- [ ] Python exposes scalar categorical inputs as the generated enum and array
  inputs as its typed `EnumArray`; raw strings, integers, arbitrary arrays, and
  normalization aliases are not silently accepted.
- [ ] Generated enum type and member documentation reflects the enum and member
  descriptions without conflating them with a function binding description.
- [ ] A manual public module is justified and delegates to generated native
  ufuncs without duplicating formulas.

## Determinism and documentation

- [ ] Regeneration is deterministic and no marked generated file was edited.
- [ ] The transition to `implemented` has evidence that all required checks
  passed.
- [ ] Public docstrings and package metadata match source metadata and expose
  no repository-only specification paths.

## Blocking findings

Classify as blocking: schema or semantic failure; formula, unit, output-order,
categorical-type, lookup, or public-API mismatch; missing retained target or
golden test; unsupported IR; nondeterministic generation; unsubstantiated
status transition; or exposed repository-only specification paths.
