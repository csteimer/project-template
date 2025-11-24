#pragma once

#include <spdlog/async.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/spdlog.h>

#include <cstring>
#include <memory>
#include <string>

namespace project_template::utils::log {

/**
 * @brief Logging severity levels.
 */
enum class Level : std::uint8_t { Trace, Debug, Info, Warn, Error, Critical, Off };

/**
 * @brief Sync vs Async mode.
 *
 * - **Sync** logs on the *caller thread*. A log call writes to all sinks immediately.
 *   This guarantees that a message is on disk/console when the call returns, but it can
 *   **block the game loop** if a sink is slow (e.g., rotating file I/O, terminal stalls).
 *
 * - **Async** pushes log records into a lock–free queue processed by a **dedicated worker
 *   thread**. The caller returns quickly (low latency impact) and the background thread
 *   performs the actual sink I/O, increasing throughput. However, messages are written
 *   **eventually**, not immediately. On process crash or abrupt exit, some queued messages
 *   might be lost if not flushed.
 *
 * Practical guidance:
 * - Use **Async** for the running game / real-time systems to keep the frame loop smooth.
 * - Use **Sync** in unit tests, small tools, or during tricky crash diagnostics where you
 *   need logs persisted at the exact call site.
 *
 * Ordering & backpressure:
 * - Per-thread ordering is preserved by spdlog, but cross-thread interleaving can differ
 *   in **Async**.
 * - If the async queue overflows, spdlog can block or drop messages depending on its
 *   overflow policy (your build can choose this when initializing the thread pool).
 *
 * Flushing:
 * - This wrapper explicitly flushes on `error()` and `critical()` to minimize loss in both
 *   modes. Call `Log::flush()` or `Log::reset_logger()` (which shuts down async pools) at
 *   clean shutdowns to ensure all messages are written.
 */
enum class Mode : std::uint8_t { Sync, Async };

/**
 * @brief A thin wrapper around spdlog to centralize logging setup.
 *
 * Calling init() again will re‑configure the existing logger in place
 * (pattern, level), and every call to instance() will re‑apply that pattern
 * to *all* sinks (even if they were pushed afterward).
 */
class Log {
  public:
    Log() = delete;

    /**
     * @brief Initialize or reconfigure the shared logger.
     *
     * Calling `init()` multiple times reuses the same underlying logger and reapplies
     * the pattern/level to all current sinks (and to sinks added later via `instance()`).
     *
     * @param level   Minimum log level.
     * @param mode    Logging mode:
     *                - `Mode::Sync`: caller thread performs sink I/O (safer for tests,
     *                  can block the frame loop).
     *                - `Mode::Async`: enqueue and return; a worker thread performs sink I/O
     *                  (preferred for real-time gameplay; flush on shutdown to avoid loss).
     * @param pattern `fmt` pattern applied to *all* sinks.
     *
     * @note In Async mode, make sure your process performs a clean shutdown (call
     *       `Log::reset_logger()` or `spdlog::shutdown()`) so the queue drains fully.
     *       This wrapper also flushes on `error()`/`critical()` by default.
     */
    static void init(Level level = Level::Info, Mode mode = Mode::Async,
                     const std::string& pattern = "[%T.%f] [%^%l%$] %v");

    /// Get (and lazily init) the underlying spdlog::logger
    static std::shared_ptr<spdlog::logger>& instance();

    /// Fully shutdown / reset logger (and async pool)
    static void reset_logger();

    /// Force‑flush all sinks immediately
    static void flush() {
        if (spd_logger_) spd_logger_->flush();
    }

    /// @name Logging functions (forward to the shared logger)
    /// @{
    template <typename... Args> static void trace(spdlog::fmt_lib::format_string<Args...> fmt_str, Args&&... args) {
        instance()->trace(fmt_str, std::forward<Args>(args)...);
    }
    template <typename... Args> static void debug(spdlog::fmt_lib::format_string<Args...> fmt_str, Args&&... args) {
        instance()->debug(fmt_str, std::forward<Args>(args)...);
    }
    template <typename... Args> static void info(spdlog::fmt_lib::format_string<Args...> fmt_str, Args&&... args) {
        instance()->info(fmt_str, std::forward<Args>(args)...);
    }
    template <typename... Args> static void warn(spdlog::fmt_lib::format_string<Args...> fmt_str, Args&&... args) {
        instance()->warn(fmt_str, std::forward<Args>(args)...);
    }
    template <typename... Args> static void error(spdlog::fmt_lib::format_string<Args...> fmt_str, Args&&... args) {
        instance()->error(fmt_str, std::forward<Args>(args)...);
        instance()->flush();
    }
    template <typename... Args> static void critical(spdlog::fmt_lib::format_string<Args...> fmt_str, Args&&... args) {
        instance()->critical(fmt_str, std::forward<Args>(args)...);
        instance()->flush();
    }
    /// @}

  private:
    static std::shared_ptr<spdlog::logger> spd_logger_;
    static std::string pattern_; // store last init‑pattern
    static Mode mode_;           // last init mode

    static spdlog::level::level_enum to_spdlog_level(Level level);
};

/// @name Function‑aware logging macros (unchanged)
/// @{
#define PROJECT_TEMPLATE_FILENAME (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)
#define LOG_TRACE(fmt, ...)                                                                                            \
    ::project_template::utils::log::Log::trace("[{}@line:{}] " fmt, PROJECT_TEMPLATE_FILENAME, __LINE__, ##__VA_ARGS__)
#define LOG_DEBUG(fmt, ...)                                                                                            \
    ::project_template::utils::log::Log::debug("[{}@line:{}] " fmt, PROJECT_TEMPLATE_FILENAME, __LINE__, ##__VA_ARGS__)
#define LOG_INFO(fmt, ...)                                                                                             \
    ::project_template::utils::log::Log::info("[{}@line:{}] " fmt, PROJECT_TEMPLATE_FILENAME, __LINE__, ##__VA_ARGS__)
#define LOG_WARN(fmt, ...)                                                                                             \
    ::project_template::utils::log::Log::warn("[{}@line:{}] " fmt, PROJECT_TEMPLATE_FILENAME, __LINE__, ##__VA_ARGS__)
#define LOG_ERROR(fmt, ...)                                                                                            \
    ::project_template::utils::log::Log::error("[{}@line:{}] " fmt, PROJECT_TEMPLATE_FILENAME, __LINE__, ##__VA_ARGS__)
#define LOG_CRITICAL(fmt, ...)                                                                                         \
    ::project_template::utils::log::Log::critical("[{}@line:{}] " fmt, PROJECT_TEMPLATE_FILENAME, __LINE__,            \
                                                  ##__VA_ARGS__)
#define LOG_WARN_IF(cond, fmt, ...)                                                                                    \
    do {                                                                                                               \
        if (cond)                                                                                                      \
            ::project_template::utils::log::Log::warn("[{}@line:{}] " fmt, PROJECT_TEMPLATE_FILENAME, __LINE__,        \
                                                      ##__VA_ARGS__);                                                  \
    } while (0)
/// @}
} // namespace project_template::utils::log
