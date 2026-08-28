cmake_minimum_required(VERSION 3.28)

set(
    CMAKE_EXPERIMENTAL_CXX_IMPORT_STD
    "f35a9ac6-8463-4d38-8eec-5d6008153e7d"
)

project(ptfkit-native-benchmarks VERSION "0.1.0" LANGUAGES C CXX)

set(BUILD_TESTING OFF)

include(FetchContent)

FetchContent_Declare(
    ptfkit
    SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../targets/ptfkit-native"
)
FetchContent_MakeAvailable(ptfkit)

add_executable(ptfkit-c-benchmarks src/bench.c)
target_link_libraries(ptfkit-c-benchmarks PRIVATE ptfkit::batch_avx512)

add_executable(ptfkit-cpp-benchmarks src/bench.cpp)
target_link_libraries(ptfkit-cpp-benchmarks PRIVATE ptfkit::cpp)
target_compile_features(ptfkit-cpp-benchmarks PRIVATE cxx_std_26)
set_target_properties(ptfkit-cpp-benchmarks PROPERTIES CXX_MODULE_STD ON)
