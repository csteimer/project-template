# Add subdirectories containing source code
add_subdirectory(utils)

# Create an executable from main.cpp
add_executable(${PROJECT_NAME} main.cpp)

target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Link against local modules
target_link_libraries(${PROJECT_NAME} PRIVATE utils_lib)
