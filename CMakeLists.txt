cmake_minimum_required(VERSION 4.00)

set(PROJECT_NAME project_template)
project(
  ${PROJECT_NAME}
  VERSION 0.1
  LANGUAGES CXX
  )

# Allow legacy subprojects that still set very old policy versions (e.g. yaml-cpp)
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include custom cmake scripts
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(EnableBenchmarks)
include(EnableCcache)
include(EnableIWYU)

# Let Conan-generated deps be visible
include(${CMAKE_BINARY_DIR}/conan_deps.cmake OPTIONAL)

# --- External dependencies ---
message(STATUS "Including dependencies.cmake file ...")
include(dependencies.cmake)

# --- Project code ---
add_subdirectory(src)

enable_iwyu_for_target(${PROJECT_NAME})
enable_iwyu_for_target(${TEST_NAME})

target_set_warnings(${PROJECT_NAME})
target_set_warnings(${TEST_NAME})

# --- Testing and code coverage report (gcovr) ---
if(BUILD_COVERAGE)
  set(BUILD_TESTING ON)
  if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message(FATAL_ERROR "Coverage only supported with GCC.")
  endif()

  find_program(
    GCOVR_EXECUTABLE gcovr
    HINTS ENV PATH
    DOC "Path to gcovr executable"
    )
  if(NOT GCOVR_EXECUTABLE)
    message(
      FATAL_ERROR
        "gcovr not found - please install gcovr:
        sudo apt-get install -y gcovr"
      )
  endif()

  add_compile_options(-O0 -g --coverage)
  add_link_options(--coverage)
endif()

if(BUILD_TESTING)
  enable_testing()
  add_subdirectory(tests)
endif()

if(BUILD_COVERAGE)
  add_custom_target(
    coverage
    COMMENT "Running tests and generating coverage report with gcovr"
    VERBATIM
    # 1) Run tests
    COMMAND ${CMAKE_CTEST_COMMAND} --test-dir ${CMAKE_BINARY_DIR} --output-on-failure
    # 2) Specify output directory
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/coverage_report
    # 3) Run gcovr from project root, include only src/
    COMMAND
      ${GCOVR_EXECUTABLE} --root ${CMAKE_SOURCE_DIR} --filter src/ --html --html-details --output
      ${CMAKE_BINARY_DIR}/coverage_report/index.html ${CMAKE_BINARY_DIR}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    )
  add_dependencies(coverage ${TEST_NAME})
endif()

if(ENABLE_IWYU AND IWYU_EXECUTABLE)
  # Try to find Python iwyu_tool.py
  find_program(PYTHON_EXECUTABLE NAMES python3 python)

  if(PYTHON_EXECUTABLE)
    add_custom_target(
      iwyu-all
      COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/cmake/iwyu_tool.py -p ${CMAKE_BINARY_DIR}
      WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
      COMMENT "Running IWYU over all translation units"
      )
  endif()
endif()

if(BUILD_BENCHMARKS)
  target_add_benchmark(example_benchmark benchmarks/benchmark_example.cpp)
endif()
