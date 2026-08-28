cmake_minimum_required(VERSION 3.26)

project(ptfkit LANGUAGES C)

include(FetchContent)

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

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)

set(PTFKIT_NATIVE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/ptfkit-native/include")
if(NOT EXISTS "${PTFKIT_NATIVE_INCLUDE_DIR}/ptfkit/ptfkit.h")
    set(PTFKIT_NATIVE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../ptfkit-native/include")
endif()

Python_add_library(_ptfkit MODULE WITH_SOABI src/ptfkit/ptfkit.c)
target_link_libraries(_ptfkit PRIVATE Python::NumPy sleef)
target_include_directories(
    _ptfkit
    PRIVATE
        src/ptfkit
        "${PTFKIT_NATIVE_INCLUDE_DIR}"
        "${simde_SOURCE_DIR}"
        "${sleef_BINARY_DIR}/include"
)
target_compile_options(_ptfkit PRIVATE -mavx512f -mfma)
install(TARGETS _ptfkit DESTINATION ptfkit)
