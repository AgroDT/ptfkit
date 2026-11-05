#ifndef PTFKIT_DETAIL_ROSETTA_CORE_H
#define PTFKIT_DETAIL_ROSETTA_CORE_H
PTFKIT_MODEL_INLINE void ptfkit_detail_stats(const double *rows, size_t n, size_t width,
                                             double *mean, double *std) {
    for (size_t j = 0; j < width; ++j) {
        mean[j] = 0;
        for (size_t i = 0; i < n; ++i)
            mean[j] += rows[i * width + j];
        mean[j] /= (double)n;
        std[j] = 0;
        for (size_t i = 0; i < n; ++i) {
            double d = rows[i * width + j] - mean[j];
            std[j] += d * d;
        }
        std[j] = sqrt(std[j] / (double)(n - 1));
    }
}

PTFKIT_MODEL_INLINE int ptfkit_detail_rosetta(const ptfkit_detail_network *networks,
                                              const double *data, unsigned level, unsigned mode,
                                              const double *x, size_t count, double *out) {
    if (!out)
        return 0;
    for (size_t i = 0; i < 14; ++i)
        out[i] = NAN;
    if (!x || level < 2 || level > 5 || mode > 2 || count != level + 1)
        return 0;
    for (size_t i = 0; i < count; ++i)
        if (!isfinite(x[i]))
            return 0;
    double sum = x[0] + x[1] + x[2];
    if (x[0] < 0 || x[1] < 0 || x[2] < 0 || sum < 99 || sum > 101 ||
        (level >= 3 && (x[3] < 0.5 || x[3] > 2.0)) || (level >= 4 && !(x[4] > 0 && x[4] < 1)) ||
        (level >= 5 && !(x[5] > 0 && x[5] < x[4])))
        return 0;
    const ptfkit_detail_network *net = &networks[level - 2];
    double raw[5000], linear[5000];
    ptfkit_detail_network_predict(net, data, x, raw);
    for (size_t i = 0; i < net->nboot; ++i)
        for (size_t j = 0; j < 5; ++j)
            linear[i * 5 + j] = j < 2 ? raw[i * 5 + j] : pow(10.0, raw[i * 5 + j]);
    double lm[5], ls[5], pm[5], ps[5], gm[5];
    ptfkit_detail_stats(raw, net->nboot, 5, lm, ls);
    ptfkit_detail_stats(linear, net->nboot, 5, pm, ps);
    for (size_t j = 0; j < 5; ++j) {
        gm[j] = j < 2 ? lm[j] : pow(10.0, lm[j]);
        out[j] = mode == 0 ? pm[j] : mode == 1 ? lm[j] : gm[j];
        out[j + 7] = mode == 1 ? ls[j] : ps[j];
    }
    const double *vg = mode == 0 ? pm : gm;
    if (!(0 <= vg[0] && vg[0] < vg[1] && vg[1] < 1 && vg[2] > 0 && vg[3] > 1))
        return 1;
    double u[200], ul[200], um[2], us[2], upm[2], ups[2];
    ptfkit_detail_network_predict(&networks[4], data, vg, u);
    for (size_t i = 0; i < 100; ++i) {
        ul[i * 2] = pow(10.0, u[i * 2]);
        ul[i * 2 + 1] = u[i * 2 + 1];
    }
    ptfkit_detail_stats(u, 100, 2, um, us);
    ptfkit_detail_stats(ul, 100, 2, upm, ups);
    out[5] = mode == 0 ? upm[0] : mode == 1 ? um[0] : pow(10.0, um[0]);
    out[12] = mode == 1 ? us[0] : ups[0];
    out[6] = um[1];
    out[13] = us[1];
    return 1;
}

#endif
