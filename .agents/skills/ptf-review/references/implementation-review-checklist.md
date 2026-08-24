# Implementation review checklist

## Specification and IR

- [ ] YAML validates against the active unversioned schema and semantic checks.
- [ ] Every record `outputs.name` is PascalCase and names generated structures
  and classes; `$defs` keys only resolve local references.
- [ ] Every public function name, argument, output, unit, and IR expression
  matches the YAML specification.
- [ ] No scientific assumption is present only in generated code.
- [ ] Every categorical input resolves through the adapter registry; every
  derived binding retains adapter, source input, component, numeric symbol, and
  meaningful source evidence in semantic IR.
- [ ] Categorical public inputs are never compiled as numeric formula symbols,
  and derived values are not exposed as public parameters.

## Formula and units

- [ ] Formula terms, constants, unit conversions, output order, and numeric
  policy match the YAML specification.

## Retained targets

- [ ] Generated Rust uses `f64` scalar computation from the semantic IR.
- [ ] Generated native NumPy ufuncs use the same IR.
- [ ] Generated adapter types/constants and category-to-value mappings exist
  once per retained target; handwritten parsers are separate from generated
  mappings and accept only exact canonical text.
- [ ] Generated target tests cover every structured golden case.
- [ ] Valid IR unsupported by a retained target is reported as a generator
  capability blocker, not replaced with hand-written computation.

## Python API

- [ ] Public module and function names, keyword-only inputs, scalar/array
  behavior, broadcasting, `out`, and `NamedTuple` output match the contract.
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
or public-API mismatch; missing retained target or golden test; unsupported IR;
nondeterministic generation; unsubstantiated status transition; or exposed
repository-only specification paths.
