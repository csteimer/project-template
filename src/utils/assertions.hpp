#pragma once

#include "logger.hpp"

#include <cstdlib>
#include <string_view>

#ifdef NDEBUG

#define ASSERT(cond) ((void) 0)
#define ASSERT_MSG(cond, fmt_str, ...) ((void) 0)

#else

// Use spdlog's bundled fmt to avoid requiring an external fmt include path
#include <spdlog/fmt/fmt.h>
#include <spdlog/spdlog.h> // for shutdown()

namespace project_template::utils::assert {

/**
 * @brief Internal helper: logs a critical assertion failure, flushes logs, and aborts.
 */
inline void handle_assertion_failure(std::string_view cond, std::string_view file, int line,
                                     std::string_view msg = {}) {
    if (msg.empty()) {
        LOG_CRITICAL("Assertion failed: '{}' at {}:{}", cond, file, line);
    } else {
        LOG_CRITICAL("Assertion failed: '{}' at {}:{} -- {}", cond, file, line, msg);
    }
    // Ensure all log messages are flushed before aborting
    ::project_template::utils::log::Log::instance()->flush();
    spdlog::shutdown();
    std::abort();
}

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
