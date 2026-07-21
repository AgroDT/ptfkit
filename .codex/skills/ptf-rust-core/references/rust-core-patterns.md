# Rust Core Patterns

## Scope

Implement only pure numeric kernels in the Rust core crate. Keep Python binding,
NumPy vectorization, broadcasting, and `out` handling outside the pure core.

## Naming

- Rust scalar kernel: `calc_ptf_<author><year>[_<extra>]`
- Inputs: snake_case names from the spec.
- Constants: uppercase only for reusable unit conversions; otherwise use clear local names.

## Function Shape

Single output:

```rust
pub fn calc_ptf_example(sand: f64, clay: f64) -> f64 {
    let intermediate = sand + clay;
    intermediate
}
```

Multiple outputs:

```rust
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ExampleResult {
    pub theta_s: f64,
    pub k_sat: f64,
}

pub fn calc_ptf_example(sand: f64, clay: f64) -> ExampleResult {
    ExampleResult {
        theta_s: sand + clay,
        k_sat: sand - clay,
    }
}
```

## Numeric Policy

- Use `f64`.
- Do not round unless the spec requires it.
- Prefer native IEEE behavior for NaN and infinities when the spec says `numpy-compatible`.
- Do not clamp, sanitize, or reinterpret invalid inputs unless the spec says so.

## Traceability

Every formula line should be recognizable from the spec. If a formula needs
algebraic rearrangement for stability, note it in code comments and tests.

## Tests

- Embed golden scalar cases from the validated spec in Rust unit tests next to
  the implementation.
- Compare floats using the spec `rtol` and `atol`.
- Cover every output field.
- Use `assertables` assertions for comparison predicates.
