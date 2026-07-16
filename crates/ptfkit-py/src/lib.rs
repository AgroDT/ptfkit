//! PyO3 bindings for ptfkit Rust kernels.

use pyo3::prelude::*;

/// Calculate Aimrun and Amin (2009) saturated hydraulic conductivity.
#[pyfunction]
fn calc_ptf_aimrun2009(clay: f64, bulk_density: f64, organic_matter: f64, gmd: f64) -> f64 {
    ptfkit_core::calc_ptf_aimrun2009(clay, bulk_density, organic_matter, gmd)
}

/// Calculate Cosby et al. (1984) univariate hydraulic parameter statistics.
#[pyfunction]
fn calc_ptf_cosby1984_univariate(
    sand: f64,
    silt: f64,
    clay: f64,
) -> (f64, f64, f64, f64, f64, f64, f64) {
    let result = ptfkit_core::calc_ptf_cosby1984_univariate(sand, silt, clay);
    (
        result.mean_b,
        result.mean_log_psi_s,
        result.mean_log_k_sat,
        result.mean_theta_s,
        result.sd_b,
        result.sd_log_k_sat,
        result.sd_theta_s,
    )
}

/// Calculate Jabro (1992) saturated hydraulic conductivity.
#[pyfunction]
fn calc_ptf_jabro1992(silt: f64, clay: f64, bulk_density: f64) -> f64 {
    ptfkit_core::calc_ptf_jabro1992(silt, clay, bulk_density)
}

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

/// Private ptfkit Rust extension module.
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calc_ptf_aimrun2009, m)?)?;
    m.add_function(wrap_pyfunction!(calc_ptf_cosby1984_univariate, m)?)?;
    m.add_function(wrap_pyfunction!(calc_ptf_jabro1992, m)?)?;
    m.add_function(wrap_pyfunction!(calc_ptf_li2007, m)?)?;
    Ok(())
}
