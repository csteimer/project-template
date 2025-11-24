# Reusable helper for setting consistent compiler warnings per target.
#
# Usage:
#   list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
#   include(TargetSetWarnings)
#
#   # Optional (global) toggles:
#   #   -DENABLE_WARNINGS=OFF
#   #   -DENABLE_WARNINGS_AS_ERRORS=ON
#
#   target_set_warnings(my_lib)
#   target_set_warnings(my_app)
#

if(NOT DEFINED ENABLE_WARNINGS)
  option(ENABLE_WARNINGS "Enable warnings in target_set_warnings()" ON)
endif()

if(NOT DEFINED ENABLE_WARNINGS_AS_ERRORS)
  option(ENABLE_WARNINGS_AS_ERRORS "Treat warnings as errors in target_set_warnings()" OFF)
endif()

function(target_set_warnings target)
  if(NOT ENABLE_WARNINGS)
    message(STATUS "TargetSetWarnings: warnings disabled globally (ENABLE_WARNINGS=OFF)")
    return()
  endif()

  if(NOT TARGET ${target})
    message(FATAL_ERROR "target_set_warnings: target '${target}' does not exist")
  endif()

  set(warnings_cxx "")
  set(warnings_c "")

  if(MSVC)
    # MSVC warning level (/W4 is fairly strict) + /permissive- for more standard compliance.
    set(common /W4 /permissive-)
    if(ENABLE_WARNINGS_AS_ERRORS)
      list(APPEND common /WX)
    endif()
    set(warnings_cxx ${common})
    set(warnings_c ${common})

  elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    # Reasonably strict, non-insane default set.
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

  else()
    message(
      STATUS "TargetSetWarnings: unknown compiler '${CMAKE_CXX_COMPILER_ID}', not setting warnings"
      )
    return()
  endif()

  if(warnings_cxx)
    target_compile_options(
      ${target}
      PRIVATE $<$<COMPILE_LANGUAGE:CXX>:${warnings_cxx}> $<$<COMPILE_LANGUAGE:C>:${warnings_c}>
      )
  endif()
endfunction()
