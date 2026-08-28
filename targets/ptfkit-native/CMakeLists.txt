cmake_minimum_required(VERSION 3.21)

include(cmake/ptfkitVersion.cmake)
project(ptfkit VERSION ${PTFKIT_VERSION} LANGUAGES C)

include(CMakePackageConfigHelpers)
include(CMakeDependentOption)
include(FetchContent)
include(GNUInstallDirs)

set(SLEEF_BUILD_DFT OFF CACHE BOOL "" FORCE)
set(SLEEF_BUILD_GNUABI_LIBS OFF CACHE BOOL "" FORCE)
set(SLEEF_BUILD_INLINE_HEADERS OFF CACHE BOOL "" FORCE)
set(SLEEF_BUILD_QUAD OFF CACHE BOOL "" FORCE)
set(SLEEF_BUILD_SCALAR_LIB OFF CACHE BOOL "" FORCE)
set(SLEEF_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(SLEEF_BUILD_LIBM ON CACHE BOOL "" FORCE)
set(SLEEF_DISABLE_MPFR ON CACHE BOOL "" FORCE)
set(SLEEF_ENABLE_LTO OFF CACHE BOOL "" FORCE)
set(SLEEF_ENABLE_TLFLOAT OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    simde
    GIT_REPOSITORY https://github.com/simd-everywhere/simde.git
    GIT_TAG 71fd833d9666141edcd1d3c109a80e228303d8d7
    GIT_SHALLOW TRUE
)
FetchContent_Declare(
    sleef
    GIT_REPOSITORY https://github.com/shibatch/sleef.git
    GIT_TAG 906ca7512ee483296780a81a21b9ca715d40dfe1
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(simde sleef)

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

add_library(ptfkit_batch INTERFACE)
add_library(ptfkit::batch ALIAS ptfkit_batch)
target_compile_options(ptfkit_batch INTERFACE -mavx2 -mfma)
target_include_directories(ptfkit_batch INTERFACE
    $<BUILD_INTERFACE:${simde_SOURCE_DIR}>
    $<BUILD_INTERFACE:${sleef_BINARY_DIR}/include>
)
target_link_libraries(ptfkit_batch INTERFACE ptfkit::c sleef)

add_library(ptfkit_batch_avx512 INTERFACE)
add_library(ptfkit::batch_avx512 ALIAS ptfkit_batch_avx512)
target_compile_options(ptfkit_batch_avx512 INTERFACE -mavx512f -mfma)
target_include_directories(ptfkit_batch_avx512 INTERFACE
    $<BUILD_INTERFACE:${simde_SOURCE_DIR}>
    $<BUILD_INTERFACE:${sleef_BINARY_DIR}/include>
)
target_link_libraries(ptfkit_batch_avx512 INTERFACE ptfkit::c sleef)

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
