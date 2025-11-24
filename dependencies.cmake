message(STATUS "${PROJECT_NAME}: Locating external dependencies (Conan / CMakeDeps) ...")

# This file assumes you are using Conan 2 with the CMakeDeps generator.
# The versions and options (e.g. spdlog header_only, yaml-cpp shared/static, etc.)
# are now controlled in your conanfile.py, not here.

# --- spdlog ---
message(STATUS "Finding spdlog ...")
find_package(spdlog REQUIRED CONFIG)

# --- magic_enum ---
message(STATUS "Finding magic_enum ...")
find_package(magic_enum REQUIRED CONFIG)

# --- yaml-cpp ---
message(STATUS "Finding yaml-cpp ...")
find_package(yaml-cpp REQUIRED CONFIG)

message(STATUS "${PROJECT_NAME}: External dependencies ready.")
