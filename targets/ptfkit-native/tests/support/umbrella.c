#include <ptfkit/ptfkit.h>

#include "close_enough.h"

int main(void) {
    const saxton2006_ptf_result result = calc_ptf_saxton2006(0.88, 0.05, 2.5);
    // Expected value from specs/functions/saxton2006.yaml, table_3_sand.
    assert_close(result.theta_1500, 0.05022058, 0.001, 0.0, "volumetric_water_content",
                 "volume_fraction", "registry", "table_3_sand");
    return 0;
}
