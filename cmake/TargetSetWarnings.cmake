# --------------------------------------------------------------------------------------------------
# TargetSetWarnings.cmake
#
# This module provides a helper function:
#
#       target_set_warnings(<target>)
#
# which applies consistent, modern, and reasonably strict compiler warning flags
# to C and C++ targets in your project.
#
# Warning configuration is controlled by two cache variables:
#
#     ENABLE_WARNINGS          = ON|OFF   (default: ON)
#     ENABLE_WARNINGS_AS_ERRORS = ON|OFF  (default: OFF)
#
# Features:
#   - Applies warning flags *per target* (not globally), just like your other tooling modules.
#   - Supports:
#       * GCC
#       * Clang
#       * MSVC (with /W4 /permissive-)
#   - Provides a strict-but-sensible baseline warning set (no excessive noise).
#   - Optionally treats all warnings as errors when ENABLE_WARNINGS_AS_ERRORS=ON.
#
# Minimal usage in your top-level CMakeLists.txt:
#
#       list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#       include(TargetSetWarnings)
#
#       # Optional overrides:
#       #   -DENABLE_WARNINGS=OFF
#       #   -DENABLE_WARNINGS_AS_ERRORS=ON
#
#       target_set_warnings(my_library)
#       target_set_warnings(my_app)
#
# This module is intentionally similar in naming to:
#   - TargetSetSanitizer.cmake
#   - EnableIWYU.cmake
#   - EnableCcache.cmake
#   - EnableCoverage.cmake
#   - EnableBenchmarks.cmake
#
# --------------------------------------------------------------------------------------------------

# Include the custom message wrappers
include(Logging)

# Warning toggles, configurable via presets or manual CMake invocation
if(NOT DEFINED ENABLE_WARNINGS)
  option(ENABLE_WARNINGS "Enable warnings in target_set_warnings()" ON)
endif()

if(NOT DEFINED ENABLE_WARNINGS_AS_ERRORS)
  option(ENABLE_WARNINGS_AS_ERRORS "Treat warnings as errors in target_set_warnings()" OFF)
endif()

# --------------------------------------------------------------------------------------------------
# target_set_warnings(<target>)
#
# Applies compiler warning flags to a specific target.
#
# Behavior:
#   - If ENABLE_WARNINGS=OFF -> does nothing.
#   - Validates that <target> exists.
#   - Chooses compiler-specific warning sets for:
#         * GCC
#         * Clang
#         * MSVC
#   - Applies -Werror or /WX when ENABLE_WARNINGS_AS_ERRORS=ON.
# --------------------------------------------------------------------------------------------------
function(target_set_warnings target)
  if(NOT ENABLE_WARNINGS)
    log_status("TargetSetWarnings: warnings disabled globally (ENABLE_WARNINGS=OFF)")
    return()
  endif()

  if(NOT TARGET ${target})
    log_fatal("target_set_warnings: target '${target}' does not exist")
  endif()

  set(warnings_cxx "")
  set(warnings_c "")

  # --- MSVC warning configuration ---------------------------------------------------------------
  if(MSVC)
    # /W4 for strict warning level
    # /permissive- for stricter C++ standard conformance
    set(common /W4 /permissive-)

    if(ENABLE_WARNINGS_AS_ERRORS)
      list(APPEND common /WX)
    endif()

    set(warnings_cxx ${common})
    set(warnings_c ${common})

    # --- Clang / GCC warning configuration ---------------------------------------------------------
  elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")

    # A strict, modern, and reasonably non-noisy default warning set
    set(common
        -Wall
        -Wextra
        -Wpedantic
        -Wconversion
        -Wsign-conversion
        -Wshadow
        -Wnon-virtual-dtor
        -Wold-style-cast
        -Woverloaded-virtual
        -Wfloat-equal
        -Wdouble-promotion
        -Wformat=2
        )

    if(ENABLE_WARNINGS_AS_ERRORS)
      list(APPEND common -Werror)
    endif()

    set(warnings_cxx ${common})
    set(warnings_c ${common})

    # --- Unknown compiler: no warnings applied -----------------------------------------------------
  else()
    log_status(
      "TargetSetWarnings: unknown compiler '${CMAKE_CXX_COMPILER_ID}', not setting warnings"
      )
    return()
  endif()

  # Apply warnings via generator expressions so C and C++ flags remain distinct
  if(warnings_cxx)
    target_compile_options(
      ${target}
      PRIVATE $<$<COMPILE_LANGUAGE:CXX>:${warnings_cxx}> $<$<COMPILE_LANGUAGE:C>:${warnings_c}>
      )
  endif()

endfunction()
