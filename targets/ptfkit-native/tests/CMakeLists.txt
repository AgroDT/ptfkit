function(ptfkit_add_native_tests case)
    cmake_parse_arguments(
        PARSE_ARGV 1 arg
        ""
        ""
        "SOURCES;LIBRARIES;DEFINITIONS;PROPERTIES"
    )
    foreach(source ${arg_SOURCES})
        get_filename_component(name ${source} NAME_WE)
        set(target ${case}_${name})
        add_executable(${target} ${source})
        target_link_libraries(${target} PRIVATE ${arg_LIBRARIES})
        if(arg_DEFINITIONS)
            target_compile_definitions(${target} PRIVATE ${arg_DEFINITIONS})
        endif()
        if(arg_PROPERTIES)
            set_target_properties(${target} PROPERTIES ${arg_PROPERTIES})
        endif()
        add_test(NAME ${target} COMMAND ${target})
    endforeach()
endfunction()

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

add_subdirectory(c)

if(PTFKIT_BUILD_CPP_MODULES)
    add_subdirectory(cpp)
endif()
