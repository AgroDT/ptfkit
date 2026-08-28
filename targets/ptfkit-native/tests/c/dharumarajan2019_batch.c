#include <ptfkit/dharumarajan2019.h>
#include <ptfkit/dharumarajan2019_batch.h>

#include "close_enough.h"

int main(void) {
    const double sand[] = {85.0, 50.23, 12.88, 40.0, 24.0};
    const double silt[] = {10.0, 38.72, 60.0, 30.0, 35.0};
    const double clay[] = {5.0, 11.05, 27.12, 30.0, 41.0};
    double infiltration[5];

    calc_ptf_dharumarajan2019_infiltration_batch(sand, silt, clay, infiltration, 5);

    for (size_t index = 0; index < 5; ++index) {
        const double expected = calc_ptf_dharumarajan2019_infiltration(sand[index], silt[index], clay[index]);
        assert_close_enough(infiltration[index], expected, 0.0, 0.00000000000002);
    }
    return 0;
}
