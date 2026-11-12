cmake_minimum_required(VERSION 4.4.2)

project(ptfkit LANGUAGES C)

if(DEFINED Python_EXECUTABLE)
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c
                "import sysconfig; print(int(bool(sysconfig.get_config_var('Py_GIL_DISABLED'))))"
        OUTPUT_VARIABLE PTFKIT_PYTHON_GIL_DISABLED
        OUTPUT_STRIP_TRAILING_WHITESPACE
        COMMAND_ERROR_IS_FATAL ANY
    )
    if(PTFKIT_PYTHON_GIL_DISABLED STREQUAL "1")
        set(Python_FIND_ABI "OFF" "OFF" "OFF" "ON")
    endif()
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)

set(PTFKIT_NATIVE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/ptfkit-native/include")
if(NOT EXISTS "${PTFKIT_NATIVE_INCLUDE_DIR}/ptfkit/ptfkit.h")
    set(PTFKIT_NATIVE_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../ptfkit-native/include")
endif()

Python_add_library(_ptfkit MODULE WITH_SOABI src/ptfkit/ptfkit.c)
target_link_libraries(_ptfkit PRIVATE Python::NumPy)
target_include_directories(_ptfkit PRIVATE src/ptfkit "${PTFKIT_NATIVE_INCLUDE_DIR}")
install(TARGETS _ptfkit DESTINATION ptfkit)

# Each dense source has an internal extension and shared immutable prepared arrays.
file(GLOB PTFKIT_DENSE_EXTENSIONS CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/src/ptfkit/_*.c")
foreach(source IN LISTS PTFKIT_DENSE_EXTENSIONS)
    get_filename_component(module "${source}" NAME_WE)
    string(SUBSTRING "${module}" 1 -1 slug)
    set(parameters "${PTFKIT_NATIVE_INCLUDE_DIR}/../prepared/${slug}_data.c")
    if(NOT EXISTS "${parameters}")
        message(FATAL_ERROR "Prepared model arrays are missing. Run mise run models:prepare before building.")
    endif()
    Python_add_library(${module} MODULE WITH_SOABI "${source}" "${parameters}")
    target_compile_features(${module} PRIVATE c_std_11)
    target_include_directories(${module} PRIVATE "${PTFKIT_NATIVE_INCLUDE_DIR}")
    if(UNIX)
        target_link_libraries(${module} PRIVATE m)
    endif()
    install(TARGETS ${module} DESTINATION ptfkit)
endforeach()
