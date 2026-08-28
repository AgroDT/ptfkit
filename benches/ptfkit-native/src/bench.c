#include <ptfkit/dharumarajan2019.h>
#include <ptfkit/dharumarajan2019_batch.h>
#include <ptfkit/dharumarajan2019_batch_avx512.h>
#include <ptfkit/li2007.h>
#include <ptfkit/li2007_batch.h>
#include <ptfkit/li2007_batch_avx512.h>
#include <ptfkit/mayr1999.h>

#include "npy.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

static long long elapsed_ns(struct timespec started, struct timespec finished) {
    return (long long)(finished.tv_sec - started.tv_sec) * 1000000000LL +
           (finished.tv_nsec - started.tv_nsec);
}

static void print_record(const char *name, size_t samples, long long nanoseconds) {
    printf("{\"target\":\"c\",\"case\":\"%s\",\"samples\":%zu,\"elapsed_ns\":%lld}\n", name,
           samples, nanoseconds);
}

static void observe(const double *values, size_t samples) {
    double total = 0.0;
    for (size_t index = 0; index < samples; ++index) {
        total += values[index];
    }
    volatile double observed = total;
    (void)observed;
}

int main(int argc, char **argv) {
    if (argc < 3 || argc > 4) {
        fprintf(stderr, "usage: ptfkit-c-benchmarks DATASET WARMUPS [LIMIT]\n");
        return 2;
    }
    const char *dataset = argv[1];
    const size_t warmups = strtoull(argv[2], NULL, 10);
    const size_t limit = argc == 4 ? strtoull(argv[3], NULL, 10) : 0;
    char path[4096];
    size_t samples;
    snprintf(path, sizeof(path), "%s/sand.npy", dataset);
    double *sand = load_npy_f64(path, &samples);
    snprintf(path, sizeof(path), "%s/silt.npy", dataset);
    double *silt = load_npy_f64(path, &samples);
    snprintf(path, sizeof(path), "%s/clay.npy", dataset);
    double *clay = load_npy_f64(path, &samples);
    snprintf(path, sizeof(path), "%s/bulk_density.npy", dataset);
    double *bulk_density = load_npy_f64(path, &samples);
    snprintf(path, sizeof(path), "%s/organic_carbon.npy", dataset);
    double *organic_carbon = load_npy_f64(path, &samples);
    if (sand == NULL || silt == NULL || clay == NULL || bulk_density == NULL ||
        organic_carbon == NULL) {
        fprintf(stderr, "failed to load benchmark inputs\n");
        return 1;
    }
    if (limit != 0) {
        samples = limit;
    }

    double *infiltration = malloc(samples * sizeof(*infiltration));
    double *mayr_a_hc = malloc(samples * sizeof(*mayr_a_hc));
    double *mayr_b_hc = malloc(samples * sizeof(*mayr_b_hc));
    double *mayr_theta_s = malloc(samples * sizeof(*mayr_theta_s));
    double *li_theta_s = malloc(samples * sizeof(*li_theta_s));
    double *li_a_vg = malloc(samples * sizeof(*li_a_vg));
    double *li_n_vg = malloc(samples * sizeof(*li_n_vg));
    double *li_k_sat = malloc(samples * sizeof(*li_k_sat));
    struct timespec started;
    struct timespec finished;

    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        for (size_t index = 0; index < samples; ++index) {
            infiltration[index] =
                calc_ptf_dharumarajan2019_infiltration(sand[index], silt[index], clay[index]);
        }
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(infiltration, samples);
        if (iteration == warmups) {
            print_record("dharumarajan2019_infiltration", samples, elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        calc_ptf_dharumarajan2019_infiltration_batch_avx512(sand, silt, clay, infiltration,
                                                            samples);
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(infiltration, samples);
        if (iteration == warmups) {
            print_record("dharumarajan2019_infiltration_batch_avx512", samples,
                         elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        calc_ptf_dharumarajan2019_infiltration_batch(sand, silt, clay, infiltration, samples);
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(infiltration, samples);
        if (iteration == warmups) {
            print_record("dharumarajan2019_infiltration_batch", samples,
                         elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        for (size_t index = 0; index < samples; ++index) {
            const mayr1999_ptf_result result = calc_ptf_mayr1999(
                sand[index], silt[index], clay[index], bulk_density[index], organic_carbon[index]);
            mayr_a_hc[index] = result.a_hc;
            mayr_b_hc[index] = result.b_hc;
            mayr_theta_s[index] = result.theta_s;
        }
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(mayr_a_hc, samples);
        observe(mayr_b_hc, samples);
        observe(mayr_theta_s, samples);
        if (iteration == warmups) {
            print_record("mayr1999", samples, elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        for (size_t index = 0; index < samples; ++index) {
            const li2007_ptf_result result = calc_ptf_li2007(
                sand[index], silt[index], clay[index], bulk_density[index], organic_carbon[index]);
            li_theta_s[index] = result.theta_s;
            li_a_vg[index] = result.a_vg;
            li_n_vg[index] = result.n_vg;
            li_k_sat[index] = result.k_sat;
        }
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(li_theta_s, samples);
        observe(li_a_vg, samples);
        observe(li_n_vg, samples);
        observe(li_k_sat, samples);
        if (iteration == warmups) {
            print_record("li2007", samples, elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        calc_ptf_li2007_batch(sand, silt, clay, bulk_density, organic_carbon, li_theta_s, li_a_vg,
                              li_n_vg, li_k_sat, samples);
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(li_theta_s, samples);
        observe(li_a_vg, samples);
        observe(li_n_vg, samples);
        observe(li_k_sat, samples);
        if (iteration == warmups) {
            print_record("li2007_batch", samples, elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        calc_ptf_li2007_batch_u35(sand, silt, clay, bulk_density, organic_carbon, li_theta_s,
                                  li_a_vg, li_n_vg, li_k_sat, samples);
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(li_theta_s, samples);
        observe(li_a_vg, samples);
        observe(li_n_vg, samples);
        observe(li_k_sat, samples);
        if (iteration == warmups) {
            print_record("li2007_batch_u35", samples, elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        calc_ptf_li2007_batch_avx512(sand, silt, clay, bulk_density, organic_carbon, li_theta_s,
                                     li_a_vg, li_n_vg, li_k_sat, samples);
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(li_theta_s, samples);
        observe(li_a_vg, samples);
        observe(li_n_vg, samples);
        observe(li_k_sat, samples);
        if (iteration == warmups) {
            print_record("li2007_batch_avx512", samples, elapsed_ns(started, finished));
        }
    }
    for (size_t iteration = 0; iteration <= warmups; ++iteration) {
        clock_gettime(CLOCK_MONOTONIC, &started);
        calc_ptf_li2007_batch_avx512_u35(sand, silt, clay, bulk_density, organic_carbon, li_theta_s,
                                         li_a_vg, li_n_vg, li_k_sat, samples);
        clock_gettime(CLOCK_MONOTONIC, &finished);
        observe(li_theta_s, samples);
        observe(li_a_vg, samples);
        observe(li_n_vg, samples);
        observe(li_k_sat, samples);
        if (iteration == warmups) {
            print_record("li2007_batch_avx512_u35", samples, elapsed_ns(started, finished));
        }
    }

    free(sand);
    free(silt);
    free(clay);
    free(bulk_density);
    free(organic_carbon);
    free(infiltration);
    free(mayr_a_hc);
    free(mayr_b_hc);
    free(mayr_theta_s);
    free(li_theta_s);
    free(li_a_vg);
    free(li_n_vg);
    free(li_k_sat);
    return 0;
}
