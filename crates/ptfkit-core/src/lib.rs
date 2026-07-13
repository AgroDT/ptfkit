//! Pure Rust numerical kernels for ptfkit.

pub mod cosby1984;

pub use cosby1984::{calc_ptf_cosby1984_univariate, Cosby1984UnivariateResult};
