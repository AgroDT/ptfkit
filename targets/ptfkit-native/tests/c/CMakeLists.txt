file(GLOB sources CONFIGURE_DEPENDS *.c)

ptfkit_add_native_tests(c
    SOURCES ${sources}
    LIBRARIES ptfkit::c
)

ptfkit_add_comparator_test(C c_comparator)
