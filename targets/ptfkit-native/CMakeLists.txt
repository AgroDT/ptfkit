cmake_minimum_required(VERSION 3.21)

include(cmake/ptfkitVersion.cmake)
project(ptfkit VERSION ${PTFKIT_VERSION} LANGUAGES C)

include(CMakePackageConfigHelpers)
include(CMakeDependentOption)
include(GNUInstallDirs)

add_library(ptfkit_c INTERFACE)
add_library(ptfkit::c ALIAS ptfkit_c)
set_target_properties(ptfkit_c PROPERTIES EXPORT_NAME c)
target_compile_features(ptfkit_c INTERFACE c_std_11)
target_compile_definitions(ptfkit_c INTERFACE
    PTFKIT_VERSION=\"${PROJECT_VERSION}\"
)
if(UNIX)
    target_link_libraries(ptfkit_c INTERFACE m)
endif()
target_include_directories(ptfkit_c INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

cmake_dependent_option(
    PTFKIT_BUILD_CPP_MODULES
    "Build the C++20 module interface target"
    ON
    "CMAKE_VERSION VERSION_GREATER_EQUAL 3.28"
    OFF
)

if(PTFKIT_BUILD_CPP_MODULES)
    enable_language(CXX)
    add_subdirectory(cpp)
    set(INSTALL_EXPORT_ARGS CXX_MODULES_DIRECTORY cxx-modules)
endif()

install(TARGETS ptfkit_c EXPORT ptfkitTargets)
install(
    DIRECTORY include/ptfkit/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/ptfkit
)
install(
    FILES README.md LICENSE
    DESTINATION ${CMAKE_INSTALL_DOCDIR}
)
install(
    EXPORT ptfkitTargets
    NAMESPACE ptfkit::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ptfkit
    ${INSTALL_EXPORT_ARGS}
)
configure_package_config_file(
    cmake/ptfkitConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/ptfkitConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ptfkit
)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/ptfkitConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)
install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/ptfkitConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/ptfkitConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ptfkit
)

include(CTest)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()
