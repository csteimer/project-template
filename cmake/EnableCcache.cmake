# Reusable helper to configure a compiler cache (ccache/sccache).
#
# Usage in top-level CMakeLists.txt:
#
#   list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
#   include(EnableCcache)
#
#   # Optionally override:
#   #   -DENABLE_CCACHE=OFF
#   #   -DCCACHE_LAUNCHER=/usr/bin/sccache
#

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
  message(STATUS "EnableCcache: ENABLE_CCACHE=OFF, not configuring compiler launcher")
  return()
endif()

# Don't clobber an existing launcher (e.g. set by parent project or toolchain file).
if(DEFINED CMAKE_CXX_COMPILER_LAUNCHER OR DEFINED CMAKE_C_COMPILER_LAUNCHER)
  message(STATUS "EnableCcache: compiler launcher already set, not overwriting")
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
  message(STATUS "EnableCcache: no compiler cache found (ccache/sccache), continuing without it")
  return()
endif()

message(STATUS "EnableCcache: using compiler launcher: ${CCACHE_LAUNCHER}")

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
