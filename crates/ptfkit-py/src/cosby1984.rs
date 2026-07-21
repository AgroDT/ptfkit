use pyo3::prelude::*;

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

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calc_ptf_cosby1984_univariate, m)?)?;
    Ok(())
}
