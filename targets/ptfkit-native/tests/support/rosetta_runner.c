#include <ptfkit/ptfkit.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    if (argc < 7 || argc > 10)
        return 2;
    ptfkit_model *model = NULL;
    ptfkit_model_status status = strcmp(argv[1], "--builtin") == 0
                                     ? ptfkit_rosetta3_builtin(&model)
                                     : ptfkit_rosetta3_load(argv[1], &model);
    if (status != PTFKIT_MODEL_OK)
        return 10 + (int)status;
    unsigned level = (unsigned)strtoul(argv[2], NULL, 10),
             mode = (unsigned)strtoul(argv[3], NULL, 10);
    double inputs[6], out[14];
    for (int i = 4; i < argc; ++i)
        inputs[i - 4] = strtod(argv[i], NULL);
    status = ptfkit_rosetta3_predict(model, level, mode, inputs, (size_t)argc - 4, out);
    if (status == PTFKIT_MODEL_OK && mode == 0) {
        ptfkit_rosetta3_statistics named;
        switch (level) {
        case 2:
            status = calc_ptf_zhang2017_mod2(model, inputs[0], inputs[1], inputs[2], &named);
            break;
        case 3:
            status =
                calc_ptf_zhang2017_mod3(model, inputs[0], inputs[1], inputs[2], inputs[3], &named);
            break;
        case 4:
            status = calc_ptf_zhang2017_mod4(model, inputs[0], inputs[1], inputs[2], inputs[3],
                                             inputs[4], &named);
            break;
        default:
            status = calc_ptf_zhang2017_mod5(model, inputs[0], inputs[1], inputs[2], inputs[3],
                                             inputs[4], inputs[5], &named);
            break;
        }
        double v[] = {named.theta_r_mean, named.theta_s_mean, named.alpha_mean, named.n_mean,
                      named.k_sat_mean,   named.k_0_mean,     named.l_mean,     named.theta_r_std,
                      named.theta_s_std,  named.alpha_std,    named.n_std,      named.k_sat_std,
                      named.k_0_std,      named.l_std};
        for (size_t i = 0; i < 14; ++i)
            if (v[i] != out[i]) {
                ptfkit_model_free(model);
                return 30;
            }
    }
    ptfkit_model_free(model);
    if (status != PTFKIT_MODEL_OK)
        return 10 + (int)status;
    for (size_t i = 0; i < 14; ++i)
        printf("%.17g\n", out[i]);
    return 0;
}
