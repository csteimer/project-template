#include <gtest/gtest.h>

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);

    // Optional: enable GoogleTest’s XML output when requested:
    // Example usage:
    //     ctest --output-on-failure -T test --verbose
    //
    // By default GoogleTest respects:
    //     --gtest_output=xml:<path>
    //
    // but we can set a fallback path if required:
    //
    // if (!::testing::GTEST_FLAG(output).size()) {
    //     ::testing::GTEST_FLAG(output) = "xml:./test_results.xml";
    // }

    // Optional: if you want colored output always enabled
    ::testing::GTEST_FLAG(color) = "yes";

    return RUN_ALL_TESTS();
}
