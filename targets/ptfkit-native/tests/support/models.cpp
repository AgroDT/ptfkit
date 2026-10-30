#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <utility>
#include <type_traits>
#include <array>
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
    return 0;
}
