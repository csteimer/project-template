# --------------------------------------------------------------------------------------------------
# EnableBenchmarks.cmake
#
# This module integrates **Google Benchmark** into your CMake project when:
#
#       BUILD_BENCHMARKS = ON
#
# It provides two main helper functions:
#
#     target_add_benchmark(<name> <sources...>)
#         - Creates a benchmark executable linked against Google Benchmark.
#         - Optionally applies your standard warning settings via target_set_warnings().
#         - Registers the target in a global list for later aggregation.
#
#     add_benchmark_aggregate_target()
#         - Creates a convenience target:
#
#               run-benchmark
#
#           that runs all registered benchmark executables and writes JSON output:
#
#               <target>_bench.json
#
# Minimal usage in your top-level CMakeLists.txt:
#
#     list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#     include(EnableBenchmarks)
#
#     if(BUILD_BENCHMARKS)
#         target_add_benchmark(example_benchmarks benchmark/example_benchmark.cpp)
#         # ... add more benchmark targets here ...
#         add_benchmark_aggregate_target()
#     endif()
#
# Requirements:
#   - Google Benchmark must be available via CMake's find_package(benchmark CONFIG).
#   - Conan 2 + CMakeDeps will typically provide the `benchmark::benchmark` targets.
#
# --------------------------------------------------------------------------------------------------

# Include the custom message wrappers
include(Logging)

if(NOT DEFINED BUILD_BENCHMARKS)
  option(BUILD_BENCHMARKS "Build benchmark executables (Google Benchmark)" OFF)
endif()

if(NOT BUILD_BENCHMARKS)
  log_status("Google Benchmark: BUILD_BENCHMARKS=OFF")
  return()
endif()

# With Conan 2 + CMakeDeps, benchmark is provided via find_package
log_status("Google Benchmark: BUILD_BENCHMARKS=ON, locating package ...")
find_package(benchmark REQUIRED CONFIG)

if(NOT TARGET benchmark::benchmark)
  log_fatal("EnableBenchmarks: benchmark::benchmark target not found.")
endif()

# Record all benchmark executables in a GLOBAL property
set_property(GLOBAL PROPERTY BENCHMARK_EXECUTABLES "")

# --------------------------------------------------------------------------------------------------
# target_add_benchmark(<name> <sources...>)
#
# Creates a Google Benchmark executable and registers it for aggregation.
#
# Arguments:
#   <name>      : Name of the benchmark executable target to create.
#   <sources...>: One or more source files for the benchmark.
#
# Behavior:
#   - If BUILD_BENCHMARKS=OFF -> returns immediately.
#   - Fails if benchmark::benchmark target is not available.
#   - Links the executable against:
#         benchmark::benchmark
#         benchmark::benchmark_main
#   - If a function target_set_warnings() exists, applies standard warnings.
#   - Appends the target name to the GLOBAL BENCHMARK_EXECUTABLES property.
# --------------------------------------------------------------------------------------------------
function(target_add_benchmark name)
  if(NOT BUILD_BENCHMARKS)
    return()
  endif()

  if(NOT TARGET benchmark::benchmark)
    log_fatal(
      "target_add_benchmark: Google Benchmark is not available (missing benchmark::benchmark target)"
      )
  endif()

  add_executable(${name} ${ARGN})

  target_link_libraries(${name} PRIVATE benchmark::benchmark benchmark::benchmark_main)

  # Optional: enable your standard warnings for benchmark as well
  if(COMMAND target_set_warnings)
    target_set_warnings(${name})
  endif()

  # Remember this benchmark executable
  set_property(GLOBAL APPEND PROPERTY BENCHMARK_EXECUTABLES ${name})

  log_status(" Added benchmark target: ${name}")
endfunction()

# --------------------------------------------------------------------------------------------------
# add_benchmark_aggregate_target()
#
# Creates a "run-benchmark" custom target that runs all registered benchmark
# executables (from BENCHMARK_EXECUTABLES) and writes JSON output files:
#
#   <exec_name>_bench.json
#
# Behavior:
#   - If BUILD_BENCHMARKS=OFF      -> returns immediately.
#   - If no benchmark registered  -> prints STATUS and does nothing.
#   - Otherwise:
#       * Defines target 'run-benchmark'.
#       * For each registered exec:
#           - Runs the executable with:
#                 --benchmark_format=json --benchmark_out=<exec>_bench.json
#           - Emits a small status echo after each run.
# --------------------------------------------------------------------------------------------------
function(add_benchmark_aggregate_target)
  if(NOT BUILD_BENCHMARKS)
    return()
  endif()

  get_property(bench_execs GLOBAL PROPERTY BENCHMARK_EXECUTABLES)
  if(NOT bench_execs)
    log_status(
      "add_benchmark_aggregate_target: no benchmarks registered, not creating run-benchmark"
      )
    return()
  endif()

  add_custom_target(
    run-benchmark
    COMMENT "Running all Google Benchmark executables (JSON output in *_bench.json) "
    VERBATIM
    )

  foreach(exec IN LISTS bench_execs)
    # Write benchmark output to <target>_bench.json next to the binary
    set(out_file " ${exec}_bench.json")

    add_custom_command(
      TARGET run-benchmark
      POST_BUILD
      COMMAND $<TARGET_FILE:${exec}> --benchmark_format=json --benchmark_out=${out_file}
      COMMAND ${CMAKE_COMMAND} -E echo "✔ Finished benchmark: ${exec} -> ${out_file}"
      WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
      VERBATIM
      )
  endforeach()

  log_status("Created aggregate benchmark target: run-benchmark")
endfunction()
