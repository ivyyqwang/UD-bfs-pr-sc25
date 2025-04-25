#include "basim.hh"
#include "mmessage.hh"
#include "types.hh"
#include "lanetypes.hh"

namespace basim
{
// Memory Space similar to what is available with UDRuntime for testing purposes
void BASim::initMemoryArrays(){
    // Initializing arrays containning mapped memory
    BASIM_INFOMSG("Allocating %lu bytes for mapped memory",
                   this->machine.MapMemSize);
    MappedMemory = new uint8_t[this->machine.MapMemSize];
    // Changing the base locations for the simulated memory regions
    this->machine.MapMemBase = reinterpret_cast<uint64_t>(MappedMemory);
    BASIM_INFOMSG("MapMemBase changed to 0x%lX", this->machine.MapMemBase);
    // ReInit Memory Manager with new machine configuration
    reset_memory_manager();
}

// Init Machine (all the updowns with the right address mapping)
void BASim::initMachine(std::string progfile, Addr _pgbase){
    globalTick = 0;
    for(auto i = 0; i < uds.size(); i++){
        Addr spBase = (i * this->machine.NumLanes * this->machine.SPBankSize); 
        uds[i]->initSetup(_pgbase, progfile, spBase, numuds);
    }
}

void BASim::pushEventOperands(networkid_t nwid, eventoperands_t eops){
    int udnum = getUDIdx(nwid, this->machine);
    uds[udnum]->pushEventOperands(eops, nwid.getLaneID());
}

// read scratchpad 
void BASim::t2ud_memcpy(void *data, uint64_t size, networkid_t nwid,
                        uint32_t offset){
    Addr addr = getSPAddr(nwid, offset);
    int udnum = getUDIdx(nwid, this->machine);
    uint8_t* data_ptr = reinterpret_cast<uint8_t *>(data);
    for (int i = 0; i < size / sizeof(word_t); i++) {
      // Address is local
      uds[udnum]->writeScratchPad(sizeof(word_t), addr, data_ptr);
      addr += sizeof(word_t);
      data_ptr += sizeof(word_t);
    } 
}
// write scratchpad 
void BASim::ud2t_memcpy(void *data, uint64_t size, networkid_t nwid,
                        uint32_t offset){
    Addr addr = getSPAddr(nwid, offset);
    int udnum = getUDIdx(nwid, this->machine);
    uds[udnum]->readScratchPad(size, addr, reinterpret_cast<uint8_t*>(data));
}

// Similar to 
void BASim::simulate(int numTicks){
  bool something_exec;
  uint64_t num_iterations = 0;
  do {
        something_exec = false;
        for (int ud = 0; ud < numuds; ud++) {
            if (!uds[ud]->isIdle()) {
                something_exec = true;
                uds[ud]->simulate(numTicks);
                postTick(NetworkID(ud));
            }
        }
        globalTick += (numTicks * period); // advance by clock cycles

    }while (something_exec &&
           (!max_sim_cycles || ++num_iterations < max_sim_cycles));
}

// Post simulating the pipeline, deal with send related tasks!
void BASim::postTick(networkid_t nwid){
    // Cycle through the send buffers of each lane in the UDs
    int udid = nwid.getUDID();
    for(int i = 0; i < this->machine.NumLanes; i++){
        if(uds[udid]->sendReady(i)){
            std::unique_ptr<MMessage> m(std::move(uds[udid]->getSendMessage(i)));
            switch(m->getType()){
                case MType::M1Type:{ 
                    // Send Message to another lane
                    eventword_t ev = m->getXe();
                    operands_t op0(m->getLen(), m->getXc());  // num opernads + cont
                    op0.setData((m->getpayload()));
                    eventoperands_t eops(&ev, &op0);
                    int ud = getUDIdx(ev.getNWID(), this->machine);
                    uds[ud]->pushEventOperands(eops, (ev.getNWID()).getLaneID());
                    break;
                }
                case (MType::M2Type):{
                    // Send to Memory
                    //eventword_t cont = m->getXc();
                    eventword_t* cont = new EventWord();
                    *cont = m->getXc();
                    if(m->isStore()){ 
                        // Writes to memory
                        word_t* dataptr = (m->getpayload()); // get the data and store it in memory
                        word_t* dst = reinterpret_cast<word_t*>(m->getdestaddr());
                        std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
                        // Post store event push
                        uint64_t noupdate_cont = 0x7fffffffffffffff;
                        operands_t op0(2, EventWord(noupdate_cont));  // num opernads + cont
                        op0.setDataWord(0, m->getdestaddr());
                        op0.setDataWord(1, m->getdestaddr());
                        eventoperands_t eops(cont, &op0);
                        int ud = getUDIdx(cont->getNWID(), this->machine);
                        uds[ud]->pushEventOperands(eops, (cont->getNWID()).getLaneID());
                    }else{
                        // Reads from memory
                        word_t* dataptr = reinterpret_cast<word_t*>(m->getdestaddr());
                        word_t* dst = new word_t[m->getLen()];
                        std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
                        uint64_t noupdate_cont = 0x7fffffffffffffff;
                        operands_t op0(m->getLen()+1, EventWord(noupdate_cont));  // num opernads + cont
                        op0.setData(dst);
                        op0.setDataWord(m->getLen(), m->getdestaddr());
                        eventoperands_t eops(cont, &op0);
                        int ud = getUDIdx(cont->getNWID(), this->machine);
                        uds[ud]->pushEventOperands(eops, (cont->getNWID()).getLaneID());
                    }
                    break;
                }
                case (MType::M3Type):{
                    // Send Message to another lane
                    eventword_t ev = m->getXe();
                    operands_t op0(m->getLen(), m->getXc());  // num opernads + cont
                    op0.setData((m->getpayload()));
                    eventoperands_t eops(&ev, &op0);
                    int ud = getUDIdx(ev.getNWID(), this->machine);
                    uds[ud]->pushEventOperands(eops, (ev.getNWID()).getLaneID());
                    break;
                }
                case (MType::M3Type_M):{
                    // Always a store (2 words)
                    BASIM_INFOMSG("PostTick:M3Type_M");
                    eventword_t cont = m->getXc();
                    BASIM_INFOMSG("Continuation Label: %d", cont.getEventLabel());
                    // Writes to memory
                    word_t* dataptr = (m->getpayload()); // get the data and store it in memory
                    word_t* dst = reinterpret_cast<word_t*>(m->getdestaddr());
                    std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
                    // Post store event push
                    uint64_t noupdate_cont = 0x7fffffffffffffff;
                    operands_t op0(2, EventWord(noupdate_cont));  // num opernads + cont
                    op0.setDataWord(0, m->getdestaddr());
                    op0.setDataWord(1, m->getdestaddr());
                    eventoperands_t eops(&cont, &op0);
                    int ud = getUDIdx(cont.getNWID(), this->machine);
                    uds[ud]->pushEventOperands(eops, (cont.getNWID()).getLaneID());
                    break;
                }
                case (MType::M4Type):{
                    // Send Message to another lane 
                    // Merge this with M3Type
                    eventword_t ev = m->getXe();
                    operands_t op0(m->getLen(), m->getXc());  // num opernads + cont
                    op0.setData((m->getpayload()));
                    eventoperands_t eops(&ev, &op0);
                    int ud = getUDIdx(ev.getNWID(), this->machine);
                    uds[ud]->pushEventOperands(eops, (ev.getNWID()).getLaneID());
                    break;
                }
                case (MType::M4Type_M):{
                    // Always a store (2 words)
                    // Merge this with M3Type_M
                    eventword_t cont = m->getXc();
                    // Writes to memory
                    word_t* dataptr = (m->getpayload()); // get the data and store it in memory
                    word_t* dst = reinterpret_cast<word_t*>(m->getdestaddr());
                    std::memcpy(dst, dataptr, m->getLen()*WORDSIZE);
                    // Post store event push
                    uint64_t noupdate_cont = 0x7fffffffffffffff;
                    operands_t op0(2, EventWord(noupdate_cont));  // num opernads + cont
                    op0.setDataWord(0, m->getdestaddr());
                    op0.setDataWord(1, m->getdestaddr());
                    eventoperands_t eops(&cont, &op0);
                    int ud = getUDIdx(cont.getNWID(), this->machine);
                    uds[ud]->pushEventOperands(eops, (cont.getNWID()).getLaneID());
                    break;
                }
                default:{
                    BASIM_ERROR("Undefined Message type in Send Buffer");
                    break;
                }
            }
            //uds[udid]->removeSendMessage(i);
        }
    }
}


// Test API
/* testing api returns value from register of whatever thread is currently active */
bool BASim::testReg(networkid_t nwid, RegId raddr, word_t val){
    int udnum = getUDIdx(nwid, this->machine);
    return(uds[udnum]->testReg(nwid.getLaneID(), raddr, val));
}

/* testing api returns value from scratchpad memory */
bool BASim::testSPMem(networkid_t nwid, Addr addr, word_t val){
    int udnum = getUDIdx(nwid, this->machine);
    return(uds[udnum]->testMem(addr, val));
}

/* testing api that tests val against value in Mapped memory */
bool BASim::testDRMem(Addr addr, word_t val){
    BASIM_INFOMSG("Yet to implement");
    return true;
}


}//basim
