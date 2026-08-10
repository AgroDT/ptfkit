//! Wang et al. (2012) hydraulic-property regressions for the Chinese Loess Plateau.
//!
//! Formula source: `specs/functions/wang2012.md`.

/// Saturated water content, field capacity, and saturated hydraulic conductivity.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Wang2012Result {
    pub theta_s: f64,
    pub theta_fc: f64,
    pub k_sat: f64,
}

/// Estimate hydraulic properties of surface loess from texture and site properties.
#[must_use]
pub fn calc_ptf_wang2012(
    sand: f64,
    silt: f64,
    clay: f64,
    bulk_density: f64,
    soil_organic_carbon: f64,
    altitude: f64,
) -> Wang2012Result {
    let soil_organic_carbon_g_per_kg = 10.0 * soil_organic_carbon;

    let log10_k_sat_cm_per_day = 1.173 + 0.038 * silt + 0.690 * sand.log10() + 0.865 / sand
        - 0.030 * bulk_density * silt
        - 0.000_009_95 * soil_organic_carbon_g_per_kg * altitude;
    let k_sat_cm_per_day = 10.0_f64.powf(log10_k_sat_cm_per_day);

    let fc_percent = 46.481
        - 4.757 * soil_organic_carbon_g_per_kg
        - 14.028 * clay.log10()
        - 13.991 * sand.log10()
        + 42.261 * soil_organic_carbon_g_per_kg.log10()
        - 11.763 / sand
        + 19.198 / soil_organic_carbon_g_per_kg
        - 5.448 * bulk_density.powi(2)
        + 0.044 * soil_organic_carbon_g_per_kg.powi(2)
        + 1.975 * bulk_density * soil_organic_carbon_g_per_kg;

    let sswc_percent = 98.813 - 21.555 / bulk_density - 39.735 / silt - 2.091 / sand
        + 3.247 / soil_organic_carbon_g_per_kg
        - 17.096 * bulk_density.powi(2);

    Wang2012Result {
        theta_s: sswc_percent / 100.0,
        theta_fc: fc_percent / 100.0,
        k_sat: k_sat_cm_per_day / 8_640_000.0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use assertables::assert_le;

    fn assert_close(actual: f64, expected: f64) {
        assert_le!(
            (actual - expected).abs(),
            1.0e-12 + 1.0e-6 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn derivation_minimum_soc_golden_case() {
        let result = calc_ptf_wang2012(85.0, 10.0, 5.0, 1.22, 0.033, 1193.0);

        assert_close(result.theta_s, 0.615_405_75);
        assert_close(result.theta_fc, 0.384_919_49);
        assert_close(result.k_sat, 3.872_974e-5);
    }

    #[test]
    fn propagates_non_finite_results_for_invalid_log_and_reciprocal_inputs() {
        let result = calc_ptf_wang2012(0.0, 0.0, 0.0, 1.22, 0.0, 1193.0);

        assert!(!result.theta_s.is_finite());
        assert!(!result.theta_fc.is_finite());
        assert!(!result.k_sat.is_finite());
    }
}
