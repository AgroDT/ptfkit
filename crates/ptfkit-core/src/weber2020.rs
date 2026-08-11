//! Weber et al. (2020) conversion from VGM to Brunswick-VGM parameters.

/// Brunswick-VGM soil hydraulic model parameters.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Weber2020Result {
    pub theta_snc_bw: f64,
    pub theta_sc_bw: f64,
    pub alpha_bw: f64,
    pub n_bw: f64,
    pub tau_bw: f64,
    pub k_sc_bw: f64,
    pub k_snc_bw: f64,
}

/// Convert VGM parameters to Brunswick-VGM parameters.
#[must_use]
pub fn calc_ptf_weber2020(
    theta_r_vgm: f64,
    theta_s_vgm: f64,
    alpha_vgm: f64,
    n_vgm: f64,
    tau_vgm: f64,
    k_s_vgm: f64,
) -> Weber2020Result {
    let theta_snc_bw = -1.58e-3 + 1.285 * theta_r_vgm;
    let theta_s_bw = 1.89e-3 + 0.993 * theta_s_vgm;
    let theta_sc_bw = theta_s_bw - theta_snc_bw;

    let alpha_bw = 10.0_f64.powf(-2.06e-2 + 0.986 * alpha_vgm.log10());
    let n_bw = 1.0 + 10.0_f64.powf(6.42e-2 + 0.933 * (n_vgm - 1.0).log10());
    let tau_vgm_constrained = tau_vgm.min(0.0);
    let tau_bw = 2.95e-2 + 1.833 * tau_vgm_constrained;
    let k_sc_bw = 10.0_f64.powf(1.16e-1 + 1.060 * k_s_vgm.log10());
    let k_snc_bw = 10.0_f64.powf(-1.72);

    Weber2020Result {
        theta_snc_bw,
        theta_sc_bw,
        alpha_bw,
        n_bw,
        tau_bw,
        k_sc_bw,
        k_snc_bw,
    }
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

    #[test]
    fn representative_vgm_parameters_golden_case() {
        let result = calc_ptf_weber2020(0.05, 0.45, 0.02, 1.6, -0.5, 100.0);

        assert_close(result.theta_snc_bw, 0.06267);
        assert_close(result.theta_sc_bw, 0.38607);
        assert_close(result.alpha_bw, 0.020_147_240_733_519_7);
        assert_close(result.n_bw, 1.719_805_426_832_89);
        assert_close(result.tau_bw, -0.887);
        assert_close(result.k_sc_bw, 172.186_857_498_601);
        assert_close(result.k_snc_bw, 0.019_054_607_179_632_5);
    }

    #[test]
    fn constrains_positive_tau_before_regression() {
        let result = calc_ptf_weber2020(0.05, 0.45, 0.02, 1.6, 1.0, 100.0);

        assert_close(result.tau_bw, 0.0295);
    }
}
