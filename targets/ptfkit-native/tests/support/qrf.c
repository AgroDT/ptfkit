#include <ptfkit/ptfkit.h>
#include <assert.h>

/* A hand-specified two-tree forest. The leaf means differ from response
   samples: quantiles of means would be .41/.5/.59 instead of .23/.5/.77. */
static const unsigned char fixture[] = {
    0x50, 0x54, 0x46, 0x4b, 0x51, 0x46, 0x30, 0x31, 1,    0,    0,    0,    2,    0,    0,    0,
    3,    0,    0,    0,    1,    0,    0,    0,    2,    0,    0,    0,    3,    0,    0,    0,
    0,    0,    0,    0,    0,    0,    0x3e, 0x40, 0,    0,    0,    0,    0,    0,    0,    0,
    0,    0,    0,    0,    0,    0,    0,    0,    0xff, 0xff, 0xff, 0xff, 0x9a, 0x99, 0x99, 0x99,
    0x99, 0x99, 0xd9, 0x3f, 0x9a, 0x99, 0x99, 0x99, 0x99, 0x99, 0xc9, 0x3f, 0,    0,    0,    0,
    0,    0,    0,    0,    0xff, 0xff, 0xff, 0xff, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0xe6, 0x3f,
    0xcd, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0xec, 0x3f, 1,    0,    0,    0,    0,    0,    0,    0,
    0,    0,    0,    0,    0xff, 0xff, 0xff, 0xff, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0xe3, 0x3f,
    0x9a, 0x99, 0x99, 0x99, 0x99, 0x99, 0xe9, 0x3f};
static const char *sha = "ba29d158e897d6037cf8e0656dcead7f315410f4e9157381bff8e4fc3c146695";

static void put_u32(unsigned char *bytes, uint32_t value) {
    for (size_t i = 0; i < 4; ++i)
        bytes[i] = (unsigned char)(value >> (8 * i));
}
static void check_multivariate(void) {
    const ptfkit_euptf2_contract contract = {9,
                                             "synthetic",
                                             "",
                                             9,
                                             6,
                                             7,
                                             {"a", "b", "c", "d", "e", "f", "g", "h", "i"},
                                             {"THS", "THR", "ALP", "N", "K0", "L", "M"},
                                             {0, 2, 1, 3, 1, 0}};
    unsigned char bytes[788];
    memcpy(bytes, "PTFKQF02", 8);
    put_u32(bytes + 8, 9);
    put_u32(bytes + 12, 9);
    put_u32(bytes + 16, 6);
    size_t offset = 20;
    for (size_t i = 0; i < 6; ++i) {
        put_u32(bytes + offset, contract.transforms[i]);
        offset += 4;
        memcpy(bytes + offset, fixture + 12, sizeof(fixture) - 12);
        put_u32(bytes + offset + 16, 8);
        offset += sizeof(fixture) - 12;
    }
    assert(offset == sizeof(bytes));
    ptfkit_euptf2_model *model = NULL;
    assert(ptfkit_detail_euptf2_parse(&contract, bytes, sizeof(bytes), &model) == PTFKIT_MODEL_OK);
    double inputs[9] = {0, 0, 0, 0, 0, 0, 0, 0, 30}, means[7], q[30];
    assert(ptfkit_euptf2_predict(model, inputs, 9, NULL, 5, means, 7, q, 30) == PTFKIT_MODEL_OK);
    const double root10 = 3.1622776601683795;
    const double expected_means[] = {.5, root10 - 1,          root10, root10 + 1, root10,
                                     .5, 1 - 1 / (root10 + 1)};
    const double expected_q[] = {.23, .35, .5, .65, .77};
    for (size_t i = 0; i < 7; ++i)
        assert(fabs(means[i] - expected_means[i]) < 1e-14);
    for (size_t i = 0; i < 5; ++i)
        assert(fabs(q[i] - expected_q[i]) < 1e-14);
    assert(fabs(q[10] - 1.6982436524617444) < 1e-13);
    const double custom[] = {.95, .05, .5};
    assert(ptfkit_euptf2_predict(model, inputs, 9, custom, 3, means, 7, q, 18) == PTFKIT_MODEL_OK);
    assert(fabs(q[0] - .77) < 1e-14 && fabs(q[1] - .23) < 1e-14 && fabs(q[2] - .5) < 1e-14);
    const double invalid[] = {0, .5};
    assert(ptfkit_euptf2_predict(model, inputs, 9, invalid, 2, means, 7, q, 12) ==
           PTFKIT_MODEL_INPUT);
    inputs[8] = NAN;
    assert(ptfkit_euptf2_predict(model, inputs, 9, NULL, 5, means, 7, q, 30) == PTFKIT_MODEL_INPUT);
    ptfkit_euptf2_free(model);
    for (size_t i = 8; i <= 20; i += 4) {
        bytes[i] ^= 1;
        model = NULL;
        assert(ptfkit_detail_euptf2_parse(&contract, bytes, sizeof(bytes), &model) ==
               PTFKIT_MODEL_FORMAT);
        assert(model == NULL);
        bytes[i] ^= 1;
    }
}

static void reject_authenticated(unsigned char *bytes, size_t size) {
    unsigned char hash[32];
    char hex[65];
    ptfkit_detail_sha256(bytes, size, hash);
    for (size_t i = 0; i < 32; ++i)
        sprintf(hex + 2 * i, "%02x", hash[i]);
    ptfkit_euptf2_ths *model = NULL;
    assert(ptfkit_detail_qrf_decode(bytes, size, hex, &model) == PTFKIT_MODEL_FORMAT);
    assert(model == NULL);
}

int main(void) {
    check_multivariate();
    assert(sizeof(fixture) == 136);
    ptfkit_euptf2_ths *model = NULL;
    assert(ptfkit_euptf2_ths_from_bytes(fixture, sizeof(fixture), &model) ==
           PTFKIT_MODEL_INTEGRITY);
    assert(model == NULL);
    assert(ptfkit_detail_qrf_decode(fixture, sizeof(fixture), sha, &model) == PTFKIT_MODEL_OK);
    double inputs[4] = {40, 40, 20, 30}, out[4];
    const double left[4] = {0.5, 0.23, 0.5, 0.77}, right[4] = {0.65, 0.805, 0.85, 0.895};
    assert(ptfkit_euptf2_ths_predict(model, inputs, out) == PTFKIT_MODEL_OK);
    for (size_t i = 0; i < 4; ++i)
        assert(fabs(out[i] - left[i]) < 1e-14);
    inputs[3] = 30.0001;
    assert(ptfkit_euptf2_ths_predict(model, inputs, out) == PTFKIT_MODEL_OK);
    for (size_t i = 0; i < 4; ++i)
        assert(fabs(out[i] - right[i]) < 1e-14);
    inputs[3] = NAN;
    assert(ptfkit_euptf2_ths_predict(model, inputs, out) == PTFKIT_MODEL_INPUT);
    for (size_t i = 0; i < 4; ++i)
        assert(isnan(out[i]));
    ptfkit_euptf2_ths_free(model);
    unsigned char bytes[137];
    const size_t offsets[] = {8, 12, 16, 20, 24, 28, 56};
    const unsigned char values[] = {2, 0, 255, 0, 1, 4, 0};
    for (size_t i = 0; i < sizeof(offsets) / sizeof(offsets[0]); ++i) {
        memcpy(bytes, fixture, sizeof(fixture));
        bytes[offsets[i]] = values[i];
        reject_authenticated(bytes, sizeof(fixture));
    }
    memcpy(bytes, fixture, sizeof(fixture));
    bytes[74] = 0xf8;
    bytes[75] = 0x7f; /* NaN response sample. */
    reject_authenticated(bytes, sizeof(fixture));
    memcpy(bytes, fixture, sizeof(fixture));
    reject_authenticated(bytes, sizeof(fixture) - 1);
    bytes[136] = 0;
    reject_authenticated(bytes, sizeof(bytes));
    return 0;
}
