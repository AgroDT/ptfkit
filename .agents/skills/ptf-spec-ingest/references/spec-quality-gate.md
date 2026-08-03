# Spec Quality Gate

## Required Location

- The spec must be a function-level file under `specs/functions/*.md`.
- `ptf-spec-ingest` may create function-level specs from a user-supplied local
  source file, but implementation may start only from specs that pass this gate.

## Required Sections

- `Status`
- `Identity`
- `Reference`
- `Scope`
- `Inputs`
- `Outputs`
- `Constants`
- `Formula`
- `Units Policy`
- `Numeric Policy`
- `Vectorization Contract`
- `Python API Contract`
- `Golden Tests`

## Required Checks

- `status` is `ready-for-implementation`.
- `function_name`, `public_module`, `public_function`, and `rust_function` are present.
- Every formula symbol is declared as an input, output, constant, or intermediate.
- Every input and output has units.
- Unit conversions are explicit constants.
- Output order matches `result_fields` for namedtuple results.
- Numeric policy defines precision, rounding, NaN, and invalid input behavior.
- Vectorization contract says whether scalar, ndarray, broadcasting, and `out` are supported.
- Golden tests include inputs, expected outputs, `rtol`, and `atol`.
- Golden tests cover every output field.

## Blocking Issues

- Missing or ambiguous formula.
- Formula references source text instead of giving implementable equations.
- Variable appears in formula but is not declared.
- Missing units for any input, output, constant, or conversion.
- Conflicting units between formula, tables, and expected outputs.
- Missing golden tests or missing expected outputs.
- Missing tolerance for floating point comparison.
- Missing output field names for multi-output functions.
- Missing public Python API contract.
- API contract breaks an existing public function without an explicit migration note.
- Unclear handling of logarithms, powers, division by zero, negative domains, or NaN.
- Spec requires categorical inputs without encoding rules.
- Current file is source material, not a function-level spec.
- Generated spec contains `TODO` in required formula, units, constants, golden
  tests, numeric policy, or Python API sections.

## Ready Decision

Mark `Ready for implementation` only when no blocking issues remain. Otherwise
return `Blocked` with a short list of questions for the spec owner.
