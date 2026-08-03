//! PyO3 bindings for ptfkit Rust kernels.

use pyo3::prelude::*;

mod ufunc;

/// Private ptfkit Rust extension module.
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    ufunc::generated::register(m)?;
    Ok(())
}
