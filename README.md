# Setup

```bash

./setup_dev_env.sh
source .venv/bin/activate
conan profile detect
```

# CMake Presets and Conan Profiles

| CMake Preset | CMAKE_BUILD_TYPE | Sanitizers / Options          | binaryDir       | Suggested Conan Host Profile |
|--------------|-------------------|------------------------------|-----------------|------------------------------|
| debug        | Debug             | none                         | build/debug     | gcc-debug                    |
| release      | Release           | none                         | build/release   | gcc-release                  |
| asan         | Debug             | ASAN + UBSAN                 | build/asan      | gcc-debug-asan               |
| tsan         | Debug             | TSAN                         | build/tsan      | gcc-debug-tsan               |
| coverage     | Debug             | coverage instrumentation     | build/coverage  | gcc-debug-coverage           |
| benchmark    | Release           | benchmarks only              | build/benchmark     | gcc-release-benchmark        |
| ci-debug     | Debug             | Werror                       | build/ci-debug  | gcc-debug or gcc-debug-ci    |

#### What each preset is for:
- **debug**: Debug; warnings on; tests on; no sanitizers; no coverage.
  -> Default preset for everyday hacking.
- **release**: Release; LTO on (`CMAKE_INTERPROCEDURAL_OPTIMIZATION=ON`); tests off.
  -> For real binaries and packaging.
- **asan**: Debug; `ENABLE_ASAN=ON`, `ENABLE_UBSAN=ON`; tests on.
  -> Use with `target_enable_sanitizers()` to catch UB and memory bugs.
- **tsan**: Debug; `ENABLE_TSAN=ON`; tests on.
  -> For multithreading race detection.
- **coverage**: Debug; `BUILD_COVERAGE=ON`; tests on.
  -> Works with your gcovr-based coverage target.
- **benchmark**: Release; `BUILD_BENCHMARKS=ON`; tests off.
  -> Builds benchmarks and enables `run-benchmarks`.
- **ci-debug**: Debug; tests on; `ENABLE_WARNINGS_AS_ERRORS=ON`.
  -> *Strict CI configuration for static analysis, compile warnings, and tests.*

# Code coverage

To generate a code coverage report run from the project root:

```bash

cmake --preset coverage
cmake --build --preset coverage --target coverage
```

Then open `build/coverage/coverage_report/index.html`


# Run benchmark target

Typical usage:
```
# run with defaults (BUILD_DIR=build/benchmark, PRESET=benchmark)
./tools/run_benchmarks.sh

# or explicitly:
BUILD_DIR=build/benchmark PRESET=benchmark ./tools/run_benchmarks.sh
```

### Create a comparison plot of a target against a baseline
Combined with the Python script, a typical manual workflow might be:
1. Run baseline (e.g. on main branch)
```
git checkout main
./tools/run_benchmarks.sh
cp build/benchmark/example_benchmark_bench.json build/benchmark/example_benchmark_baseline.json
```

1. Switch to feature branch and run benchmarks again
```
git checkout feature/my-change
./tools/run_benchmarks.sh
```

1. Compare and plot
```
./tools/plot_benchmark_compare.py --baseline build/benchmark/example_benchmark_baseline.json --current build/benchmark/example_benchmark_bench.json --output build/benchmark/benchmark_compare.png
```

## Generate Documentation

This project uses **Doxygen** to generate code documentation.

```console
doxygen
xdg-open docs/html/index.html
```

## Generate Code Coverage

```console
cmake --build --preset coverage
xdg-open build/debug/coverage_report/index.html
```

## Logging

This project provides a unified logging wrapper around **spdlog**, plus a small assertion system
(`ASSERT` / `ASSERT_MSG`) that integrates directly with the logger.

### Initializing the Logger

You must initialize the logger once, typically in `main.cpp`:

```cpp
#include "utils/log/logger.hpp"

using project_template::utils::log::Level;
using project_template::utils::log::Log;
using project_template::utils::log::Mode;

int main() {
    Log::init(
        Level::Debug,         // minimum level to display
        Mode::Async,          // or Mode::Sync for unit tests
        "[%T.%f] [%^%l%$] %v" // log pattern (timestamps, colors, message)
    );
}
```

### Sync vs Async mode

- `Mode::Sync` -> logging happens on the calling thread. Useful for deterministic unit tests.
- `Mode::Async` -> logging is queued and processed by a worker thread. Best for fast runtime behavior.
- `Log::reset_logger()` and `Log::flush()` ensure all logs are written before shutdown.

### Logging Macros
All macros automatically prepend the filename and line number to the message:
```c++
#include "logger.hpp"
...
LOG_TRACE("Starting system init");
LOG_DEBUG("Value of x: {}", x);
LOG_INFO("Loaded config '{}'", config_path);
LOG_WARN("Low memory: {} MB remaining", free_mb);
LOG_ERROR("Cannot open file '{}'", filename);
LOG_CRITICAL("Unexpected state encountered");
```
These expand to calls like:
```console
[23:04:05.123456] [info] [main.cpp@line:42] Loaded config 'settings.json'
```

### Clean Shutdown

To ensure no messages are lost in async mode:
```c++
Log::flush();
Log::reset_logger();   // also shuts down spdlog's thread pool
```

## Assertions

The project provides `ASSERT` and `ASSERT_MSG`:
```c++
#include "utils/assert/assert.hpp"

ASSERT(x == 10);
ASSERT_MSG(y != 0, "Invalid divisor: y = {} must not be zero!", y);
```
Behavior:
- In Release builds (NDEBUG) -> assertions are disabled
- In Debug builds:
  - A failing assertion logs via LOG_CRITICAL
  - All logs are flushed
  - spdlog is shut down
  - The program aborts

Example failure output:
```console
[12:45:17.983211] [critical] [math.cpp@line:88] Assertion failed: 'y != 0' at math.cpp:88 -- Invalid divisor: y = 0 must not be zero!
```
