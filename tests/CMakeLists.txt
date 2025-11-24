# --- Project Setup ---
set(TEST_NAME project_template_tests)

project(
  ${TEST_NAME}
  VERSION 0.1
  LANGUAGES CXX
  )

# -----------------------------
# Additional Dependencies
# -----------------------------
fetchcontent_declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
  DOWNLOAD_NO_PROGRESS TRUE
  )
fetchcontent_makeavailable(googletest)

# -----------------------------
# Unit Tests Executable
# -----------------------------
add_executable(${TEST_NAME} unit_tests_main.cpp)

target_link_libraries(${TEST_NAME} PRIVATE GTest::gtest)

# -----------------------------
# GoogleTest Discovery
# -----------------------------
include(GoogleTest)

set_target_properties(${TEST_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/tests")

# Always rediscover just before running to avoid stale test lists
gtest_discover_tests(
  ${TEST_NAME} DISCOVERY_MODE PRE_TEST
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  TEST_PREFIX "unit.test." DISCOVERY_TIMEOUT 30
  PROPERTIES LABELS "unit"
  )

# -----------------------------
# Custom Targets for Convenience
# -----------------------------
add_custom_target(
  run_all_unit_tests
  COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure -L unit
  DEPENDS ${TEST_NAME}
  COMMENT "Running all unit tests"
  )
