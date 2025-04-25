#include <gtest/gtest.h>
#include "udlane.hh"
#include "types.hh"
#include "lanetypes.hh"

using namespace basim;

class LaneTest : public ::testing::Test {
 protected:
    size_t num_threads = 2; // 4*16 - 4 threads
    //void SetUp() override {
    //    //lane0 = UDLane(0);
    //}

    // void TearDown() override {}
    UDLane lane0 = UDLane(0);
};

/* Testing Empty queue*/
TEST_F(LaneTest, Init) {
    // Read in the program file
    lane0.initSetup(0,"testprogs/binaries/addi.bin", 0);
    // check Program Loading 

    // Check Lane Initialization
}

/** Testing Size of Lane if used */
TEST_F(LaneTest, PushEvents)
{
    int numop = 2;
    eventword_t ev0(0);
    ev0.setNumOperands(numop);
    operands_t op0(numop);
    word_t* data = new word_t[numop];
    for(auto i = 0; i < numop; i++)
        data[i] = i+5;
    
    op0.setData(data);
    eventoperands_t eops(&ev0, &op0);
    lane0.pushEventOperands(eops);
    EXPECT_EQ(lane0.getEventQSize(), 1);
    EXPECT_FALSE(lane0.isIdle());
}
//
TEST_F(LaneTest, SingleTick){
    lane0.initSetup(0,"testprogs/binaries/addi.bin", 0);
    int numop = 2;
    eventword_t ev0(0);
    ev0.setNumOperands(numop);
    operands_t op0(numop);
    word_t* data = new word_t[numop];
    for(auto i = 0; i < numop; i++)
        data[i] = i+5;
    
    op0.setData(data);
    eventoperands_t eops(&ev0, &op0);
    lane0.pushEventOperands(eops);
    lane0.tick();
    // Check state after a tick (uip, next_inst, threadState etc, reg value)

}

TEST_F(LaneTest, MultipleTick){
    int numop = 2;
    eventword_t ev0(0);
    ev0.setNumOperands(numop);
    operands_t op0(numop);
    word_t* data = new word_t[numop];
    for(auto i = 0; i < numop; i++)
        data[i] = i+5;
    
    op0.setData(data);
    eventoperands_t eops(&ev0, &op0);
    lane0.pushEventOperands(eops);
    lane0.tick();
    lane0.tick();

}