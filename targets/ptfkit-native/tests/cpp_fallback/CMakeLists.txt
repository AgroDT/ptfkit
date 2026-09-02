file(GLOB sources CONFIGURE_DEPENDS ../c/*.c)

set_source_files_properties(
    ${sources}
    PROPERTIES LANGUAGE CXX
)

ptfkit_add_native_tests(cpp_fallback
    SOURCES ${sources}
    LIBRARIES ptfkit::c
)
