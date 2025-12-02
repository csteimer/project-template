# Enables Google Benchmark support when BUILD_BENCHMARKS=ON.
# Provides:
#   target_add_benchmark(<name> <sources...>)
#   add_benchmark_aggregate_target() -> creates "run-benchmarks" target
#
# Typical usage in your top-level CMakeLists.txt:
#
#   list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
#   include(EnableBenchmarks)
#
#   if(BUILD_BENCHMARKS)
#       target_add_benchmark(example_benchmarks benchmarks/example_benchmark.cpp)
#       # ... add more ...
#       add_benchmark_aggregate_target()
#   endif()
#

if(NOT DEFINED BUILD_BENCHMARKS)
  option(BUILD_BENCHMARKS "Build benchmark executables (Google Benchmark)" OFF)
endif()

if(NOT BUILD_BENCHMARKS)
  message(STATUS "Google Benchmark: BUILD_BENCHMARKS=OFF")
  return()
endif()

# With Conan 2 + CMakeDeps, benchmark is provided via find_package
message(STATUS "Google Benchmark: BUILD_BENCHMARKS=ON, locating package ...")
find_package(benchmark REQUIRED CONFIG)

if(NOT TARGET benchmark::benchmark)
  message(FATAL_ERROR "EnableBenchmarks: benchmark::benchmark target not found.")
endif()

# Record all benchmark executables in a GLOBAL property
set_property(GLOBAL PROPERTY BENCHMARK_EXECUTABLES "")

function(target_add_benchmark name)
  if(NOT BUILD_BENCHMARKS)
    return()
  endif()

  if(NOT TARGET benchmark::benchmark)
    message(
      FATAL_ERROR "target_add_benchmark: Google Benchmark is not available "
                  "(missing benchmark::benchmark target)"
      )
  endif()

  add_executable(${name} ${ARGN})

  target_link_libraries(${name} PRIVATE benchmark::benchmark benchmark::benchmark_main)

  # Optional: enable your standard warnings for benchmarks as well
  if(COMMAND target_set_warnings)
    target_set_warnings(${name})
  endif()

  # Remember this benchmark executable
  set_property(GLOBAL APPEND PROPERTY BENCHMARK_EXECUTABLES ${name})

  message(STATUS "Added benchmark target: ${name}")
endfunction()

# This creates a "run-benchmarks" target that runs all registered benchmark executables.
# Each executable is run with:
#   --benchmark_format=json --benchmark_out=<name>_bench.json
# in the current binary dir.
function(add_benchmark_aggregate_target)
  if(NOT BUILD_BENCHMARKS)
    return()
  endif()

  get_property(bench_execs GLOBAL PROPERTY BENCHMARK_EXECUTABLES)
  if(NOT bench_execs)
    message(
      STATUS "add_benchmark_aggregate_target: no benchmarks registered, not creating run-benchmarks"
      )
    return()
  endif()

  add_custom_target(
    run-benchmarks
    COMMENT "Running all Google Benchmark executables (JSON output in *_bench.json)"
    VERBATIM
    )

  foreach(exec IN LISTS bench_execs)
    # Write benchmark output to <target>_bench.json next to the binary
    set(out_file "${exec}_bench.json")

    add_custom_command(
      TARGET run-benchmarks
      POST_BUILD
      COMMAND $<TARGET_FILE:${exec}> --benchmark_format=json --benchmark_out=${out_file}
      COMMAND ${CMAKE_COMMAND} -E echo "✔ Finished benchmark: ${exec} -> ${out_file}"
      WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
      VERBATIM
      )
  endforeach()

  message(STATUS "Created aggregate benchmark target: run-benchmarks")
endfunction()
