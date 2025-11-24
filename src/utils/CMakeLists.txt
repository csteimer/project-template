set(UTILS_SOURCES logger.cpp)

set(UTILS_HEADERS assertions.hpp logger.hpp)

add_library(utils_lib STATIC ${UTILS_SOURCES} ${UTILS_HEADERS})

target_include_directories(utils_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(utils_lib PUBLIC spdlog::spdlog_header_only)
