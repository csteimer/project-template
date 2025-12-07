# Changelog – v1.0.0

### New Features
- Introduced complete project structure with separate `app/`, `src/`, `tests/`, `tools/`, and `cmake/` modules.
- Added modular CMake targets for internal libraries and a dedicated application target.
- Added comprehensive CMake helper modules (warnings, sanitizers, coverage, IWYU, benchmarks).
- Added full set of CMake presets (`debug`, `release`, `asan`, `tsan`, `coverage`, `benchmark`, `iwyu`, `ci-debug`).
- Implemented Conan 2 integration, including:
    - `conan_install.py` for per-preset dependency installation.
    - `release_conan_packages.py` for automated package creation and optional upload.
    - Automatic version derivation from Git tags or `PKG_VERSION`.
- Added GoogleTest integration with organized unit, integration, and benchmark test directories.
- Added Google Benchmark support and benchmark comparison tooling (`benchmark_runner.py`).
- Added IWYU workflow and standalone CMake preset.
- Introduced logging framework using `spdlog` with sync/async modes and macro-based logging.
- Added automated development environment bootstrap script (`setup_dev_env.sh`).
- Added pre-commit configuration (clang-format, black, YAML formatting, whitespace checks, typos).
- Added static analysis workflows for clang-tidy and cppcheck.
- Added code coverage target with HTML report generation.
- Added Doxygen configuration for documentation generation.

### Deprecated
- None (initial release).

### Removed
- None (initial release).

### Fixed
- None (initial release).
