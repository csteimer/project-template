#pragma once

#include <cstdlib>
#include <cstring> // for strrchr
#include <string_view>

#ifdef NDEBUG

#define ASSERT(cond) ((void) 0)
#define ASSERT_MSG(cond, fmt_str, ...) ((void) 0)

#else

// Use spdlog's bundled fmt to avoid requiring an external fmt include path
#include <spdlog/fmt/fmt.h>

namespace project_template::utils::assert {

/**
 * @brief Internal helper: logs a critical assertion failure, flushes logs, and aborts.
 *
 * Implemented in a .cpp file that can include logger.hpp.
 */
[[noreturn]] void handle_assertion_failure(std::string_view cond, std::string_view file, int line,
                                           std::string_view msg = {});
} // namespace project_template::utils::assert

#define PROJECT_TEMPLATE_FILENAME (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)

/**
 * @brief Simple assertion: if `cond` is false, logs and aborts.
 */
#define ASSERT(cond)                                                                                                   \
    do {                                                                                                               \
        if (!(cond)) {                                                                                                 \
            ::project_template::utils::assert::handle_assertion_failure(#cond, PROJECT_TEMPLATE_FILENAME, __LINE__);   \
        }                                                                                                              \
    } while (0)

/**
 * @brief Assertion with a custom formatted message.
 */
#define ASSERT_MSG(cond, fmt_str, ...)                                                                                 \
    do {                                                                                                               \
        if (!(cond)) {                                                                                                 \
            ::project_template::utils::assert::handle_assertion_failure(#cond, PROJECT_TEMPLATE_FILENAME, __LINE__,    \
                                                                        fmt::format(fmt_str, ##__VA_ARGS__));          \
        }                                                                                                              \
    } while (0)

#endif // NDEBUG
