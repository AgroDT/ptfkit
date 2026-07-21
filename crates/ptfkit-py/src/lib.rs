//! PyO3 bindings for ptfkit Rust kernels.

use pyo3::prelude::*;

mod aimrun2009;
mod cosby1984;
mod jabro1992;
mod li2007;

/// Private ptfkit Rust extension module.
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    aimrun2009::register(m)?;
    cosby1984::register(m)?;
    jabro1992::register(m)?;
    li2007::register(m)?;
    Ok(())
}
