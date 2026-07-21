//! Li et al. (2007) Fengqiu County soil hydraulic PTF.
//!
//! Formula source:
//! `specs/functions/2007_Li_Estimating_soil_hydraulic_properties_of_Fengqiu_County_soils.md`.

const CM_PER_DAY_TO_M_PER_SEC: f64 = 1.0 / 8_640_000.0;

/// Results of the Li et al. (2007) PTF.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Li2007Result {
    /// Saturated water content (cm^3/cm^3).
    pub theta_s: f64,
    /// van Genuchten alpha parameter (cm^-1).
    pub a_vg: f64,
    /// van Genuchten n parameter.
    pub n_vg: f64,
    /// Saturated hydraulic conductivity (m/s).
    pub k_sat: f64,
}

/// Calculate van Genuchten parameters and saturated hydraulic conductivity.
///
/// Inputs are sand, silt, clay, and soil organic matter in percent, and bulk
/// density in g/cm^3. Outputs follow `Li2007Result` field order.
#[must_use]
pub fn calc_ptf_li2007(
    sand: f64,
    silt: f64,
    clay: f64,
    bulk_density: f64,
    soil_organic_matter: f64,
) -> Li2007Result {
    let sand_ln = sand.ln();
    let silt_ln = silt.ln();
    let clay_ln = clay.ln();
    let soil_organic_matter_ln = soil_organic_matter.ln();
    let bulk_density_ln = bulk_density.ln();

    let theta_s = (-1.531 + 0.212 * sand_ln + 0.006 * silt
        - 0.051 * soil_organic_matter
        - 0.566 * bulk_density_ln)
        .exp();

    let a_vg = (-67.408 - 0.040 * silt - 0.670 * silt_ln - 2.189 * soil_organic_matter
        + 1.410 * soil_organic_matter_ln
        + 78.400 * bulk_density
        - 121.331 * bulk_density_ln)
        .exp();

    let n_vg = 1.488 + 0.002 * silt_ln + 0.013 * clay - 0.248 * clay_ln
        + 0.048 * soil_organic_matter_ln
        + 0.451 * bulk_density_ln;

    let k_sat_cm_per_day = (13.262
        - 1.914 * sand_ln
        - 0.974 * silt_ln
        - 0.058 * clay
        - 1.709 * soil_organic_matter_ln
        + 2.885 * soil_organic_matter
        - 8.026 * bulk_density_ln)
        .exp();

    Li2007Result {
        theta_s,
        a_vg,
        n_vg,
        k_sat: k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC,
    }
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

    fn assert_result_close(actual: Li2007Result, expected: Li2007Result) {
        assert_close(actual.theta_s, expected.theta_s);
        assert_close(actual.a_vg, expected.a_vg);
        assert_close(actual.n_vg, expected.n_vg);
        assert_close(actual.k_sat, expected.k_sat);
    }

    #[test]
    fn calc_golden_cases() {
        assert_result_close(
            calc_ptf_li2007(85.0, 10.0, 5.0, 1.20, 0.21),
            Li2007Result {
                theta_s: 0.5256803583157499,
                a_vg: 0.9491464758307142,
                n_vg: 1.1657804980997006,
                k_sat: 6.549110367333547e-06,
            },
        );
        assert_result_close(
            calc_ptf_li2007(50.23, 38.72, 11.05, 1.42, 0.65),
            Li2007Result {
                theta_s: 0.49659526127697506,
                a_vg: 0.009519989841950734,
                n_vg: 1.1806286355149054,
                k_sat: 4.5117324656202257e-07,
            },
        );
        assert_result_close(
            calc_ptf_li2007(12.88, 60.0, 27.12, 1.48, 1.02),
            Li2007Result {
                theta_s: 0.4053061510618609,
                a_vg: 0.0018530400762371828,
                n_vg: 1.2080428739797433,
                k_sat: 1.5151432632107234e-06,
            },
        );
    }
}
