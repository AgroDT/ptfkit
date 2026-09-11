#include "close_enough.h"
#include <string.h>

int main(int argc, char **argv) {
    const struct {
        const char *name;
        double expected, absolute, relative, tolerance, below, boundary, above;
    } cases[] = {
        {"absolute", 4.0, 0.5, 0.0625, 0.5, 4.25, 4.5, 5.0},
        {"relative", 4.0, 0.125, 0.25, 1.0, 4.5, 5.0, 6.0},
        {"negative", -4.0, 0.125, 0.25, 1.0, -4.5, -5.0, -6.0},
        {"zero", 0.0, 0.125, 0.25, 0.125, 0.0625, 0.125, 0.25},
        // At zero, the literal guard is also the exact boundary value.
        {"guard", 0.0, 0.0, 0.0, 1e-14, 5e-15, 1e-14, 2e-14},
    };
    const size_t case_count = sizeof(cases) / sizeof(cases[0]);
    if (argc != 1) {
        if (argc == 3 && strcmp(argv[1], "reject") == 0) {
            if (strcmp(argv[2], "nan") == 0) {
                _close_enough_impl(__FILE__, __LINE__, NAN, 1.0, 0.125, 0.25, "test_quantity", "1",
                                   "registry", "nan");
                return EXIT_SUCCESS;
            }
            for (size_t index = 0; index < case_count; ++index) {
                if (strcmp(argv[2], cases[index].name) == 0) {
                    _close_enough_impl(__FILE__, __LINE__, cases[index].above,
                                       cases[index].expected, cases[index].absolute,
                                       cases[index].relative, "test_quantity", "1", "registry",
                                       cases[index].name);
                    return EXIT_SUCCESS;
                }
            }
        }
        fprintf(stderr, "usage: %s [reject {absolute|relative|negative|zero|guard|nan}]\n",
                argv[0]);
        return 2;
    }
    for (size_t index = 0; index < case_count; ++index) {
        if (resolved_tolerance(cases[index].expected, cases[index].absolute,
                               cases[index].relative) != cases[index].tolerance ||
            !is_close(cases[index].below, cases[index].expected, cases[index].absolute,
                      cases[index].relative) ||
            !is_close(cases[index].boundary, cases[index].expected, cases[index].absolute,
                      cases[index].relative) ||
            is_close(cases[index].above, cases[index].expected, cases[index].absolute,
                     cases[index].relative)) {
            fprintf(stderr, "assertion failed: comparator case=%s\n", cases[index].name);
            return EXIT_FAILURE;
        }
        _close_enough_impl(__FILE__, __LINE__, cases[index].below, cases[index].expected,
                           cases[index].absolute, cases[index].relative, "test_quantity", "1",
                           "registry", cases[index].name);
        _close_enough_impl(__FILE__, __LINE__, cases[index].boundary, cases[index].expected,
                           cases[index].absolute, cases[index].relative, "test_quantity", "1",
                           "registry", cases[index].name);
    }
    if (is_close(NAN, 1.0, 0.125, 0.25)) {
        fprintf(stderr, "assertion failed: comparator must reject NaN\n");
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}
