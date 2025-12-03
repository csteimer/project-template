#include "example.hpp"

#include <benchmark/benchmark.h>

using benchmark_example::make_test_vector;
using benchmark_example::sum_accumulate;
using benchmark_example::sum_naive;

static void BM_SumNaive(benchmark::State& state) {
    const std::size_t size = static_cast<std::size_t>(state.range(0));
    const auto data        = make_test_vector(size);

    for (auto _ : state) {
        auto result = sum_naive(data);
        benchmark::DoNotOptimize(result);
        benchmark::ClobberMemory();
    }

    state.SetItemsProcessed(static_cast<int64_t>(state.iterations()) * static_cast<int64_t>(size));
}

static void BM_SumAccumulate(benchmark::State& state) {
    const std::size_t size = static_cast<std::size_t>(state.range(0));
    const auto data        = make_test_vector(size);

    for (auto _ : state) {
        auto result = sum_accumulate(data);
        benchmark::DoNotOptimize(result);
        benchmark::ClobberMemory();
    }

    state.SetItemsProcessed(static_cast<int64_t>(state.iterations()) * static_cast<int64_t>(size));
}

BENCHMARK(BM_SumNaive)->Arg(1 << 10)->Arg(1 << 15)->Arg(1 << 20);

BENCHMARK(BM_SumAccumulate)->Arg(1 << 10)->Arg(1 << 15)->Arg(1 << 20);

BENCHMARK_MAIN();
