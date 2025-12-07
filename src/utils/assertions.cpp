#include "assertions.hpp"

#include "logger.hpp"

#include <spdlog/spdlog.h>

namespace project_template::utils::assert {

[[noreturn]] void handle_assertion_failure(std::string_view cond, std::string_view file, int line,
                                           std::string_view msg) {
    if (msg.empty()) {
        LOG_CRITICAL("Assertion failed: '{}' at {}:{}", cond, file, line);
    } else {
        LOG_CRITICAL("Assertion failed: '{}' at {}:{} -- {}", cond, file, line, msg);
    }

    ::project_template::utils::log::Log::instance()->flush();
    spdlog::shutdown();
    std::abort();
}

} // namespace project_template::utils::assert
