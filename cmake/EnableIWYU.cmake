# --------------------------------------------------------------------------------------------------
# EnableIWYU.cmake
#
# This module integrates **Include-What-You-Use (IWYU)** into your CMake project.
#
# IWYU analyzes translation units and reports which headers should or shouldn't be included.
#
# Conan or CMake presets enable this functionality using:
#
#       ENABLE_IWYU = ON|OFF
#
# Features provided by this module:
#
#   - Detects the IWYU executable (`include-what-you-use` or `iwyu`) once at configure time.
#   - Defines:
#
#         enable_iwyu_for_target(<target>)
#
#     which applies IWYU checks to that specific target only (not globally).
#
#   - Optionally creates a helper target `iwyu-all` that runs IWYU over all translation units
#     using the helper script `iwyu_tool.py`.
#
# Minimal usage in your top-level CMakeLists.txt:
#
#       list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#       include(EnableIWYU)
#
#       if(TARGET ${PROJECT_NAME})
#           enable_iwyu_for_target(${PROJECT_NAME})
#       endif()
#
#       if(DEFINED UNIT_TEST_NAME AND TARGET ${UNIT_TEST_NAME})
#           enable_iwyu_for_target(${UNIT_TEST_NAME})
#       endif()
#
# Requirements:
#   - IWYU must be installed and available in PATH.
#   - IWYU integration works with compilers supported by IWYU (Clang and GCC).
#
# --------------------------------------------------------------------------------------------------

include(CheckCXXCompilerFlag)

# --- Locate IWYU once at configure time ------------------------------------------------------------

if(ENABLE_IWYU)
  find_program(
    IWYU_EXECUTABLE
    NAMES include-what-you-use iwyu
    DOC "Path to the include-what-you-use executable"
    )

  if(NOT IWYU_EXECUTABLE)
    message(
      WARNING "ENABLE_IWYU=ON but include-what-you-use was not found in PATH. "
              "No IWYU checks will be applied."
      )
  else()
    message(STATUS "Found include-what-you-use: ${IWYU_EXECUTABLE}")
  endif()
endif()

# --- Per-target IWYU configuration -----------------------------------------------------------------

function(enable_iwyu_for_target target)
  if(NOT ENABLE_IWYU)
    return()
  endif()

  if(NOT TARGET "${target}")
    message(FATAL_ERROR "enable_iwyu_for_target(): target '${target}' does not exist.")
  endif()

  if(NOT IWYU_EXECUTABLE)
    message(STATUS "IWYU executable not found — skipping IWYU for target '${target}'")
    return()
  endif()

  # Additional IWYU flags may be added here (mapping files, filters, etc.)
  set(iwyu_args
      "${IWYU_EXECUTABLE}"
      # Example arguments (uncomment/adapt as needed):
      # "-Xiwyu" "--mapping_file=${CMAKE_SOURCE_DIR}/cmake/iwyu_mappings.imp"
      # "-Xiwyu" "--no_fwd_decls"
      )

  message(STATUS "Enabling IWYU for target '${target}'")

  # Enable IWYU for this specific target
  set_property(TARGET ${target} PROPERTY CXX_INCLUDE_WHAT_YOU_USE "${iwyu_args}")
endfunction()

# --- Optional: helper target to run IWYU over all translation units -------------------------------

if(ENABLE_IWYU AND IWYU_EXECUTABLE)
  find_program(PYTHON_EXECUTABLE NAMES python3 python)

  if(PYTHON_EXECUTABLE)
    add_custom_target(
      iwyu-all
      COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/cmake/iwyu_tool.py -p ${CMAKE_BINARY_DIR}
      WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
      COMMENT "Running IWYU over all translation units"
      )
  endif()
endif()
