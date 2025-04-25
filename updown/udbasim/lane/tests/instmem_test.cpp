#include <gtest/gtest.h>
#include "encodings.hh"
#include "types.hh"
#include "instructionmemory.hh"

using namespace basim;

class InstructionMemoryTest : public ::testing::Test {
 protected:
    void SetUp() override {
        instmem = InstructionMemory(0);
    }

    // void TearDown() override {}
    InstructionMemory instmem;
};

/* Testing InstructionMemory Loading*/
TEST_F(InstructionMemoryTest, LoadProg) {
    instmem.loadProgBinary("testprogs/binaries/addi.bin");
    EncInst inst = instmem.getNextInst(0);
}

/** Testing small instruction memory program parsing opcodes*/
TEST_F(InstructionMemoryTest, ProgParse)
{
    instmem.loadProgBinary("testprogs/binaries/addi.bin");
    Addr uip = instmem.getPGBase();
    EncInst inst = instmem.getNextInst(uip);
    EXPECT_TRUE(extrTransType(inst) == TransitionType::EVENTCARRY);
    uip+=(extrInstEventtrAttach(inst) << 2);
    inst = instmem.getNextInst(uip);
    EXPECT_TRUE(extrInstOpcode(inst) == Opcode::MOVIR);
    uip+=4;
    inst = instmem.getNextInst(uip);
    EXPECT_TRUE(extrInstOpcode(inst) == Opcode::ADDI);
    uip+=4;
    inst = instmem.getNextInst(uip);
    EXPECT_TRUE(extrInstOpcode(inst) == Opcode::ADDI);
    uip+=4;
    inst = instmem.getNextInst(uip);
    EXPECT_TRUE(extrInstOpcode(inst) == Opcode::MOVRL);
    uip+=4;
    inst = instmem.getNextInst(uip);
    EXPECT_TRUE(extrInstOpcode(inst) == Opcode::YIELDT);
    uip+=4;
}
//
