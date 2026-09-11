#ifndef PTFKIT_TEST_CLOSE_ENOUGH_H
#define PTFKIT_TEST_CLOSE_ENOUGH_H

#ifdef __cplusplus
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <print>

inline double resolved_tolerance(double expected, double absolute, double relative) {
    return std::max({absolute, relative * std::abs(expected), 0.00000000000001});
}

inline bool is_close(double actual, double expected, double absolute, double relative) {
    return std::abs(actual - expected) <= resolved_tolerance(expected, absolute, relative);
}

inline void _close_enough_impl(const char *file, int line, double actual, double expected,
                               double absolute, double relative, const char *quantity,
                               const char *unit, const char *source, const char *case_id) {
    const double tolerance = resolved_tolerance(expected, absolute, relative);
    const double difference = std::abs(actual - expected);
    if (!is_close(actual, expected, absolute, relative)) {
        std::println(stderr,
                     "assertion failed: {}:{}: case={}, actual={}, expected={}, difference={}, "
                     "tolerance={}, quantity={}, unit={}, source={}",
                     file, line, case_id, actual, expected, difference, tolerance, quantity, unit,
                     source);
        std::exit(EXIT_FAILURE);
    }
}

#else
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static inline double resolved_tolerance(double expected, double absolute, double relative) {
    return fmax(fmax(absolute, relative * fabs(expected)), 0.00000000000001);
}

static inline int is_close(double actual, double expected, double absolute, double relative) {
    return fabs(actual - expected) <= resolved_tolerance(expected, absolute, relative);
}

static inline void _close_enough_impl(const char *file, int line, double actual, double expected,
                                      double absolute, double relative, const char *quantity,
                                      const char *unit, const char *source, const char *case_id) {
    const double tolerance = resolved_tolerance(expected, absolute, relative);
    const double difference = fabs(actual - expected);
    if (!is_close(actual, expected, absolute, relative)) {
        fprintf(stderr,
                "assertion failed: %s:%d: case=%s, actual=%.17g, expected=%.17g, difference=%.17g, "
                "tolerance=%.17g, quantity=%s, unit=%s, source=%s\n",
                file, line, case_id, actual, expected, difference, tolerance, quantity, unit,
                source);
        exit(EXIT_FAILURE);
    }
}
#endif

#define assert_close(actual, expected, absolute, relative, quantity, unit, source, case_id)        \
    do {                                                                                           \
        _close_enough_impl(__FILE__, __LINE__, (actual), (expected), (absolute), (relative),       \
                           (quantity), (unit), (source), (case_id));                               \
    } while (0)

#endif
