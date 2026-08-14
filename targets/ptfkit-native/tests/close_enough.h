#ifndef PTFKIT_TEST_CLOSE_ENOUGH_H
#define PTFKIT_TEST_CLOSE_ENOUGH_H

#ifdef __cplusplus
#include <cstdlib>
#include <cstdio>
#include <cmath>
#include <print>

inline void _close_enough_impl(const char *file, int line, double actual, double expected, double atol, double rtol) {
    if (std::fabs(actual - expected) > atol + rtol * std::fabs(expected)) {
        std::println(stderr, "asserion failed: {}:{}:\n\n\t{} ≈ {}", file, line, actual, expected);
        std::exit(EXIT_FAILURE);
    }
}

#else
#include <stdlib.h>
#include <math.h>
#include <stdio.h>

static inline void _close_enough_impl(const char *file, int line, double actual, double expected, double atol, double rtol) {
    if (fabs(actual - expected) > atol + rtol * fabs(expected)) {
        fprintf(stderr, "asserion failed: %s:%d:\n\n\t%f ≈ %f\n", file, line, actual, expected);
        exit(EXIT_FAILURE);
    }
}

#endif

#define assert_close_enough(actual, expected, atol, rtol) \
    do { _close_enough_impl(__FILE__, __LINE__, (actual), (expected), (atol), (rtol)); } while (0)

// #define assert_close_enough(actual, expected, atol, rtol)       \
//     do {                                                        \
//         if (!(close_enough(actual, expected, atol, rtol))) {    \
//             fprintf(                                            \
//                 stderr,                                         \
//                 "asserion failed: %s:%d: %s ≈ %\n",             \
//                 __FILE__,                                       \
//                 __LINE__,                                       \
//                 #actual,                                        \
//                 #expected                                       \
//             );                                                  \
//             return 1;                                           \
//         }                                                       \
//     } while (0)

#endif
