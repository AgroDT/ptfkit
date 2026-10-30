#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ptfkit/ptfkit.h>
#include <assert.h>
#include <string.h>
#include "affine_model.h"

int main(void) {
    /* Standard SHA-256 known-answer vectors, including two-block padding. */
    const char *messages[] = {"", "abc",
                              "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"};
    const char *hashes[] = {"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                            "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"};
    for (size_t j = 0; j < 3; ++j) {
        unsigned char digest[32];
        ptfkit_detail_sha256((const unsigned char *)messages[j], strlen(messages[j]), digest);
        for (size_t i = 0; i < 32; ++i)
            assert(digest[i] == ptfkit_detail_unhex(hashes[j][2 * i]) * 16 +
                                    ptfkit_detail_unhex(hashes[j][2 * i + 1]));
    }
    ptfkit_model *model = NULL;
    unsigned char source[sizeof(affine_model)];
    memcpy(source, affine_model, sizeof(source));
    assert(ptfkit_model_from_bytes(source, sizeof(source), affine_sha256, &model) ==
           PTFKIT_MODEL_OK);
    memset(source, 0, sizeof(source));
    char verified[65];
    assert(ptfkit_model_sha256(model, verified) == PTFKIT_MODEL_OK &&
           !strcmp(verified, affine_sha256));
    assert(ptfkit_model_network_count(model) == 1);
    double input[] = {3, 4}, out[2];
    assert(ptfkit_model_predict_network(model, 0, input, 2, out, 2) == PTFKIT_MODEL_OK);
    assert(out[0] == 21 && out[1] == 9);
    assert(ptfkit_model_predict_network(model, 1, input, 2, out, 2) == PTFKIT_MODEL_INPUT);
    assert(ptfkit_model_predict_network(model, 0, input, 2, out, 1) == PTFKIT_MODEL_INPUT);
    double results[14];
    assert(ptfkit_rosetta3_predict(model, 2, 0, input, 2, results) == PTFKIT_MODEL_INTEGRITY);
    ptfkit_model_free(model);
    unsigned char changed[sizeof(affine_model)];
    memcpy(changed, affine_model, sizeof(changed));
    changed[sizeof(changed) - 1] ^= 1;
    model = NULL;
    assert(ptfkit_model_from_bytes(changed, sizeof(changed), affine_sha256, &model) ==
               PTFKIT_MODEL_INTEGRITY &&
           model == NULL);
    /* Correct hashes of malformed containers exercise parsing, not just hashing. */
    for (size_t n = 0; n < sizeof(affine_model); ++n) {
        unsigned char digest[32];
        char hex[65];
        static const char digits[] = "0123456789abcdef";
        ptfkit_detail_sha256(affine_model, n, digest);
        for (size_t i = 0; i < 32; ++i) {
            hex[2 * i] = digits[digest[i] >> 4];
            hex[2 * i + 1] = digits[digest[i] & 15];
        }
        hex[64] = 0;
        assert(ptfkit_model_from_bytes(affine_model, n, hex, &model) == PTFKIT_MODEL_FORMAT &&
               model == NULL);
    }
    ptfkit_model_free(NULL);
    return 0;
}
