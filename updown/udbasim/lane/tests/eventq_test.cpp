#include <gtest/gtest.h>
#include "eventq.hh"

#include "types.hh"
#include "lanetypes.hh"

using namespace basim;

class EventQTest : public ::testing::Test {
 protected:
    size_t capacity = 5;
    void SetUp() override {
        q1 = EventQ<eventword_t>(capacity);
        q1.push(EventWord(1));
        q1.push(EventWord(2));
        q1.push(EventWord(3));
    }

    // void TearDown() override {}
    EventQ<eventword_t> q0;
    EventQ<eventword_t> q1;
};

/* Testing Empty queue*/
TEST_F(EventQTest, IsEmpty) {
    // Expect to be empty.
    EXPECT_EQ(q0.getSize(), 0);
}

/** Testing Size of EventQ if used */
TEST_F(EventQTest, Capacity)
{
    EXPECT_EQ(q1.getCapacity(), capacity);
}

TEST_F(EventQTest, QueueFull){
    q1.push(EventWord(4));
    q1.push(EventWord(5));
    EXPECT_EQ(q1.getSize(), capacity);
    ASSERT_FALSE(q1.push(EventWord(8)));
}

TEST_F(EventQTest, QueueEmpty){
    EXPECT_TRUE(q1.pop());
    EXPECT_TRUE(q1.pop());
    EXPECT_EQ(q1.getSize(), 1);
    EXPECT_TRUE(q1.pop());
    EXPECT_EQ(q1.getSize(), 0);
    ASSERT_FALSE(q1.pop());
}

TEST_F(EventQTest, ReadEventQ){
    q1.push(4);
    q1.push(5);
    for(int i = 0; i < capacity; i++){
        EXPECT_EQ(q1.peek().eventword, i+1);
        q1.pop();
        ASSERT_EQ(q1.getSize(), capacity-i-1);
    }
}

TEST_F(EventQTest, Name){
    EXPECT_STREQ(q1.name(), "EventQ");
}