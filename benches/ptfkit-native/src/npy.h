#ifndef PTFKIT_BENCH_NPY_H
#define PTFKIT_BENCH_NPY_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static inline double *load_npy_f64(const char *path, size_t *length) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        return NULL;
    }

    unsigned char prefix[10];
    if (fread(prefix, 1, sizeof(prefix), file) != sizeof(prefix)) {
        fclose(file);
        return NULL;
    }

    const size_t header_length_size = prefix[6] == 1 ? 2 : 4;
    unsigned char header_length_bytes[4] = {0};
    if (fread(header_length_bytes, 1, header_length_size, file) != header_length_size) {
        fclose(file);
        return NULL;
    }
    const uint32_t header_length = header_length_bytes[0] | (header_length_bytes[1] << 8) |
                                   (header_length_bytes[2] << 16) | (header_length_bytes[3] << 24);
    if (fseek(file, (long)header_length, SEEK_CUR) != 0) {
        fclose(file);
        return NULL;
    }

    const long data_start = ftell(file);
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return NULL;
    }
    const long data_end = ftell(file);
    if (data_start < 0 || data_end < data_start) {
        fclose(file);
        return NULL;
    }
    *length = (size_t)(data_end - data_start) / sizeof(double);
    double *values = (double *)malloc(*length * sizeof(*values));
    if (values == NULL || fseek(file, data_start, SEEK_SET) != 0 ||
        fread(values, sizeof(*values), *length, file) != *length) {
        free(values);
        fclose(file);
        return NULL;
    }
    fclose(file);
    return values;
}

#endif
