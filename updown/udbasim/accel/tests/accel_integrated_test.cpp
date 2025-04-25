#include "lanetypes.hh"
#include "types.hh"
#include "udaccelerator.hh"
#include "udlane.hh"
#include <gtest/gtest.h>

using namespace basim;

class AcceleratorTest : public ::testing::Test {
protected:
  size_t num_threads = 2; // 4*16 - 4 threads
  // void SetUp() override {
  //     //lane0 = UDAccelerator(0);
  // }

  // void TearDown() override {}
  int numLanes = 2;
  UDAccelerator acc0 = UDAccelerator(numLanes, 0, 1);
  int buffsize1 = 1024;
  int buffsize2 = 1024;
};

/* Testing Empty queue*/
TEST_F(AcceleratorTest, Init) {
  // Read in the program file
  acc0.initSetup(0, "testprogs/binaries/addi.bin", 0);
  // check Program Loading

  // Check Accelerator Initialization
}

/** Testing Size of Accelerator if used */
TEST_F(AcceleratorTest, PushEvents) {
  int numop = 2;
  eventword_t ev0(0);
  ev0.setNumOperands(numop);
  operands_t op0(numop);
  word_t *data = new word_t[numop];
  for (auto i = 0; i < numop; i++)
    data[i] = i + 5;

  op0.setData(data);
  eventoperands_t eops(&ev0, &op0);
  // into lane 0
  acc0.pushEventOperands(eops, 0);
  // into lane 1
  acc0.pushEventOperands(eops, 1);
  EXPECT_EQ(acc0.getEventQSize(0), 1);
  EXPECT_EQ(acc0.getEventQSize(1), 1);
  EXPECT_FALSE(acc0.isIdle());
}
//
TEST_F(AcceleratorTest, SingleTick) {
  acc0.initSetup(0, "testprogs/binaries/addi.bin", 0);
  int numop = 2;
  eventword_t ev0(0);
  ev0.setNumOperands(numop);
  operands_t op0(numop);
  word_t *data = new word_t[numop];
  for (auto i = 0; i < numop; i++)
    data[i] = i + 5;

  op0.setData(data);
  eventoperands_t eops(&ev0, &op0);
  acc0.pushEventOperands(eops, 0);
  acc0.pushEventOperands(eops, 1);
  acc0.simulate(1);
  // Check state after a tick (uip, next_inst, threadState etc, reg value)
}

TEST_F(AcceleratorTest, AddiBasicAccel) {
  acc0.initSetup(0, "testprogs/binaries/addi.bin", 0);
  int numop = 2;
  eventword_t ev0(0);
  ev0.setNumOperands(numop);
  operands_t op0(numop);
  word_t *data = new word_t[numop];
  for (auto i = 0; i < numop; i++)
    data[i] = i + 5;

  op0.setData(data);
  eventoperands_t eops(&ev0, &op0);
  acc0.pushEventOperands(eops, 0);
  acc0.pushEventOperands(eops, 1);
  while(!acc0.isIdle()){
    acc0.simulate(1);
  }
}

TEST_F(AcceleratorTest, AddiBasicSimulate) {
  acc0.initSetup(0, "testprogs/binaries/addi.bin", 0);
  int numop = 2;
  eventword_t ev0(0);
  ev0.setNumOperands(numop);
  operands_t op0(numop);
  word_t *data = new word_t[numop];
  for (auto i = 0; i < numop; i++)
    data[i] = i + 5;

  op0.setData(data);
  eventoperands_t eops(&ev0, &op0);
  acc0.pushEventOperands(eops, 0);
  acc0.pushEventOperands(eops, 1);
  while(!acc0.isIdle()){
    acc0.simulate(1);
  }
}

TEST_F(AcceleratorTest, AddiBasicSimulateNumTicks) {
  // Below can be common for almost all tests
  uint64_t* sendbuff1 = (uint64_t *)malloc(sizeof(uint64_t)*buffsize1);
  uint64_t* sendbuff2 = (uint64_t *)malloc(sizeof(uint64_t)*buffsize2);
  acc0.initSetup(0, "testprogs/binaries/addi.bin", 0);
  int numop = 2;
  eventword_t ev0(0);
  ev0.setNumOperands(numop);
  operands_t op0(numop);
  word_t *data = new word_t[numop];
  data[0] = reinterpret_cast<word_t>(sendbuff1);
  data[1] = reinterpret_cast<word_t>(sendbuff2);

  op0.setData(data);
  eventoperands_t eops(&ev0, &op0);
  for(auto i = 0; i < numLanes; i++)
    acc0.pushEventOperands(eops, i);

  while(!acc0.isIdle()){
    acc0.simulate(2);
  }

  // Checks specific for tests being written
  for(auto i = 0; i < numLanes; i++){
    EXPECT_TRUE(acc0.testReg(0, RegId::X17, 30));
    EXPECT_TRUE(acc0.testMem(i << 16, 30));
  }
}

