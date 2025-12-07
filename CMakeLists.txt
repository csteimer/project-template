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

# ------------------------------------------------------------------------------
# Tooling / helper modules
# ------------------------------------------------------------------------------
# Make custom CMake modules discoverable
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Wrappers for cmake messages
include(Logging)

# Compiler cache (ccache / sccache)
include(EnableCcache)

# Warnings per target
include(TargetSetWarnings)

# Sanitizers per target (ASan / TSan)
include(TargetSetSanitizer)

# include-what-you-use integration
include(EnableIWYU)

# Coverage integration (gcovr)
include(EnableCoverage)

# Google Benchmark helpers
include(EnableBenchmarks)

# ------------------------------------------------------------------------------
# Options that might not be set by Conan / presets
# ------------------------------------------------------------------------------

# Ensure BUILD_TESTING exists even if not set by toolchain/presets
if(NOT DEFINED BUILD_TESTING)
  option(BUILD_TESTING "Build tests" ON)
endif()

# Let Conan-generated deps be visible (CMakeDeps)
include(${CMAKE_BINARY_DIR}/conan_deps.cmake OPTIONAL)

# ------------------------------------------------------------------------------
# External dependencies
# ------------------------------------------------------------------------------
log_status("Including dependencies.cmake file")
include(dependencies.cmake)

# ------------------------------------------------------------------------------
# Project code
# ------------------------------------------------------------------------------

add_subdirectory(app)
add_subdirectory(src)

# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

if(BUILD_TESTING)
  enable_testing()
  add_subdirectory(tests/integration)
  add_subdirectory(tests/unit)
endif()

# ------------------------------------------------------------------------------
# Benchmarks
# ------------------------------------------------------------------------------
if(BUILD_BENCHMARKS)
  add_subdirectory(tests/benchmark)
endif()

# ------------------------------------------------------------------------------
# Apply IWYU + warnings + sanitizers after targets exist
# ------------------------------------------------------------------------------

# Project library / executable targets
foreach(tgt IN ITEMS ${PROJECT_NAME} ${PROJECT_NAME}_exec)
  if(TARGET ${tgt})
    enable_iwyu_for_target(${tgt})
    target_set_warnings(${tgt})
    target_set_sanitizer(${tgt})
  endif()
endforeach()

# Test target
if(DEFINED UNIT_TEST_NAME AND TARGET ${UNIT_TEST_NAME})
  enable_iwyu_for_target(${UNIT_TEST_NAME})
  target_set_warnings(${UNIT_TEST_NAME})
  target_set_sanitizer(${UNIT_TEST_NAME})
endif()

# ------------------------------------------------------------------------------
# Coverage target (gcovr)
# ------------------------------------------------------------------------------
# Coverage flags come from Conan/presets; this only adds the 'coverage' custom target.
if(BUILD_COVERAGE
   AND BUILD_TESTING
   AND DEFINED UNIT_TEST_NAME
   AND TARGET ${UNIT_TEST_NAME}
   )
  enable_coverage(${UNIT_TEST_NAME})
endif()
