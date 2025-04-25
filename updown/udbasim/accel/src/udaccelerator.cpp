#include "udaccelerator.hh"
#include "types.hh"
#include "lanetypes.hh"
#include "fstream"
#include <cstdio>

namespace basim
{   
    UDAccelerator::UDAccelerator(int _numLanes, uint32_t udid, int lmMode, uint64_t inter_node_latency): numLanes(_numLanes), lmMode(lmMode){
        spd = new ScratchPad(numLanes);
        this->_inter_node_latency = inter_node_latency;
        this->curTimeStamp = 0;
        this->udid = udid;
        for(auto i = 0; i < _numLanes; i++){
            uint32_t nwid = (udid & 0XFFFFFFC0 ) | (i & 0x3F);
            UDLanePtr lane = new UDLane(nwid, spd);
            udLanes.push_back(lane);
        }
        this->udstats = new UDStats();
    }

    /*  Should reflect Boot sequence - setting up base addresses, translations etc.  */
    void UDAccelerator::initSetup(Addr _pgbase, std::string progfile, Addr _lmbase){
        initSetup(_pgbase, progfile, _lmbase, 1);
    }

    void UDAccelerator::initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, int _num_uds){
        scratchpadBase = _lmbase;
        scratchpadSize = SCRATCHPAD_SIZE;
        spd->setBase(_lmbase);
        // Initialize Translation Memory
        transmem = new TranslationMemory(udid, _num_uds, _lmbase);
        instmem = new InstructionMemory();
        instmem->loadProgBinary(progfile);
        BASIM_INFOMSG("Translation Memory %p initialized with %d updowns on updown %d\n", transmem, _num_uds, udid);
        // Initialize all the lanes - need to add perflog, logging file etc
        for(auto i = 0; i < numLanes; i++){
            udLanes[i]->initSetup(_pgbase, instmem, _lmbase, transmem, lmMode);
        }
    }
    
    void UDAccelerator::initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, int _num_uds, uint64_t nnodes){
        scratchpadBase = _lmbase;
        scratchpadSize = SCRATCHPAD_SIZE;
        spd->setBase(_lmbase);
        // Initialize Translation Memory
        transmem = new TranslationMemory(udid, _num_uds, _lmbase, nnodes);
        instmem = new InstructionMemory();
        instmem->loadProgBinary(progfile);
        BASIM_INFOMSG("Translation Memory %p initialized with %d updowns on updown %d\n", transmem, _num_uds, udid);
        // Initialize all the lanes - need to add perflog, logging file etc
        for(auto i = 0; i < numLanes; i++){
            udLanes[i]->initSetup(_pgbase, instmem, _lmbase, transmem, lmMode);
        }
    }

    size_t UDAccelerator::getEventQSize(int laneid){
        return (udLanes[laneid]->getEventQSize());
    }

    bool UDAccelerator::isIdle(){
        // Check idle condition on all lanes
        bool idle = this->_remote_message_time_stamp.empty();
        for(auto i = 0; i < numLanes; i++){
            idle = idle && udLanes[i]->isIdle();
        }
        return idle;
    }

    bool UDAccelerator::isIdle(uint32_t laneID){
        return udLanes[laneID]->isIdle();
    }

    bool UDAccelerator::pushEventOperands(eventoperands_t eop, uint32_t laneid){
        bool result = udLanes[laneid]->pushEventOperands(eop);
        if(!(result)) {
           BASIM_ERROR("Push into UD:%d Lane:%d EventQ failed\n", udid, laneid);
        }
        return true;
    }
    
    /* write data into the scratchpad */
    void UDAccelerator::writeScratchPad(int size, Addr addr, uint8_t* data){
        // implement this for all data sizes before release
        spd->writeBytes(size, addr, data);
    }
    
    /* read data from the scratchpad */
    //word_t UDAccelerator::readScratchPad(Addr addr){
    void UDAccelerator::readScratchPad(int size, Addr addr, uint8_t* data){
        //int laneid = (addr - scratchpadBase) / SCRATCHPAD_SIZE;
        // @todo implement all other sizes
        spd->readBytes(size, addr, data);
    }

    void UDAccelerator::readScratchPadBank(uint8_t laneid, uint8_t* data){
        spd->readScratchpadBank(laneid, data);
    }
    
    /* Pointer to all scratchpad data */
    void UDAccelerator::readAllScratchPad(uint8_t* data){
        spd->readAllScratchpad(data);
    }

    void UDAccelerator::writeScratchPadBank(uint8_t laneid, const uint8_t* data){
        spd->writeScratchpadBank(laneid, data);
    }
  
    /* Pointer to all scratchpad data */
    void UDAccelerator::writeAllScratchPad(const uint8_t* data){
        spd->writeAllScratchpad(data);
    }

    void UDAccelerator::tick(uint64_t timestamp){
        // iterate through the vector of lanes
        for(auto ln = udLanes.begin(); ln != udLanes.end(); ++ln){
            (*ln)->tick(timestamp);
        }
    }

    void UDAccelerator::tock(uint64_t timestamp){
        this->curTimeStamp += timestamp;
    }

    void UDAccelerator::pushDelayedMessage(std::unique_ptr<MMessage> m) {
        this->_remote_message.push(std::move(m));
        this->_remote_message_time_stamp.push(this->curTimeStamp);
    }

    uint64_t UDAccelerator::DelayedMessageLen() {
        return this->_remote_message.size();
    }

    std::unique_ptr<MMessage> UDAccelerator::popDelayedMessage() {
        std::unique_ptr<MMessage> m;
        if(!(this->_remote_message_time_stamp.empty()) && (this->_remote_message_time_stamp.front() + this->_inter_node_latency <= this->curTimeStamp)){
            m = std::move(this->_remote_message.front());
            this->_remote_message.pop();
            this->_remote_message_time_stamp.pop();
        } else {
            m.reset();
        }
        return m;
    }
    
    bool UDAccelerator::sendReady(uint32_t laneid){
        return udLanes[laneid]->sendReady();
    }

    std::unique_ptr<MMessage> UDAccelerator::getSendMessage(int laneid){
        return udLanes[laneid]->peekSendBuffer();
    }
    
    void UDAccelerator::removeSendMessage(int laneid){
        return udLanes[laneid]->popSendBuffer();
    }

    /* simulate API for accelerator runs through all lanes */
    void UDAccelerator::simulate(uint64_t numTicks, uint64_t timestamp){
        int simTicks = 0;
        while(simTicks < numTicks){
            for(auto ln = udLanes.begin(); ln != udLanes.end(); ++ln){
                if(!(*ln)->isIdle())
                    (*ln)->tick(timestamp);
            }
            simTicks++;
        }

    }

    int UDAccelerator::getLanebyPolicy(int laneid, uint8_t policy){
        if(policy == 0){
          return laneid;
        }
        int start_ln = 0;
        int end_ln = 63;
        int ln_choose = laneid;
        int q_size;
        switch(policy){
            case 1:
                start_ln = 0;
                end_ln = 64;
                q_size = MAX_Q_SIZE;
            break;
            case 2:
                start_ln = 0;
                end_ln = 32;
                q_size = MAX_Q_SIZE;
            break;
            case 3:
                start_ln = 32;
                end_ln = 64;
                q_size = MAX_Q_SIZE;
            break;
            case 4:
                start_ln = 0;
                end_ln = 32;
                q_size = 0;
            break;
            case 5:
                start_ln = 32;
                end_ln = 64;
                q_size = 0;
            break;
            case 6:
                start_ln = 0;
                end_ln = 64;
                q_size = 0;
            break;
            default:
                return laneid;
            break;
        }
        if(policy < 4){
            for(int ln = start_ln; ln < end_ln; ln++){
                if(udLanes[ln]->getEventQSize() == 0){
                    ln_choose = ln;
                    break;
                }
                if(udLanes[ln]->getEventQSize() < q_size){
                    q_size = udLanes[ln]->getEventQSize();
                    ln_choose = ln;
                }
            }
        }else{
            for(int ln = start_ln; ln < end_ln; ln++){
                if(udLanes[ln]->getEventQSize() > q_size){
                    q_size = udLanes[ln]->getEventQSize();
                    ln_choose = ln;
                }
            }
        }
        return ln_choose;
    }
    
    /* Simulate API to call per lane */
    void UDAccelerator::simulate(uint32_t laneID, uint64_t numTicks, uint64_t timestamp){
        int simTicks = 0;
        while(simTicks < numTicks){
            udLanes[laneID]->tick(timestamp);
            simTicks++;
        }
    }

    void UDAccelerator::resetStats(){
        for (auto &ln :udLanes){
            ln->resetStats();
        }
    }

    UDAccelerator::~UDAccelerator(){
      for (auto &ln : udLanes) {
        delete ln;
      }
      delete spd;
      delete udstats;
      delete transmem;
      delete instmem;
    }
    
}//basim
