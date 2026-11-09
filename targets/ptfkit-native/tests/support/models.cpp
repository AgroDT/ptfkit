#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <utility>
#include <type_traits>
#include <array>
#include <cmath>
#include "affine_model.h"
import ptfkit;
int main() {
    static_assert(!std::is_copy_constructible_v<ptfkit::Model>);
    auto original = ptfkit::Model::from_bytes(affine_model, affine_sha256);
    auto model = std::move(original);
    assert(model.network_count() == 1);
    auto shape = model.network_shape(0);
    assert(shape.inputs == 2 && shape.outputs == 1 && shape.members == 2);
    assert(original.native_handle() == nullptr);
    const double x[] = {3, 4};
    auto result = model.predict_network(0, x);
    assert(result.size() == 2 && result[0][0] == 21 && result[1][0] == 9);
    bool rejected = false;
    try {
        auto wrong = ptfkit::Rosetta3(std::move(model));
        (void)wrong;
    } catch (const ptfkit::ModelError &error) {
        rejected = error.status == ptfkit::ModelStatus::Integrity;
    }
    assert(rejected);
    // Frozen upstream case mod2_arith_clay_loam; no model file is loaded.
    auto bundled = ptfkit::Rosetta3::builtin();
    const double soil[] = {30, 30, 40};
    auto prediction = bundled.predict(2, ptfkit::Estimate::Arithmetic, soil);
    const double expected[] = {0.11921313412479762,   0.4348486578079577,   0.009109686083606867,
                               1.3094213646469939,    8.74047181417013,     1.3099307799553759,
                               -1.009187960743742,    0.009022699466985867, 0.010140469075525323,
                               0.0022509742698824248, 0.0366504620061113,   2.930411333703784,
                               0.843530623042398,     1.547848314232419};
    for (size_t i = 0; i < 7; ++i) {
        assert(std::abs(prediction.mean()[i] - expected[i]) <=
               std::fmax(1e-11, 1e-12 * std::abs(expected[i])));
        assert(std::abs(prediction.stddev()[i] - expected[i + 7]) <=
               std::fmax(1e-11, 1e-12 * std::abs(expected[i + 7])));
    }
    return 0;
}
