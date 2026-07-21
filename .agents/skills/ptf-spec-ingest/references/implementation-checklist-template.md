# Implementation Checklist Template

```markdown
# Implementation Checklist: <function_name>

## Spec Status

- [ ] Function-level spec path: `specs/functions/<function_name>.md`
- [ ] Spec version recorded.
- [ ] No blocking issues.

## Formula Traceability

- [ ] Inputs mapped to Rust parameters.
- [ ] Constants mapped to named Rust constants or local bindings.
- [ ] Intermediates mapped to local variables.
- [ ] Outputs mapped in declared order.
- [ ] Units and conversions implemented exactly as specified.

## Rust Core

- [ ] Pure Rust scalar `f64` kernel added.
- [ ] No Python, PyO3, NumPy, or allocation logic in pure core.
- [ ] Golden scalar cases covered.
- [ ] Domain behavior follows numeric policy.

## Python Bindings

- [ ] PyO3/maturin binding added.
- [ ] Public wrapper remains keyword-only.
- [ ] Scalar inputs tested.
- [ ] NumPy array inputs tested.
- [ ] Broadcasting tested when supported.
- [ ] `out` tested when supported.
- [ ] NamedTuple fields and order tested when applicable.

## Documentation

- [ ] Module docstring matches spec reference, scope, models, territory, and dataset.
- [ ] Function docstring documents inputs, units, outputs, and return value.
- [ ] Result class docs match output fields.

## Review

- [ ] `ptf-review` completed.
- [ ] Project checks recorded.
```
