//! Beniaich et al. (2023) soil-water regressions for four Moroccan regions.
//!
//! Formula source: `specs/functions/beniaich2023.md`.

/// Gravimetric water contents at saturation, field capacity, and wilting point.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Beniaich2023Result {
    pub water_saturation: f64,
    pub water_field_capacity: f64,
    pub water_wilting_point: f64,
}

fn result(
    saturation_percent: f64,
    field_capacity_percent: f64,
    wilting_percent: f64,
) -> Beniaich2023Result {
    Beniaich2023Result {
        water_saturation: saturation_percent / 100.0,
        water_field_capacity: field_capacity_percent / 100.0,
        water_wilting_point: wilting_percent / 100.0,
    }
}

/// Estimate water contents with the clay-only simple linear regressions.
#[must_use]
pub fn calc_ptf_beniaich2023_slr1(clay: f64) -> Beniaich2023Result {
    result(
        46.307 + 0.556 * clay,
        10.277 + 0.365 * clay,
        3.081 + 0.327 * clay,
    )
}

/// Estimate water contents with the silt-only simple linear regressions.
#[must_use]
pub fn calc_ptf_beniaich2023_slr2(silt: f64) -> Beniaich2023Result {
    result(
        59.508 + 0.299 * silt,
        16.178 + 0.290 * silt,
        10.521 + 0.187 * silt,
    )
}

/// Estimate water contents with the sand-only simple linear regressions.
#[must_use]
pub fn calc_ptf_beniaich2023_slr3(sand: f64) -> Beniaich2023Result {
    result(
        81.420 - 0.427 * sand,
        34.680 - 0.324 * sand,
        23.927 - 0.257 * sand,
    )
}

/// Estimate water contents from the sum of clay and silt.
#[must_use]
pub fn calc_ptf_beniaich2023_slr4(clay: f64, silt: f64) -> Beniaich2023Result {
    let clay_silt = clay + silt;
    result(
        89.401 - 0.298 * clay_silt,
        45.178 - 0.290 * clay_silt,
        29.265 - 0.187 * clay_silt,
    )
}

/// Estimate water contents from the clay-to-silt ratio.
#[must_use]
pub fn calc_ptf_beniaich2023_slr5(clay: f64, silt: f64) -> Beniaich2023Result {
    let clay_silt_ratio = clay / silt;
    result(
        68.851 - 0.546 * clay_silt_ratio,
        23.278 + 1.819 * clay_silt_ratio,
        16.298 - 0.244 * clay_silt_ratio,
    )
}

/// Estimate water contents from soil organic matter.
#[must_use]
pub fn calc_ptf_beniaich2023_slr6(soil_organic_matter: f64) -> Beniaich2023Result {
    result(
        61.163 + 2.793 * soil_organic_matter,
        21.331 + 1.339 * soil_organic_matter,
        13.758 + 0.902 * soil_organic_matter,
    )
}

/// Estimate water contents from silt, sand, and soil organic matter.
#[must_use]
pub fn calc_ptf_beniaich2023_mlr1(
    silt: f64,
    sand: f64,
    soil_organic_matter: f64,
) -> Beniaich2023Result {
    result(
        87.342 - 0.281 * silt - 0.548 * sand + 2.377 * soil_organic_matter,
        35.844 - 0.085 * silt - 0.359 * sand + 0.947 * soil_organic_matter,
        28.734 - 0.148 * silt - 0.324 * sand + 0.636 * soil_organic_matter,
    )
}

/// Estimate water contents from sand and soil organic matter.
#[must_use]
pub fn calc_ptf_beniaich2023_mlr2(sand: f64, soil_organic_matter: f64) -> Beniaich2023Result {
    result(
        75.366 - 0.417 * sand + 2.219 * soil_organic_matter,
        32.227 - 0.320 * sand + 0.899 * soil_organic_matter,
        22.421 - 0.254 * sand + 0.552 * soil_organic_matter,
    )
}

/// Estimate water contents from silt and soil organic matter.
#[must_use]
pub fn calc_ptf_beniaich2023_mlr3(silt: f64, soil_organic_matter: f64) -> Beniaich2023Result {
    result(
        53.777 + 0.278 * silt + 2.457 * soil_organic_matter,
        13.847 + 0.281 * silt + 0.999 * soil_organic_matter,
        8.929 + 0.182 * silt + 0.683 * soil_organic_matter,
    )
}

/// Estimate water contents from clay and soil organic matter.
#[must_use]
pub fn calc_ptf_beniaich2023_mlr4(clay: f64, soil_organic_matter: f64) -> Beniaich2023Result {
    result(
        39.432 + 0.553 * clay + 2.699 * soil_organic_matter,
        7.023 + 0.364 * clay + 1.278 * soil_organic_matter,
        0.923 + 0.327 * clay + 0.847 * soil_organic_matter,
    )
}

/// Estimate water contents from clay, silt, and soil organic matter.
#[must_use]
pub fn calc_ptf_beniaich2023_mlr5(
    clay: f64,
    silt: f64,
    soil_organic_matter: f64,
) -> Beniaich2023Result {
    result(
        32.505 + 0.548 * clay + 0.267 * silt + 2.377 * soil_organic_matter,
        -0.094 + 0.359 * clay + 0.274 * silt + 0.947 * soil_organic_matter,
        -3.623 + 0.324 * clay + 0.175 * silt + 0.636 * soil_organic_matter,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use assertables::assert_le;

    fn assert_close(actual: f64, expected: f64) {
        assert_le!(
            (actual - expected).abs(),
            1.0e-12 + 1.0e-12 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    fn assert_result(actual: Beniaich2023Result, expected: [f64; 3]) {
        assert_close(actual.water_saturation, expected[0]);
        assert_close(actual.water_field_capacity, expected[1]);
        assert_close(actual.water_wilting_point, expected[2]);
    }

    #[test]
    fn table_5_golden_cases() {
        assert_result(
            calc_ptf_beniaich2023_slr1(20.0),
            [0.57427, 0.17577, 0.09621],
        );
        assert_result(
            calc_ptf_beniaich2023_slr2(30.0),
            [0.68478, 0.24878, 0.16131],
        );
        assert_result(
            calc_ptf_beniaich2023_slr3(50.0),
            [0.60070, 0.18480, 0.11077],
        );
        assert_result(
            calc_ptf_beniaich2023_slr4(20.0, 30.0),
            [0.74501, 0.30678, 0.19915],
        );
        assert_result(
            calc_ptf_beniaich2023_slr5(20.0, 40.0),
            [0.68578, 0.241875, 0.16176],
        );
        assert_result(calc_ptf_beniaich2023_slr6(2.0), [0.66749, 0.24009, 0.15562]);
    }

    #[test]
    fn table_6_golden_cases() {
        assert_result(
            calc_ptf_beniaich2023_mlr1(30.0, 50.0, 2.0),
            [0.56266, 0.17238, 0.09366],
        );
        assert_result(
            calc_ptf_beniaich2023_mlr2(50.0, 2.0),
            [0.58954, 0.18025, 0.10825],
        );
        assert_result(
            calc_ptf_beniaich2023_mlr3(30.0, 2.0),
            [0.67031, 0.24275, 0.15755],
        );
        assert_result(
            calc_ptf_beniaich2023_mlr4(20.0, 2.0),
            [0.55890, 0.16859, 0.09157],
        );
        assert_result(
            calc_ptf_beniaich2023_mlr5(20.0, 30.0, 2.0),
            [0.56229, 0.17200, 0.09379],
        );
    }

    #[test]
    fn slr5_propagates_zero_silt() {
        let actual = calc_ptf_beniaich2023_slr5(20.0, 0.0);
        assert!(!actual.water_saturation.is_finite());
        assert!(!actual.water_field_capacity.is_finite());
        assert!(!actual.water_wilting_point.is_finite());
    }
}
