execute_process(
    COMMAND "${EXECUTABLE}" reject "${CASE}"
    RESULT_VARIABLE result
    OUTPUT_VARIABLE output
    ERROR_VARIABLE error
    TIMEOUT 10
)

if(NOT "${result}" STREQUAL "1")
    message(FATAL_ERROR
        "Expected assertion exit code 1 for ${CASE}, got '${result}'.\n${output}${error}"
    )
endif()

if(NOT error MATCHES "assertion failed: [^\n]*: case=${CASE},")
    message(FATAL_ERROR
        "Missing assertion diagnostic for ${CASE}.\n${output}${error}"
    )
endif()
