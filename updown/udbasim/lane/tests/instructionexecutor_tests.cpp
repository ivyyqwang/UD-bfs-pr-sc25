#include <gtest/gtest.h>
#include "encodings.hh"
#include "opbuffer.hh"
#include "archstate.hh"
#include "inst_decode.hh"
#include "threadstate.hh"
#include "tstable.hh"
#include "eventq.hh"
#include "scratchpadbank.hh"
#include "instructionmemory.hh"

using namespace basim;

class InstructionExecutorTest : public ::testing::Test {
 protected:
    // Setup arch state
    // push data
    // execute instructions
    // Check

    /* Setup arch state for execution */ 
    void SetUp() override {
        // Add two threads to the thread state table
        // add these to the constructor
        uint32_t nwid = 0;
        instmem = new InstructionMemory(0);
        opbuff = new OpBuffer<operands_t>(); 
        eventq = new EventQ<eventword_t>();
        spd = new ScratchPad(1);
        tstable = new TSTable();
        lanestate = LaneState::NULLSTATE;

        // Add elements to a combined archstate for convenience in instruction execution
        archstate = new ArchState();
        archstate->instmem = instmem;
        archstate->opbuff = opbuff;
        archstate->eventq = eventq;
        archstate->spd = spd; 
        archstate->uip = uip; 
        archstate->lanestate = &lanestate;
        //
        cyclesRemaining = basim::Cycles(0);
        instCycles = basim::Cycles(0);

    }

    InstructionMemoryPtr instmem;
    OpBufferPtr opbuff;
    EventQPtr eventq;
    ScratchPadPtr spd;
    TSTablePtr tstable;
    ArchStatePtr archstate;
    lanestate_t lanestate;
    Addr uip;
    ThreadStatePtr ts;
    basim::Cycles cyclesRemaining;
    basim::Cycles instCycles;

    // Instruction/s under test
    EncInst inst;


};

/* Testing data structure accesses*/
TEST_F(InstructionExecutorTest, Basic) {
    ThreadStatePtr thread0;
    uint8_t tid0 = tstable->getTID();
    thread0 = new ThreadState(tid0, 0, 0, 0);
    tstable->addtoTST(thread0);
    archstate->threadstate = thread0; 
    archstate->lanestats = new LaneStats();
    inst = constrInstAddi(RegId::X16, RegId::X17, 10);
    thread0->writeReg(RegId::X16, 5);
    thread0->writeReg(RegId::X17, 10);
    Cycles cycle = decodeInst(inst).exe(*archstate, inst);
    //std::cout << "Cycles:" << cycle << std::endl;
    // read_reg() == reg + imm
    EXPECT_EQ(thread0->readReg(RegId::X17), 5+10);
    EXPECT_EQ(cycle, basim::Cycles(1));
    // Expect to be empty.
}
