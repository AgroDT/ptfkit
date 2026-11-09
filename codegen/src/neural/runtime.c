/* Portable dense ensemble interpreter. No external numerical runtime. */
#include "engine.h"
#include <math.h>

typedef struct {
    int kind;
    double p[3];
} Scale;
typedef struct {
    size_t nboot, nlayer, widths[17], offset;
    int activations[16];
    Scale inputs[64], outputs[64];
} Network;

/* Model metadata and trained parameters are separate translation units. */
#include "metadata.h"
extern const double ptfkit_model_data[];

static double scale_value(Scale s, double x) {
    switch (s.kind) {
    case 0:
        return x;
    case 1:
        return x / s.p[0];
    case 2:
        return log10(x) / s.p[0] + s.p[1];
    case 3:
        return s.p[0] * (x + s.p[1]);
    case 4:
        return (x - s.p[0]) * s.p[1] + s.p[2];
    default:
        return x * s.p[0] + s.p[1];
    }
}

static void network_predict(const Network *net, const double *x, double *out) {
    size_t offset = net->offset;
    size_t width = net->widths[net->nlayer];
    for (size_t b = 0; b < net->nboot; ++b) {
        double a[64] = {0};
        for (size_t i = 0; i < net->widths[0]; ++i)
            a[i] = scale_value(net->inputs[i], x[i]);
        for (size_t layer = 0; layer < net->nlayer; ++layer) {
            size_t nin = net->widths[layer], nout = net->widths[layer + 1];
            double next[64] = {0};
            for (size_t node = 0; node < nout; ++node) {
                double sum = 0;
                for (size_t j = 0; j < nin; ++j)
                    sum += a[j] * ptfkit_model_data[offset + node * nin + j];
                sum += ptfkit_model_data[offset + nin * nout + node];
                switch (net->activations[layer]) {
                case 0:
                    next[node] = sum;
                    break;
                case 1:
                    next[node] = 1.0 / (1.0 + exp(-sum));
                    break;
                case 2:
                    next[node] = -1.0 + 2.0 / (1.0 + exp(-2.0 * sum));
                    break;
                default:
                    next[node] = fmax(0.0, sum);
                    break;
                }
            }
            offset += nin * nout + nout;
            for (size_t i = 0; i < nout; ++i)
                a[i] = next[i];
        }
        for (size_t i = 0; i < width; ++i)
            out[b * width + i] = scale_value(net->outputs[i], a[i]);
    }
}

static void stats(const double *rows, size_t n, size_t width, double *mean, double *std) {
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

int ptfkit_calc_ptf_zhang2017(unsigned level, unsigned mode, const double *x, size_t count,
                              double *out) {
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
    const Network *net = &networks[level - 2];
    double raw[5000], linear[5000];
    network_predict(net, x, raw);
    for (size_t i = 0; i < net->nboot; ++i)
        for (size_t j = 0; j < 5; ++j)
            linear[i * 5 + j] = j < 2 ? raw[i * 5 + j] : pow(10.0, raw[i * 5 + j]);
    double lm[5], ls[5], pm[5], ps[5], gm[5];
    stats(raw, net->nboot, 5, lm, ls);
    stats(linear, net->nboot, 5, pm, ps);
    for (size_t j = 0; j < 5; ++j) {
        gm[j] = j < 2 ? lm[j] : pow(10.0, lm[j]);
        out[j] = mode == 0 ? pm[j] : mode == 1 ? lm[j] : gm[j];
        out[j + 7] = mode == 1 ? ls[j] : ps[j];
    }
    const double *vg = mode == 0 ? pm : gm;
    if (!(0 <= vg[0] && vg[0] < vg[1] && vg[1] < 1 && vg[2] > 0 && vg[3] > 1))
        return 1;
    double u[200], ul[200], um[2], us[2], upm[2], ups[2];
    network_predict(&networks[4], vg, u);
    for (size_t i = 0; i < 100; ++i) {
        ul[i * 2] = pow(10.0, u[i * 2]);
        ul[i * 2 + 1] = u[i * 2 + 1];
    }
    stats(u, 100, 2, um, us);
    stats(ul, 100, 2, upm, ups);
    out[5] = mode == 0 ? upm[0] : mode == 1 ? um[0] : pow(10.0, um[0]);
    out[12] = mode == 1 ? us[0] : ups[0];
    out[6] = um[1];
    out[13] = us[1];
    return 1;
}
