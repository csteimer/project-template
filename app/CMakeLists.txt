# -------------------------------------------------------
# Main application executable
# -------------------------------------------------------
# Name the executable based on the project name.
set(PROJECT_EXEC_NAME ${PROJECT_NAME}_exec)

add_executable(${PROJECT_EXEC_NAME} main.cpp)

# Make the current source dir's headers visible to this executable
target_include_directories(${PROJECT_EXEC_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Link the executable against local libraries / modules
target_link_libraries(${PROJECT_EXEC_NAME} PRIVATE utils_lib)
