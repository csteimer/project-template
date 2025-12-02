# Name of the unit test executable (visible to parent scope)
set(UNIT_TEST_NAME "${PROJECT_NAME}_unit_tests")
set(UNIT_TEST_NAME
    "${UNIT_TEST_NAME}"
    PARENT_SCOPE
    )

# -----------------------------
# GTest package (library + targets)
# -----------------------------
find_package(GTest CONFIG REQUIRED)

# -----------------------------
# Add test modules
# -----------------------------
add_subdirectory(utils)

# -----------------------------
# Unit test executable
# -----------------------------
add_executable(${UNIT_TEST_NAME} main.unit_test.cpp # add more test sources here
               )

target_link_libraries(
  ${UNIT_TEST_NAME}
  PRIVATE GTest::gtest # you provide your own main()
          # GTest::gmock       # add if you start using gMock
          utils_unit_test_lib
          # add more ..._unit_test_lib
  )

set_target_properties(
  ${UNIT_TEST_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/unit_test_output"
  )

# -----------------------------
# Include GoogleTest CMake helpers (like gtest_discover_tests, ...)
# -----------------------------
include(GoogleTest)

# Always rediscover just before running to avoid stale test lists
gtest_discover_tests(
  ${UNIT_TEST_NAME} DISCOVERY_MODE PRE_TEST
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  TEST_PREFIX "unit." DISCOVERY_TIMEOUT 30
  PROPERTIES LABELS "unit"
  )

# -----------------------------
# Convenience target
# -----------------------------
add_custom_target(
  run_unit_tests
  COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure -L unit
  DEPENDS ${UNIT_TEST_NAME}
  COMMENT "Running all unit tests"
  )
