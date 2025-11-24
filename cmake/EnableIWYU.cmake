include(CheckCXXCompilerFlag)

# Try to locate the IWYU binary once
if(ENABLE_IWYU)
  find_program(
    IWYU_EXECUTABLE
    NAMES include-what-you-use iwyu
    DOC "Path to the include-what-you-use executable"
    )

  if(NOT IWYU_EXECUTABLE)
    message(WARNING "ENABLE_IWYU=ON but include-what-you-use was not found in PATH.")
  else()
    message(STATUS "Found include-what-you-use: ${IWYU_EXECUTABLE}")
  endif()
endif()

function(enable_iwyu_for_target target)
  if(NOT ENABLE_IWYU)
    return()
  endif()

  if(NOT IWYU_EXECUTABLE)
    message(STATUS "IWYU not available, skipping configuration for target '${target}'")
    return()
  endif()

  # Add additional IWYU flags here
  # Example: mapping files, stdlib mappings, etc.
  set(iwyu_args
      "${IWYU_EXECUTABLE}"
      # Example extra args (uncomment/adjust as needed):
      # "-Xiwyu" "--mapping_file=${CMAKE_SOURCE_DIR}/cmake/iwyu_mappings.imp"
      # "-Xiwyu" "--no_fwd_decls"
      )

  message(STATUS "Enabling IWYU for target '${target}'")

  # Use target property so we can enable it per-target, not globally
  set_property(TARGET ${target} PROPERTY CXX_INCLUDE_WHAT_YOU_USE "${iwyu_args}")
endfunction()
