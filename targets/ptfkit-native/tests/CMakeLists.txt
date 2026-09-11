function(ptfkit_add_native_tests case)
    cmake_parse_arguments(
        PARSE_ARGV 1 arg
        ""
        ""
        "SOURCES;LIBRARIES;PROPERTIES;COMPILE_FEATURES"
    )
    foreach(source ${arg_SOURCES})
        get_filename_component(name ${source} NAME_WE)
        set(target ${case}_${name})
        add_executable(${target} ${source})
        target_link_libraries(${target} PRIVATE ${arg_LIBRARIES})
        if(arg_PROPERTIES)
            set_target_properties(${target} PROPERTIES ${arg_PROPERTIES})
        endif()
        if(arg_COMPILE_FEATURES)
            target_compile_features(${target} PRIVATE ${arg_COMPILE_FEATURES})
        endif()
        add_test(NAME ${target} COMMAND ${target})
    endforeach()
endfunction()

function(ptfkit_add_comparator_test language target)
    set(source "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/support/comparator.c")
    # Source LANGUAGE properties are scoped to the calling directory. C and C++
    # register this source from separate subdirectories to keep their modes independent.
    set_source_files_properties("${source}" PROPERTIES LANGUAGE ${language})
    add_executable(${target} "${source}")
    target_link_libraries(${target} PRIVATE ptfkit::c)
    set_target_properties(${target} PROPERTIES
        C_STANDARD 11 C_STANDARD_REQUIRED ON C_EXTENSIONS OFF
        CXX_STANDARD 23 CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF
    )
    add_test(NAME ${target} COMMAND ${target})
    foreach(case IN ITEMS absolute relative negative zero guard nan)
        add_test(NAME ${target}_reject_${case}
            COMMAND ${CMAKE_COMMAND}
                "-DEXECUTABLE=$<TARGET_FILE:${target}>"
                "-DCASE=${case}"
                -P "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/support/check_rejection.cmake"
        )
    endforeach()
endfunction()

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

add_subdirectory(c)

include(CheckLanguage)
check_language(CXX)
if(CMAKE_CXX_COMPILER)
    enable_language(CXX)
    add_subdirectory(cpp_fallback)
endif()

if(PTFKIT_BUILD_CPP_MODULES)
    add_subdirectory(cpp)
endif()
