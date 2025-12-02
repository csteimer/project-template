cmake_minimum_required(VERSION 3.28.3)

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
include(EnableBenchmark)
include(EnableCcache)
include(EnableIWYU)
include(EnableCoverage)
include(TargetSetWarnings)

# Let Conan-generated deps be visible (CMakeDeps)
include(${CMAKE_BINARY_DIR}/conan_deps.cmake OPTIONAL)

# --- External dependencies ---
message(STATUS "Including dependencies.cmake file ...")
include(dependencies.cmake)

# --- Project code ---
add_subdirectory(src)

# --- Tests ---
if(BUILD_TESTING)
  enable_testing()
  add_subdirectory(tests)
endif()

# --- Apply IWYU + warnings after targets exist ---
# Project target
if(TARGET ${PROJECT_NAME})
  enable_iwyu_for_target(${PROJECT_NAME})
  target_set_warnings(${PROJECT_NAME})
endif()

# Test target (if tests defined TEST_NAME in tests/CMakeLists.txt)
if(DEFINED TEST_NAME AND TARGET ${TEST_NAME})
  enable_iwyu_for_target(${TEST_NAME})
  target_set_warnings(${TEST_NAME})
endif()

# --- Coverage target (gcovr) ---
# Coverage flags come from Conan/presets; this only adds the 'coverage' custom target.
if(BUILD_COVERAGE
   AND BUILD_TESTING
   AND DEFINED TEST_NAME
   AND TARGET ${TEST_NAME}
   )
  enable_coverage(${TEST_NAME})
endif()

# --- Benchmarks ---
if(BUILD_BENCHMARKS)
  add_subdirectory(benchmarks)
endif()
