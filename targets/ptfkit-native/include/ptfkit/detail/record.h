#ifndef PTFKIT_DETAIL_RECORD_H
#define PTFKIT_DETAIL_RECORD_H

#ifdef __cplusplus
#define PTFKIT_RECORD_LITERAL(type, ...)                                                           \
    type { __VA_ARGS__ }
#else
#define PTFKIT_RECORD_LITERAL(type, ...)                                                           \
    (type) { __VA_ARGS__ }
#endif

#endif
