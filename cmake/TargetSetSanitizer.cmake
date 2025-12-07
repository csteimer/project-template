# --------------------------------------------------------------------------------------------------
# TargetSetSanitizer.cmake
#
# This module provides a helper function:
#
#     target_set_sanitizer(<target>)
#
# It applies the appropriate sanitizer flags (ASan or TSan) to *specific targets*.
# The sanitizer selection is controlled by Conan, which sets one of:
#
#     ENABLE_ASAN = ON|OFF
#     ENABLE_TSAN = ON|OFF
#
# Features:
#   - Ensures ASan and TSan are *not* enabled simultaneously.
#   - Applies sanitizer flags only to the given target (NOT globally).
#   - Supports GCC and Clang.
#
# Minimal usage in your top-level CMakeLists.txt:
#
#     list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#     include(TargetSetSanitizer)
#
#     if(TARGET ${PROJECT_NAME})
#         target_set_sanitizer(${PROJECT_NAME})
#     endif()
#
#     if(DEFINED UNIT_TEST_NAME AND TARGET ${UNIT_TEST_NAME})
#         target_set_sanitizer(${UNIT_TEST_NAME})
#     endif()
#
# --------------------------------------------------------------------------------------------------

# Include the custom message wrappers
include(Logging)

# --- Mutual exclusion check ----------------------------------------------------
if(ENABLE_ASAN AND ENABLE_TSAN)
  log_fatal(
    "Both ENABLE_ASAN and ENABLE_TSAN are ON.\n" "ASan and TSan cannot be enabled together."
    )
endif()

# --- Function to apply sanitizer flags to a specific target ---------------------
function(target_set_sanitizer target)
  if(NOT TARGET "${target}")
    log_fatal("target_set_sanitizer(): target '${target}' does not exist")
  endif()

  # No sanitizers selected → nothing to do
  if(NOT ENABLE_ASAN AND NOT ENABLE_TSAN)
    return()
  endif()

  # Only GCC/Clang support these flags in this form
  if(NOT (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU"))
    log_warning(
      "Sanitizers requested, but compiler '${CMAKE_CXX_COMPILER_ID}' "
      "does not support ASan/TSan in the expected form. "
      "Ignoring sanitizer configuration for target '${target}'."
      )
    return()
  endif()

  # --- AddressSanitizer + UBSan ---------------------------------------------
  if(ENABLE_ASAN)
    target_compile_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(${target} PRIVATE -fsanitize=address,undefined)
    log_status("Applied ASan+UBSan to target: ${target}")
    return()
  endif()

  # --- ThreadSanitizer ----------------------------------------------
  if(ENABLE_TSAN)
    target_compile_options(${target} PRIVATE -fsanitize=thread)
    target_link_options(${target} PRIVATE -fsanitize=thread)
    log_status("Applied TSan to target: ${target}")
    return()
  endif()

endfunction()
