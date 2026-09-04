#include "close_enough.h"

int main() {
    constexpr double expected = 2.0;
    constexpr double tolerance = 1e-12 + 1e-5 * expected;
    if (!is_close(expected + tolerance * 0.5, expected)) {
        return EXIT_FAILURE;
    }
    if (is_close(expected + tolerance * 2.0, expected)) {
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}
