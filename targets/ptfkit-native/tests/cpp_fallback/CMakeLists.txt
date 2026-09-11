file(GLOB sources CONFIGURE_DEPENDS ../c/*.c)
list(APPEND sources "${CMAKE_CURRENT_SOURCE_DIR}/../support/umbrella.c")

set_source_files_properties(
    ${sources}
    PROPERTIES LANGUAGE CXX
)

ptfkit_add_native_tests(cpp_fallback
    SOURCES ${sources}
    LIBRARIES ptfkit::c
    COMPILE_FEATURES cxx_std_23
)

ptfkit_add_comparator_test(CXX cpp_comparator)

set_target_properties(cpp_fallback_umbrella PROPERTIES
    CXX_STANDARD 23 CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF
)
