cmake_minimum_required(VERSION 3.21)

project(ptfkit VERSION 0.1.0 LANGUAGES C CXX)

include(CMakePackageConfigHelpers)
include(CMakeDependentOption)
include(GNUInstallDirs)

add_library(ptfkit_c INTERFACE)
add_library(ptfkit::c ALIAS ptfkit_c)
set_target_properties(ptfkit_c PROPERTIES EXPORT_NAME c)
target_compile_features(ptfkit_c INTERFACE c_std_11)
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
    include(cmake/ptfkitModules.cmake)
    add_library(ptfkit_cpp)
    add_library(ptfkit::cpp ALIAS ptfkit_cpp)
    set_target_properties(ptfkit_cpp PROPERTIES
        EXPORT_NAME cpp CXX_SCAN_FOR_MODULES ON
    )
    target_compile_features(ptfkit_cpp PUBLIC cxx_std_20)
    target_compile_options(ptfkit_cpp PUBLIC
        $<$<CXX_COMPILER_ID:GNU>:-fmodules-ts>
    )
    target_sources(ptfkit_cpp PUBLIC
        FILE_SET CXX_MODULES
        FILES ${PTFKIT_CPP_MODULES}
    )
endif()

install(TARGETS ptfkit_c EXPORT ptfkitTargets)
install(
    DIRECTORY include/ptfkit/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/ptfkit
)
if(PTFKIT_BUILD_CPP_MODULES)
    install(
        TARGETS ptfkit_cpp
        EXPORT ptfkitTargets
        FILE_SET CXX_MODULES DESTINATION ${CMAKE_INSTALL_LIBDIR}/ptfkit/modules
    )
endif()
install(
    EXPORT ptfkitTargets
    NAMESPACE ptfkit::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ptfkit
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
