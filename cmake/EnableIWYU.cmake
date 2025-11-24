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

  # Add additional IWYU flags here (mapping files, etc.)
  set(iwyu_args
      "${IWYU_EXECUTABLE}"
      # Example extra args (uncomment/adjust as needed):
      # "-Xiwyu" "--mapping_file=${CMAKE_SOURCE_DIR}/cmake/iwyu_mappings.imp"
      # "-Xiwyu" "--no_fwd_decls"
      )

  message(STATUS "Enabling IWYU for target '${target}'")

  # Enable IWYU per-target via property
  set_property(TARGET ${target} PROPERTY CXX_INCLUDE_WHAT_YOU_USE "${iwyu_args}")
endfunction()

# Optional global helper target: runs IWYU over all TUs via iwyu_tool.py
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
