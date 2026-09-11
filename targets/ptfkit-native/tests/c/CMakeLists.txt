file(GLOB sources CONFIGURE_DEPENDS *.c)

ptfkit_add_native_tests(c
    SOURCES ${sources} ../support/umbrella.c
    LIBRARIES ptfkit::c
)

set_target_properties(c_umbrella PROPERTIES
    C_STANDARD 11 C_STANDARD_REQUIRED ON C_EXTENSIONS OFF
)

ptfkit_add_comparator_test(C c_comparator)
