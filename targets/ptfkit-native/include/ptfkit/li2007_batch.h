#ifndef PTFKIT_LI2007_BATCH_H
#define PTFKIT_LI2007_BATCH_H

#include <ptfkit/li2007.h>
#include <sleef.h>
#include <simde/x86/avx.h>

#include <stddef.h>

#ifdef __cplusplus
#define PTFKIT_RESTRICT
#else
#define PTFKIT_RESTRICT restrict
#endif

typedef simde__m256d (*ptfkit_li2007_log_fn)(simde__m256d);

static inline void calc_ptf_li2007_batch_impl(
    const double *PTFKIT_RESTRICT sand, const double *PTFKIT_RESTRICT silt,
    const double *PTFKIT_RESTRICT clay, const double *PTFKIT_RESTRICT bulk_density,
    const double *PTFKIT_RESTRICT soil_organic_matter, double *PTFKIT_RESTRICT theta_s,
    double *PTFKIT_RESTRICT a_vg, double *PTFKIT_RESTRICT n_vg, double *PTFKIT_RESTRICT k_sat,
    size_t length, ptfkit_li2007_log_fn log_fn) {
    const simde__m256d k_sat_scale = simde_mm256_set1_pd(1.0 / 8640000.0);
    size_t index = 0;
    for (; index + 4 <= length; index += 4) {
        const simde__m256d sand_value = simde_mm256_loadu_pd(sand + index);
        const simde__m256d silt_value = simde_mm256_loadu_pd(silt + index);
        const simde__m256d clay_value = simde_mm256_loadu_pd(clay + index);
        const simde__m256d bulk_density_value = simde_mm256_loadu_pd(bulk_density + index);
        const simde__m256d soil_organic_matter_value =
            simde_mm256_loadu_pd(soil_organic_matter + index);
        const simde__m256d sand_ln = log_fn(sand_value);
        const simde__m256d silt_ln = log_fn(silt_value);
        const simde__m256d clay_ln = log_fn(clay_value);
        const simde__m256d soil_organic_matter_ln = log_fn(soil_organic_matter_value);
        const simde__m256d bulk_density_ln = log_fn(bulk_density_value);
        const simde__m256d theta_s_exponent = simde_mm256_sub_pd(
            simde_mm256_add_pd(
                simde_mm256_add_pd(simde_mm256_set1_pd(-1.531),
                                   simde_mm256_mul_pd(simde_mm256_set1_pd(0.212), sand_ln)),
                simde_mm256_mul_pd(simde_mm256_set1_pd(0.006), silt_value)),
            simde_mm256_add_pd(
                simde_mm256_mul_pd(simde_mm256_set1_pd(0.051), soil_organic_matter_value),
                simde_mm256_mul_pd(simde_mm256_set1_pd(0.566), bulk_density_ln)));
        const simde__m256d a_vg_exponent = simde_mm256_sub_pd(
            simde_mm256_add_pd(
                simde_mm256_add_pd(
                    simde_mm256_add_pd(
                        simde_mm256_add_pd(
                            simde_mm256_set1_pd(-67.408),
                            simde_mm256_mul_pd(simde_mm256_set1_pd(-0.040), silt_value)),
                        simde_mm256_mul_pd(simde_mm256_set1_pd(-0.670), silt_ln)),
                    simde_mm256_mul_pd(simde_mm256_set1_pd(-2.189), soil_organic_matter_value)),
                simde_mm256_mul_pd(simde_mm256_set1_pd(1.410), soil_organic_matter_ln)),
            simde_mm256_sub_pd(
                simde_mm256_mul_pd(simde_mm256_set1_pd(121.331), bulk_density_ln),
                simde_mm256_mul_pd(simde_mm256_set1_pd(78.400), bulk_density_value)));
        const simde__m256d n_vg_value = simde_mm256_add_pd(
            simde_mm256_add_pd(
                simde_mm256_add_pd(simde_mm256_set1_pd(1.488),
                                   simde_mm256_mul_pd(simde_mm256_set1_pd(0.002), silt_ln)),
                simde_mm256_mul_pd(simde_mm256_set1_pd(0.013), clay_value)),
            simde_mm256_add_pd(
                simde_mm256_add_pd(
                    simde_mm256_mul_pd(simde_mm256_set1_pd(-0.248), clay_ln),
                    simde_mm256_mul_pd(simde_mm256_set1_pd(0.048), soil_organic_matter_ln)),
                simde_mm256_mul_pd(simde_mm256_set1_pd(0.451), bulk_density_ln)));
        const simde__m256d k_sat_exponent = simde_mm256_add_pd(
            simde_mm256_add_pd(
                simde_mm256_add_pd(
                    simde_mm256_add_pd(
                        simde_mm256_add_pd(
                            simde_mm256_set1_pd(13.262),
                            simde_mm256_mul_pd(simde_mm256_set1_pd(-1.914), sand_ln)),
                        simde_mm256_mul_pd(simde_mm256_set1_pd(-0.974), silt_ln)),
                    simde_mm256_mul_pd(simde_mm256_set1_pd(-0.058), clay_value)),
                simde_mm256_mul_pd(simde_mm256_set1_pd(-1.709), soil_organic_matter_ln)),
            simde_mm256_add_pd(
                simde_mm256_mul_pd(simde_mm256_set1_pd(2.885), soil_organic_matter_value),
                simde_mm256_mul_pd(simde_mm256_set1_pd(-8.026), bulk_density_ln)));
        simde_mm256_storeu_pd(theta_s + index, Sleef_finz_expd4_u10avx2(theta_s_exponent));
        simde_mm256_storeu_pd(a_vg + index, Sleef_finz_expd4_u10avx2(a_vg_exponent));
        simde_mm256_storeu_pd(n_vg + index, n_vg_value);
        simde_mm256_storeu_pd(
            k_sat + index,
            simde_mm256_mul_pd(Sleef_finz_expd4_u10avx2(k_sat_exponent), k_sat_scale));
    }
    for (; index < length; ++index) {
        const li2007_ptf_result result = calc_ptf_li2007(
            sand[index], silt[index], clay[index], bulk_density[index], soil_organic_matter[index]);
        theta_s[index] = result.theta_s;
        a_vg[index] = result.a_vg;
        n_vg[index] = result.n_vg;
        k_sat[index] = result.k_sat;
    }
}

static inline void calc_ptf_li2007_batch(const double *PTFKIT_RESTRICT sand,
                                         const double *PTFKIT_RESTRICT silt,
                                         const double *PTFKIT_RESTRICT clay,
                                         const double *PTFKIT_RESTRICT bulk_density,
                                         const double *PTFKIT_RESTRICT soil_organic_matter,
                                         double *PTFKIT_RESTRICT theta_s,
                                         double *PTFKIT_RESTRICT a_vg, double *PTFKIT_RESTRICT n_vg,
                                         double *PTFKIT_RESTRICT k_sat, size_t length) {
    calc_ptf_li2007_batch_impl(sand, silt, clay, bulk_density, soil_organic_matter, theta_s, a_vg,
                               n_vg, k_sat, length, Sleef_finz_logd4_u10avx2);
}

static inline void calc_ptf_li2007_batch_u35(
    const double *PTFKIT_RESTRICT sand, const double *PTFKIT_RESTRICT silt,
    const double *PTFKIT_RESTRICT clay, const double *PTFKIT_RESTRICT bulk_density,
    const double *PTFKIT_RESTRICT soil_organic_matter, double *PTFKIT_RESTRICT theta_s,
    double *PTFKIT_RESTRICT a_vg, double *PTFKIT_RESTRICT n_vg, double *PTFKIT_RESTRICT k_sat,
    size_t length) {
    calc_ptf_li2007_batch_impl(sand, silt, clay, bulk_density, soil_organic_matter, theta_s, a_vg,
                               n_vg, k_sat, length, Sleef_finz_logd4_u35avx2);
}

#undef PTFKIT_RESTRICT

#endif
