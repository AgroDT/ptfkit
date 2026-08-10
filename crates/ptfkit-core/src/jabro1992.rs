//! Jabro (1992) saturated hydraulic conductivity PTF.
//!
//! Formula source: `specs/functions/jabro1992.md`.

const CM_PER_HOUR_TO_M_PER_SEC: f64 = 1.0 / 360_000.0;

/// Calculate saturated hydraulic conductivity with Jabro (1992).
///
/// Inputs are silt and clay content in percent and bulk density in g/cm^3.
/// The output is saturated hydraulic conductivity in m/s.
#[must_use]
pub fn calc_ptf_jabro1992(silt: f64, clay: f64, bulk_density: f64) -> f64 {
    let log10_k_sat_cm_per_hour =
        9.56 - 0.81 * silt.log10() - 1.09 * clay.log10() - 4.64 * bulk_density;
    10.0_f64.powf(log10_k_sat_cm_per_hour) * CM_PER_HOUR_TO_M_PER_SEC
}

#[cfg(test)]
mod tests {
    use super::*;
    use assertables::assert_le;

    fn assert_close(actual: f64, expected: f64) {
        assert_le!(
            (actual - expected).abs(),
            1e-12 + 1e-8 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn calc_golden_cases() {
        assert_close(calc_ptf_jabro1992(10.0, 5.0, 1.26), 0.0003849640675896946);
        assert_close(
            calc_ptf_jabro1992(38.72, 11.05, 1.42),
            9.804037952717678e-06,
        );
        assert_close(calc_ptf_jabro1992(52.0, 30.0, 1.97), 7.292435947882127e-09);
        assert_close(calc_ptf_jabro1992(0.2, 44.0, 1.61), 2.032824027706267e-05);
    }
}
