/* Local verification binds the shared inference core to imported model data. */
#include "engine.h"
#include "model_api.h"
#include "dense.h"
#include "rosetta_core.h"
#include "metadata.h"
extern const double ptfkit_model_data[];

int ptfkit_calc_ptf_zhang2017(unsigned level, unsigned mode, const double *x, size_t count,
                              double *out) {
    return ptfkit_detail_rosetta(networks, ptfkit_model_data, level, mode, x, count, out);
}
