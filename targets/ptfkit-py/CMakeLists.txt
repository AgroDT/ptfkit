cmake_minimum_required(VERSION 3.26)

project(ptfkit LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)

set(PTFKIT_NATIVE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/ptfkit-native/include")
if(NOT EXISTS "${PTFKIT_NATIVE_INCLUDE_DIR}/ptfkit/ptfkit.h")
    set(PTFKIT_NATIVE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../ptfkit-native/include")
endif()

Python_add_library(_ptfkit MODULE WITH_SOABI src/ptfkit/ptfkit.c)
target_link_libraries(_ptfkit PRIVATE Python::NumPy)
target_include_directories(_ptfkit PRIVATE src/ptfkit "${PTFKIT_NATIVE_INCLUDE_DIR}")
install(TARGETS _ptfkit DESTINATION ptfkit)
