# Only define the option if not already set by presets/toolchain
if(NOT DEFINED BUILD_COVERAGE)
  option(BUILD_COVERAGE "Build with coverage instrumentation and add 'coverage' target" OFF)
endif()

# Public entry point:
#   enable_coverage(<test_target>)
#
# This:
#   - checks BUILD_COVERAGE
#   - ensures GCC
#   - finds gcovr
#   - defines a 'coverage' custom target that:
#       * runs ctest
#       * generates HTML report in <build>/coverage_report/index.html
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
        "gcovr not found - please install gcovr, e.g.:
         sudo apt-get install -y gcovr"
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
