file(GLOB sources CONFIGURE_DEPENDS *.cpp)

ptfkit_add_native_tests(cpp
    SOURCES ${sources}
    LIBRARIES ptfkit::cpp
    PROPERTIES
        CXX_SCAN_FOR_MODULES ON
)

ptfkit_add_native_tests(cpp_umbrella
    SOURCES ${sources}
    LIBRARIES ptfkit::cpp
    DEFINITIONS IMPORT_UMBRELLA
    PROPERTIES
        CXX_SCAN_FOR_MODULES ON
)
