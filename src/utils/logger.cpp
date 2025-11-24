#include "logger.hpp"

namespace project_template::utils::log {

// definitions of our statics
std::shared_ptr<spdlog::logger> Log::spd_logger_ = nullptr;
std::string Log::pattern_                        = "";
Mode Log::mode_                                  = Mode::Sync;

void Log::init(const Level level, const Mode mode, const std::string& pattern) {
    // remember the pattern for everyone
    pattern_ = pattern;

    // decide if we need a full rebuild (no logger yet, or mode switched)
    if (const bool need_rebuild = !spd_logger_ || (mode != mode_); !need_rebuild) {
        // same mode → just reconfigure existing sinks & level
        for (const auto& s : spd_logger_->sinks())
            s->set_pattern(pattern_);
        const auto lvl = to_spdlog_level(level);
        spd_logger_->set_level(lvl);
        spd_logger_->flush_on(spdlog::level::err);
        return;
    }
    // mode changed (or first time) → full teardown + rebuild
    mode_ = mode;
    spdlog::shutdown();
    spd_logger_.reset();

    // make two sinks
    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console_sink->set_pattern(pattern_);

    auto file_sink =
        std::make_shared<spdlog::sinks::rotating_file_sink_mt>("logs/project_template.log", 1024 * 1024 * 5, 3);
    file_sink->set_pattern(pattern_);

    // pick sync vs async
    if (mode == Mode::Async) {
        spdlog::init_thread_pool(8192, 1);
        spd_logger_ =
            std::make_shared<spdlog::async_logger>("project_template", spdlog::sinks_init_list{console_sink, file_sink},
                                                   spdlog::thread_pool(), spdlog::async_overflow_policy::block);
    } else {
        spd_logger_ =
            std::make_shared<spdlog::logger>("project_template", spdlog::sinks_init_list{console_sink, file_sink});
        spdlog::register_logger(spd_logger_);
    }

    // apply level + always flush on errors/criticals
    const auto lvl = to_spdlog_level(level);
    spd_logger_->set_level(lvl);
    spd_logger_->flush_on(spdlog::level::err);
}

std::shared_ptr<spdlog::logger>& Log::instance() {
    if (!spd_logger_) {
        init(); // Info, Async, default‑pattern
    }
    // **re‑apply** the last init() pattern on every sink,
    // so sinks added later (like your oss_sink_) pick it up:
    for (const auto& s : spd_logger_->sinks()) {
        s->set_pattern(pattern_);
    }
    return spd_logger_;
}

void Log::reset_logger() {
    spdlog::shutdown();
    spd_logger_.reset();
    pattern_.clear();
    mode_ = Mode::Sync;
}

spdlog::level::level_enum Log::to_spdlog_level(const Level level) {
    switch (level) {
        case Level::Trace:
            return spdlog::level::trace;
        case Level::Debug:
            return spdlog::level::debug;
        case Level::Info:
            return spdlog::level::info;
        case Level::Warn:
            return spdlog::level::warn;
        case Level::Error:
            return spdlog::level::err;
        case Level::Critical:
            return spdlog::level::critical;
        case Level::Off:
            return spdlog::level::off;
    }
    return spdlog::level::info; // fallback
}

} // namespace project_template::utils::log
