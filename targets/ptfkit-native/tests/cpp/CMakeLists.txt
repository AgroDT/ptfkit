file(GLOB sources CONFIGURE_DEPENDS *.cpp)

ptfkit_add_native_tests(cpp
    SOURCES ${sources} ../support/umbrella.cpp
    LIBRARIES ptfkit::cpp
    PROPERTIES
        CXX_SCAN_FOR_MODULES ON
)
