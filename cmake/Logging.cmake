# Logging.cmake
#
# Project-local logging helpers that prepend all messages with the project name.
#
# Usage:
#   list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
#   include(Logging)
#
#   project_log("Plain message")
#   project_log(STATUS "Configuring target" ${target})
#
#   log_status("Configuring target" ${target})
#   log_warning("This is unusual, but continuing")
#   log_error("Configuration failed for" ${target})
#   log_fatal("Unrecoverable error, stopping now")
#
# Optionally override prefix before including:
#   set(PROJECT_LOGGING_PREFIX "[MyApp] ")

include_guard(GLOBAL)

# ----------------------------------------------------------------------
# Prefix configuration
# ----------------------------------------------------------------------

if(NOT DEFINED PROJECT_LOGGING_PREFIX)
  if(DEFINED PROJECT_NAME)
    set(PROJECT_LOGGING_PREFIX "[${PROJECT_NAME}] ")
  else()
    # Fallback if PROJECT_NAME is not set
    set(PROJECT_LOGGING_PREFIX "")
  endif()
endif()

# Valid CMake message modes
set(_PROJECT_LOG_MESSAGE_MODES
    STATUS
    WARNING
    AUTHOR_WARNING
    SEND_ERROR
    FATAL_ERROR
    DEPRECATION
    )

# ----------------------------------------------------------------------
# Core helper: project_log(...)
#
# Forms:
#   project_log("message ...")
#   project_log(STATUS "message ...")
#   project_log(WARNING "message ...")
#   ...
# ----------------------------------------------------------------------
function(project_log)
  if(ARGC EQUAL 0)
    return()
  endif()

  set(prefix "${PROJECT_LOGGING_PREFIX}")
  set(first_arg "${ARGV0}")

  # Check whether the first argument is a known message mode
  list(FIND _PROJECT_LOG_MESSAGE_MODES "${first_arg}" _mode_index)

  if(_mode_index GREATER -1)
    # Syntax: project_log(MODE msg...)
    if(ARGC GREATER 1)
      list(
        SUBLIST
        ARGV
        1
        -1
        _rest
        )
      string(JOIN " " _msg ${_rest})
      message(${first_arg} "${prefix}${_msg}")
    else()
      # No message text, just forward the mode
      message(${first_arg})
    endif()
  else()
    # Syntax: project_log(msg...)
    string(JOIN " " _msg ${ARGV})
    message("${prefix}${_msg}")
  endif()
endfunction()

# ----------------------------------------------------------------------
# Convenience wrappers
# ----------------------------------------------------------------------

function(log_status)
  if(ARGC EQUAL 0)
    return()
  endif()
  project_log(STATUS ${ARGV})
endfunction()

function(log_warning)
  if(ARGC EQUAL 0)
    return()
  endif()
  project_log(WARNING ${ARGV})
endfunction()

function(log_author_warning)
  if(ARGC EQUAL 0)
    return()
  endif()
  project_log(AUTHOR_WARNING ${ARGV})
endfunction()

function(log_error)
  if(ARGC EQUAL 0)
    return()
  endif()
  project_log(SEND_ERROR ${ARGV})
endfunction()

function(log_fatal)
  if(ARGC EQUAL 0)
    return()
  endif()
  project_log(FATAL_ERROR ${ARGV})
endfunction()

function(log_deprecation)
  if(ARGC EQUAL 0)
    return()
  endif()
  project_log(DEPRECATION ${ARGV})
endfunction()
