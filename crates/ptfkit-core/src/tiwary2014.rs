//! Tiwary et al. (2014) hydraulic PTFs for two major soil regions of India.
//!
//! Formula source: `specs/functions/tiwary2014.md`.

const MM_PER_HOUR_TO_M_PER_SEC: f64 = 1.0 / 3_600_000.0;

/// Results of the Tiwary et al. (2014) black soil region PTF.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Tiwary2014PTFResult {
    /// Gravimetric water content at 33 kPa (%).
    pub w_33: f64,
    /// Gravimetric water content at 100 kPa (%).
    pub w_100: f64,
    /// Gravimetric water content at 1500 kPa (%).
    pub w_1500: f64,
    /// Saturated hydraulic conductivity (m/s).
    pub k_sat: f64,
}

/// Estimate saturated hydraulic conductivity for Indo-Gangetic Plains soils.
#[must_use]
pub fn calc_ptf_tiwary2014_igp(sand: f64, bulk_density: f64, esp: f64) -> f64 {
    let k_sat_mm_per_hour = 4.079 + 0.047 * sand - 0.054 * esp - 2.238 * bulk_density;
    k_sat_mm_per_hour * MM_PER_HOUR_TO_M_PER_SEC
}

/// Estimate water retention and saturated conductivity for the black soil region.
#[must_use]
pub fn calc_ptf_tiwary2014_bsr(
    clay: f64,
    ph: f64,
    cation_exchange_capacity: f64,
    esp: f64,
    emp: f64,
    excm: f64,
) -> Tiwary2014PTFResult {
    let w_33 = 2.583 + 0.346 * cation_exchange_capacity + 0.249 * clay + 0.494 * esp;
    let w_100 = -1.918 + 0.383 * cation_exchange_capacity + 0.228 * clay + 0.361 * esp;
    let w_1500 = 0.541 + 0.306 * cation_exchange_capacity + 0.146 * esp + 0.058 * emp;
    let k_sat_mm_per_hour = 120.637 - 13.094 * ph - 0.102 * clay + 1.151 * excm;

    Tiwary2014PTFResult {
        w_33,
        w_100,
        w_1500,
        k_sat: k_sat_mm_per_hour * MM_PER_HOUR_TO_M_PER_SEC,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use assertables::assert_le;

    fn assert_close(actual: f64, expected: f64) {
        assert_le!(
            (actual - expected).abs(),
            1e-12 + 1e-10 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn calc_igp_golden_case() {
        assert_close(calc_ptf_tiwary2014_igp(37.3, 1.674, 4.6), 5.103578e-07);
    }

    #[test]
    fn calc_bsr_golden_case() {
        let result = calc_ptf_tiwary2014_bsr(54.9, 7.6, 61.6, 7.3, 21.4, 3.32);

        assert_close(result.w_33, 41.1729);
        assert_close(result.w_100, 36.8273);
        assert_close(result.w_1500, 21.6976);
        assert_close(result.k_sat, 5.373367e-06);
    }

    #[test]
    fn propagates_nan() {
        assert!(calc_ptf_tiwary2014_igp(f64::NAN, 1.674, 4.6).is_nan());

        let result = calc_ptf_tiwary2014_bsr(54.9, 7.6, f64::NAN, 7.3, 21.4, 3.32);
        assert!(result.w_33.is_nan());
        assert!(result.w_100.is_nan());
        assert!(result.w_1500.is_nan());
    }
}
