#pragma once

#include <cstdint>
#include <numeric> // std::accumulate
#include <vector>

namespace benchmark_example {

/**
 * @brief Compute the sum of all elements using a simple for-loop.
 */
std::int64_t sum_naive(const std::vector<int>& data);

/**
 * @brief Compute the sum of all elements using std::accumulate.
 */
std::int64_t sum_accumulate(const std::vector<int>& data);

/**
 * @brief Create a test vector of the given size with deterministic content.
 *
 * Fills the vector with values 0, 1, 2, ..., size-1 (mod 100).
 */
std::vector<int> make_test_vector(std::size_t size);

} // namespace benchmark_example
