use pyo3::prelude::*;

/// Calculate Jabro (1992) saturated hydraulic conductivity.
#[pyfunction]
fn calc_ptf_jabro1992(silt: f64, clay: f64, bulk_density: f64) -> f64 {
    ptfkit_core::calc_ptf_jabro1992(silt, clay, bulk_density)
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calc_ptf_jabro1992, m)?)?;
    Ok(())
}
