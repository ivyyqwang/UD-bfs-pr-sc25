#include <gtest/gtest.h>
#include "inst_decode.hh"

using namespace basim;

class InstDecodeTest : public ::testing::Test {
 protected:
    size_t capacity = 5;
    void SetUp() override {
        // read in encoded file

    }

    // void TearDown() override {}
};

///* Testing Empty queue*/
//TEST_F(InstDecodeTest, IsEmpty) {
//    // Expect to be empty.
//    EXPECT_EQ(q0.getSize(), 0);
//}
//
///** Testing Size of InstDecode if used */
//TEST_F(InstDecodeTest, Capacity)
//{
//    EXPECT_EQ(q1.getCapacity(), capacity);
//}
//
//TEST_F(InstDecodeTest, QueueFull){
//    q1.push(4);
//    q1.push(5);
//    EXPECT_EQ(q1.getSize(), capacity);
//    ASSERT_FALSE(q1.push(8));
//}
//
//TEST_F(InstDecodeTest, QueueEmpty){
//    EXPECT_TRUE(q1.pop());
//    EXPECT_TRUE(q1.pop());
//    EXPECT_EQ(q1.getSize(), 1);
//    EXPECT_TRUE(q1.pop());
//    EXPECT_EQ(q1.getSize(), 0);
//    ASSERT_FALSE(q1.pop());
//}
//
//TEST_F(InstDecodeTest, ReadInstDecode){
//    q1.push(4);
//    q1.push(5);
//    for(int i = 0; i < capacity; i++){
//        EXPECT_EQ(q1.peek(), i+1);
//        q1.pop();
//        ASSERT_EQ(q1.getSize(), capacity-i-1);
//    }
//}
//
//TEST_F(InstDecodeTest, Name){
//    EXPECT_STREQ(q1.name(), "InstDecode");
//}