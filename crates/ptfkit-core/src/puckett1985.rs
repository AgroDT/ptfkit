//! Puckett et al. (1985) water-retention and saturated-conductivity regressions.
//!
//! Formula source: `specs/functions/puckett1985.md`.

/// Point water-retention estimates and saturated hydraulic conductivity.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Puckett1985Result {
    pub theta_0: f64,
    pub theta_1: f64,
    pub theta_5: f64,
    pub theta_10: f64,
    pub theta_30: f64,
    pub theta_60: f64,
    pub theta_100: f64,
    pub theta_500: f64,
    pub theta_1000: f64,
    pub theta_1500: f64,
    pub k_sat: f64,
}

/// Estimate a point water-retention curve and saturated hydraulic conductivity.
#[must_use]
pub fn calc_ptf_puckett1985(
    sand: f64,
    fine_sand: f64,
    clay: f64,
    bulk_density: f64,
    porosity: f64,
) -> Puckett1985Result {
    Puckett1985Result {
        theta_0: 0.264 * bulk_density + 1.60 * porosity - 0.706,
        theta_1: 0.318 * bulk_density + 1.69 * porosity - 0.834,
        theta_5: 0.000_193_0 * fine_sand - 0.000_357 * sand + 0.000_182 * clay + 0.410,
        theta_10: 0.000_071_2 * fine_sand - 0.000_383 * sand + 0.000_243 * clay + 0.415,
        theta_30: 0.000_005_9 * fine_sand - 0.000_348 * sand + 0.000_321 * clay + 0.365,
        theta_60: 0.000_000_3 * fine_sand - 0.000_319 * sand + 0.000_351 * clay + 0.330,
        theta_100: 0.000_001_9 * fine_sand - 0.000_302 * sand + 0.000_362 * clay + 0.310,
        theta_500: 0.000_014_0 * fine_sand - 0.000_262 * sand + 0.000_375 * clay + 0.265,
        theta_1000: 0.000_019_7 * fine_sand - 0.000_244 * sand + 0.000_378 * clay + 0.264,
        theta_1500: 0.000_025_4 * fine_sand - 0.000_239 * sand + 0.000_380 * clay + 0.239,
        k_sat: 4.36e-5 * (-0.1975 * clay).exp(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use assertables::assert_le;

    fn assert_close(actual: f64, expected: f64) {
        assert_le!(
            (actual - expected).abs(),
            1.0e-12 + 1.0e-8 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn cahaba_ap_golden_case() {
        let result = calc_ptf_puckett1985(70.9, 36.4, 11.8, 1.67, 0.380);

        assert_close(result.theta_0, 0.34288);
        assert_close(result.theta_1, 0.33926);
        assert_close(result.theta_5, 0.3938615);
        assert_close(result.theta_10, 0.39330438);
        assert_close(result.theta_30, 0.34432936);
        assert_close(result.theta_60, 0.31153562);
        assert_close(result.theta_100, 0.29292896);
        assert_close(result.theta_500, 0.2513588);
        assert_close(result.theta_1000, 0.25187788);
        assert_close(result.theta_1500, 0.22746346);
        assert_close(result.k_sat, 4.2399741e-06);
    }

    #[test]
    fn propagates_nan() {
        let result = calc_ptf_puckett1985(f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN);

        assert!(result.theta_0.is_nan());
        assert!(result.theta_1.is_nan());
        assert!(result.theta_5.is_nan());
        assert!(result.theta_10.is_nan());
        assert!(result.theta_30.is_nan());
        assert!(result.theta_60.is_nan());
        assert!(result.theta_100.is_nan());
        assert!(result.theta_500.is_nan());
        assert!(result.theta_1000.is_nan());
        assert!(result.theta_1500.is_nan());
        assert!(result.k_sat.is_nan());
    }
}
