//! Rawls et al. (1982) water-retention regressions for soils across the USA.
//!
//! Formula source: `specs/functions/rawls1982.md`.

/// Twelve-point water-retention curve.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Rawls1982FullWrcResult {
    pub theta_4: f64,
    pub theta_7: f64,
    pub theta_10: f64,
    pub theta_20: f64,
    pub theta_33: f64,
    pub theta_60: f64,
    pub theta_100: f64,
    pub theta_200: f64,
    pub theta_400: f64,
    pub theta_700: f64,
    pub theta_1000: f64,
    pub theta_1500: f64,
}

/// Estimate volumetric water content at -1500 kPa.
#[must_use]
pub fn calc_ptf_rawls1982_theta_1500(clay: f64, organic_matter: f64) -> f64 {
    0.0260 + 0.0050 * clay + 0.0158 * organic_matter
}

/// Estimate volumetric water content at -33 kPa.
#[must_use]
pub fn calc_ptf_rawls1982_theta_33(sand: f64, organic_matter: f64, theta_1500: f64) -> f64 {
    0.2391 - 0.0019 * sand + 0.0210 * organic_matter + 0.72 * theta_1500
}

/// Estimate a twelve-point water-retention curve.
#[must_use]
pub fn calc_ptf_rawls1982_full_wrc(
    sand: f64,
    organic_matter: f64,
    bulk_density: f64,
    theta_33: f64,
    theta_1500: f64,
) -> Rawls1982FullWrcResult {
    Rawls1982FullWrcResult {
        theta_4: 0.1829 - 0.0246 * organic_matter - 0.0376 * bulk_density + 1.89 * theta_33
            - 1.38 * theta_1500,
        theta_7: 0.8888 - 0.0003 * sand - 0.0107 * organic_matter + 1.53 * theta_33
            - 0.81 * theta_1500,
        theta_10: 0.0619 - 0.0002 * sand - 0.0067 * organic_matter + 1.34 * theta_33
            - 0.51 * theta_1500,
        theta_20: 0.0319 - 0.0002 * sand + 1.01 * theta_33 - 0.06 * theta_1500,
        theta_33,
        theta_60: 0.0136 - 0.0091 * bulk_density + 0.66 * theta_33 + 0.39 * theta_1500,
        theta_100: -0.0034 + 0.0022 * organic_matter + 0.52 * theta_33 + 0.54 * theta_1500,
        theta_200: -0.0043 + 0.0026 * organic_matter + 0.36 * theta_33 + 0.69 * theta_1500,
        theta_400: -0.0038 + 0.0026 * organic_matter + 0.24 * theta_33 + 0.79 * theta_1500,
        theta_700: -0.0027 + 0.0024 * organic_matter + 0.16 * theta_33 + 0.86 * theta_1500,
        theta_1000: -0.0019 + 0.0022 * organic_matter + 0.11 * theta_33 + 0.89 * theta_1500,
        theta_1500,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use assertables::assert_le;

    fn assert_close(actual: f64, expected: f64) {
        assert_le!(
            (actual - expected).abs(),
            1.0e-12 + 1.0e-10 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn theta_1500_golden_case() {
        assert_close(calc_ptf_rawls1982_theta_1500(5.12, 0.1), 0.05318);
    }

    #[test]
    fn theta_33_golden_case() {
        assert_close(calc_ptf_rawls1982_theta_33(85.0, 0.1, 0.05318), 0.1179896);
    }

    #[test]
    fn full_wrc_golden_case() {
        let result = calc_ptf_rawls1982_full_wrc(85.0, 0.66, 1.22, 0.091, 0.033);

        assert_close(result.theta_4, 0.247242);
        assert_close(result.theta_7, 0.968738);
        assert_close(result.theta_10, 0.145588);
        assert_close(result.theta_20, 0.10483);
        assert_close(result.theta_33, 0.091);
        assert_close(result.theta_60, 0.075428);
        assert_close(result.theta_100, 0.063192);
        assert_close(result.theta_200, 0.052946);
        assert_close(result.theta_400, 0.045826);
        assert_close(result.theta_700, 0.041824);
        assert_close(result.theta_1000, 0.038932);
        assert_close(result.theta_1500, 0.033);
    }
}
