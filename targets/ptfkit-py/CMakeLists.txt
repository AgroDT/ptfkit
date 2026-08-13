cmake_minimum_required(VERSION 3.26)

project(ptfkit LANGUAGES C)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module NumPy)

Python_add_library(_ptfkit MODULE WITH_SOABI src/ptfkit/ptfkit.c)
target_link_libraries(_ptfkit PRIVATE Python::NumPy)
target_include_directories(_ptfkit PRIVATE src/ptfkit)
install(TARGETS _ptfkit DESTINATION ptfkit)
