set(UTILS_UNIT_TEST_SOURCES logger.unit_test.cpp)

add_library(utils_unit_test_lib OBJECT ${UTILS_UNIT_TEST_SOURCES})

target_link_libraries(utils_unit_test_lib PRIVATE GTest::gtest utils_lib)
