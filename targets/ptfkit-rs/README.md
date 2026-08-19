# ptfkit for Rust

Rust implementations of the pedotransfer functions provided by ptfkit.
Functions use `f64` inputs and outputs and are grouped into modules named after
their source publications.

## Installation

```toml
[dependencies]
ptfkit = "0.1"
```

## Usage

```rust
use ptfkit::jabro1992::calc_ptf_jabro1992;

let k_sat = calc_ptf_jabro1992(20.0, 30.0, 1.3);
```

## Documentation

- [Rust API on docs.rs](https://docs.rs/ptfkit/)
- [PTF source catalogue](https://agrodt.github.io/ptfkit/ptf-catalog/)
- [Repository](https://github.com/AgroDT/ptfkit)

The applicability of each PTF depends on the dataset, territory, measurement
methods, and variable ranges reported by its source publication.
