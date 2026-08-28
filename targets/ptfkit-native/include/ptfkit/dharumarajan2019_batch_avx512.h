#ifndef PTFKIT_DHARUMARAJAN2019_BATCH_AVX512_H
#define PTFKIT_DHARUMARAJAN2019_BATCH_AVX512_H

#include <ptfkit/dharumarajan2019.h>
#include <simde/x86/avx512.h>

#include <stddef.h>

#ifdef __cplusplus
#define PTFKIT_RESTRICT
#else
#define PTFKIT_RESTRICT restrict
#endif

static inline void calc_ptf_dharumarajan2019_infiltration_batch_avx512(
    const double *PTFKIT_RESTRICT sand, const double *PTFKIT_RESTRICT silt,
    const double *PTFKIT_RESTRICT clay, double *PTFKIT_RESTRICT infiltration, size_t length) {
    size_t index = 0;
    for (; index + 8 <= length; index += 8) {
        const simde__m512d sand_value = simde_mm512_loadu_pd(sand + index);
        const simde__m512d silt_value = simde_mm512_loadu_pd(silt + index);
        const simde__m512d clay_value = simde_mm512_loadu_pd(clay + index);
        const simde__m512d result = simde_mm512_sub_pd(
            simde_mm512_sub_pd(
                simde_mm512_sub_pd(simde_mm512_set1_pd(177.55),
                                   simde_mm512_mul_pd(simde_mm512_set1_pd(1.47), sand_value)),
                simde_mm512_mul_pd(simde_mm512_set1_pd(1.80), clay_value)),
            simde_mm512_mul_pd(simde_mm512_set1_pd(1.58), silt_value));
        simde_mm512_storeu_pd(infiltration + index, result);
    }
    for (; index < length; ++index) {
        infiltration[index] =
            calc_ptf_dharumarajan2019_infiltration(sand[index], silt[index], clay[index]);
    }
}

#undef PTFKIT_RESTRICT

#endif
