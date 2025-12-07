# --------------------------------------------------------------------------------------------------
# EnableCcache.cmake
#
# This module configures a **compiler cache** (e.g. `ccache` or `sccache`) as the compiler launcher
# for C and C++ targets in your project.
#
# It is designed to be:
#   - Opt-in / opt-out via a cache variable
#   - Safe in superproject / toolchain setups (won't override an existing launcher)
#   - Flexible enough to support both `ccache` and `sccache`
#
# Configuration variables:
#
#   ENABLE_CCACHE  (BOOL, default: ON)
#       Controls whether a compiler cache should be configured at all.
#       Can be set by Conan, CMakePresets, or manually:
#
#           -DENABLE_CCACHE=OFF
#
#   CCACHE_LAUNCHER (FILEPATH)
#       Explicit path to the compiler cache program (e.g. `/usr/bin/ccache` or `/usr/bin/sccache`).
#       If left empty, the module will try to `find_program()` one of:
#           - ccache
#           - sccache
#
# Behavior:
#   - If ENABLE_CCACHE=OFF              -> no launcher is configured.
#   - If a compiler launcher is already set (CMAKE_*_COMPILER_LAUNCHER), it is **not** overwritten.
#   - Otherwise, a launcher is discovered or taken from CCACHE_LAUNCHER and set globally:
#         CMAKE_C_COMPILER_LAUNCHER
#         CMAKE_CXX_COMPILER_LAUNCHER
#   - Adds a convenience target:
#
#         compiler-cache-stats
#
#     which calls `<launcher> -s` to show cache statistics.
#
# Minimal usage in your top-level CMakeLists.txt:
#
#     list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#     include(EnableCcache)
#
#     # Optional overrides:
#     #   cmake -DENABLE_CCACHE=OFF ...
#     #   cmake -DCCACHE_LAUNCHER=/usr/bin/sccache ...
#
# --------------------------------------------------------------------------------------------------

# Include the custom message wrappers
include(Logging)

# Only define the option if not already defined (allows superprojects/toolchains to control it).
if(NOT DEFINED ENABLE_CCACHE)
  option(ENABLE_CCACHE "Enable compiler cache (ccache/sccache) as compiler launcher" ON)
endif()

# Allow explicit override of the launcher via cache variable.
set(CCACHE_LAUNCHER
    ""
    CACHE FILEPATH "Path to compiler cache launcher (ccache, sccache, etc.)"
    )

# Early out if disabled.
if(NOT ENABLE_CCACHE)
  log_status("EnableCcache: ENABLE_CCACHE=OFF, not configuring compiler launcher")
  return()
endif()

# Don't clobber an existing launcher (e.g. set by parent project or toolchain file).
if(DEFINED CMAKE_CXX_COMPILER_LAUNCHER OR DEFINED CMAKE_C_COMPILER_LAUNCHER)
  log_status("EnableCcache: compiler launcher already set, not overwriting")
  return()
endif()

# If user did not specify a launcher explicitly, try to find one.
if(NOT CCACHE_LAUNCHER)
  find_program(
    CCACHE_LAUNCHER
    NAMES ccache sccache
    DOC "Compiler cache program (ccache/sccache)"
    )
endif()

if(NOT CCACHE_LAUNCHER)
  log_status("EnableCcache: no compiler cache found (ccache/sccache), continuing without it")
  return()
endif()

log_status("EnableCcache: using compiler launcher: ${CCACHE_LAUNCHER}")

# Set as global launcher for C and C++
set(CMAKE_C_COMPILER_LAUNCHER
    "${CCACHE_LAUNCHER}"
    CACHE STRING "C compiler launcher" FORCE
    )
set(CMAKE_CXX_COMPILER_LAUNCHER
    "${CCACHE_LAUNCHER}"
    CACHE STRING "C++ compiler launcher" FORCE
    )

# Optional convenience target to inspect cache statistics (if ccache/sccache supports it).
add_custom_target(
  compiler-cache-stats
  COMMAND "${CCACHE_LAUNCHER}" -s
  COMMENT "Showing compiler cache statistics"
  VERBATIM
  )
