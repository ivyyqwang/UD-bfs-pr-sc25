//
// Created by alefel on 20/07/23.
//

#include <gtest/gtest.h>
#include <cstdint>
#include "buffer.hh"


using namespace basim;

class BufferTest : public ::testing::Test {
     protected:
        std::size_t capacity = 5;
        uint32_t latency = 2;
        Buffer<uint32_t>* buffer;

        void SetUp() override {
            buffer = new Buffer<uint32_t>(latency, capacity);
        }

        void TearDown() override {
            delete buffer;
        }
};

using BufferDeathTest = BufferTest;

TEST_F(BufferTest, ControlSignals) {
    EXPECT_TRUE(buffer->isEmpty());
    EXPECT_FALSE(buffer->hasData());
    EXPECT_FALSE(buffer->isFull());
    buffer->push(2);
    EXPECT_FALSE(buffer->isEmpty());
    EXPECT_FALSE(buffer->hasData()); // data becomes available only in the next to next clock cycle since latency = 2
    EXPECT_FALSE(buffer->isFull());
    buffer->tick(); // advance by 1 clock cycle
    EXPECT_FALSE(buffer->isEmpty());
    EXPECT_FALSE(buffer->hasData());
    EXPECT_FALSE(buffer->isFull());
    buffer->tick(); // advance by 1 clock cycle
    EXPECT_FALSE(buffer->isEmpty());
    EXPECT_TRUE(buffer->hasData());
    EXPECT_FALSE(buffer->isFull());
    EXPECT_EQ(buffer->peek(), 2); // just gets the data without popping it
    EXPECT_FALSE(buffer->isEmpty());
    EXPECT_TRUE(buffer->hasData());
    EXPECT_FALSE(buffer->isFull());
    buffer->pop(); // pops the data only, no return
    EXPECT_TRUE(buffer->isEmpty());
    EXPECT_FALSE(buffer->hasData());
    EXPECT_FALSE(buffer->isFull());
    buffer->reset();
}


TEST_F(BufferTest, Capacity) {
    buffer->push(0);
    buffer->push(1);
    buffer->push(2);
    buffer->push(3);
    buffer->push(4);
    EXPECT_FALSE(buffer->isEmpty());
    EXPECT_FALSE(buffer->hasData());
    EXPECT_TRUE(buffer->isFull());
    buffer->tick();
    EXPECT_FALSE(buffer->isEmpty());
    EXPECT_FALSE(buffer->hasData());
    EXPECT_TRUE(buffer->isFull());
    buffer->tick();
    EXPECT_FALSE(buffer->isEmpty());
    EXPECT_TRUE(buffer->hasData());
    EXPECT_TRUE(buffer->isFull());
    buffer->reset();
}



TEST_F(BufferDeathTest, AssertionsEmptyPeek) {
    ASSERT_DEATH(buffer->peek(), "The buffer is empty!");
}

TEST_F(BufferDeathTest, AssertionsEmptyPop) {
    ASSERT_DEATH(buffer->pop(), "The buffer is empty!");
}

TEST_F(BufferDeathTest, AssertionsInsufficientLatencyPeek0) {
    buffer->push(0);
    ASSERT_DEATH(buffer->peek(), "No element is ready yet!");
}

TEST_F(BufferDeathTest, AssertionsInsufficientLatencyPop0) {
    buffer->push(0);
    ASSERT_DEATH(buffer->pop(), "No element is ready yet!");
}

TEST_F(BufferDeathTest, AssertionsInsufficientLatencyPeek1) {
    buffer->push(0);
    buffer->tick();
    ASSERT_DEATH(buffer->peek(), "No element is ready yet!");
}

TEST_F(BufferDeathTest, AssertionsInsufficientLatencyPop1) {
    buffer->push(0);
    buffer->tick();
    ASSERT_DEATH(buffer->pop(), "No element is ready yet!");
}

TEST_F(BufferDeathTest, AssertionsCapacityExceeded) {
    buffer->push(0);
    buffer->push(1);
    buffer->push(2);
    buffer->push(3);
    buffer->push(4);
    ASSERT_DEATH(buffer->push(5),"The buffer is full!");
}


