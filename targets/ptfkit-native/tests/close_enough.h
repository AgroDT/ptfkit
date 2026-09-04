#ifndef PTFKIT_TEST_CLOSE_ENOUGH_H
#define PTFKIT_TEST_CLOSE_ENOUGH_H

#ifdef __cplusplus
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <print>

inline bool is_close(double actual, double expected, double published_tolerance = 0.0) {
    const double tolerance = published_tolerance + 1e-12 + 1e-5 * std::abs(expected);
    return std::abs(actual - expected) <= tolerance;
}

inline void _close_enough_impl(const char *file, int line, double actual, double expected,
                               double published_tolerance) {
    const double tolerance = published_tolerance + 1e-12 + 1e-5 * std::abs(expected);
    if (!is_close(actual, expected, published_tolerance)) {
        std::println(stderr, "assertion failed: {}:{}: |{} - {}| > {}", file, line, actual,
                     expected, tolerance);
        std::exit(EXIT_FAILURE);
    }
}

#else
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static inline int is_close(double actual, double expected, double published_tolerance) {
    const double tolerance = published_tolerance + 1e-12 + 1e-5 * fabs(expected);
    return fabs(actual - expected) <= tolerance;
}

static inline void _close_enough_impl(const char *file, int line, double actual, double expected,
                                      double published_tolerance) {
    const double tolerance = published_tolerance + 1e-12 + 1e-5 * fabs(expected);
    if (!is_close(actual, expected, published_tolerance)) {
        fprintf(stderr, "assertion failed: %s:%d: |%.17g - %.17g| > %.17g\n", file, line, actual,
                expected, tolerance);
        exit(EXIT_FAILURE);
    }
}
#endif

#define assert_close(actual, expected, published_tolerance)                                        \
    do {                                                                                           \
        _close_enough_impl(__FILE__, __LINE__, (actual), (expected), (published_tolerance));       \
    } while (0)

#endif
