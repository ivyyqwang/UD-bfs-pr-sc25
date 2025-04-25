#include <gtest/gtest.h>
#include "opbuffer.hh"

using namespace basim;

class OpBufferTest : public ::testing::Test {
 protected:
    size_t capacity = 32;
    void SetUp() override {
        obuff1 = OpBuffer<uint64_t>(capacity);
        obuff1.push(1);
        obuff1.push(2);
        obuff1.push(3);
    }

    // void TearDown() override {}
    OpBuffer<uint32_t> obuff0;
    OpBuffer<uint64_t> obuff1;
};

/* Testing Empty queue*/
TEST_F(OpBufferTest, IsEmpty) {
    // Expect to be empty.
    EXPECT_EQ(obuff0.getSize(), 0);
}

/** Testing Size of OpBuffer if used */
TEST_F(OpBufferTest, Capacity)
{
    EXPECT_EQ(obuff1.getCapacity(), capacity);
}

TEST_F(OpBufferTest, OpBuffFull){
    for(int i = 0; i < capacity - 3; i++) obuff1.push(i+4);
    EXPECT_EQ(obuff1.getSize(), capacity);
    ASSERT_FALSE(obuff1.push(8));
}

TEST_F(OpBufferTest, OpBuffEmpty){
    EXPECT_TRUE(obuff1.clear(1));
    EXPECT_TRUE(obuff1.clear(2));
    EXPECT_EQ(obuff1.getSize(), 0);
    ASSERT_FALSE(obuff1.clear(1));
}

TEST_F(OpBufferTest, ReadOpBuffer){
    for(int i = 0; i < capacity - 3; i++) obuff1.push(i+4);
    for(int i = 0; i < capacity; i++){
        ASSERT_EQ(obuff1.read(i), i+1);
    }
}

TEST_F(OpBufferTest, Name){
    EXPECT_STREQ(obuff1.name(), "OpBuffer");
    EXPECT_STREQ(obuff0.name(), "OpBuffer");
}