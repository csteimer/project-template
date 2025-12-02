set(BENCHMARK_NAME ${PROJECT_NAME}_benchmark)

set(BENCHMARK_HEADERS example.hpp)

set(BENCHMARK_SOURCES example.cpp)

target_add_benchmark(${BENCHMARK_NAME} ${BENCHMARK_SOURCES} ${BENCHMARK_HEADERS})

target_link_libraries(${BENCHMARK_NAME} PRIVATE ${PROJECT_NAME_EXEC} example.benchmark.cpp)

# Make sure the benchmark can include headers from src/.
target_include_directories(${BENCHMARK_NAME} PRIVATE ${PROJECT_SOURCE_DIR}/src)

add_benchmark_aggregate_target()
