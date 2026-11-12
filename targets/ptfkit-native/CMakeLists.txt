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
    target_link_libraries(ptfkit_c INTERFACE $<BUILD_INTERFACE:m>)
endif()
target_include_directories(ptfkit_c INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

file(GLOB PTFKIT_PREPARED_MODELS CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/prepared/*_data.c")
if(NOT PTFKIT_PREPARED_MODELS)
    message(FATAL_ERROR "Prepared model arrays are missing. In a repository checkout run mise run models:prepare; distributions must include prepared arrays.")
endif()
if(PTFKIT_PREPARED_MODELS)
    add_library(ptfkit_model_data STATIC ${PTFKIT_PREPARED_MODELS})
    target_include_directories(ptfkit_model_data PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
    target_compile_features(ptfkit_model_data PRIVATE c_std_11)
    set_target_properties(ptfkit_model_data PROPERTIES POSITION_INDEPENDENT_CODE ON)
    target_link_libraries(ptfkit_c INTERFACE $<BUILD_INTERFACE:ptfkit_model_data>)
    # Keep native archives compiler-independent: consumers compile this data once.
    install(FILES ${PTFKIT_PREPARED_MODELS} DESTINATION ${CMAKE_INSTALL_DATADIR}/ptfkit)
endif()

cmake_dependent_option(
    PTFKIT_BUILD_CPP_MODULES
    "Provide the C++23 module interface target"
    ON
    "CMAKE_VERSION VERSION_GREATER_EQUAL 3.28"
    OFF
)

if(PTFKIT_BUILD_CPP_MODULES)
    enable_language(CXX)
    add_subdirectory(cpp)
endif()

install(TARGETS ptfkit_c EXPORT ptfkitTargets)
install(
    DIRECTORY include/ptfkit/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/ptfkit
)
install(
    FILES README.md LICENSE MODEL_NOTICE.txt
    DESTINATION ${CMAKE_INSTALL_DOCDIR}
)
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
    ARCH_INDEPENDENT
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
