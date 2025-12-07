#include "example.hpp"

namespace benchmark_example {

std::int64_t sum_naive(const std::vector<int>& data) {
    std::int64_t sum = 0;
    for (const int value : data) {
        sum += value;
    }
    return sum;
}

std::int64_t sum_accumulate(const std::vector<int>& data) {
    return std::accumulate(data.begin(), data.end(), std::int64_t{0});
}

std::vector<int> make_test_vector(const std::size_t size) {
    std::vector<int> data;
    data.reserve(size);

    for (std::size_t i = 0; i < size; ++i) {
        // Keep values small and deterministic
        data.push_back(static_cast<int>(i % 100));
    }

    return data;
}

} // namespace benchmark_example
