#include <gtest/gtest.h>
#include "streambuffer.hh"

using namespace basim;

class StreamBufferTest : public ::testing::Test {
 protected:
    size_t capacity = 64;
    void SetUp() override {
        stbuff = new StreamBuffer(capacity);
    }

    // void TearDown() override {}
    StreamBufferPtr stbuff;
};

/* Testing Empty queue*/
TEST_F(StreamBufferTest, IsEmpty) {
    EXPECT_TRUE(stbuff->empty());
}

/** Testing Size of StreamBuffer if used */
TEST_F(StreamBufferTest, Capacity)
{
    EXPECT_EQ(stbuff->getCapacity(), capacity);
}

TEST_F(StreamBufferTest, StBuffFull){
    for(int i = 0; i < capacity; i++) stbuff->writeIntoSB(i, i*8);
    EXPECT_EQ(stbuff->getSize(), capacity * 8);
    //EXPECT_DEATH(stbuff->writeIntoSB(i*8+1, 5),"The stream buffer is full!");
}

TEST_F(StreamBufferTest, ReadStreamBufferBits){
    for(int i = 0; i < capacity; i++) stbuff->writeIntoSB(i, i);
    int bits = 4;
    for(int i = 0; i < capacity*8; i+=bits){
        if(i % 8 == 4){
            ASSERT_EQ(stbuff->getVarSymbol(i, bits), (int)((i >> 3)/16));
        }
        else{
            ASSERT_EQ(stbuff->getVarSymbol(i, bits), (int)((i >> 3)& 0xF));
        }
    }
}

TEST_F(StreamBufferTest, ReadStreamBufferBitsUnAligned){
    for(int i = 0; i < capacity; i++) stbuff->writeIntoSB(i, 0xa5);
    int bits = 3;
    int countmod = 0;
    for(int i = 0; i < capacity*8; i+=bits){
        switch(countmod){
            case 0:
            case 7:
                ASSERT_EQ(stbuff->getVarSymbol(i, bits), 5);
                break;
            case 1:
                ASSERT_EQ(stbuff->getVarSymbol(i, bits), 4);
                break;
            case 2:
                ASSERT_EQ(stbuff->getVarSymbol(i, bits), 6);
                break;
            case 3:
            case 4:
                ASSERT_EQ(stbuff->getVarSymbol(i, bits), 2);
                break;
            case 5:
                ASSERT_EQ(stbuff->getVarSymbol(i, bits), 3);
                break;
            case 6:
                ASSERT_EQ(stbuff->getVarSymbol(i, bits), 1);
                break;
        }
        (countmod = (countmod + 1)%8);
    }
}

