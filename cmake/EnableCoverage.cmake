# --------------------------------------------------------------------------------------------------
# EnableCoverage.cmake
#
# This module integrates **code coverage** generation (via `gcovr`) into your CMake project.
#
# It provides a single public function:
#
#     enable_coverage(<test_target>)
#
# which:
#   - Respects the cache variable:
#
#         BUILD_COVERAGE = ON|OFF
#
#     (typically set by Conan/CMake presets).
#
#   - When BUILD_COVERAGE=ON:
#       * Applies GCC coverage instrumentation flags equivalent to the legacy
#         coverage Conan profile:
#             C/C++ compile flags:  -O0 -g --coverage
#             Link flags:          --coverage
#       * Ensures a supported compiler (GCC).
#       * Locates the `gcovr` executable.
#       * Defines a custom target:
#
#             coverage
#
#         that:
#           - runs the test suite (`ctest`) in the build directory
#           - generates an HTML coverage report under:
#
#             <build>/coverage_report/index.html
#
# Minimal usage in your top-level CMakeLists.txt:
#
#     list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#     include(EnableCoverage)
#
#     if(BUILD_TESTING AND DEFINED UNIT_TEST_NAME AND TARGET ${UNIT_TEST_NAME})
#         enable_coverage(${UNIT_TEST_NAME})
#     endif()
#
# Typically, Conan or your CMakePresets will set:
#
#     -DBUILD_COVERAGE=ON
#
# for a dedicated "coverage" preset.
#
# --------------------------------------------------------------------------------------------------

# Allow presets/toolchain to control BUILD_COVERAGE. Only define the option if not set yet.
if(NOT DEFINED BUILD_COVERAGE)
  option(BUILD_COVERAGE "Build with coverage instrumentation and add 'coverage' target" OFF)
endif()

# If coverage is enabled, set up global compile/link flags equivalent to the old coverage profile.
if(BUILD_COVERAGE)
  # Coverage logic here assumes GCC-style coverage flags
  if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message(
      FATAL_ERROR "EnableCoverage: BUILD_COVERAGE=ON but compiler is not GCC. "
                  "Current compiler: ${CMAKE_CXX_COMPILER_ID}"
      )
  endif()

  # Instrument all C/C++ targets in this project with coverage flags.
  add_compile_options(-O0 -g --coverage)
  add_link_options(--coverage)
endif()

# --------------------------------------------------------------------------------------------------
# enable_coverage(<test_target>)
#
# Public entry point to configure coverage reporting for a given test executable target.
#
# Arguments:
#   <test_target> : Name of an existing CTest / GTest executable target.
#
# Behavior:
#   - If BUILD_COVERAGE=OFF     -> does nothing (prints a STATUS message).
#   - If BUILD_COVERAGE=ON      -> enforces:
#       * BUILD_TESTING=ON
#       * `gcovr` must be available in PATH
#       * Adds a "coverage" custom target that:
#             - runs all tests
#             - generates an HTML report via gcovr
# --------------------------------------------------------------------------------------------------
function(enable_coverage test_target)
  if(NOT BUILD_COVERAGE)
    message(STATUS "Coverage: BUILD_COVERAGE=OFF, not adding coverage target")
    return()
  endif()

  if(NOT TARGET ${test_target})
    message(FATAL_ERROR "enable_coverage: test target '${test_target}' does not exist")
  endif()

  # For coverage runs we want tests built/enabled
  set(BUILD_TESTING
      ON
      CACHE BOOL "Build tests" FORCE
      )

  find_program(
    GCOVR_EXECUTABLE gcovr
    HINTS ENV PATH
    DOC "Path to gcovr executable"
    )
  if(NOT GCOVR_EXECUTABLE)
    message(
      FATAL_ERROR "gcovr not found - please install gcovr, for example:\n"
                  "  sudo apt-get install -y gcovr"
      )
  endif()

  add_custom_target(
    coverage
    COMMENT "Running tests and generating coverage report with gcovr"
    VERBATIM
    # 1) Run tests
    COMMAND ${CMAKE_CTEST_COMMAND} --test-dir ${CMAKE_BINARY_DIR} --output-on-failure
    # 2) Ensure output directory exists
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/coverage_report
    # 3) Run gcovr from project root, include only src/
    COMMAND
      ${GCOVR_EXECUTABLE} --root ${CMAKE_SOURCE_DIR} --filter src/ --html --html-details --output
      ${CMAKE_BINARY_DIR}/coverage_report/index.html ${CMAKE_BINARY_DIR}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    )

  add_dependencies(coverage ${test_target})
endfunction()
