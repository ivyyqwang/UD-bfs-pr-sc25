#include <gtest/gtest.h>
#include "lanetypes.hh"
#include "basim.hh"

using namespace basim;

class PseudoTest : public ::testing::Test {
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
TEST_F(PseudoTest, Init)
{
    sim.initMachine("testprogs/binaries/send_lm_pseudo_ret.bin", 0);
    sim.initMachine("testprogs/binaries/send_lm_pseudo.bin", 0);
    sim.initMachine("testprogs/binaries/sendm_pseudo_ret.bin", 0);
    sim.initMachine("testprogs/binaries/sendm_pseudo.bin", 0);
    sim.initMachine("testprogs/binaries/sendmr_pseudo_ret.bin", 0);
    sim.initMachine("testprogs/binaries/sendmr_pseudo.bin", 0);
    sim.initMachine("testprogs/binaries/sendmr2_pseudo_ret.bin", 0);
    sim.initMachine("testprogs/binaries/sendmr2_pseudo.bin", 0);
    sim.initMachine("testprogs/binaries/sendr_pseudo.bin", 0);
    sim.initMachine("testprogs/binaries/sendr_pseudo_ret.bin", 0);
    sim.initMachine("testprogs/binaries/sendr3_pseudo.bin", 0);
    sim.initMachine("testprogs/binaries/sendr3_pseudo_ret.bin", 0);
    
}

TEST_F(PseudoTest, Send_LM){
    sim.initMachine("testprogs/binaries/send_lm_pseudo.bin", 0);
    sim.initMemoryArrays();
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes];
    printf("Addr of memdata:%lx\n", (uint64_t)memdata);
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
    uint64_t* val = new uint64_t[numlanes];
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            sim.ud2t_memcpy(&val[i], 8, NetworkID(i), 0);
            status = status && ((val[i] == 1) || (val[i] == 2));
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    for(int i = 0; i < numlanes; i++)
        EXPECT_EQ(val[i], 1);
}

TEST_F(PseudoTest, Send_LM_Wret){
    sim.initMachine("testprogs/binaries/send_lm_pseudo_ret.bin", 0);
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
    uint64_t* val = new uint64_t[numlanes];
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            sim.ud2t_memcpy(&val[i], 8, NetworkID(i), 0);
            status = status && ((val[i] == 1) || (val[i] == 2));
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    for(int i = 0; i < numlanes; i++)
        EXPECT_EQ(val[i], 1);
}

TEST_F(PseudoTest, Sendr3_Pseudo){
    sim.initMachine("testprogs/binaries/sendr3_pseudo.bin", 0);
    sim.initMemoryArrays();
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes];
    printf("Addr of memdata:%lx\n", (uint64_t)memdata);
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
    uint64_t* val = new uint64_t[numlanes];
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            sim.ud2t_memcpy(&val[i], 8, NetworkID(i), 0);
            status = status && ((val[i] == 1) || (val[i] == 2));
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    for(int i = 0; i < numlanes; i++)
        EXPECT_EQ(val[i], 1);
}

TEST_F(PseudoTest, Sendr3_Pseudo_ret){
    sim.initMachine("testprogs/binaries/sendr3_pseudo_ret.bin", 0);
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
    uint64_t* val = new uint64_t[numlanes];
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            sim.ud2t_memcpy(&val[i], 8, NetworkID(i), 0);
            status = status && ((val[i] == 1) || (val[i] == 2));
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    for(int i = 0; i < numlanes; i++)
        EXPECT_EQ(val[i], 1);
}

TEST_F(PseudoTest, Sendr_Pseudo){
    sim.initMachine("testprogs/binaries/sendr_pseudo.bin", 0);
    sim.initMemoryArrays();
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes];
    printf("Addr of memdata:%lx\n", (uint64_t)memdata);
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
    uint64_t* val = new uint64_t[numlanes];
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            sim.ud2t_memcpy(&val[i], 8, NetworkID(i), 0);
            status = status && ((val[i] == 1) || (val[i] == 2));
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    for(int i = 0; i < numlanes; i++)
        EXPECT_EQ(val[i], 1);
}

TEST_F(PseudoTest, Sendr_Pseudo_ret){
    sim.initMachine("testprogs/binaries/sendr_pseudo_ret.bin", 0);
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
    uint64_t* val = new uint64_t[numlanes];
    while(1){
        status = true;
        for(int i = 0; i < numlanes; i++){
            sim.ud2t_memcpy(&val[i], 8, NetworkID(i), 0);
            status = status && ((val[i] == 1) || (val[i] == 2));
        }
        if(status)
            break;
    }
    printf("Total Sim Cycles :%ld\n", sim.getCurTick());
    for(int i = 0; i < numlanes; i++)
        EXPECT_EQ(val[i], 1);
}

TEST_F(PseudoTest, Sendmr2_Pseudo){
    sim.initMachine("testprogs/binaries/sendmr2_pseudo.bin", 0);
    sim.initMemoryArrays();
    
    word_t* memdata = new word_t[numlanes];
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
        EXPECT_EQ(val, 225+ i);
    }
}

TEST_F(PseudoTest, Sendmr2_Pseudo_Ret){
    sim.initMachine("testprogs/binaries/sendmr2_pseudo_ret.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes];
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(2);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[i]));
        op0.setDataWord(1, i);
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
        EXPECT_EQ(val, 225+i);
    }
}

TEST_F(PseudoTest, Sendmr_Pseudo){
    sim.initMachine("testprogs/binaries/sendmr_pseudo.bin", 0);
    sim.initMemoryArrays();
    
    word_t* memdata = new word_t[numlanes];
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
        EXPECT_EQ(val, 225+ i);
    }
}

TEST_F(PseudoTest, Sendmr_Pseudo_Ret){
    sim.initMachine("testprogs/binaries/sendmr_pseudo_ret.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes];
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(2);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[i]));
        op0.setDataWord(1, i);
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
        EXPECT_EQ(val, 225+i);
    }
}

TEST_F(PseudoTest, Sendm_Pseudo_Ret){
    sim.initMachine("testprogs/binaries/sendm_pseudo_ret.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes];
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(2);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[i]));
        op0.setDataWord(1, i);
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
        EXPECT_EQ(val, 225+i);
    }
}

TEST_F(PseudoTest, Sendm_Pseudo){
    sim.initMachine("testprogs/binaries/sendm_pseudo.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    word_t* memdata = new word_t[numlanes];
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(2);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[i]));
        op0.setDataWord(1, i);
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
        EXPECT_EQ(val, 225+i);
    }
}

TEST_F(PseudoTest, SendOps_Pseudo){
    sim.initMachine("testprogs/binaries/sendops_pseudo.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(4);
        op0.setDataWord(0, i);
        op0.setDataWord(1, 2*i);
        op0.setDataWord(2, 3*i);
        op0.setDataWord(3, 4*i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(4);
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
    EXPECT_EQ(status, 1);
    for(int i = 0; i < numlanes; i++){
        uint64_t val;
        sim.ud2t_memcpy(&val, 8, nwid[i], 8);
        EXPECT_EQ(val, 10*i);
    }
}

TEST_F(PseudoTest, SendOps_wret_Pseudo){
    sim.initMachine("testprogs/binaries/sendops_pseudo_ret.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(4);
        op0.setDataWord(0, i);
        op0.setDataWord(1, 2*i);
        op0.setDataWord(2, 3*i);
        op0.setDataWord(3, 4*i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(4);
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
    EXPECT_EQ(status, 1);
    for(int i = 0; i < numlanes; i++){
        uint64_t val;
        sim.ud2t_memcpy(&val, 8, nwid[i], 8);
        EXPECT_EQ(val, 10*i);
    }
}

TEST_F(PseudoTest, SendMOps_wret_Pseudo){
    sim.initMachine("testprogs/binaries/sendmops_pseudo.bin", 0);
    sim.initMemoryArrays();
    networkid_t* nwid = new networkid_t[numlanes];
    
    // Setup initial events
    word_t* memdata = new word_t[4*numlanes];
    for(int i = 0; i < numlanes; i++){
        nwid[i] = NetworkID(i);
        operands_t op0(5);
        op0.setDataWord(0, reinterpret_cast<uint64_t>(&memdata[4*i]));
        op0.setDataWord(1, i);
        op0.setDataWord(2, 2*i);
        op0.setDataWord(3, 3*i);
        op0.setDataWord(4, 4*i);
        eventword_t ev = EventWord(0);
        ev.setNumOperands(5);
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
    EXPECT_EQ(status, 1);
    for(int i = 0; i < numlanes; i++){
        EXPECT_EQ(i, memdata[4*i]);
        EXPECT_EQ(2*i, memdata[4*i+1]);
        EXPECT_EQ(3*i, memdata[4*i+2]);
        EXPECT_EQ(4*i, memdata[4*i+3]);
    }
}

