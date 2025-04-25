/**
**********************************************************************************************************************************************************************************************************************************
* @file:	udlane.hh
* @author:	Andronicus
* @date:	
* @brief:   Class definition for UpDown Lane	
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __UDLANE__H__
#define __UDLANE__H__
#include <iostream>
#include "types.hh"
#include "lanetypes.hh"
#include "instructionmemory.hh"
#include "eventq.hh"
#include "opbuffer.hh"
#include "tickobject.hh"
#include "scratchpadbank.hh"
#include "threadstate.hh"
#include "tstable.hh"
#include "archstate.hh"
#include <arpa/inet.h>
#include "buffer.hh"
#include "mmessage.hh"
#include "translationmemory.hh"
#include "sendbuffer.hh"
#include "streambuffer.hh"
#include "stats.hh"
#include <omp.h>

namespace basim
{
    class UDLane : public TickObject
    {
    private:
        /* nwid of Lane */
        NetworkID nwid;

        /* All state Elements to be included */
        InstructionMemoryPtr instmem;
        OpBufferPtr opbuff;
        EventQPtr eventq;
        //ScratchPadBankPtr spdbank;
        ScratchPadPtr spd;
        TSTablePtr tstable;
        ArchStatePtr archstate;
        // Send buffer 
        BufferPtr sendbuffer; // = new Buffer<uint32_t>(latency, capacity);
        StreamBufferPtr streambuffer; // = new Buffer<uint32_t>(latency, capacity);
        // Translation table
        TranslationMemoryPtr transmem; 

        /* Lane State */
        lanestate_t lanestate;
        Addr uip;
        ThreadStatePtr ts;

        omp_lock_t * omp_lock;

        /* some state that goes into all threads for now */
        Addr pgbase;
        Addr lmbase;
        int lmMode;

        /* dynamic data*/
        Cycles instCycles;
        Cycles cyclesRemaining;

        Addr calcTranAddr();
    
        Addr calcDefMajTranAddr();
    
        bool signatureCheck(encoded_inst trans);
        
        Addr calcTranActionAddr(encoded_inst trans);

        uint64_t getNextSymbol();
        
        bool checkActionTerm();
        
        SBState updateSBP();

        // Execute all non event transitions 
        Cycles execNonEventTx(encoded_inst);
#ifdef DETAIL_STATS
        uint64_t curr_event_inst_cnt;
#endif

    public:
        /* default constructor will never be used*/
        //UDLane(){};
        
        /* Actual constructor for the UpDownLane*/
        UDLane(uint32_t _nwid, ScratchPadPtr _spd = nullptr){
            nwid = _nwid;
            //instmem = new InstructionMemory();
            opbuff = new OpBuffer<operands_t>(); 
            eventq = new EventQ<eventword_t>();
            //spdbank = new ScratchPadBank(SCRATCHPAD_SIZE);
            tstable = new TSTable(nwid);
            lanestate = LaneState::NULLSTATE;
            spd = _spd;

            // Max size buffer to start
            sendbuffer = new Buffer<std::unique_ptr<MMessage> >(SENDLAT); 
            streambuffer = new StreamBuffer(SBSIZE); 

            // Add elements to a combined archstate for convenience in instruction execution
            archstate = new ArchState();
            //archstate->instmem = instmem;
            archstate->opbuff = opbuff;
            archstate->eventq = eventq;
            //archstate->spdbank = spdbank; 
            archstate->spd = _spd;
            archstate->uip = uip; 
            archstate->lanestate = &lanestate;
            archstate->tstable = tstable;
            archstate->sendbuffer = sendbuffer;
            archstate->streambuffer = streambuffer;
            archstate->lanestats = new LaneStats();
#ifdef DETAIL_STATS
            for(int i = 0; i < MAX_BINS; i++){
                (archstate->lanestats)->inst_per_event[i] = 0;
                (archstate->lanestats)->inst_per_tx[i] = 0;
            }
            archstate->curr_event_inst_count = 0;
            archstate->curr_tx_inst_count = 0;
            archstate->prev_event_lm_load_count = 0;
            archstate->prev_event_lm_store_count = 0;
            archstate->prev_event_dram_load_count = 0;
            archstate->prev_event_dram_store_count = 0;
            archstate->prev_event_lm_load_bytes = 0;
            archstate->prev_event_lm_store_bytes = 0;
            archstate->prev_event_dram_load_bytes = 0;
            archstate->prev_event_dram_store_bytes = 0;
#endif
            archstate->currtrans = CurrentTrans(0, true); // Setting default to event type?
            // thread state will be updated dynamically 

            //
            cyclesRemaining = basim::Cycles(0);
            instCycles = basim::Cycles(0);

        }

        /* Interface functions */        
        /* Setup Initial State of Lane*/
        void initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, int lmMode=1);
        
        void initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, TranslationMemoryPtr _transmem, int lmMode=1);

        void initSetup(Addr _pgbase, InstructionMemoryPtr _instmem, Addr _lmbase, TranslationMemoryPtr _transmem, int lmMode=1);
        
        /*  simulate a single cycle */
        void tick(uint64_t timestamp = 0) override;
        
        //void postTick();
        
        ///* do all the send messages from send buffer pre tick to simulate 1 cycle delay in sending*/
        //void preTick();

        /* pre cycle simulation*/
        bool isIdle();

        /* push into the event and operand queues*/
        bool pushEventOperands(eventoperands_t eop);
        
        /* push into the event and operand queues*/
        bool sendReady(){
            return sendbuffer->hasData();
        }
        
        void pushSendBuffer(std::unique_ptr<MMessage> m){
            return sendbuffer->push(std::move(m));
        }
        
        std::unique_ptr<MMessage> peekSendBuffer(){
            std::unique_ptr<MMessage>buffval = std::move(sendbuffer->peek());
            sendbuffer->pop();
            return buffval;
        }
        
        void popSendBuffer(){
            return sendbuffer->pop();
        }

        /* push into the event and operand queues*/
        size_t getEventQSize();
        
        /* write data into the scratchpad */
        //void writeScratchPad(Addr addr, uint8_t* dataptr, int size);
        void writeScratchPad(int size, Addr addr, uint8_t* data);
        
        /* read data from the scratchpad */
        void readScratchPad(int size, Addr addr, uint8_t* data);
        //word_t readScratchPad(Addr addr);

        /* Testing only API not to be exposed outside */
        void writeReg(RegId raddr, word_t data){
            (archstate->threadstate)->writeReg(raddr, data);
        }
        
        word_t readReg(RegId raddr){
            return (archstate->threadstate)->readReg(raddr);
        }

        /* testing api returns value from register of whatever thread is currently active */
        bool testReg(RegId raddr, word_t val, uint64_t mask=0xFFFFFFFFFFFFFFFF){
            ThreadStatePtr tst = archstate->threadstate;
            return ((mask & tst->readReg(raddr)) == (mask & val));            
        }
        
        /* testing api returns value from scratchpad memory */
        bool testMem(Addr memaddr, word_t val){
            ScratchPadPtr spd = archstate->spd;
            return (spd->readWord(memaddr) == val);            
        }
        
        /**
         * @brief pop a message from send buffer
         * 
         * @todo implement this
        */
        //sendmessage_t popSendBuffer(){}

        LaneStats* getLaneStats(){
            return archstate->lanestats;
        }

#ifdef INST_HIST
        uint32_t* getInstCount(){
            return archstate->instCount;
        }        
#endif

        void resetStats(){
            (archstate->lanestats)->reset();
        }

        /* destructor*/
        ~UDLane()
        {
          delete sendbuffer;
          delete streambuffer;
          delete archstate->lanestats;
          //delete instmem;
          delete opbuff;
          delete eventq;
          delete tstable;
          delete archstate;
          #ifndef GEM5_MODE
          delete omp_lock;
          #endif
        }

        void reorder_freetids() {
            tstable->reorder_freetids();
        }
    };

    typedef UDLane* UDLanePtr;

    class UDMem : public TickObject {
    private:
        uint64_t _latency;
        uint64_t _bandwidth;
        uint64_t _inter_node_latency;

        omp_lock_t * omp_lock;

        /* queue to add latency for coming messages */
        std::queue<std::unique_ptr<MMessage> > _message;
        std::queue<uint64_t> _message_time_stamp;

        /* queue to add latency for outgoing message */
        std::queue<std::unique_ptr<MMessage> > _remote_message;
        std::queue<uint64_t> _remote_message_time_stamp;

        // Per Stack stats
        StackStats* stack_stats; 
        uint64_t output_count;
        uint64_t output_limit;
        uint64_t curTimeStamp;
    public:
        UDMem() : _latency(200), _bandwidth(1200), _inter_node_latency(1000) {}

        UDMem(uint64_t latency, uint64_t bandwidth, uint64_t inter_node_latency);


        void tick(uint64_t timestamp = 0) override;

        bool isIdle();

        void pushMessage(std::unique_ptr<MMessage> m);

        void pushDelayedMessage(std::unique_ptr<MMessage> m);

        std::unique_ptr<MMessage> popMessage();

        std::unique_ptr<MMessage> popDelayedMessage();

        std::unique_ptr<MMessage> peekMessage();

        StackStats* getStackStats(){
            return stack_stats;
        }

        void resetStats(){
            stack_stats->reset();
        }

        void updateStats();

        ~UDMem();
    };

    typedef UDMem* UDMemPtr;

}//basim


#endif  //!__LANE__H__

