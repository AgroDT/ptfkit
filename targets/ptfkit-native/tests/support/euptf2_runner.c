#include <ptfkit/ptfkit.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
int main(int argc, char **argv) {
    if (argc >= 4 && strcmp(argv[1], "--collection") == 0) {
        ptfkit_euptf2_model *model = NULL;
        ptfkit_model_status status = ptfkit_euptf2_load(argv[2], argv[3], &model);
        if (status != PTFKIT_MODEL_OK)
            return 10 + (int)status;
        double probabilities[64] = {.05, .25, .5, .75, .95};
        size_t nq = 5;
        if (argc > 4) {
            nq = (size_t)argc - 4;
            if (nq > 64) {
                ptfkit_euptf2_free(model);
                return 15;
            }
            for (size_t i = 0; i < nq; ++i)
                probabilities[i] = strtod(argv[i + 4], NULL);
        }
        char line[4096];
        while (fgets(line, sizeof(line), stdin)) {
            double inputs[64], means[7], quantiles[384];
            size_t nin = 0;
            char *cursor = line, *end;
            while (nin < 64) {
                while (isspace((unsigned char)*cursor))
                    ++cursor;
                if (!*cursor)
                    break;
                inputs[nin] = strtod(cursor, &end);
                if (end == cursor)
                    break;
                ++nin;
                cursor = end;
            }
            const ptfkit_euptf2_contract *c = model->detail_contract;
            status = *cursor ? PTFKIT_MODEL_INPUT
                             : ptfkit_euptf2_predict(model, inputs, nin, probabilities, nq, means,
                                                     c->means, quantiles, c->components * nq);
            if (status != PTFKIT_MODEL_OK) {
                puts("error15");
                continue;
            }
            for (size_t i = 0; i < c->means; ++i)
                printf("%.17g ", means[i]);
            for (size_t i = 0; i < c->components * nq; ++i)
                printf("%.17g ", quantiles[i]);
            putchar('\n');
        }
        ptfkit_euptf2_free(model);
        return 0;
    }
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
