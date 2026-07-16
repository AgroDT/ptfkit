//! Aimrun and Amin (2009) saturated hydraulic conductivity PTF.
//!
//! Formula source: `specs/functions/calc_ptf_aimrun2009.md`.

const M_PER_DAY_TO_M_PER_SEC: f64 = 1.0 / 86_400.0;

/// Calculate saturated hydraulic conductivity with Aimrun and Amin (2009).
///
/// Inputs are clay and organic matter in percent, bulk density in g/cm^3, and
/// geometric mean diameter in mm. The output is saturated hydraulic
/// conductivity in m/s.
#[must_use]
pub fn calc_ptf_aimrun2009(clay: f64, bulk_density: f64, organic_matter: f64, gmd: f64) -> f64 {
    let ln_k_sat_m_per_day = -2.368 + 3.846 * bulk_density + 0.091 * organic_matter
        - 6.203 * bulk_density.ln()
        - 0.343 * organic_matter.ln()
        - 2.334 * clay.ln()
        - 0.411 * gmd.ln();

    ln_k_sat_m_per_day.exp() * M_PER_DAY_TO_M_PER_SEC
}

#[cfg(test)]
mod tests {
    use super::*;

    fn assert_close(actual: f64, expected: f64) {
        assert!(
            (actual - expected).abs() <= 1e-12 + 1e-8 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn calc_golden_cases() {
        assert_close(
            calc_ptf_aimrun2009(43.88, 0.94, 12.07, 0.010),
            7.358406556179513e-08,
        );
        assert_close(
            calc_ptf_aimrun2009(50.21, 1.19, 8.55, 0.007),
            3.07872446717209e-08,
        );
        assert_close(
            calc_ptf_aimrun2009(58.81, 1.13, 5.12, 0.005),
            2.3343051908963327e-08,
        );
        assert_close(
            calc_ptf_aimrun2009(47.50, 1.08, 1.43, 0.008),
            3.831168764444974e-08,
        );
    }
}
