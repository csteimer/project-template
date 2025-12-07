# Project Template

A modern C++ project template featuring a clean CMake structure, Conan 2 dependency management, built‑in
testing and benchmarking support, and a streamlined developer environment setup. The goal is to provide a minimal but
professional foundation that you can extend into real projects without carrying unnecessary complexity.

---

### 0.1 Create a New Project From This Template

Follow these steps to initialize a fresh project based on this template:

1. **Create a repository copy**
- If using GitHub: click **Use this template** -> **Create a new repository**,
  or manually clone and re-initialize:
  ```
  git clone <template-repo-url> <new-project-name>
  cd <new-project-name>
  rm -rf .git
  git init
  git add .
  git commit -m "Initial project setup"
  ```

2. **Rename all template identifiers**
   Perform a project-wide search and replace for: `project_template`
   Replace it with your actual project name.
   This updates CMake target names, namespaces, include paths, and documentation.

Proceed with the setup steps below once the renaming is complete.

---

# 1. Quick Start

### 1.1 Prepare the Development Environment

```bash
./setup_dev_env.sh
source .venv/bin/activate
```

This script:

- Recreates a fresh Python virtual environment under `.venv`
- Installs Python‑based development tools:
    - `pre-commit`, `cpplint`, `black`, `clang-format`, `cmakelang`, `gcovr`, `conan`
- Installs native system dependencies via `apt`:
    - `ninja-build`, `clang-tidy`, `cppcheck`, `ccache`, `doxygen`, `iwyu`, `graphviz`
- Configures `ccache` (size + directory)
- Installs this repository’s pre‑commit hooks

Activate the environment in future shells:

```bash
source .venv/bin/activate
```

### 1.2 Install Dependencies for a Build Preset

Dependency installation is handled via:

```bash
./conan/conan_install.py <preset>
```

Examples:

```bash
./conan/conan_install.py debug
./conan/conan_install.py asan
./conan/conan_install.py release
```

This populates `build/<preset>/generators/` with Conan toolchains and dependency
files. The script contains detailed documentation (`--help`).
The available options for `<preset>` corresponds to the cmake presets (see [Section 2](#2-cmake-presets)).

Remark: Use the `all` argument to call `conan install` in the build directories of all build presets.

### 1.3 Building the Project

Configure and build the project:
```bash
cmake --preset <cmake-preset>
cmake --build --preset <cmake-preset>
```

---

# 2. CMake Presets

Defined in `CMakeUserPresets.json`:

| Preset      | Type    | Features                                       | Build Dir         |
|-------------|---------|------------------------------------------------|-------------------|
| `debug`     | Debug   | basic dev, tests enabled                       | `build/debug`     |
| `release`   | Release | Link time optimized build                      | `build/release`   |
| `asan`      | Debug   | AddressSanitizer + UndefinedBehaviourSanitizer | `build/asan`      |
| `tsan`      | Debug   | ThreadSanitizer                                | `build/tsan`      |
| `coverage`  | Debug   | gcov instrumentation + coverage target         | `build/coverage`  |
| `benchmark` | Release | benchmark‑only build                           | `build/benchmark` |
| `iwyu`      | Debug   | Include‑What‑You‑Use analysis                  | `build/iwyu`      |
| `ci-debug`  | Debug   | strict warnings-as-errors                      | `build/ci-debug`  |

---

# 3. Project Structure

```
project_template/
  ├── app/                  # Application executable (links internal libraries)
  ├── cmake/                # Custom CMake helper modules (warnings, sanitizers, coverage, IWYU, benchmarks, ...)
  ├── conan/                # Conan scripts, profiles, and automation helpers
  ├── src/                  # Internal libraries (modular CMake targets)
  ├── tests/                # All test suites
  │     ├── benchmark/      # Google Benchmark sources
  │     ├── integration/    # Integration tests (end-to-end behavior)
  │     └── unit/           # GoogleTest unit tests (per-module testing)
  ├── tools/                # Utility scripts (e.g., benchmark comparison tools)
  ├── CMakeLists.txt        # Top-level CMake entry point for the entire project
  ├── CMakeUserPresets.json # User-specific presets for configuring & building (inherits project presets)
  ├── Doxyfile              # Doxygen configuration for generating documentation
  ├── README.md             # Project documentation and usage guide
  ├── conanfile.py          # Conan package recipe (dependencies, build, packaging, versioning)
  ├── dependencies.cmake    # Central declaration of required third-party CMake dependencies
  └── setup_dev_env.sh      # Script to setup development environment (venv + tools + apt deps)
```

---

# 4. Conan Package Workflow

### 4.1 Package Generation and Upload
This repository provides a helper script to **build and (optionally) upload**
Conan packages for all or selected profiles in `conan/profiles/`.
It uses `conan create` under the hood and automatically:

- Detects the package name from the local `conanfile.py` via `conan inspect`.
- Detects available profiles in `conan/profiles/`.
- Builds the package for one or more **build profiles**.
- Optionally uploads the resulting packages to a chosen **remote**.
- Supports cross-compilation by separating **build** and **host** profiles.

Run from the project root:

```bash
./conan/release_conan_packages.py --remote <remote-name>
```

The `<remote-name>` must be a configured Conan remote (see `conan remote list`).

The upload step can be disabled with the `--disable-upload` flag:

```bash
# Build for all detected profiles, but do not upload anything
./conan/release_conan_packages.py --disable-upload
```

#### Common usage examples

Build and upload for **all** profiles under `conan/profiles/` (host == build):

```bash
./conan/release_conan_packages.py --remote local-test
```

Build and upload for a **single** profile (e.g. `gcc-release`):

```bash
./conan/release_conan_packages.py --remote local-test --profile gcc-release
```

Build and upload for **multiple** build profiles:

```bash
./conan/release_conan_packages.py --remote local-test \
    --profile gcc-debug --profile gcc-release
```

Cross-compilation: build with `gcc-debug`, target host profile `gcc-release`:

```bash
./conan/release_conan_packages.py --remote local-test \
    --profile gcc-debug --host-profile gcc-release
```

If any profile or remote is missing, the script aborts with a clear error
message to avoid publishing incomplete or misconfigured packages.

### 4.2. Versioning

The Conan recipe automatically derives versions from:

1. `PKG_VERSION` (if set), or
2. Git tag at HEAD, otherwise
3. `"latest"`

Each package also embeds `metadata/git_commit.txt`.

---

# 5. Testing

### 5.1 Unit Tests

Located under: `tests/unit/`

Uses GoogleTest and link against modular test libraries.

Run:

```bash
ctest --preset <cmake-preset>
```

### 5.2 Integration Tests

Located under: `tests/integration/`

Remark: Empty placeholder.

### 5.3 Benchmark Tests

Located under: `tests/benchmark`

Configure and build via `--preset benchmark`

See [Section 6](#6-benchmarks--performance-comparison) for instructions on how to use the helper script for
running benchmarks and comparing multiple runs.

---

# 6. Benchmarks & Performance Comparison

This project integrates **Google Benchmark** and provides a helper script
`tools/benchmark_runner.py` for running and comparing performance results.

The script supports three workflows:

### 6.1 Run Benchmarks for the Current Working Tree

This command:

- Ensures Conan dependencies are installed for the `benchmark` preset
- Configures CMake using preset `benchmark`
- Builds benchmarks in `build/benchmark`
- Runs the aggregate benchmark target `run-benchmark`
- Produces JSON files such as `*_bench.json` in `build/benchmark`

```bash
./tools/benchmark_runner.py run
```

Use this before comparing results or when profiling performance manually.

### 6.2 Compare Two Benchmark Outputs

The `compare-json` subcommand compares performance between:

- Two individual JSON benchmark files **or**
- Two directories containing multiple `*_bench.json` files

It prints a table showing:

- Baseline time
- Current time
- Speedup factor
- Percentage change

Example (two files):

```bash
./tools/benchmark_runner.py compare-json \
--baseline base.json \
--current  curr.json
```

Example (directories):

```bash
./tools/benchmark_runner.py compare-json \
--baseline build/base/benchmark \
--current  build/curr/benchmark
```

You can choose the metric:

- `--time-key real_time` (default, wall-clock time)
- `--time-key cpu_time` (CPU usage)

### 6.3 Compare Performance Across Two Git Commits

```bash
./tools/benchmark_runner.py compare-commits <baseline-ref> <current-ref>
```

This command:

1. Creates (or reuses) isolated **git worktrees** under
   `build/benchmark/benchmark_worktrees/<short-ref>/`
2. Runs the full benchmark workflow (`conan install`, configure, build, run) for each commit
3. Loads results from both worktrees
4. Prints a detailed performance comparison table

Example:

```bash
./tools/benchmark_runner.py compare-commits main feature/my-optimization
```

This allows you to confirm whether a change improves performance before merging.

### 6.4 Need Help?

```bash
./tools/benchmark_runner.py --help
./tools/benchmark_runner.py run --help
./tools/benchmark_runner.py compare-json --help
./tools/benchmark_runner.py compare-commits --help
```

---

# 7. Code Coverage

Enable coverage instrumentation:

```bash
./conan/conan_install.py coverage
cmake --preset coverage
cmake --build --preset coverage
```

Open in browser:

```
build/coverage/coverage_report/index.html
```

---

# 8. IWYU (Include-What-You-Use)

IWYU helps you automatically detect missing or unnecessary `#include` directives.
This keeps compile times low, avoids hidden dependencies,
and ensures every file explicitly includes what it needs.

Using a standalone preset ensures IWYU does not slow down everyday development.

Run IWYU:

```bash
cmake --preset iwyu
cmake --build --preset iwyu --target iwyu-all
```

---

# 9. Logging Framework

`src/utils/log/logger.hpp` provides a unified `spdlog`‑based logger:

- sync & async modes
- file‑and‑line aware macros (`LOG_INFO`, `LOG_DEBUG`, …)
- automatic flush on error/critical

Example:

```cpp
Log::init(Level::Debug, Mode::Async);
LOG_INFO("Starting application");
```

---

# 10. Pre‑Commit Hooks

Installed automatically via `setup_dev_env.sh`.

Includes:

- clang-format
- black
- whitespace & EOF checks
- YAML formatting
- typo detection

Run manually:

```bash
pre-commit run --all-files
```

To explicitly skip all pre-commit hooks for a single commit:

```bash
git commit --no-verify -m "This commit won't run the pre-commit hooks"
```

---

# 11. Static Analysis

### 11.1 clang-tidy

Before running clang-tidy, ensure the project is configured so that a
`compile_commands.json` exists in the build directory:

```bash
cmake --preset debug
```

#### Run clang-tidy for an entire build directory

```bash
run-clang-tidy -p <build-directory>
```

Use any other preset's build directory as needed:

#### Run clang-tidy only on changed files

Last commit:

```bash
git diff --name-only HEAD~1 -- '*.cpp' '*.cc' '*.cxx' | xargs -r run-clang-tidy -p <build-directory>
```

Against a branch:

```bash
git diff --name-only origin/main...HEAD -- '*.cpp' '*.cc' '*.cxx' \
  | xargs -r run-clang-tidy -p <build-directory>
```

## 11.2 cppcheck

**cppcheck** is a static analysis tool which can read your project’s
`compile_commands.json` to understand include paths, compiler definitions, and
build flags. Because cppcheck uses its own simplified preprocessor, it may
produce false positives for:

- **third-party headers** (e.g., Conan-provided libraries -> `missingIncludeSystem`)
- **complex variadic macros**, especially logging wrappers built on top of
  **spdlog** and **fmt** (`syntaxError` during macro expansion)

These diagnostics do **not** indicate real issues in the compiled code,
so they are selectively suppressed in the examples given below.

#### Run cppcheck using the compile database

Use the compile database generated by CMake for a specific preset:

```bash
cppcheck \
  --enable=all \
  --inconclusive \
  --std=c++20 \
  --project=<build-directory>/compile_commands.json \
  --suppress=missingIncludeSystem \
  --suppress=syntaxError
```

---

# 12. Documentation

The project provides both Doxygen-based C++ API documentation and a unified Sphinx website that integrates the generated XML output.

## 12.1 Doxygen (C++ API)

Generate Doxygen output (XML + optional HTML):

```bash
cd docs/doxygen
doxygen Doxyfile
```

Open the HTML output under `docs/doxygen/build/html/index.html` in a browser for direct inspection.

## 12.2 Sphinx (full documentation site)

The Sphinx documentation automatically consumes the Doxygen XML via Breathe.

Build the HTML site:

```bash
make -C docs/sphinx html
```

Output:
`docs/sphinx/build/html/index.html`

## 12.3 One-step build

Use the helper script to generate both:

```bash
./tools/generate_docs.sh
```



------

If starting a new project from this template, simply delete unused modules and extend `src/` with your own library
targets.

Enjoy building clean, maintainable C++ software!
