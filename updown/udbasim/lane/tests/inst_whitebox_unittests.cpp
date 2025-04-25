#include "lanetypes.hh"
#include "types.hh"
#include "udlane.hh"
#include <gtest/gtest.h>

using namespace basim;

class InstLaneUnitTests : public ::testing::Test {
protected:
  size_t num_threads = 2; // 4*16 - 4 threads
    //void SetUp() override {
    //    lane0 = UDLane(0);
    //}

  // void TearDown() override {}
  UDLane lane0 = UDLane(0);

};

/* Testing Empty queue*/
TEST_F(InstLaneUnitTests, Init) {
  // Read in the program file
  lane0.initSetup(0, "testprogs/binaries/addi.bin", 0);
  // check Program Loading

  // Check Lane Initialization
}

//
TEST_F(InstLaneUnitTests, AddiBasic) {
  // Load Program into Instruction Memory
  lane0.initSetup(0, "testprogs/binaries/addi.bin", 0);

  // Setup basic Event and Operands to push into Lane
  uint8_t numop = 2;
  eventword_t ev0(0);
  ev0.setNumOperands(numop);
  operands_t op0(numop);
  word_t *data = new word_t[numop];
  for (auto i = 0; i < numop; i++)
    data[i] = i + 5;

  op0.setData(data);
  eventoperands_t eops(&ev0, &op0);
  lane0.pushEventOperands(eops);

  // Simulate until  done
  while (!lane0.isIdle())
    lane0.tick();
  EXPECT_TRUE(lane0.testReg(RegId::X17, 30));
  EXPECT_TRUE(lane0.testMem(0, 30));
  // Check state after a tick (uip, next_inst, threadState etc, reg value)
}