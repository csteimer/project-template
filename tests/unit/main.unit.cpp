#include <gtest/gtest.h>

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);

    // Optional: if you want colored output always enabled
    ::testing::GTEST_FLAG(color) = "yes";

    return RUN_ALL_TESTS();
}
