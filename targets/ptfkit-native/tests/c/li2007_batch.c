#include <ptfkit/li2007.h>
#include <ptfkit/li2007_batch.h>

#include "close_enough.h"

int main(void) {
    const double sand[] = {85.0, 50.23, 12.88, 40.0, 24.0};
    const double silt[] = {10.0, 38.72, 60.0, 30.0, 35.0};
    const double clay[] = {5.0, 11.05, 27.12, 30.0, 41.0};
    const double bulk_density[] = {1.2, 1.42, 1.48, 1.35, 1.5};
    const double soil_organic_matter[] = {0.21, 0.65, 1.02, 0.8, 1.2};
    double theta_s[5];
    double a_vg[5];
    double n_vg[5];
    double k_sat[5];

    calc_ptf_li2007_batch(sand, silt, clay, bulk_density, soil_organic_matter, theta_s, a_vg, n_vg,
                          k_sat, 5);

    for (size_t index = 0; index < 5; ++index) {
        const li2007_ptf_result expected = calc_ptf_li2007(
            sand[index], silt[index], clay[index], bulk_density[index], soil_organic_matter[index]);
        assert_close_enough(theta_s[index], expected.theta_s, 0.0, 0.00000000000002);
        assert_close_enough(a_vg[index], expected.a_vg, 0.0, 0.00000000000002);
        assert_close_enough(n_vg[index], expected.n_vg, 0.0, 0.00000000000002);
        assert_close_enough(k_sat[index], expected.k_sat, 0.0, 0.00000000000002);
    }
    return 0;
}
