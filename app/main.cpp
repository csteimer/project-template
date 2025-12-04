#include "../src/utils/assertions.hpp"

#include <cstdlib>
#include <string>

using project_template::utils::log::Level;
using project_template::utils::log::Log;
using project_template::utils::log::Mode;

int main() {
    // ------------------------------------------------------------
    // 1. Logger initialization
    // ------------------------------------------------------------
    Log::init(Level::Debug, Mode::Async, "[%T.%f] [%^%l%$] %v");

    LOG_INFO("Project-template demo starting up");
    LOG_DEBUG("Debug log example with value={}", 123);
    LOG_TRACE("Trace example (may be hidden if level > Trace)");

    // ------------------------------------------------------------
    // 2. Demonstrate conditional warnings
    // ------------------------------------------------------------
    const bool feature_enabled = true;
    LOG_WARN_IF(feature_enabled, "Feature '{}' is enabled (demo warning)", "experimental-mode");

    // ------------------------------------------------------------
    // 3. Demonstrate error + critical logs
    // ------------------------------------------------------------
    LOG_ERROR("Something went wrong, but this is just a demo");
    LOG_CRITICAL("Critical condition encountered — continuing demo");

    // ------------------------------------------------------------
    // 4. Demonstrate assertions
    // ------------------------------------------------------------
    int x = 10;
    int y = 0;

    LOG_INFO("Testing ASSERT with x={}, y={}", x, y);

    // Basic assert
    ASSERT(x == 10);

    // This assert would normally fail; commented out for demonstration:
    // ASSERT(y != 0);

    // Custom assertion with message (will abort)
    // Uncomment to test:
    // ASSERT_MSG(y != 0, "Invalid divisor: y={} must not be zero!", y);

    // ------------------------------------------------------------
    // 5. Normal exit
    // ------------------------------------------------------------
    LOG_INFO("Demo completed. Shutting down cleanly...");
    Log::flush();
    Log::reset_logger();

    return EXIT_SUCCESS;
}
