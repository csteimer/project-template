set(BENCHMARKS_NAME ${PROJECT_NAME}_benchmarks)

set(BENCHMARK_HEADERS example.hpp)

set(BENCHMARK_SOURCES example.cpp example.benchmark.cpp)

target_add_benchmark(${BENCHMARKS_NAME} ${BENCHMARK_SOURCES} ${BENCHMARK_HEADERS})

target_link_libraries(${BENCHMARKS_NAME} PRIVATE ${PROJECT_NAME})

# Make sure the benchmark can include headers from src/.
target_include_directories(${BENCHMARKS_NAME} PRIVATE ${PROJECT_SOURCE_DIR}/src)

add_benchmark_aggregate_target()
