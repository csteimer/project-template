#include <gtest/gtest.h>

// A simple fixture-free test
TEST(SanityTests, BasicMathWorks) {
    EXPECT_EQ(1 + 1, 2);
    EXPECT_NE(5 * 5, 20);
    EXPECT_LT(3, 10);
    EXPECT_GT(10, 3);
}

// A small fixture to show structure
class ExampleFixture : public ::testing::Test {
  protected:
    void SetUp() override {
        value = 42;
    }

    int value{};
};

TEST_F(ExampleFixture, FixtureInitializesCorrectly) {
    EXPECT_EQ(value, 42);
}

TEST_F(ExampleFixture, OperationsWork) {
    value += 8;
    EXPECT_EQ(value, 50);
}
