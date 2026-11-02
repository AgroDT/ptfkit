#ifndef PTFKIT_MODELS_H
#define PTFKIT_MODELS_H
#include <ptfkit/detail/model_api.h>
#include <ptfkit/detail/neural.h>
#include <ptfkit/detail/sha256.h>
#include <stdio.h>
#include <stdlib.h>
#include <float.h>

#define PTFKIT_MODEL_MAX_BYTES ((size_t)67108864)
typedef enum {
    PTFKIT_MODEL_OK = 0,
    PTFKIT_MODEL_IO = 1,
    PTFKIT_MODEL_INTEGRITY = 2,
    PTFKIT_MODEL_FORMAT = 3,
    PTFKIT_MODEL_MEMORY = 4,
    PTFKIT_MODEL_INPUT = 5
} ptfkit_model_status;
/* Owned model handle. Treat all detail fields as private and immutable. */
typedef struct {
    size_t detail_count, detail_values;
    ptfkit_detail_network *detail_networks;
    double *detail_data;
    unsigned char detail_digest[32];
} ptfkit_model;

PTFKIT_MODEL_INLINE void ptfkit_model_free(ptfkit_model *model) {
    if (model) {
        free(model->detail_networks);
        free(model->detail_data);
        free(model);
    }
}
PTFKIT_MODEL_INLINE size_t ptfkit_model_network_count(const ptfkit_model *model) {
    return model ? model->detail_count : 0;
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_model_sha256(const ptfkit_model *model,
                                                            char out[65]) {
    if (!model || !out)
        return PTFKIT_MODEL_INPUT;
    static const char digits[] = "0123456789abcdef";
    for (size_t i = 0; i < 32; ++i) {
        out[2 * i] = digits[model->detail_digest[i] >> 4];
        out[2 * i + 1] = digits[model->detail_digest[i] & 15];
    }
    out[64] = 0;
    return PTFKIT_MODEL_OK;
}
typedef struct {
    const unsigned char *data;
    size_t size, pos;
    int invalid;
} ptfkit_detail_reader;
PTFKIT_MODEL_INLINE uint64_t ptfkit_detail_read(ptfkit_detail_reader *r, size_t n) {
    if (r->invalid || n > r->size - r->pos) {
        r->invalid = 1;
        return 0;
    }
    uint64_t value = 0;
    for (size_t i = 0; i < n; ++i)
        value |= (uint64_t)r->data[r->pos++] << (8 * i);
    return value;
}
PTFKIT_MODEL_INLINE double ptfkit_detail_read_double(ptfkit_detail_reader *r) {
    uint64_t bits = ptfkit_detail_read(r, 8);
    double value;
    memcpy(&value, &bits, 8);
    if (!isfinite(value))
        r->invalid = 1;
    return value;
}
PTFKIT_MODEL_INLINE ptfkit_detail_scale ptfkit_detail_read_scale(ptfkit_detail_reader *r) {
    ptfkit_detail_scale scale;
    uint64_t kind = ptfkit_detail_read(r, 4);
    scale.kind = (int)kind;
    for (size_t i = 0; i < 3; ++i)
        scale.p[i] = ptfkit_detail_read_double(r);
    static const unsigned arity[6] = {0, 1, 2, 2, 3, 2};
    if (kind > 5) {
        r->invalid = 1;
        return scale;
    }
    for (unsigned i = arity[scale.kind]; i < 3; ++i)
        if (scale.p[i] != 0)
            r->invalid = 1;
    if ((scale.kind == 1 || scale.kind == 2) && scale.p[0] == 0)
        r->invalid = 1;
    return scale;
}
/* On failure, *out is NULL. Success owns a copy of all data; caller frees it once. */
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_model_from_bytes(const unsigned char *bytes,
                                                                size_t size,
                                                                const char *expected_sha256,
                                                                ptfkit_model **out) {
    if (!out)
        return PTFKIT_MODEL_INPUT;
    *out = NULL;
    if (!bytes || size < 12 || size > PTFKIT_MODEL_MAX_BYTES || !expected_sha256 ||
        strlen(expected_sha256) != 64 || sizeof(double) != 8 || DBL_MANT_DIG != 53 ||
        DBL_MAX_EXP != 1024)
        return PTFKIT_MODEL_FORMAT;
    unsigned char expected[32], actual[32];
    for (size_t i = 0; i < 32; ++i) {
        int a = ptfkit_detail_unhex(expected_sha256[2 * i]),
            b = ptfkit_detail_unhex(expected_sha256[2 * i + 1]);
        if (a < 0 || b < 0)
            return PTFKIT_MODEL_FORMAT;
        expected[i] = (unsigned char)(a * 16 + b);
    }
    ptfkit_detail_sha256(bytes, size, actual);
    if (memcmp(expected, actual, 32))
        return PTFKIT_MODEL_INTEGRITY;
    if (memcmp(bytes, "PTFKNN01", 8))
        return PTFKIT_MODEL_FORMAT;
    ptfkit_detail_reader r = {bytes, size, 8, 0};
    size_t count = (size_t)ptfkit_detail_read(&r, 4);
    if (count < 1 || count > 64)
        return PTFKIT_MODEL_FORMAT;
    ptfkit_model *model = (ptfkit_model *)calloc(1, sizeof(ptfkit_model));
    if (!model)
        return PTFKIT_MODEL_MEMORY;
    model->detail_count = count;
    memcpy(model->detail_digest, actual, 32);
    model->detail_networks = (ptfkit_detail_network *)calloc(count, sizeof(ptfkit_detail_network));
    if (!model->detail_networks) {
        ptfkit_model_free(model);
        return PTFKIT_MODEL_MEMORY;
    }
    size_t end = 0;
    for (size_t index = 0; index < count && !r.invalid; ++index) {
        ptfkit_detail_network *net = &model->detail_networks[index];
        net->nboot = (size_t)ptfkit_detail_read(&r, 4);
        net->nlayer = (size_t)ptfkit_detail_read(&r, 4);
        if (net->nboot < 2 || net->nboot > 1000 || net->nlayer < 1 || net->nlayer > 16) {
            r.invalid = 1;
            break;
        }
        for (size_t i = 0; i <= net->nlayer; ++i) {
            net->widths[i] = (size_t)ptfkit_detail_read(&r, 4);
            if (net->widths[i] < 1 || net->widths[i] > 64)
                r.invalid = 1;
        }
        if (r.invalid)
            break;
        size_t stride = 0;
        for (size_t i = 0; i < net->nlayer; ++i) {
            uint64_t act = ptfkit_detail_read(&r, 4);
            if (act > 3)
                r.invalid = 1;
            net->activations[i] = (int)act;
            stride += net->widths[i] * net->widths[i + 1] + net->widths[i + 1];
        }
        for (size_t i = 0; i < net->widths[0]; ++i)
            net->inputs[i] = ptfkit_detail_read_scale(&r);
        for (size_t i = 0; i < net->widths[net->nlayer]; ++i)
            net->outputs[i] = ptfkit_detail_read_scale(&r);
        uint64_t offset = ptfkit_detail_read(&r, 8);
        if (offset != end || stride * net->nboot > PTFKIT_MODEL_MAX_BYTES / 8 - end) {
            r.invalid = 1;
            break;
        }
        net->offset = end;
        end += stride * net->nboot;
    }
    uint64_t values = ptfkit_detail_read(&r, 8);
    if (r.invalid || values != end || size - r.pos != end * 8) {
        ptfkit_model_free(model);
        return PTFKIT_MODEL_FORMAT;
    }
    model->detail_values = end;
    model->detail_data = (double *)malloc(end * sizeof(double));
    if (!model->detail_data) {
        ptfkit_model_free(model);
        return PTFKIT_MODEL_MEMORY;
    }
    for (size_t i = 0; i < end; ++i)
        model->detail_data[i] = ptfkit_detail_read_double(&r);
    if (r.invalid) {
        ptfkit_model_free(model);
        return PTFKIT_MODEL_FORMAT;
    }
    *out = model;
    return PTFKIT_MODEL_OK;
}
/* Path uses the platform C runtime encoding. from_bytes supports caller-managed I/O. */
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_model_load(const char *path,
                                                          const char *expected_sha256,
                                                          ptfkit_model **out) {
    if (!out)
        return PTFKIT_MODEL_INPUT;
    *out = NULL;
    if (!path)
        return PTFKIT_MODEL_INPUT;
    FILE *file = fopen(path, "rb");
    if (!file)
        return PTFKIT_MODEL_IO;
    if (fseek(file, 0, SEEK_END)) {
        fclose(file);
        return PTFKIT_MODEL_IO;
    }
    long size = ftell(file);
    if (size < 0 || (unsigned long)size > PTFKIT_MODEL_MAX_BYTES) {
        fclose(file);
        return PTFKIT_MODEL_FORMAT;
    }
    if (fseek(file, 0, SEEK_SET)) {
        fclose(file);
        return PTFKIT_MODEL_IO;
    }
    unsigned char *bytes = (unsigned char *)malloc(size ? (size_t)size : 1);
    if (!bytes) {
        fclose(file);
        return PTFKIT_MODEL_MEMORY;
    }
    if (fread(bytes, 1, (size_t)size, file) != (size_t)size || fgetc(file) != EOF || ferror(file)) {
        free(bytes);
        fclose(file);
        return PTFKIT_MODEL_IO;
    }
    fclose(file);
    ptfkit_model_status status = ptfkit_model_from_bytes(bytes, (size_t)size, expected_sha256, out);
    free(bytes);
    return status;
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_model_network_shape(const ptfkit_model *model,
                                                                   size_t index, size_t *inputs,
                                                                   size_t *outputs,
                                                                   size_t *members) {
    if (!model || index >= model->detail_count || !inputs || !outputs || !members)
        return PTFKIT_MODEL_INPUT;
    const ptfkit_detail_network *net = &model->detail_networks[index];
    *inputs = net->widths[0];
    *outputs = net->widths[net->nlayer];
    *members = net->nboot;
    return PTFKIT_MODEL_OK;
}
/* Row-major output: [member][parameter], in original network output scales. */
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_model_predict_network(const ptfkit_model *model,
                                                                     size_t index,
                                                                     const double *input,
                                                                     size_t count, double *out,
                                                                     size_t capacity) {
    size_t nin, nout, nboot;
    if (ptfkit_model_network_shape(model, index, &nin, &nout, &nboot) != PTFKIT_MODEL_OK ||
        !input || !out || count != nin || capacity < nout * nboot)
        return PTFKIT_MODEL_INPUT;
    for (size_t i = 0; i < count; ++i)
        if (!isfinite(input[i]))
            return PTFKIT_MODEL_INPUT;
    ptfkit_detail_network_predict(&model->detail_networks[index], model->detail_data, input, out);
    return PTFKIT_MODEL_OK;
}
#endif
