# Project Template

A modern, modular C++ project template using **Conan 2**, **CMakePresets**, **GoogleTest**, **Google Benchmark**, **sanitizers**, **code coverage**, and a unified **logging + assertion** system.

This template provides:

- Reproducible builds with Conan profiles
- Strict CMake configuration and toolchain integration
- Presets for debug, sanitizers, coverage, CI, and benchmarks
- Unified logging (spdlog) and assertion utilities
- Doxygen documentation integration
- Benchmark comparison tooling
- Optional Include-What-You-Use (IWYU) analysis
- Automated Conan package versioning with Git tag + commit tracking

---

# 1. Setup

```bash
./setup_dev_env.sh
source .venv/bin/activate
conan profile detect
```

This sets up:

- A Python virtual environment
- Development tools for formatting, Doxygen, coverage, plotting, etc.
- Conan profiles for reproducible builds

---

# 2. CMake User Presets

CMake allows separation between **project-defined presets** (`cmake/CMakePresets.json`)
and **user-defined overrides** (`CMakeUserPresets.json`).

To keep the repository clean and customizable, create a `CMakeUserPresets.json` file in the project root:

```json
{
  "version": 4,

  "include": [
    "cmake/CMakePresets.json"
  ],

  "configurePresets": [],
  "buildPresets": [],
  "testPresets": []
}
```

This file:
- Inherits 100% of the presets from `cmake/CMakePresets.json`
- Allows developers to add local presets without modifying project files

---

# 3. CMake Presets and Conan Profiles

| CMake Preset | CMAKE_BUILD_TYPE | Sanitizers / Options      | binaryDir         | Suggested Host Profile     |
|--------------|------------------|---------------------------|-------------------|-----------------------------|
| debug        | Debug            | none                      | build/debug       | gcc-debug                  |
| release      | Release          | none                      | build/release     | gcc-release                |
| asan         | Debug            | ASAN + UBSAN              | build/asan        | gcc-debug-asan             |
| tsan         | Debug            | TSAN                      | build/tsan        | gcc-debug-tsan             |
| coverage     | Debug            | coverage instrumentation  | build/coverage    | gcc-debug-coverage         |
| benchmark    | Release          | benchmarks only           | build/benchmark   | gcc-release-benchmark      |
| ci-debug     | Debug            | Werror                    | build/ci-debug    | gcc-debug or gcc-debug-ci  |

## What each preset does

### **debug**
- Standard development configuration
- Warnings enabled, tests enabled
- No sanitizers or coverage overhead
  **Use this for everyday development.**

### **release**
- Optimized build with LTO
  **Use for product-ready binaries and packaging.**

### **asan**
- AddressSanitizer + UndefinedBehaviorSanitizer
  **Use to catch memory errors and undefined behavior.**

### **tsan**
- ThreadSanitizer
  **Use to detect multithreading race conditions.**

### **coverage**
- `BUILD_COVERAGE=ON` + gcov instrumentation
  **Use to generate coverage HTML reports.**

### **benchmark**
- Only benchmarks enabled
- Provides `run-benchmarks` aggregate target
  **Use for performance regression testing.**

### **ci-debug**
- Warnings-as-errors enabled
- Debug + tests
  **Use for CI pipelines.**

---

# 4. Building the Project

Example:

```bash
cmake --preset debug
cmake --build --preset debug
```

Run tests:

```bash
ctest --test-dir build/debug --output-on-failure
```

---

# 5. Code Coverage

```bash
cmake --preset coverage
cmake --build --preset coverage --target coverage
```

Open:

```
build/coverage/coverage_report/index.html
```

---

# 6. Running Benchmarks

```bash
./tools/run_benchmarks.sh
```

Explicit build directory:

```bash
BUILD_DIR=build/benchmark PRESET=benchmark ./tools/run_benchmarks.sh
```

## Benchmark comparison workflow

### 1. Generate baseline on main

```bash
git checkout main
./tools/run_benchmarks.sh
cp build/benchmark/example_benchmark_bench.json    build/benchmark/example_benchmark_baseline.json
```

### 2. Switch to feature branch

```bash
git checkout feature/my-change
./tools/run_benchmarks.sh
```

### 3. Compare and plot

```bash
./tools/benchmark_runner.py   --baseline build/benchmark/example_benchmark_baseline.json   --current  build/benchmark/example_benchmark_bench.json   --output   build/benchmark/benchmark_compare.png
```

---

# 7. Documentation Generation (Doxygen)

```bash
doxygen
xdg-open docs/html/index.html
```

---

# 8. Logging System

The project provides a unified logging wrapper around **spdlog**.

## Initialization

```cpp
#include "utils/log/logger.hpp"

int main() {
    Log::init(
        Level::Debug,
        Mode::Async,
        "[%T.%f] [%^%l%$] %v"
    );
}
```

## Logging macros

```cpp
LOG_TRACE("Starting system init");
LOG_DEBUG("X = {}", x);
LOG_INFO("Loaded '{}'", file);
LOG_WARN("Low memory: {} MB", free_mb);
LOG_ERROR("Failed to open '{}'", filename);
LOG_CRITICAL("Unexpected state!");
```

Example output:

```
[23:04:05.123456] [info] [main.cpp@line:42] Loaded config 'settings.json'
```

## Clean shutdown

```cpp
Log::flush();
Log::reset_logger();
```

---

# 9. Assertions

```cpp
ASSERT(x == 10);
ASSERT_MSG(y != 0, "Invalid divisor y = {}", y);
```

### Debug build behavior
- Logs `LOG_CRITICAL`
- Flushes logs
- Shuts down spdlog thread pool
- Aborts program

---

# 10. Conan Package Creation

This project supports full `conan create` workflows.

## Build a package

```bash
conan create . --profile:host=conan/profiles/gcc-release
```

Included in the package:

- `lib/`, `bin/` artifacts
- `include/` headers
- `licenses/`
- `metadata/git_commit.txt`
- Conan metadata
- Auto-generated version number

## Install the package locally

```bash
conan install project-template/<version>@
```

Or in another project:

```ini
[requires]
project-template/<version>
```

---

# 11. Versioning: Git-Driven Automatic Versioning

Version is determined by:

1. If `PKG_VERSION` is set → use it
2. Else if `HEAD` is exactly on a Git tag → use the tag
3. Else → version = `latest`

Commit hash is stored in:

```
metadata/git_commit.txt
```

---

# 12. Include-What-You-Use (IWYU)

Enable with:

```bash
cmake --preset iwyu
```

Run:

```bash
cmake --build --preset iwyu --target iwyu-all
```

---

# 13. Repository Structure

```
project-template/
  ├── src/
  ├── tests/
  ├── cmake/
  ├── conan/
  ├── tools/
  ├── docs/
  ├── CMakeLists.txt
  ├── CMakeUserPresets.json
  ├── conanfile.py
  ├── README.md
  └── ...
```

---

Enjoy building clean, maintainable C++ software!
