//! Pidgeon (1972) available-water regressions for ferrallitic soils.
//!
//! Formula source: `specs/functions/pidgeon1972.md`.

/// Estimate gravimetric field capacity from method-2 silt and clay and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_fc(silt: f64, clay: f64, organic_matter: f64) -> f64 {
    7.38 + 0.16 * silt + 0.30 * clay + 1.54 * organic_matter
}

/// Estimate gravimetric field capacity from method-2 sand.
#[must_use]
pub fn calc_ptf_pidgeon1972_fc_sand(sand: f64) -> f64 {
    36.16 - 0.25 * sand
}

/// Estimate gravimetric field capacity from method-2 sand and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_fc_sand_organic_matter(sand: f64, organic_matter: f64) -> f64 {
    34.27 - 0.27 * sand + 1.25 * organic_matter
}

/// Estimate volumetric field capacity from method-2 sand and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_fc_vol_sand_organic_matter(sand: f64, organic_matter: f64) -> f64 {
    38.15 - 0.17 * sand + 0.77 * organic_matter
}

/// Estimate permanent wilting point from method-2 silt and clay and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_pwp(silt: f64, clay: f64, organic_matter: f64) -> f64 {
    -4.19 + 0.19 * silt + 0.39 * clay + 0.90 * organic_matter
}

/// Estimate permanent wilting point from method-1 sand.
#[must_use]
pub fn calc_ptf_pidgeon1972_pwp_sand(sand: f64) -> f64 {
    28.41 - 0.29 * sand
}

/// Estimate permanent wilting point from method-2 sand and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_pwp_sand_organic_matter(sand: f64, organic_matter: f64) -> f64 {
    32.90 - 0.37 * sand + 0.44 * organic_matter
}

/// Estimate available water capacity from method-1 clay and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_awc(clay: f64, organic_matter: f64) -> f64 {
    169.3 - 1.50 * clay + 6.09 * organic_matter
}

/// Estimate available water capacity from method-2 sand and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_awc_sand_organic_matter(sand: f64, organic_matter: f64) -> f64 {
    1.0 + 1.84 * sand + 8.12 * organic_matter
}

/// Estimate available water capacity from method-1 coarse sand.
#[must_use]
pub fn calc_ptf_pidgeon1972_awc_coarse_sand(coarse_sand: f64) -> f64 {
    68.5 + 2.33 * coarse_sand
}

/// Estimate available water capacity from method-1 fine sand.
#[must_use]
pub fn calc_ptf_pidgeon1972_awc_fine_sand(fine_sand: f64) -> f64 {
    66.7 + 2.66 * fine_sand
}

/// Estimate available water capacity from method-1 very fine sand.
#[must_use]
pub fn calc_ptf_pidgeon1972_awc_very_fine_sand(very_fine_sand: f64) -> f64 {
    66.9 + 4.58 * very_fine_sand
}

/// Estimate extended available water capacity from method-2 silt and clay and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_eawc(silt: f64, clay: f64, organic_matter: f64) -> f64 {
    121.1 - 3.03 * silt - 1.38 * clay + 6.76 * organic_matter
}

/// Estimate extended available water capacity from method-2 sand.
#[must_use]
pub fn calc_ptf_pidgeon1972_eawc_sand(sand: f64) -> f64 {
    -25.8 + 1.55 * sand
}

/// Estimate extended available water capacity from method-1 sand and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_eawc_sand_organic_matter(sand: f64, organic_matter: f64) -> f64 {
    -10.8 + 1.15 * sand + 4.78 * organic_matter
}

/// Estimate extended available water capacity from method-1 coarse sand and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter(
    coarse_sand: f64,
    organic_matter: f64,
) -> f64 {
    -7.4 + 2.37 * coarse_sand + 6.86 * organic_matter
}

/// Estimate extended available water capacity from method-1 fine sand and organic matter.
#[must_use]
pub fn calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter(
    fine_sand: f64,
    organic_matter: f64,
) -> f64 {
    -18.0 + 3.11 * fine_sand + 7.69 * organic_matter
}

#[cfg(test)]
mod tests {
    use super::*;
    use assertables::assert_le;

    fn assert_close(actual: f64, expected: f64) {
        assert_le!(
            (actual - expected).abs(),
            1e-12 + 1e-12 * expected.abs(),
            "actual {actual} != expected {expected}"
        );
    }

    #[test]
    fn calc_golden_cases() {
        assert_close(calc_ptf_pidgeon1972_fc(30.0, 20.0, 2.0), 21.26);
        assert_close(calc_ptf_pidgeon1972_fc_sand(50.0), 23.66);
        assert_close(
            calc_ptf_pidgeon1972_fc_sand_organic_matter(50.0, 2.0),
            23.27,
        );
        assert_close(
            calc_ptf_pidgeon1972_fc_vol_sand_organic_matter(50.0, 2.0),
            31.19,
        );
        assert_close(calc_ptf_pidgeon1972_pwp(30.0, 20.0, 2.0), 11.11);
        assert_close(calc_ptf_pidgeon1972_pwp_sand(50.0), 13.91);
        assert_close(
            calc_ptf_pidgeon1972_pwp_sand_organic_matter(50.0, 2.0),
            15.28,
        );
        assert_close(calc_ptf_pidgeon1972_awc(20.0, 2.0), 151.48);
        assert_close(
            calc_ptf_pidgeon1972_awc_sand_organic_matter(50.0, 2.0),
            109.24,
        );
        assert_close(calc_ptf_pidgeon1972_awc_coarse_sand(20.0), 115.1);
        assert_close(calc_ptf_pidgeon1972_awc_fine_sand(20.0), 119.9);
        assert_close(calc_ptf_pidgeon1972_awc_very_fine_sand(10.0), 112.7);
        assert_close(calc_ptf_pidgeon1972_eawc(30.0, 20.0, 2.0), 16.12);
        assert_close(calc_ptf_pidgeon1972_eawc_sand(50.0), 51.7);
        assert_close(
            calc_ptf_pidgeon1972_eawc_sand_organic_matter(50.0, 2.0),
            56.26,
        );
        assert_close(
            calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter(20.0, 2.0),
            53.72,
        );
        assert_close(
            calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter(20.0, 2.0),
            59.58,
        );
    }

    #[test]
    fn propagates_nan() {
        assert!(calc_ptf_pidgeon1972_fc(f64::NAN, 20.0, 2.0).is_nan());
        assert!(calc_ptf_pidgeon1972_awc(f64::NAN, 2.0).is_nan());
        assert!(calc_ptf_pidgeon1972_eawc_sand(f64::NAN).is_nan());
    }
}
