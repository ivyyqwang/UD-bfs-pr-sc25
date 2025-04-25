#include <gtest/gtest.h>
#include "threadstate.hh"
#include "types.hh"

using namespace basim;

class ThreadStateTest : public ::testing::Test {
 protected:
    size_t num_threads = 4; // 4*16 - 4 threads
    void SetUp() override {
        ts = new ThreadState(0, 0, 0, 0);
    }

    // void TearDown() override {}
    ThreadStatePtr ts;
};

/* Testing Empty queue*/
TEST_F(ThreadStateTest, Init) {
    // Register file should be initialized to 0
    for(int i = 16; i < NUM_GPRS; i++) {
        EXPECT_EQ(ts->readReg(static_cast<RegId>(i)), 0);
    }
}

/** Testing Size of ThreadState if used */
TEST_F(ThreadStateTest, UnsignedIntRW)
{
    for(int i = 16; i < NUM_GPRS; i++) {
        ts->writeReg(static_cast<RegId>(i), 1UL << ((i+1)*4 - 1));
    }
    for(int i = 16; i < NUM_GPRS; i++) {
        EXPECT_EQ(ts->readReg(static_cast<RegId>(i)), 1UL << ((i+1)*4 - 1));
    }
}