# ptfkit for Rust

Rust implementations of the pedotransfer functions provided by ptfkit.
Functions use `f64` inputs and outputs and are grouped into modules named after
their source publications.

## Installation

```toml
[dependencies]
ptfkit = "0.2"
```

## Usage

```rust
use ptfkit::jabro1992::calc_ptf_jabro1992;

let k_sat = calc_ptf_jabro1992(20.0, 30.0, 1.3);
```

## Features

The `inline` feature is enabled by default. It marks generated PTF functions
with `#[inline]`, making their bodies available to downstream optimization and
letting the compiler decide whether inlining is beneficial at each call site.
This is useful when an application evaluates several PTFs in a single pass over
a dataset while keeping control of its own data layout and iteration strategy.

For example, two saturated hydraulic conductivity estimates can be collected
in separate arrays during the same pass over the input data:

```rust
use ptfkit::ferrerjulia2004::{
    calc_ptf_ferrerjulia2004_campbell_shiozawa,
    calc_ptf_ferrerjulia2004_saxton,
};

let sand = [50.0, 42.0, 61.0];
let clay = [25.0, 31.0, 18.0];
let mut campbell_shiozawa = Vec::with_capacity(sand.len());
let mut saxton = Vec::with_capacity(sand.len());

for i in 0..sand.len() {
    campbell_shiozawa.push(calc_ptf_ferrerjulia2004_campbell_shiozawa(
        sand[i], clay[i],
    ));
    saxton.push(calc_ptf_ferrerjulia2004_saxton(sand[i], clay[i]));
}
```

To disable the inline hint, disable the crate's default features:

```toml
[dependencies]
ptfkit = { version = "0.2", default-features = false }
```

## Documentation

- [Rust API on docs.rs](https://docs.rs/ptfkit/)
- [PTF source catalogue](https://agrodt.github.io/ptfkit/ptf-catalog/)
- [Repository](https://github.com/AgroDT/ptfkit)

The applicability of each PTF depends on the dataset, territory, measurement
methods, and variable ranges reported by its source publication.
