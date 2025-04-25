#include <gtest/gtest.h>
#include "lanetypes.hh"
#include "basim.hh"

using namespace basim;

class BASimTest : public ::testing::Test {
 protected:
    void SetUp() override {
        m.NumLanes = numlanes;
        m.NumNodes = 1;
        m.NumUDs = 1;
        m.NumStacks = 1;
        m.LocalMemAddrMode = 1;
        sim = BASim(m);
    }

    // void TearDown() override {}
    BASim sim;
    machine_t m;
    int numlanes = 2;
};

/** Testing small instruction memory program parsing opcodes*/
TEST_F(BASimTest, Init)
{
    sim.initMachine("testprogs/binaries/sendtest.bin", 0);
    sim.initMemoryArrays();
    
}

TEST_F(BASimTest, BasicEvent){
    sim.initMachine("testprogs/binaries/sendtest.bin", 0);
    sim.initMemoryArrays();
    
    // Setup initial events
    for(int i = 0; i < numlanes; i++){
        operands_t op0(2);
        op0.setDataWord(0, i);
        op0.setDataWord(1, i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(2);
        ev.setThreadID(0xFF);
        ev.setNWIDbits(i);
        eventoperands_t eops(&ev, &op0);
        networkid_t nwid = NetworkID(i);
        sim.pushEventOperands(nwid, eops);
    }

    // Launch simulation
    sim.simulate();
    bool status;
    // Check if all lanes are done
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            uint64_t val;
            sim.ud2t_memcpy(&val, 8, NetworkID(i), 0);
            status = status && (val == 1);
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    EXPECT_EQ(status, 1);
}

TEST_F(BASimTest, BasicMemStore){
    sim.initMachine("testprogs/binaries/sendmtest.bin", 0);
    sim.initMemoryArrays();
    
    word_t* memdata = new word_t[numlanes];
    printf("Addr of memdata:%lx\n", (uint64_t)memdata);
    // Setup initial events
    for(int i = 0; i < numlanes; i++){
        operands_t op0(2);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[i]));
        op0.setDataWord(1, i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(2);
        ev.setThreadID(0xFF);
        ev.setNWIDbits(i);
        eventoperands_t eops(&ev, &op0);
        networkid_t nwid = NetworkID(i);
        sim.pushEventOperands(nwid, eops);
    }

    // Launch simulation
    sim.simulate();
    bool status;
    // Check if all lanes are done
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            uint64_t val;
            sim.ud2t_memcpy(&val, 8, NetworkID(i), 0);
            status = status && (val == 1);
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    EXPECT_EQ(status, 1);
    for(int i = 0; i < numlanes; i++)
        EXPECT_EQ(memdata[i], 225+i);
}

TEST_F(BASimTest, BasicMemLoad){
    sim.initMachine("testprogs/binaries/sendmldtest.bin", 0);
    sim.initMemoryArrays();
    
    word_t* memdata = new word_t[numlanes*2];
    printf("Addr of memdata:%lx\n", (uint64_t)memdata);
    // Setup initial events
    for(int i = 0; i < numlanes; i++){
        memdata[2*i] = 225+ 2*i;
        memdata[2*i + 1] = 225+ 2*i + 1;
        operands_t op0(2);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[2*i]));
        op0.setDataWord(1, i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(2);
        ev.setThreadID(0xFF);
        ev.setNWIDbits(i);
        eventoperands_t eops(&ev, &op0);
        networkid_t nwid = NetworkID(i);
        sim.pushEventOperands(nwid, eops);
    }

    // Launch simulation
    sim.simulate();
    bool status;
    // Check if all lanes are done
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            uint64_t val;
            sim.ud2t_memcpy(&val, 8, NetworkID(i), 0);
            status = status && (val == 1);
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    EXPECT_EQ(status, 1);
    for(int i = 0; i < numlanes; i++){
        uint64_t val;
        sim.ud2t_memcpy(&val, 8, NetworkID(i), 8);
        EXPECT_EQ(val, 225+ 2*i);
    }
}

TEST_F(BASimTest, BasicSendOpsLane){
    sim.initMachine("testprogs/binaries/sendopstest.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(2);
        op0.setDataWord(0, i);
        op0.setDataWord(1, 255 + i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(2);
        ev.setThreadID(0xFF);
        ev.setNWIDbits(i);
        eventoperands_t eops(&ev, &op0);
        sim.pushEventOperands(nwid[i], eops);
    }

    // Launch simulation
    sim.simulate();
    bool status;
    // Check if all lanes are done
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            uint64_t val;
            sim.ud2t_memcpy(&val, 8, nwid[i], 0);
            status = status && (val == 1);
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    EXPECT_EQ(status, 1);
    for(int i = 0; i < numlanes; i++){
        uint64_t val;
        sim.ud2t_memcpy(&val, 8, nwid[i], 8);
        EXPECT_EQ(val, i);
        sim.ud2t_memcpy(&val, 8, nwid[i], 16);
        EXPECT_EQ(val, 255+i);
    }
}

TEST_F(BASimTest, BasicSendMopsLane){
    sim.initMachine("testprogs/binaries/sendmopstest.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes*2];
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(2);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[2*i]));
        op0.setDataWord(1, 255 + i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(2);
        ev.setThreadID(0xFF);
        ev.setNWIDbits(i);
        eventoperands_t eops(&ev, &op0);
        sim.pushEventOperands(nwid[i], eops);
    }

    // Launch simulation
    sim.simulate();
    bool status;
    // Check if all lanes are done
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            uint64_t val;
            sim.ud2t_memcpy(&val, 8, nwid[i], 0);
            status = status && (val == 1);
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    EXPECT_EQ(status, 1);
    for(int i = 0; i < numlanes; i++){
        EXPECT_EQ(memdata[2*i], reinterpret_cast<uint64_t>(&memdata[2*i]));
        EXPECT_EQ(memdata[2*i+1], 255+i);
    }
}
//
