#pragma once

#include <spdlog/async.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/spdlog.h>

#include <cstring>
#include <memory>
#include <string>

namespace project_template::utils::log {
/**
 * @brief Logging severity levels.
 *
 * These correspond to spdlog's log levels and control which messages will
 * be emitted. Higher levels filter out more verbose messages.
 *
 * Common usage:
 *  - Trace: extremely detailed flow information
 *  - Debug: development diagnostics
 *  - Info: high-level operational messages
 *  - Warn: unexpected but non-fatal situations
 *  - Error: recoverable errors
 *  - Critical: unrecoverable failures
 *  - Off: disable logging entirely
 */
enum class Level : std::uint8_t { Trace, Debug, Info, Warn, Error, Critical, Off };

/**
 * @brief Logging execution mode.
 *
 * - **Sync**
 *   Logging is performed on the caller thread. Every log call immediately
 *   writes to all sinks (console, files, etc.). This guarantees that messages
 *   are persisted when the call returns, which is ideal for:
 *     * unit tests
 *     * debugging crashes
 *     * short-running tools and scripts
 *     * deterministic logging requirements
 *
 *   The downside is that slow sinks (I/O, terminal stalls) may block the caller.
 *
 * - **Async**
 *   Logging calls enqueue the record on a lock-free queue and return
 *   immediately. A background worker thread performs the actual I/O.
 *   This reduces latency and improves throughput, especially in applications
 *   that produce many logs or perform frequent I/O.
 *
 *   Async mode is suitable for:
 *     * long-running applications
 *     * services
 *     * CLI tools where performance matters
 *
 *   Because writes are deferred, applications should flush or shut down the
 *   logger cleanly to avoid losing queued messages at shutdown.
 *
 * Ordering notes:
 *  - Per-thread message order is preserved
 *  - Cross-thread interleaving may differ in async mode
 */
enum class Mode : std::uint8_t { Sync, Async };

/**
 * @brief Centralized logging facility for the project.
 *
 * This class wraps a shared `spdlog::logger` instance to ensure all modules
 * within the project use consistent logging behavior, formatting, levels, and
 * sink configuration.
 *
 * Key responsibilities:
 *  - Configure a global logger (pattern, level, mode)
 *  - Provide thread-safe access to the logger instance
 *  - Manage sync/async execution modes
 *  - Handle flush and shutdown operations
 *  - Provide a unified entry point for the project’s logging macros
 *
 * Behavior:
 *  - Calling `init()` multiple times reconfigures the existing logger.
 *  - The logger pattern and level are reapplied for all sinks via `instance()`.
 *  - In async mode, `reset_logger()` shuts down the async thread pool.
 *
 * Recommended use:
 *  - Call `Log::init()` once at program startup.
 *  - For libraries or tests, calling `init()` defensively is fine; it simply
 *    reuses and reconfigures the static logger.
 */
class Log {
  public:
    Log() = delete;

    /**
     * @brief Initialize or reconfigure the shared logger.
     *
     * Calling this method multiple times is allowed. The existing logger
     * instance is reused and reconfigured in place.
     *
     * @param level
     *        Minimum severity level to emit (Trace → Critical).
     *
     * @param mode
     *        - Mode::Sync: log on the caller thread
     *        - Mode::Async: enqueue and return immediately
     *
     * @param pattern
     *        spdlog-compatible formatting pattern shared by all sinks.
     *        The default includes timestamp, colored level, and the message.
     *
     * Notes:
     *  - In async mode, call `Log::reset_logger()` or `spdlog::shutdown()` at
     *    shutdown to ensure all queued messages are flushed.
     *  - High severity logs (`error`, `critical`) automatically trigger flushes.
     */
    static void init(Level level = Level::Info, Mode mode = Mode::Async,
                     const std::string& pattern = "[%T.%f] [%^%l%$] %v");

    /// @brief Retrieve (and lazily initialize) the shared logger.
    static std::shared_ptr<spdlog::logger>& instance();

    /// @brief Shutdown and reset the logger (including async thread pool).
    static void reset_logger();

    /// @brief Flush all sinks immediately.
    static void flush() {
        if (spd_logger_) spd_logger_->flush();
    }

    /// @name Logging convenience functions
    /// These forward directly to the shared spdlog logger.
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
    static std::string pattern_; ///< last applied pattern
    static Mode mode_;           ///< last selected mode

    /// @brief Convert Log::Level to spdlog's native level enum.
    static spdlog::level::level_enum to_spdlog_level(Level level);
};

/**
 * @name File-and-line aware logging macros
 *
 * These macros automatically prepend `[filename@line]` to each message,
 * providing valuable context during debugging. They expand to lightweight
 * wrappers around the Log class.
 *
 * Example:
 *   LOG_INFO("Loaded configuration '{}'", path);
 *
 * Output:
 *   [config.cpp@line:42] Loaded configuration '/etc/app/config.yaml'
 *
 * This format makes it easier to trace log origins across large codebases.
 */
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
