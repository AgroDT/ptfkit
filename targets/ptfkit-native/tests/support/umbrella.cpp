import ptfkit;

#include "close_enough.h"

int main() {
    const ptfkit::saxton2006::Saxton2006PTFResult result =
        ptfkit::saxton2006::calc_ptf_saxton2006(0.88, 0.05, 2.5);
    // Expected value from specs/functions/saxton2006.yaml, table_3_sand.
    assert_close(result.theta_1500, 0.05022058, 0.001, 0.0, "volumetric_water_content",
                 "volume_fraction", "registry", "table_3_sand");
    return 0;
}
