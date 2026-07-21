use pyo3::prelude::*;

/// Calculate Li et al. (2007) soil hydraulic parameters.
#[pyfunction]
fn calc_ptf_li2007(
    sand: f64,
    silt: f64,
    clay: f64,
    bulk_density: f64,
    soil_organic_matter: f64,
) -> (f64, f64, f64, f64) {
    let result = ptfkit_core::calc_ptf_li2007(sand, silt, clay, bulk_density, soil_organic_matter);
    (result.theta_s, result.a_vg, result.n_vg, result.k_sat)
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calc_ptf_li2007, m)?)?;
    Ok(())
}
