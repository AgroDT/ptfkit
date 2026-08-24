add_library(ptfkit_cpp)
add_library(ptfkit::cpp ALIAS ptfkit_cpp)
set_target_properties(ptfkit_cpp PROPERTIES
    EXPORT_NAME cpp CXX_SCAN_FOR_MODULES ON
)
target_compile_features(ptfkit_cpp PUBLIC cxx_std_20)
target_compile_definitions(ptfkit_cpp PUBLIC
    PTFKIT_VERSION=\"${PROJECT_VERSION}\"
)
target_compile_options(ptfkit_cpp PUBLIC
    $<$<CXX_COMPILER_ID:GNU>:-fmodules-ts>
)
target_link_libraries(ptfkit_cpp PRIVATE ptfkit::c)
file(GLOB_RECURSE PTFKIT_CPP_MODULES CONFIGURE_DEPENDS *.cppm)
target_sources(ptfkit_cpp PUBLIC
    FILE_SET CXX_MODULES
    FILES ${PTFKIT_CPP_MODULES}
)
install(
    TARGETS ptfkit_cpp
    EXPORT ptfkitTargets
    FILE_SET CXX_MODULES DESTINATION ${CMAKE_INSTALL_LIBDIR}/ptfkit/modules
)
