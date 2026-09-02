#ifndef PTFKIT_TEST_CLOSE_ENOUGH_H
#define PTFKIT_TEST_CLOSE_ENOUGH_H

#ifdef __cplusplus
#include <cstdio>
#include <cstdlib>
#include <print>

inline void _in_interval_impl(const char *file, int line, double actual, double lower,
                              double upper) {
    if (!(actual >= lower && actual <= upper)) {
        std::println(stderr, "assertion failed: {}:{}: {} not in [{}, {}]", file, line, actual,
                     lower, upper);
        std::exit(EXIT_FAILURE);
    }
}

#else
#include <stdio.h>
#include <stdlib.h>

static inline void _in_interval_impl(const char *file, int line, double actual, double lower,
                                     double upper) {
    if (!(actual >= lower && actual <= upper)) {
        fprintf(stderr, "assertion failed: %s:%d: %.17g not in [%.17g, %.17g]\n", file, line,
                actual, lower, upper);
        exit(EXIT_FAILURE);
    }
}
#endif

#define assert_in_interval(actual, lower, upper)                                                   \
    do {                                                                                           \
        _in_interval_impl(__FILE__, __LINE__, (actual), (lower), (upper));                         \
    } while (0)

#define assert_exact(actual, expected) assert_in_interval((actual), (expected), (expected))

#endif
