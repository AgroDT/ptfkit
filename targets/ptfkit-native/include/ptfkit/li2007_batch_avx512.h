#ifndef PTFKIT_LI2007_BATCH_AVX512_H
#define PTFKIT_LI2007_BATCH_AVX512_H

#include <ptfkit/li2007.h>
#include <sleef.h>
#include <simde/x86/avx512.h>

#include <stddef.h>

#ifdef __cplusplus
#define PTFKIT_RESTRICT
#else
#define PTFKIT_RESTRICT restrict
#endif

typedef simde__m512d (*ptfkit_li2007_log_avx512_fn)(simde__m512d);

static inline void calc_ptf_li2007_batch_avx512_impl(
    const double *PTFKIT_RESTRICT sand, const double *PTFKIT_RESTRICT silt,
    const double *PTFKIT_RESTRICT clay, const double *PTFKIT_RESTRICT bulk_density,
    const double *PTFKIT_RESTRICT soil_organic_matter, double *PTFKIT_RESTRICT theta_s,
    double *PTFKIT_RESTRICT a_vg, double *PTFKIT_RESTRICT n_vg, double *PTFKIT_RESTRICT k_sat,
    size_t length, ptfkit_li2007_log_avx512_fn log_fn) {
    const simde__m512d k_sat_scale = simde_mm512_set1_pd(1.0 / 8640000.0);
    size_t index = 0;
    for (; index + 8 <= length; index += 8) {
        const simde__m512d sand_value = simde_mm512_loadu_pd(sand + index);
        const simde__m512d silt_value = simde_mm512_loadu_pd(silt + index);
        const simde__m512d clay_value = simde_mm512_loadu_pd(clay + index);
        const simde__m512d bulk_density_value = simde_mm512_loadu_pd(bulk_density + index);
        const simde__m512d soil_organic_matter_value =
            simde_mm512_loadu_pd(soil_organic_matter + index);
        const simde__m512d sand_ln = log_fn(sand_value);
        const simde__m512d silt_ln = log_fn(silt_value);
        const simde__m512d clay_ln = log_fn(clay_value);
        const simde__m512d soil_organic_matter_ln = log_fn(soil_organic_matter_value);
        const simde__m512d bulk_density_ln = log_fn(bulk_density_value);
        const simde__m512d theta_s_exponent = simde_mm512_sub_pd(
            simde_mm512_add_pd(
                simde_mm512_add_pd(simde_mm512_set1_pd(-1.531),
                                   simde_mm512_mul_pd(simde_mm512_set1_pd(0.212), sand_ln)),
                simde_mm512_mul_pd(simde_mm512_set1_pd(0.006), silt_value)),
            simde_mm512_add_pd(
                simde_mm512_mul_pd(simde_mm512_set1_pd(0.051), soil_organic_matter_value),
                simde_mm512_mul_pd(simde_mm512_set1_pd(0.566), bulk_density_ln)));
        const simde__m512d a_vg_exponent = simde_mm512_sub_pd(
            simde_mm512_add_pd(
                simde_mm512_add_pd(
                    simde_mm512_add_pd(
                        simde_mm512_add_pd(
                            simde_mm512_set1_pd(-67.408),
                            simde_mm512_mul_pd(simde_mm512_set1_pd(-0.040), silt_value)),
                        simde_mm512_mul_pd(simde_mm512_set1_pd(-0.670), silt_ln)),
                    simde_mm512_mul_pd(simde_mm512_set1_pd(-2.189), soil_organic_matter_value)),
                simde_mm512_mul_pd(simde_mm512_set1_pd(1.410), soil_organic_matter_ln)),
            simde_mm512_sub_pd(
                simde_mm512_mul_pd(simde_mm512_set1_pd(121.331), bulk_density_ln),
                simde_mm512_mul_pd(simde_mm512_set1_pd(78.400), bulk_density_value)));
        const simde__m512d n_vg_value = simde_mm512_add_pd(
            simde_mm512_add_pd(
                simde_mm512_add_pd(simde_mm512_set1_pd(1.488),
                                   simde_mm512_mul_pd(simde_mm512_set1_pd(0.002), silt_ln)),
                simde_mm512_mul_pd(simde_mm512_set1_pd(0.013), clay_value)),
            simde_mm512_add_pd(
                simde_mm512_add_pd(
                    simde_mm512_mul_pd(simde_mm512_set1_pd(-0.248), clay_ln),
                    simde_mm512_mul_pd(simde_mm512_set1_pd(0.048), soil_organic_matter_ln)),
                simde_mm512_mul_pd(simde_mm512_set1_pd(0.451), bulk_density_ln)));
        const simde__m512d k_sat_exponent = simde_mm512_add_pd(
            simde_mm512_add_pd(
                simde_mm512_add_pd(
                    simde_mm512_add_pd(
                        simde_mm512_add_pd(
                            simde_mm512_set1_pd(13.262),
                            simde_mm512_mul_pd(simde_mm512_set1_pd(-1.914), sand_ln)),
                        simde_mm512_mul_pd(simde_mm512_set1_pd(-0.974), silt_ln)),
                    simde_mm512_mul_pd(simde_mm512_set1_pd(-0.058), clay_value)),
                simde_mm512_mul_pd(simde_mm512_set1_pd(-1.709), soil_organic_matter_ln)),
            simde_mm512_add_pd(
                simde_mm512_mul_pd(simde_mm512_set1_pd(2.885), soil_organic_matter_value),
                simde_mm512_mul_pd(simde_mm512_set1_pd(-8.026), bulk_density_ln)));
        simde_mm512_storeu_pd(theta_s + index, Sleef_finz_expd8_u10avx512f(theta_s_exponent));
        simde_mm512_storeu_pd(a_vg + index, Sleef_finz_expd8_u10avx512f(a_vg_exponent));
        simde_mm512_storeu_pd(n_vg + index, n_vg_value);
        simde_mm512_storeu_pd(
            k_sat + index,
            simde_mm512_mul_pd(Sleef_finz_expd8_u10avx512f(k_sat_exponent), k_sat_scale));
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

static inline void calc_ptf_li2007_batch_avx512(
    const double *PTFKIT_RESTRICT sand, const double *PTFKIT_RESTRICT silt,
    const double *PTFKIT_RESTRICT clay, const double *PTFKIT_RESTRICT bulk_density,
    const double *PTFKIT_RESTRICT soil_organic_matter, double *PTFKIT_RESTRICT theta_s,
    double *PTFKIT_RESTRICT a_vg, double *PTFKIT_RESTRICT n_vg, double *PTFKIT_RESTRICT k_sat,
    size_t length) {
    calc_ptf_li2007_batch_avx512_impl(sand, silt, clay, bulk_density, soil_organic_matter, theta_s,
                                      a_vg, n_vg, k_sat, length, Sleef_finz_logd8_u10avx512f);
}

static inline void calc_ptf_li2007_batch_avx512_u35(
    const double *PTFKIT_RESTRICT sand, const double *PTFKIT_RESTRICT silt,
    const double *PTFKIT_RESTRICT clay, const double *PTFKIT_RESTRICT bulk_density,
    const double *PTFKIT_RESTRICT soil_organic_matter, double *PTFKIT_RESTRICT theta_s,
    double *PTFKIT_RESTRICT a_vg, double *PTFKIT_RESTRICT n_vg, double *PTFKIT_RESTRICT k_sat,
    size_t length) {
    calc_ptf_li2007_batch_avx512_impl(sand, silt, clay, bulk_density, soil_organic_matter, theta_s,
                                      a_vg, n_vg, k_sat, length, Sleef_finz_logd8_u35avx512f);
}

#undef PTFKIT_RESTRICT

#endif
