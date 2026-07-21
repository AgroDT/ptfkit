use pyo3::prelude::*;

/// Calculate Aimrun and Amin (2009) saturated hydraulic conductivity.
#[pyfunction]
fn calc_ptf_aimrun2009(clay: f64, bulk_density: f64, organic_matter: f64, gmd: f64) -> f64 {
    ptfkit_core::calc_ptf_aimrun2009(clay, bulk_density, organic_matter, gmd)
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calc_ptf_aimrun2009, m)?)?;
    Ok(())
}
