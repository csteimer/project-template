/**
 * @file logger.unit_tests.cpp
 * @brief Unit tests for project_template::utils::log::Log and related macros.
 *
 */

#include "logger.hpp"

#include <gtest/gtest.h>
#include <spdlog/sinks/ostream_sink.h>

#include <sstream>

using namespace project_template::utils::log;

/** @defgroup LoggerTests Logger tests
 *  @brief Tests for the project_template::utils::log::Log class and macros.
 *  @{
 */

// --------------------------
// Test Fixture Setup
// --------------------------
/**
 * @brief Test fixture that sets up a fresh, synchronous logger at TRACE level
 *        and routes output into a std::ostringstream sink for inspection.
 */
class LoggerTest : public ::testing::Test {
  protected:
    /** Shared logger instance under test. */
    std::shared_ptr<spdlog::logger> logger_;

    /** OStream sink capturing formatted log messages. */
    std::shared_ptr<spdlog::sinks::ostream_sink_mt> oss_sink_;

    /** Backing stringstream for oss_sink_. */
    std::ostringstream oss_;

    /**
     * @brief Set up resets and initializes the logger, then installs
     *        an ostream sink to intercept output.
     */
    void SetUp() override {
        Log::reset_logger();
        Log::init(Level::Trace, Mode::Sync, "%v");
        logger_ = Log::instance();

        // Replace all sinks with our test sink
        logger_->sinks().clear();
        oss_.str("");
        oss_.clear();
        oss_sink_ = std::make_shared<spdlog::sinks::ostream_sink_mt>(oss_);
        logger_->sinks().push_back(oss_sink_);

        // Capture every level and flush on each message
        logger_->set_level(spdlog::level::trace);
        logger_->flush_on(spdlog::level::trace);
    }

    /**
     * @brief Splits the captured stream contents into non-empty lines.
     * @return Vector of log messages.
     */
    std::vector<std::string> lines() const {
        std::vector<std::string> out;
        std::istringstream iss(oss_.str());
        std::string line;
        while (std::getline(iss, line)) {
            if (!line.empty()) out.push_back(line);
        }
        return out;
    }
};

// --------------------------
// BufferedSink: Custom sink for flush behavior tests
// --------------------------
#include <spdlog/sinks/base_sink.h>

#include <mutex>

/**
 * @brief BufferedSink buffers all formatted messages in memory
 *        and only moves them to 'output' when flush() is called.
 */
class BufferedSink final : public spdlog::sinks::base_sink<std::mutex> {
  public:
    /** Holds messages until flush() is invoked. */
    std::vector<std::string> buffer;

    /** Holds messages after a flush(). */
    std::vector<std::string> output;

  protected:
    void sink_it_(const spdlog::details::log_msg& msg) override {
        buffer.push_back(fmt::to_string(msg.payload));
    }

    void flush_() override {
        output.insert(output.end(), buffer.begin(), buffer.end());
        buffer.clear();
    }
};

// --------------------------
// Test Cases
// --------------------------

/**
 * @brief Verifies that each Level enum value maps correctly to spdlog levels.
 */
TEST_F(LoggerTest, LevelMapping) {
    struct Case {
        Level lvl;
        spdlog::level::level_enum want;
    };
    std::vector<Case> cases = {
        {.lvl = Level::Trace, .want = spdlog::level::trace}, {.lvl = Level::Debug, .want = spdlog::level::debug},
        {.lvl = Level::Info, .want = spdlog::level::info},   {.lvl = Level::Warn, .want = spdlog::level::warn},
        {.lvl = Level::Error, .want = spdlog::level::err},   {.lvl = Level::Critical, .want = spdlog::level::critical},
        {.lvl = Level::Off, .want = spdlog::level::off},
    };

    for (auto [lvl, want] : cases) {
        Log::reset_logger();
        Log::init(lvl, Mode::Sync, "%v");
        EXPECT_EQ(Log::instance()->level(), want) << "Level " << static_cast<int>(lvl) << " mapped incorrectly";
    }
}

/**
 * @brief Ensures lazy initialization defaults to the INFO level.
 */
TEST_F(LoggerTest, LazyInitDefaultsToInfo) {
    Log::reset_logger();
    const auto inst = Log::instance();
    EXPECT_EQ(inst->level(), spdlog::level::info);
}

/**
 * @brief Tests all 6 logging functions produce the correct messages in order.
 */
TEST_F(LoggerTest, BasicLoggingFunctions) {
    Log::trace("T{}", 1);
    Log::debug("D{}", 2);
    Log::info("I{}", 3);
    Log::warn("W{}", 4);
    Log::error("E{}", 5);
    Log::critical("C{}", 6);

    const auto l = lines();
    ASSERT_EQ(l.size(), 6u);
    EXPECT_EQ(l[0], "T1");
    EXPECT_EQ(l[1], "D2");
    EXPECT_EQ(l[2], "I3");
    EXPECT_EQ(l[3], "W4");
    EXPECT_EQ(l[4], "E5");
    EXPECT_EQ(l[5], "C6");
}

/**
 * @brief Verifies the LOG_WARN_IF macro only logs when the condition is true,
 *        and includes filename@line information.
 */
TEST_F(LoggerTest, MacrosIncludeFilenameAndLine) {
    oss_.str("");
    oss_.clear();
    LOG_WARN_IF(false, "skip {}", 42);
    EXPECT_TRUE(lines().empty());

    LOG_WARN_IF(true, "got {}", 99);
    const auto l = lines();
    ASSERT_EQ(l.size(), 1u);
    EXPECT_NE(l[0].find("got 99"), std::string::npos);
    EXPECT_NE(l[0].find("logger_tests.cpp@line:"), std::string::npos);
}

/**
 * @brief Re-initializing with a new pattern should override the old pattern.
 */
TEST_F(LoggerTest, ReinitAppliesNewPattern) {
    // Initial pattern without prefix
    Log::init(Level::Info, Mode::Sync, "%v");
    logger_->sinks().clear();
    logger_->sinks().push_back(oss_sink_);
    Log::info("foo");
    EXPECT_EQ(lines().back(), "foo");

    // Reset and apply a prefix pattern
    oss_.str("\"");
    oss_.clear();
    Log::reset_logger();
    Log::init(Level::Info, Mode::Sync, "PRE:%v");
    logger_ = Log::instance();
    logger_->sinks().clear();
    logger_->sinks().push_back(oss_sink_);
    logger_->set_level(spdlog::level::info);
    logger_->flush_on(spdlog::level::info);
    Log::info("bar");
    EXPECT_EQ(lines().back(), "PRE:bar");
}

/**
 * @brief Verifies messages below the set level are filtered out correctly.
 */
TEST_F(LoggerTest, LogsRespectLevelFilter) {
    Log::reset_logger();
    Log::init(Level::Warn, Mode::Sync, "%v");
    const auto lgr = Log::instance();
    lgr->sinks().clear();
    lgr->sinks().push_back(oss_sink_);
    lgr->set_level(spdlog::level::warn);
    lgr->flush_on(spdlog::level::warn);

    Log::trace("T");
    Log::debug("D");
    Log::info("I");
    Log::warn("W");
    Log::error("E");
    const auto out = lines();
    ASSERT_EQ(out.size(), 2u);
    EXPECT_EQ(out[0], "W");
    EXPECT_EQ(out[1], "E");
}

/**
 * @brief Level::Off should disable all logging output.
 */
TEST_F(LoggerTest, OffLevelDisablesAllLogging) {
    Log::reset_logger();
    Log::init(Level::Off, Mode::Sync, "%v");
    const auto lgr = Log::instance();
    lgr->sinks().clear();
    lgr->sinks().push_back(oss_sink_);
    lgr->set_level(spdlog::level::off);
    lgr->flush_on(spdlog::level::off);

    Log::trace("T");
    Log::debug("D");
    Log::info("I");
    Log::warn("W");
    Log::error("E");
    Log::critical("C");
    EXPECT_TRUE(lines().empty());
}

/**
 * @brief Ensures init() is idempotent: repeated init retains the same logger instance.
 */
TEST_F(LoggerTest, InitIsIdempotent) {
    Log::reset_logger();
    Log::init(Level::Info, Mode::Sync, "%v");
    auto* const first = Log::instance().get();
    Log::init(Level::Debug, Mode::Sync, "P:%v");
    auto* const second = Log::instance().get();
    EXPECT_EQ(first, second);
}

/**
 * @brief Pattern propagation to sinks added after initialization.
 */
TEST_F(LoggerTest, PatternPropagatesToNewSink) {
    Log::reset_logger();
    Log::init(Level::Info, Mode::Sync, "[%l] %v");
    const auto lgr = Log::instance();
    lgr->sinks().clear();

    lgr->sinks().push_back(oss_sink_);
    Log::info("foo");
    EXPECT_EQ(lines().back(), "[info] foo");

    std::ostringstream oss2;
    const auto sink2 = std::make_shared<spdlog::sinks::ostream_sink_mt>(oss2);
    lgr->sinks().push_back(sink2);
    Log::info("bar");
    const auto out1 = lines().back();
    std::string line2;
    std::getline(std::istringstream(oss2.str()), line2);
    EXPECT_EQ(out1, "[info] bar");
    EXPECT_EQ(line2, "[info] bar");
}

/**
 * @brief Verifies error() triggers a flush on buffered sinks, while info() does not.
 */
TEST_F(LoggerTest, ErrorAndCriticalOnlyFlushSinkOnError) {
    Log::reset_logger();
    Log::init(Level::Trace, Mode::Sync, "%v");
    const auto lgr = Log::instance();
    lgr->sinks().clear();

    const auto buf_sink = std::make_shared<BufferedSink>();
    lgr->sinks().push_back(buf_sink);
    lgr->flush_on(spdlog::level::off);

    Log::info("nope");
    EXPECT_EQ(buf_sink->buffer.size(), 1u);
    EXPECT_TRUE(buf_sink->output.empty());

    Log::error("boom");
    ASSERT_EQ(buf_sink->buffer.size(), 0u);
    ASSERT_EQ(buf_sink->output.size(), 2u);
    EXPECT_EQ(buf_sink->output[0], "nope");
    EXPECT_EQ(buf_sink->output[1], "boom");
}

/**
 * @brief Default init() should lazy-initialize at INFO level (async by default).
 */
TEST_F(LoggerTest, DefaultInitUsesInfoAndAsync) {
    Log::reset_logger();
    const auto l = Log::instance();
    EXPECT_EQ(l->level(), spdlog::level::info);
    // Could inspect async nature via dynamic_cast<spdlog::async_logger*>
}

/**
 * @brief Re-initializing from Async to Sync should replace the async logger.
 */
TEST_F(LoggerTest, CanReinitModeSyncAfterAsync) {
    Log::reset_logger();
    Log::init(Level::Info, Mode::Async, "%v");
    auto* const async_ptr = dynamic_cast<spdlog::async_logger*>(Log::instance().get());
    ASSERT_NE(async_ptr, nullptr);

    Log::init(Level::Info, Mode::Sync, "%v");
    auto* const sync_ptr = dynamic_cast<spdlog::async_logger*>(Log::instance().get());
    EXPECT_EQ(sync_ptr, nullptr);
}

/**
 * @brief Level::Off should silence an ostream sink.
 */
TEST_F(LoggerTest, OffLevelSilencesOstreamSink) {
    Log::reset_logger();
    Log::init(Level::Off, Mode::Sync, "%v");
    const auto l = Log::instance();
    l->sinks().clear();
    l->sinks().push_back(oss_sink_);
    Log::warn("won't show");
    EXPECT_TRUE(lines().empty());
}
