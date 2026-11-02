#include <ptfkit/ptfkit.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    if (argc != 6)
        return 2;
    ptfkit_euptf2_ths *model = NULL;
    ptfkit_model_status status = ptfkit_euptf2_ths_load(argv[1], &model);
    if (status != PTFKIT_MODEL_OK)
        return 10 + (int)status;
    double inputs[4], out[4];
    for (int i = 0; i < 4; ++i)
        inputs[i] = strtod(argv[i + 2], NULL);
    status = ptfkit_euptf2_ths_predict(model, inputs, out);
    ptfkit_euptf2_ths_free(model);
    if (status != PTFKIT_MODEL_OK)
        return 10 + (int)status;
    for (size_t i = 0; i < 4; ++i)
        printf("%.17g\n", out[i]);
    return 0;
}
