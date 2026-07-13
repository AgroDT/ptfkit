//! Cosby et al. (1984) univariate hydraulic parameter statistics.
//!
//! Formulas are taken from `specs/functions/calc_ptf_cosby1984_univariate.md`.

/// Results of the Cosby et al. (1984) univariate pilot PTF.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Cosby1984UnivariateResult {
    /// Mean slope of the moisture characteristic.
    pub mean_b: f64,
    /// Mean log saturation matric potential.
    pub mean_log_psi_s: f64,
    /// Mean log saturated hydraulic conductivity.
    pub mean_log_k_sat: f64,
    /// Mean saturated water content (% volume/volume).
    pub mean_theta_s: f64,
    /// Standard deviation of `b`.
    pub sd_b: f64,
    /// Standard deviation of log saturated hydraulic conductivity.
    pub sd_log_k_sat: f64,
    /// Standard deviation of saturated water content (% volume/volume).
    pub sd_theta_s: f64,
}

/// Calculate Cosby et al. (1984) univariate hydraulic parameter statistics.
///
/// Inputs are sand, silt, and clay content in percent. Outputs follow the
/// field order declared in `calc_ptf_cosby1984_univariate.md`.
#[must_use]
pub fn calc_ptf_cosby1984_univariate(sand: f64, silt: f64, clay: f64) -> Cosby1984UnivariateResult {
    Cosby1984UnivariateResult {
        mean_b: 2.91 + 0.159 * clay,
        mean_log_psi_s: 1.88 - 0.0131 * sand,
        mean_log_k_sat: -0.884 + 0.0153 * sand,
        mean_theta_s: 48.9 - 0.126 * sand,
        sd_b: 1.34 + 0.0500 * clay,
        sd_log_k_sat: 0.459 + 0.00321 * silt,
        sd_theta_s: 7.73 - 0.0730 * clay,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn assert_close(actual: f64, expected: f64) {
        assert!(
            (actual - expected).abs() <= 1e-12,
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn calc_mid_texture_golden_case() {
        let result = calc_ptf_cosby1984_univariate(50.0, 30.0, 20.0);

        assert_close(result.mean_b, 6.09);
        assert_close(result.mean_log_psi_s, 1.225);
        assert_close(result.mean_log_k_sat, -0.119);
        assert_close(result.mean_theta_s, 42.6);
        assert_close(result.sd_b, 2.34);
        assert_close(result.sd_log_k_sat, 0.5553);
        assert_close(result.sd_theta_s, 6.27);
    }

    #[test]
    fn calc_sandy_texture_golden_case() {
        let result = calc_ptf_cosby1984_univariate(80.0, 15.0, 5.0);

        assert_close(result.mean_b, 3.705);
        assert_close(result.mean_log_psi_s, 0.832);
        assert_close(result.mean_log_k_sat, 0.34);
        assert_close(result.mean_theta_s, 38.82);
        assert_close(result.sd_b, 1.59);
        assert_close(result.sd_log_k_sat, 0.50715);
        assert_close(result.sd_theta_s, 7.365);
    }
}
