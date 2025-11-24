set(TEST_NAME project_template_tests)
# Expose TEST_NAME to the parent scope so top-level CMakeLists.txt can use it
set(TEST_NAME
    ${TEST_NAME}
    PARENT_SCOPE
    )

# -----------------------------
# GoogleTest
# -----------------------------
find_package(GTest CONFIG REQUIRED)

# -----------------------------
# Unit Tests Executable
# -----------------------------
add_executable(
  ${TEST_NAME} example.test.cpp unit_tests_main.cpp # add more test sources here, e.g.:
  )

target_link_libraries(
  ${TEST_NAME}
  PRIVATE GTest::gtest
          # GTest::gtest_main          # only if you want the default main instead of your own
  )

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
