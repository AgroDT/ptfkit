#ifndef PTFKIT_DETAIL_POWER_H
#define PTFKIT_DETAIL_POWER_H

static inline double ptfkit_pow4(double value) {
    const double square = value * value;
    return square * square;
}

#endif
