file(GLOB_RECURSE PTFKIT_CPP_MODULES CONFIGURE_DEPENDS *.cppm)

add_library(ptfkit::cpp INTERFACE IMPORTED GLOBAL)
target_compile_features(ptfkit::cpp INTERFACE cxx_std_23)
target_compile_definitions(ptfkit::cpp INTERFACE
    PTFKIT_VERSION=\"${PROJECT_VERSION}\"
)
target_compile_options(ptfkit::cpp INTERFACE
    $<$<CXX_COMPILER_ID:GNU>:-fmodules-ts>
)
target_sources(ptfkit::cpp INTERFACE
    FILE_SET CXX_MODULES
    BASE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}
    FILES ${PTFKIT_CPP_MODULES}
)

set(PTFKIT_CPP_MODULE_INSTALL_DIR ${CMAKE_INSTALL_LIBDIR}/ptfkit/modules)
install(
    FILES ${PTFKIT_CPP_MODULES}
    DESTINATION ${PTFKIT_CPP_MODULE_INSTALL_DIR}
)

set(PTFKIT_CPP_MODULE_PACKAGE_FILES)
foreach(module IN LISTS PTFKIT_CPP_MODULES)
    get_filename_component(module_name ${module} NAME)
    list(APPEND PTFKIT_CPP_MODULE_PACKAGE_FILES
        "\${PACKAGE_PREFIX_DIR}/${PTFKIT_CPP_MODULE_INSTALL_DIR}/${module_name}"
    )
endforeach()
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/../cmake/ptfkitCppModules.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/ptfkitCppModules.cmake
    @ONLY
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/ptfkitCppModules.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ptfkit
)
