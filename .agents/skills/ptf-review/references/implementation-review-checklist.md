# Implementation Review Checklist

## Spec Traceability

- [ ] Implementation uses a source-oriented spec from `specs/functions/*.md`.
- [ ] Spec passed `ptf-spec-ingest`.
- [ ] No formulas, constants, units, or expected values were inferred beyond the
  validated source specification.
- [ ] Every implemented variable maps to spec input, output, constant, or intermediate.

## Formula And Units

- [ ] Formula terms match the spec.
- [ ] Constants match exact spec values.
- [ ] Unit conversions are explicit and tested.
- [ ] Output order matches the ordered YAML `outputs` list.
- [ ] Numeric policy for rounding, NaN, and invalid inputs is respected.

## Golden Tests

- [ ] Golden cases cover every output.
- [ ] Scalar public API tests exist.
- [ ] NumPy ndarray tests exist.
- [ ] Broadcasting tests exist when supported.
- [ ] `out` tests exist when supported.
- [ ] Tolerances match the spec.

## Rust Core

- [ ] Pure core uses `f64`.
- [ ] Pure core does not depend on Python, PyO3, or NumPy.
- [ ] Rust tests compare against golden cases when a Rust test harness exists.

## Python API

- [ ] Public module and function names are correct.
- [ ] Wrapper remains keyword-only.
- [ ] Type overloads are present or intentionally updated.
- [ ] Multi-output functions return the documented `NamedTuple`.
- [ ] Existing public API compatibility is preserved.
- [ ] Omitted top-level `python_generation` is treated as generated; a manual
      module has a justified `python_generation: manual` entry.

## Documentation

- [ ] Module docstring matches reference and scope from spec.
- [ ] Module summary is the hand-authored `source.summary` (at most 100
      characters); the APA citation and DOI identifier/URL match the spec.
- [ ] Module and function territories are rendered from independent scope fields
      without inheritance or combination.
- [ ] Function docstring lists input and output units.
- [ ] Result class docs match output fields.

## Blocking Findings

Classify as blocking:

- Missing function-level spec.
- Missing or failing golden tests.
- Unit mismatch.
- Formula mismatch.
- Output field order mismatch.
- Public API break without explicit approval.
- Missing vectorized behavior promised by the spec.
