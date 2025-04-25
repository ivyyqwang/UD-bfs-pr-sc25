#include "udlane.hh"
#include "encodings.hh"
#include "transition.hh"
#include "inst_decode.hh"
#include "lanetypes.hh"
#include "translationmemory.hh"
#include "types.hh"
#include "debug.hh"
#include <string>

namespace basim
{   
    void UDLane::initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, int _lmMode){
           pgbase = _pgbase;
           lmbase = _lmbase;
           lmMode = _lmMode;
           //spdbank->setBankBase(_lmbase);
           instmem->setPGBase(pgbase);
           instmem->loadProgBinary(progfile);
           transmem = new TranslationMemory(nwid.getUDID(), 1, _lmbase);
           archstate->transmem = transmem;
           archstate->uip = pgbase;
           archstate->pgbase = pgbase;
           lanestate = lanestate_t::NULLSTATE;
           if(spd == nullptr){
                spd = new ScratchPad(1, _lmbase);
                archstate->spd = spd;
           }
            #ifndef GEM5_MODE
            this->omp_lock = new omp_lock_t();
            omp_init_lock(omp_lock);
            #endif
    }

    void UDLane::initSetup(Addr _pgbase, std::string progfile, Addr _lmbase, TranslationMemoryPtr _transmem, int _lmMode){
           pgbase = _pgbase;
           lmbase = _lmbase;
           lmMode = _lmMode;
           transmem = _transmem;
           //spdbank->setBankBase(_lmbase);
           instmem->setPGBase(pgbase);
           instmem->loadProgBinary(progfile);
           archstate->transmem = transmem;
           archstate->uip = pgbase;
           archstate->pgbase = pgbase;
           lanestate = lanestate_t::NULLSTATE;
           if(spd == nullptr){
                spd = new ScratchPad(1, _lmbase);
                archstate->spd = spd;
           }
            #ifndef GEM5_MODE
            this->omp_lock = new omp_lock_t();
            omp_init_lock(omp_lock);
            #endif
    }

    void UDLane::initSetup(Addr _pgbase, InstructionMemoryPtr _instmem, Addr _lmbase, TranslationMemoryPtr _transmem, int _lmMode){
           pgbase = _pgbase;
           lmbase = _lmbase;
           lmMode = _lmMode;
           transmem = _transmem;
           instmem = _instmem;
           //spdbank->setBankBase(_lmbase);
           instmem->setPGBase(pgbase);
           archstate->transmem = transmem;
           archstate->instmem = instmem;
           archstate->uip = pgbase;
           archstate->pgbase = pgbase;
           lanestate = lanestate_t::NULLSTATE;
           if(spd == nullptr){
                spd = new ScratchPad(1, _lmbase);
                archstate->spd = spd;
           }
            #ifndef GEM5_MODE
            this->omp_lock = new omp_lock_t();
            omp_init_lock(omp_lock);
            #endif
    }

    size_t UDLane::getEventQSize(){
        return (eventq->getSize());
    }

    bool UDLane::isIdle(){
        // Idle if eventQ is empty and ThreadStateTable has no suspended/live threads
        return((lanestate == LaneState::NULLSTATE && eventq->isEmpty()) && (tstable->noThreadsActive()));
    }

    bool UDLane::pushEventOperands(eventoperands_t eop){
        #ifndef GEM5_MODE
        omp_set_lock(this->omp_lock);
        if(!eventq->push(*(eop.eventword))){
            BASIM_ERROR("%s:push into EventQ failed\n", eventq->name());
        }
        if (eventq->getSize() > archstate->lanestats->eventq_len_max) {
            archstate->lanestats->eventq_len_max = eventq->getSize();
        }
        if(!opbuff->push(*(eop.operands))){
            BASIM_ERROR("%s:push into OperandBuffer failed\n", opbuff->name());
        }
        if (opbuff->getSize() > archstate->lanestats->opbuff_len_max) {
            archstate->lanestats->opbuff_len_max = opbuff->getSize();
        }
        omp_unset_lock(this->omp_lock);
        #else
        if(!eventq->push(*(eop.eventword))){
            BASIM_ERROR("%s:push into EventQ failed\n", eventq->name());
        }
        if (eventq->getSize() > archstate->lanestats->eventq_len_max) {
            archstate->lanestats->eventq_len_max = eventq->getSize();
        }
        if(!opbuff->push(*(eop.operands))){
            BASIM_ERROR("%s:push into OperandBuffer failed\n", opbuff->name());
        }
        if (opbuff->getSize() > archstate->lanestats->opbuff_len_max) {
            archstate->lanestats->opbuff_len_max = opbuff->getSize();
        }
        #endif
#ifdef GEM5_MODE
        if (eventq->getSize() > EVENTQTHRESHOLD){
            printf("\033[1;31m");
            printf("NWID:%u EventQ Size:%lu > threshold:%lu\n", this->nwid, eventq->getSize(), EVENTQTHRESHOLD);
            printf("\033[0m");
        }
#endif

        return true;
    }
    
    /* write data into the scratchpad */
    void UDLane::writeScratchPad(int size, Addr addr, uint8_t* data){
        Addr baseaddr = addr;
        if(size >=8){
            // >= 1 word
            for(int i = 0; i < size / 8; i++){
                word_t worddata = bytestoword(&data[8*i]);
                //spdbank->writeWord(addr, worddata);
                //int laneid = (addr - lmbase) / SCRATCHPADBANK_SIZE;
                addr = baseaddr + 8*i;
                (archstate->spd)->writeWord(addr, worddata);
            }
        }else{
            //// Get word aligned address
            //Addr alignedaddr = wordalignedaddr(baseaddr);
            //// get existing word from LM
            //word_t lmword = (archstate->spd)->readWord(alignedaddr);
            //// Do RMW on exact position
            //uint64_t mask = wordmask(baseaddr, size);
            // < word writes access a word and do RMW
            (archstate->spd)->writeBytes(size, addr, data);
        }
    }
    
    /* read data from the scratchpad */
    void UDLane::readScratchPad(int size, Addr addr, uint8_t* data){
    //word_t UDLane::readScratchPad(Addr addr){
        // @todo implement all other sizes
        //return(spdbank->readWord(addr));
        //int laneid = (addr - lmbase) / SCRATCHPADBANK_SIZE;
        //return (archstate->spd)->readWord(addr);
        (archstate->spd)->readBytes(size, addr, data);
        //return((archstate->accel)->readScratchPad(addr));
    }

    uint64_t UDLane::getNextSymbol(){
        //Check LM/SB mode
        //Get SBCR 
        //Read symbol from LM or SB and return
        // Add default / value to not read any buffer that is not supposed to be read
        uint64_t symbol; 

        SBCR sbcr = ts->getSBCR();

        if(sbcr.getRdMode() == RdMode::LMMODE){
            readScratchPad(sbcr.getIssueWidth(), ts->readReg(RegId::X5), reinterpret_cast<uint8_t*>(&symbol));
            switch(sbcr.getIssueWidth()){
                case 1:
                   symbol = symbol & 0xFF; 
                break;
                case 2:
                   symbol = symbol & 0xFFFF; 
                break;
                case 4:
                   symbol = symbol & 0xFFFFFFFF; 
                break;
                case 8:
                   symbol = symbol & 0xFFFFFFFFFFFFFFFF; 
                break;
                default:
                    BASIM_ERROR("Unsupported IssueWidth %ld for next symbol retrival!", sbcr.getIssueWidth());
            }
            BASIM_INFOMSG("NWID:%u, TID:%u,reading from LM[%ld : %ld+%ld] => %ld", ts->getNWIDbits(), ts->getTID(),ts->readReg(RegId::X5), ts->readReg(RegId::X5),sbcr.getIssueWidth(),symbol);
        }else{
            symbol = (archstate->streambuffer)->getVarSymbol(ts->readReg(RegId::X5),sbcr.getIssueWidth());
            uint64_t mask = (1<< sbcr.getIssueWidth()) - 1;
            symbol = symbol & mask;
            BASIM_INFOMSG("NWID:%u, TID:%u,reading from SB[%ld : %ld+%ld] => %ld", ts->getNWIDbits(), ts->getTID(),ts->readReg(RegId::X5), ts->readReg(RegId::X5),sbcr.getIssueWidth(),symbol);
        }
        return symbol;
    }
    
    /**
     * @brief Calculate the Transition fetch address based on the state property
     * 
     * @param stateproperty, uip, input symbol, X16
     * @return Addr 
     */
    Addr UDLane::calcTranAddr(){
        stateproperty_t sp = (ts->getStateProperty());
        Addr retAddr;
        Addr retAddr_state;
        uint64_t x16_reg; //= ts->readReg(RegId::X16);
        uint64_t symbol; //= getNextSymbol();
        //archstate->currtrans.setCurrSymbol(symbol);

        // Note : Majority and Default will need changes
        switch(sp.getType()){
            case StateProperty::COMMON:
                symbol = getNextSymbol();
                archstate->currtrans.setCurrSymbol(symbol);
            case StateProperty::EPSILON:
                sp = ts->getStateProperty();
                retAddr =  (archstate->uip & EFABASEMASK) + (sp.getState()<<2); 
                retAddr_state = retAddr;
                BASIM_INFOMSG("NWID:%u, TID:%u, TX Fetching: Epsilon OR Common Tranistion (Symbol: %d, state addr: %d, tx addr: %d)", ts->getNWIDbits(), ts->getTID(), symbol,retAddr_state,retAddr);
                break;
            case StateProperty::BASIC:
            //case StateProperty::REFILL:
            case StateProperty::MAJORITY:
            case StateProperty::DEFAULT:
                symbol = getNextSymbol();
                archstate->currtrans.setCurrSymbol(symbol);
                sp = ts->getStateProperty();
                retAddr =  (archstate->uip & EFABASEMASK) + (sp.getState()<<2) + (symbol<<2);
                retAddr_state = (archstate->uip & EFABASEMASK) + (sp.getState()<<2);
                BASIM_INFOMSG("NWID:%u, TID:%u, TX Fetching: Basic (Refill)/Def/Maj Tranistion (Symbol %d, state addr: %d, tx addr:%d)", ts->getNWIDbits(), ts->getTID(),symbol,retAddr_state,retAddr);
                break;
            case StateProperty::FLAG:
            case StateProperty::FLAG_DEFAULT:
            case StateProperty::FLAG_MAJORITY:
                x16_reg = ts->readReg(RegId::X16);
                sp = ts->getStateProperty();
                retAddr =  (archstate->uip & EFABASEMASK) + (sp.getState()<<2) + (x16_reg<<2);
                retAddr_state =  (archstate->uip & EFABASEMASK) + (sp.getState()<<2);
                BASIM_INFOMSG("NWID:%u, TID:%u, Fetching Flag/FlagDef/FlagMaj Tranistion (X16: %d, state addr: %d, tx addr %d)", ts->getNWIDbits(), ts->getTID(), x16_reg,retAddr_state,retAddr);
                break;
            default:
                BASIM_ERROR("unsupported state property type for transition address calculation! (for stateID: %ld)", sp.getState());
                //BASIM_ERROR("unsupported state property for transition address calculation!");
        }
        return retAddr;
    }

    bool UDLane::signatureCheck(encoded_inst trans){
        stateproperty_t sp = (ts->getStateProperty());
        bool sigcheck = true;
        uint64_t symbol = getNextSymbol();
        if(sp.getType() == StateProperty::MAJORITY ||
            sp.getType() == StateProperty::DEFAULT){
                if(/*archstate->currtrans.getCurrSymbol()*/symbol != extrInstMajoritytxSignature(trans))
                    sigcheck = false;
            }
        else if(sp.getType() == StateProperty::FLAG_MAJORITY ||
            sp.getType() == StateProperty::FLAG_DEFAULT){
                if(archstate->threadstate->readReg(RegId::X16) != extrInstMajoritytxSignature(trans))
                    sigcheck = false;
            }
        else if(sp.getType() == StateProperty::BASIC){
               if(symbol != extrInstBasictxSignature(trans) )
                    sigcheck = false;
            }
        else if(sp.getType() == StateProperty::FLAG ){
               if(archstate->threadstate->readReg(RegId::X16) != extrInstBasictxSignature(trans) )
                    sigcheck = false;
            }
        return sigcheck;
    }


    Addr UDLane::calcDefMajTranAddr(){
        stateproperty_t sp = (ts->getStateProperty());
        Addr retAddr;
        // Address for Default and Majority is based on the state property
        // StateID + Value
        retAddr = (archstate->uip & EFABASEMASK) + (sp.getState() << 2) + (sp.getValue() << 2);
        BASIM_INFOMSG("NWID:%u, TID:%u, TX Fetching: Majority OR Default Tranistion (state addr: %d, offset addr:%d, tx addr: %d)", ts->getNWIDbits(), ts->getTID(),(sp.getState() << 2),(sp.getValue() << 2) ,retAddr);
        return retAddr;
    }

    /**
     * @brief  Caclculate the Transition Action addresses for _WITHACTION transitions based on the state property
     * 
     * @param stateproperty, uip, input symbol, X16
     * @return Addr 
     */
    Addr UDLane::calcTranActionAddr(encoded_inst trans){
        stateproperty_t sp = (ts->getStateProperty());
        Addr retAddr;
        uint64_t x16_reg = ts->readReg(RegId::X16);
        uint64_t symbol = getNextSymbol();
        uint64_t tr_base_count = 0;
        // Note : Majority and Default will need changes
        switch(sp.getType()){
            case StateProperty::COMMON:
            case StateProperty::EPSILON:
                retAddr = archstate->uip + (extrInstCommontxAttach(trans) << 2); // Change this to reflect uip + attach
                BASIM_INFOMSG("NWID:%u, TID:%u, ACTIONS Fetching: Epsilon or Common (addr: %d) ",ts->getNWIDbits(), ts->getTID(),retAddr);
            break;
            case StateProperty::BASIC:
            //case StateProperty::REFILL:
            case StateProperty::MAJORITY:
            case StateProperty::DEFAULT:
                if(archstate->currtrans.getType() != TransitionType::REFILL_WITH_ACTION && archstate->currtrans.getType() != TransitionType::REFILL){
                    if(archstate->currtrans.getAttachModeRefill() == 0b11 ){
                        tr_base_count = pow(2,(archstate->currtrans.getAttachBase()+1)); 
                        retAddr = (archstate->uip & EFABASEMASK) + (sp.getState()<<2) + (tr_base_count<<2) + ((extrInstBasictxSignature(trans)<< archstate->currtrans.getAttachScalar())<<2);
                        BASIM_INFOMSG("NWID:%u, TID:%u, ACTIONS Fetching: Basic/Def/Maj  (addr: %d)[base:%d scalar:%d]",ts->getNWIDbits(), ts->getTID(),retAddr,archstate->currtrans.getAttachBase(),archstate->currtrans.getAttachScalar());
                    }
                    else{
                        retAddr = archstate->uip + (archstate->currtrans.getAttach() << 2);
                        BASIM_INFOMSG("NWID:%u, TID:%u, ACTIONS Fetching: Basic/Def/Maj  (addr: %d)[attach:%d]",ts->getNWIDbits(), ts->getTID(),retAddr, archstate->currtrans.getAttach());
                    }
                }else{
                    tr_base_count = pow(2,(archstate->currtrans.getAttachBase()+1));
                    retAddr = (archstate->uip & 0xFFFFFFFFFFFFC000) + (sp.getState()<<2) + (tr_base_count<<2) + ((extrInstBasictxSignature(trans)<< archstate->currtrans.getAttachScalar())<<2);
                    BASIM_INFOMSG("NWID:%u, TID:%u, ACTIONS Fetching: Basic (Refill)  (addr: %d)[base:%d scalar:%d]",ts->getNWIDbits(), ts->getTID(),retAddr,archstate->currtrans.getAttachBase(),archstate->currtrans.getAttachScalar());
                }
            break;
            case StateProperty::FLAG:
            case StateProperty::FLAG_DEFAULT:
            case StateProperty::FLAG_MAJORITY:
                if(archstate->currtrans.getAttachModeRefill() == 0b11 ){
                    tr_base_count = pow(2,(archstate->currtrans.getAttachBase()+1)); 
                    retAddr = (archstate->uip & EFABASEMASK) + (sp.getState()<<2) + (tr_base_count<<2) + ((extrInstBasictxSignature(trans)<< archstate->currtrans.getAttachScalar())<<2);
                    BASIM_INFOMSG("NWID:%u, TID:%u, ACTIONS Fetching: Flag/FlagDef/FlagMaj  (addr: %d)[base:%d scalar:%d]",ts->getNWIDbits(), ts->getTID(),retAddr,archstate->currtrans.getAttachBase(),archstate->currtrans.getAttachScalar());
                }
                else{
                    retAddr = archstate->uip + (archstate->currtrans.getAttach() << 2);
                    BASIM_INFOMSG("NWID:%u, TID:%u, ACTIONS Fetching: Flag/FlagDef/FlagMaj  (addr: %d)[attach:%d]",ts->getNWIDbits(), ts->getTID(),retAddr,archstate->currtrans.getAttach());
                }
            break;
            default:
                BASIM_ERROR("unsupported state property type for Action address calculation! (for stateID: %ld)", sp.getState());
        }
        return retAddr;
    }

    // Will execute a specific dispatch based on the transition type
    Cycles UDLane::execNonEventTx(encoded_inst inst){
        // Check current transition type and do dispatch
        // Do they always have actions or not
        BASIM_INFOMSG("NWID:%u, TID:%u, Executing NonEvent Transition",ts->getNWIDbits(), ts->getTID());
        if(!(archstate->currtrans).hasAction()){
            // No actions 
            *archstate->lanestate = LaneState::SBREFILL_TERM;
            instCycles = Cycles(1);
        }else{
            // Has Actions - set UIP to base of action block 
            archstate->uip = calcTranActionAddr(inst);
            *archstate->lanestate = LaneState::TRANS_ACTION;
            // Save the base UIP 
            archstate->currtrans.setActionBaseUIP(archstate->uip);
        }
        return instCycles;
    }


    // Check for action termination
    bool UDLane::checkActionTerm(){

        if(*archstate->lanestate != LaneState::TRANS_ACTION){
            // This means last action or yield was executed and 
            // state already has been changed
            return false;
        }
        else{
            //if((archstate->threadstate)->getStateProperty().getType() == StateProperty::REFILL){
            if(((archstate->currtrans).getType() == TransitionType::REFILL_WITH_ACTION) || ((archstate->currtrans).getType() == TransitionType::REFILL )) {
                if((archstate->uip - (archstate->currtrans).getActionBaseUIP()) >= 
                    ((archstate->currtrans).getNumActions()<<2)){
                    BASIM_INFOMSG("NWID:%u, TID:%u,Refill action block is ending after %ld actions", ts->getNWIDbits(), ts->getTID(), (archstate->uip - (archstate->currtrans).getActionBaseUIP())>>2);
                    return true;
                }else{ 
                    BASIM_INFOMSG("NWID:%u, TID:%u,in Refill action block %ld actions have been executed", ts->getNWIDbits(), ts->getTID(), (archstate->uip - (archstate->currtrans).getActionBaseUIP())>>2);
                }    return false;
                
            }else{
                switch(archstate->currtrans.getAttachModeRefill()){
                    case 3:{
                        if((archstate->uip - (archstate->currtrans).getActionBaseUIP()) >= 
                            ((archstate->currtrans).getNumActions()<<2)){
                            BASIM_INFOMSG("NWID:%u, TID:%u,Attach Mode is 3 and action block is ending after %ld actions", ts->getNWIDbits(), ts->getTID(), archstate->uip - (archstate->currtrans).getActionBaseUIP());
                            return true;}
                        else {
                            BASIM_INFOMSG("NWID:%u, TID:%u,Attach Mode is 3 and %ld actions have been executed", ts->getNWIDbits(), ts->getTID(), archstate->uip - (archstate->currtrans).getActionBaseUIP());
                            return false;}
                        break;
                    }
                    case 0:{
                        BASIM_INFOMSG("NWID:%u, TID:%u,Attach Mode is 0 and current action is not yield/yieldt/lastact", ts->getNWIDbits(), ts->getTID());
                        return false;
                        break;
                    }
                    case 1:
                    case 2:
                    default:
                        BASIM_ERROR("Attach Mode not supported yet");
                        return false;
                        break;
                }
            }
        }
    }

    SBState UDLane::updateSBP(){
        // check state property 
        stateproperty_t sp = (ts->getStateProperty());
        SBCR sbcr = ts->getSBCR();
        uint64_t curr_sbp = ts->readReg(RegId::X5);
        SBState retstate = SBState::AVAIL;
        int64_t old_curr_sbp = curr_sbp;
        switch(sp.getType()){
            case StateProperty::COMMON:
            case StateProperty::BASIC:
            //case StateProperty::REFILL:
            case StateProperty::MAJORITY:
            case StateProperty::DEFAULT:
                // These are the ones that consume symbol from stream (SB or LM)
                //SBP += SBCR.advance_width
                if  (archstate->currtrans.getType() != TransitionType::EVENT){
                    curr_sbp += sbcr.getAdvanceWidth();
                    if(((archstate->currtrans).getType() == TransitionType::REFILL_WITH_ACTION) ||((archstate->currtrans).getType() == TransitionType::REFILL))
                        curr_sbp = curr_sbp - archstate->currtrans.getAttachModeRefill(); 
                    BASIM_INFOMSG("NWID:%u, TID:%u , maxSBP+X7:%ld, Updated SBP to (%ld)", 
                            ts->getNWIDbits(), ts->getTID(), ts->getMaxSBP() + ts->readReg(RegId::X7), ts->readReg(RegId::X5) );
		            ts->writeReg(RegId::X5,curr_sbp);
		        }
                if((sbcr.getRdMode() == RdMode::LMMODE) && (curr_sbp >= (ts->getMaxSBP() + ts->readReg(RegId::X7)))){
                    // Termination
                    return SBState::TERM;
                }
                else if((sbcr.getRdMode() == RdMode::SBMODE) && (curr_sbp >= (ts->getMaxSBP() + (ts->readReg(RegId::X7) << 3)))){
                    // Termination
                    BASIM_INFOMSG("NWID:%u, TID:%u ,TERM CHECK in SBMODE: %d >= %d + %ld ? ", 
                            ts->getNWIDbits(), ts->getTID(),curr_sbp, ts->getMaxSBP() , ts->readReg(RegId::X7) << 3 ); 
                    return SBState::TERM;
                }
                else if((sbcr.getRdMode() == RdMode::SBMODE) &&
                    (((old_curr_sbp & 0x1FF) + 2*sbcr.getAdvanceWidth()) > (SBSIZE << 3))){
                    return SBState::REFILL;
                }
                return retstate;
            case StateProperty::FLAG:
            case StateProperty::EPSILON:
            case StateProperty::FLAG_DEFAULT:
            case StateProperty::FLAG_MAJORITY:
            default:
                // Nothing to be done for these
                return retstate;
        }
    }

    void UDLane::tick(uint64_t timestamp){
        // if previous work is still going on skip 
        // check if state property is null
        // pop event 
        // else get next instruction or transition 
        archstate->timestamp = timestamp;
        if(cyclesRemaining > 0){
            cyclesRemaining = cyclesRemaining - Cycles(1);
            return;
        }else{
            // Check if lane is in nullstate to fetch from queue 
            // else we check if instruction execution is to be done 
            // or next transition ? 
            instCycles = Cycles(0);

            while(instCycles == 0){
                switch(lanestate){
                    case LaneState::NULLSTATE:{
                        // fetch the event word from event queue and proceed
                        // set thread state 
                        // set rf window and then proceed
                        eventword_t curr_event; // = eventq->peek();
                        if(!eventq->isEmpty())
                            curr_event = eventq->peek();
                        else{
                            BASIM_INFOMSG("NWID:%u Empty EventQ", this->nwid.networkid);
                            return;
                        }

                        //Empty line for readability
                        BASIM_EMPTY;
                        // get thread from tstable - before checking for the transition
                        ts = tstable->getThreadState(curr_event.getThreadID());

                        //Check if thread exists already
                        if(ts == nullptr){
#ifndef BASIM_STANDALONE
                            if(!(curr_event.getThreadID() == 0xFF)){
                                printf("[NWID :%u] Invalid or terminated Thread ID %d in event word with event label = %d\n", this->nwid.networkid, curr_event.getThreadID(), curr_event.getEventLabel());
                                exit(1);
                            }
#endif
                            // Thread does not exist set it up
                            // get a TID
                            uint8_t tid = tstable->getTID();

                            // Update in current event new threadID
                            curr_event.setThreadID(tid);

                            // Setup ThreadState for TID
                            ts = new ThreadState(curr_event.getThreadID(), this->nwid, this->lmbase, this->pgbase, this->lmMode);

                            // Set the threadmode
                            ts->setTmode(curr_event.getThreadMode());

                            // Add to Thread State table
                            tstable->addtoTST(ts);

                            archstate->lanestats->thread_count++;
                            // For new threads always start with STATEPROPERTY=EVENT
                            stateproperty_t sp;
                            sp.setType(StateProperty::EVENT);
                            ts->setStateProperty(sp);
                            if(archstate->lanestats->max_thread_count < tstable->numActiveThreads()){
                                archstate->lanestats->max_thread_count = tstable->numActiveThreads();
                            }
                            if((tstable->numActiveThreads() > 128) && (archstate->lanestats->start_gt128th == -1)){
                                archstate->lanestats->start_gt128th = archstate->timestamp;
                            }
                        }
                        ts->writeEvent(curr_event);
                        ts->writeOperands(opbuff->read(0));
                        // have to set X6? (important for Transitions) return to this
                        // ts->writeTSReg(regid::X6, ?);

                    #ifdef DETAIL_STATS
                        archstate->curr_event_inst_count = 0;
                        archstate->curr_tx_inst_count = 0;
                        if (archstate->lanestats->event_activation_count.find(curr_event.getEventLabel()) == archstate->lanestats->event_activation_count.end()) {
                            archstate->lanestats->event_activation_count[curr_event.getEventLabel()] = 1;
                        } else {
                            archstate->lanestats->event_activation_count[curr_event.getEventLabel()]++;
                        }
                        if (archstate->lanestats->event_cycle_count.find(curr_event.getEventLabel()) == archstate->lanestats->event_cycle_count.end()) {
                            archstate->lanestats->event_cycle_count[curr_event.getEventLabel()] = 0;
                        }
                    #endif
                        // Initialize archstate struct? --> all done in initSetup/constructor
                        // set UIP to the right value based on event (currently for testing)
                        // We should be setting this to the base of either the event / program based on the instruction 
                        // in Null State alwasys fetch the Event Transition
                        archstate->uip = pgbase + static_cast<Addr>(curr_event.getEventLabel());
                        archstate->threadstate = ts;
                    #ifdef DEBUG_MODE
                        auto sym_name_map = instmem->getSymbolNameMap();
                        auto m_place = sym_name_map.find(curr_event.getEventLabel());
                        std::string name;
                        if (m_place != sym_name_map.end()) {
                            name = m_place -> second;
                        } else {
                            name = "Unknown event name";
                        }
                        BASIM_INFOMSG_LEVEL(0, "NWID:%u, TID:%u, Executing EventLabel: %u, EventName: %s", ts->getNWIDbits(), ts->getTID(), curr_event.getEventLabel(), name.c_str());
                    #endif
                        //execute the event transition and add cycles
                        EncInst trans = instmem->getNextInst(archstate->uip);
                    #ifdef DEBUG_INST_TRACE
                        BASIM_PRINT("NWID:%u, TID:%u, UIP:0x%lx, DISASM - %s", archstate->threadstate->getNWIDbits(), archstate->threadstate->getTID(), archstate->uip, disasmTranseventTX(trans).c_str());
                    #endif
                        BASIM_INFOMSG("NWID:%u, TID:%u, UIP:0x%lx, DISASM - %s", archstate->threadstate->getNWIDbits(), archstate->threadstate->getTID(), archstate->uip, disasmTranseventTX(trans).c_str());
                        // Holds the state of the current transition (do this every transition)
                        archstate->currtrans = CurrentTrans(trans, true);
                        // Transition execution will basically update the instruction pointer 
                        instCycles = exeTranseventTX(*archstate, trans);
                        //archstate->lanestats->tran_count_event++;
                        archstate->lanestats->tran_count++;
                        archstate->lanestats->cycle_count += instCycles;
                        archstate->lanestats->cur_activation_cycle_count = instCycles;

                        break;
                    }
                    case LaneState::EVENT_ACTION:
                    case LaneState::SBREFILL_TERM_ACTION:{
                    #ifdef DETAIL_STATS
                        archstate->curr_event_inst_count++;
                        archstate->curr_tx_inst_count++;
                        archstate->lanestats->event_cycle_count[archstate->threadstate->getEventWord().getEventLabel()]++;
                    #endif
                        // Some Event is in progress - exeute based on state
                        // If state-property is event - actions continue to be executed
                        // for other state-properties, check numActions executed, lastAction etc
                        // Event Based programs typically keep executing instructions till yield
                        EncInst inst = instmem->getNextInst(archstate->uip);
                        //ouput should be no of cycles
                    #ifdef DEBUG_INST_TRACE
                        BASIM_PRINT("NWID:%u, TID:%u, UIP:0x%lx, DISASM - %s", archstate->threadstate->getNWIDbits(), archstate->threadstate->getTID(), archstate->uip, decodeInst(inst).disasm(inst).c_str());
                    #endif
                        BASIM_INFOMSG("NWID:%u, TID:%u, UIP:0x%lx, DISASM - %s", archstate->threadstate->getNWIDbits(), archstate->threadstate->getTID(), archstate->uip, decodeInst(inst).disasm(inst).c_str());
                        instCycles = decodeInst(inst).exe(*archstate, inst);
                        archstate->lanestats->inst_count++;
                        archstate->lanestats->cycle_count += instCycles;
                        archstate->lanestats->cur_activation_cycle_count += instCycles;
                        break;
                    }
                    case LaneState::TRANS:{
                    #ifdef DETAIL_STATS
                        archstate->curr_tx_inst_count=0;
                    #endif
                        // fetch tran based on state property 
                        // setup lane state etc for execution ()
                        ts = archstate->threadstate;

                        // Update the UIP to point to the next transition 
                        archstate->uip = calcTranAddr();
                        EncInst trans = instmem->getNextInst(archstate->uip);

                        // Update current transition
                        archstate->currtrans = CurrentTrans(trans, false);

                        // signature check
                        if(signatureCheck(trans)){
                            // Execute the trantision

                            instCycles = execNonEventTx(trans);
                        } else {
                            // Signature Check failed --> default / majority
                            // No state property update for default / majority 
                            // Change Lane state to default / majority
                            StateProperty sp = archstate->threadstate->getStateProperty().getType();
                            if(sp == StateProperty::FLAG_MAJORITY ||
                                sp == StateProperty::MAJORITY){
                                *archstate->lanestate = LaneState::TRANS_MAJORITY;
                                }
                            else if(sp == StateProperty::FLAG_DEFAULT ||
                                sp == StateProperty::DEFAULT){
                                *archstate->lanestate = LaneState::TRANS_DEFAULT;
                                }
                            else
                                BASIM_ERROR("NWID:%u, TID:%u, Invalid StateProperty seen for signature fail!", archstate->threadstate->getNWIDbits(), archstate->threadstate->getTID());
                        }

                        break;
                    }
                    case LaneState::TRANS_DEFAULT:{
                        // Get the transition address 
                        // fetch the transition
                    #ifdef DETAIL_STATS
                        archstate->curr_tx_inst_count=0;
                    #endif
                        archstate->uip = calcDefMajTranAddr();
                        EncInst trans = instmem->getNextInst(archstate->uip);

                        // Update current transition
                        archstate->currtrans = CurrentTrans(trans, false);

                        //update the state property
                        //fetch the next transition (while there are no SBP update)
                        ts->setStateProperty(archstate->currtrans.getNextSp());
                        BASIM_INFOMSG("NWID:%u, TID:%u, Updated StateProperty after default TX to (%s,state addr:%ld,value:%ld)", (archstate->threadstate)->getNWIDbits(), (archstate->threadstate)->getTID(), ((archstate->threadstate)->getStateProperty()).print_type(((archstate->threadstate)->getStateProperty()).getType()),((archstate->threadstate)->getStateProperty()).getState()<<2,((archstate->threadstate)->getStateProperty()).getValue());
                        *archstate->lanestate = LaneState::TRANS;

                        break;
                    }
                    case LaneState::TRANS_MAJORITY:{
                        // Get the transition address 
                        // fetch the transition
                    #ifdef DETAIL_STATS
                        archstate->curr_tx_inst_count=0;
                    #endif
                        archstate->uip = calcDefMajTranAddr();
                        EncInst trans = instmem->getNextInst(archstate->uip);

                        // Update current transition
                        archstate->currtrans = CurrentTrans(trans, false);

                        // Execute the transition and proceed as before
                        instCycles = execNonEventTx(trans);

                        break;
                    }
                    case LaneState::TRANS_ACTION:{
                    #ifdef DETAIL_STATS
                        archstate->curr_tx_inst_count++;
                    #endif
                        // Fetch the action and execute
                        // After execution of each action check for actionblock termination
                        // 1. numActions --> mode == 11
                        // 2. lastaction --> mode == 00
                        // 3. yield/yield_terminate - nothing to do here
                        EncInst inst = instmem->getNextInst(archstate->uip);
                        //ouput should be no of cycles
                        //BASIM_PRINT("NWID:%u, TID:%u, UIP:0x%lx, DISASM - %s", archstate->threadstate->getNWIDbits(), archstate->threadstate->getTID(), archstate->uip, decodeInst(inst).disasm(inst).c_str());
                        BASIM_INFOMSG("NWID:%u, TID:%u, UIP:0x%lx, DISASM - %s", archstate->threadstate->getNWIDbits(), archstate->threadstate->getTID(), archstate->uip, decodeInst(inst).disasm(inst).c_str());
                        instCycles = decodeInst(inst).exe(*archstate, inst);

                        // Check for term, refill 
                        // Change only when end of action block is reached
                        // Do not change if lastaction or yield/yieldt have changed lanestate
                        if(checkActionTerm()){
                            *archstate->lanestate = LaneState::SBREFILL_TERM;
                        }
                        // Stats Update 
                        archstate->lanestats->inst_count++;
                        archstate->lanestats->cycle_count += instCycles;
                        archstate->lanestats->cur_activation_cycle_count += instCycles;
                        break;
                    }
                    case LaneState::SBREFILL_TERM:{
                        // Update SBP function
                        switch(updateSBP()){
                            case SBState::REFILL:
                                // Do shared block for SBRefill
                                // SBREFILLBLOCK 0x2C // 4*61
                                archstate->uip = (archstate->uip & EFABASEMASK) + REFILLBLOCK;
                                *archstate->lanestate = LaneState::SBREFILL_TERM_ACTION;
                                // change currentstate attach to execute untill lastact/yield/yieldt 
                                // (all automatically triggered shared blocks will end with lastact/yield/yieldt)
                                // change currentstate type if refill to not to use consider default attach mode 3
                                //if((archstate->threadstate)->getStateProperty().getType() == StateProperty::REFILL)
                                //   (archstate->threadstate)->getStateProperty().setType(StateProperty::BASIC);  
                                if(((archstate->currtrans).getType() == TransitionType::REFILL_WITH_ACTION) ||((archstate->currtrans).getType() == TransitionType::REFILL))
                                   (archstate->currtrans).setType(TransitionType::BASIC_WITH_ACTION);
                                if(( (archstate->currtrans).getAttachModeRefill()) != 0)
                                   (archstate->currtrans).setAttachModeRefill(0);
                                if (archstate->currtrans.getType() != TransitionType::EVENT){
                                    ts->setStateProperty(archstate->currtrans.getNextSp());
                                    BASIM_INFOMSG("NWID:%u, TID:%u, Updated StateProperty after ActionTerm to (%s,stateID:%ld,value:%ld)", (archstate->threadstate)->getNWIDbits(), (archstate->threadstate)->getTID(), ((archstate->threadstate)->getStateProperty()).print_type(((archstate->threadstate)->getStateProperty()).getType()),((archstate->threadstate)->getStateProperty()).getState(),((archstate->threadstate)->getStateProperty()).getValue());}
                            break;
                            case SBState::TERM:
                                // Do shared block for Avail
                                // TERMBLOCK 0x0 // 4*0
                                BASIM_INFOMSG("NWID:%u, TID:%u, Input Termination shared block triggered!",(archstate->threadstate)->getNWIDbits(), (archstate->threadstate)->getTID());
                                archstate->uip = (archstate->uip & EFABASEMASK) + TERMBLOCK;
                                *archstate->lanestate = LaneState::SBREFILL_TERM_ACTION;
                                // change currentstate attach to execute untill lastact/yield/yieldt 
                                // change currentstate type if refill to not to use consider default attach mode 3
                                //if((archstate->threadstate)->getStateProperty().getType() == StateProperty::REFILL)
                                //   (archstate->threadstate)->getStateProperty().setType(StateProperty::BASIC);  
                                if(((archstate->currtrans).getType() == TransitionType::REFILL_WITH_ACTION) ||((archstate->currtrans).getType() == TransitionType::REFILL))
                                   (archstate->currtrans).setType(TransitionType::BASIC_WITH_ACTION);
                                if(( (archstate->currtrans).getAttachModeRefill()) != 0)
                                   (archstate->currtrans).setAttachModeRefill(0);
                                if (archstate->currtrans.getType() != TransitionType::EVENT){
                                    ts->setStateProperty(archstate->currtrans.getNextSp());
                                    BASIM_INFOMSG("NWID:%u, TID:%u, Updated StateProperty after ActionTerm to (%s,stateID:%ld,value:%ld)", (archstate->threadstate)->getNWIDbits(), (archstate->threadstate)->getTID(), ((archstate->threadstate)->getStateProperty()).print_type(((archstate->threadstate)->getStateProperty()).getType()),((archstate->threadstate)->getStateProperty()).getState(),((archstate->threadstate)->getStateProperty()).getValue());}
                            break;
                            case SBState::AVAIL:
                                if (archstate->currtrans.getType() != TransitionType::EVENT){
                                    ts->setStateProperty(archstate->currtrans.getNextSp());
                                    BASIM_INFOMSG("NWID:%u, TID:%u, Updated StateProperty after ActionTerm to (%s,stateID:%ld,value:%ld)", (archstate->threadstate)->getNWIDbits(), (archstate->threadstate)->getTID(), ((archstate->threadstate)->getStateProperty()).print_type(((archstate->threadstate)->getStateProperty()).getType()),((archstate->threadstate)->getStateProperty()).getState(),((archstate->threadstate)->getStateProperty()).getValue());}
                                *archstate->lanestate = LaneState::TRANS;
                            break;
                            default:
                                BASIM_ERROR("Incorrect Value returned after SBP update");
                        }

                        break;
                    }
                    default:
                        BASIM_ERROR("Invalid Lane State Encountered");
                }
            }
        }
        if(instCycles > 1)
            cyclesRemaining = instCycles - Cycles(1); 
    }


    UDMem::UDMem(uint64_t latency, uint64_t bandwidth, uint64_t inter_node_latency) {
        this->_latency = latency;
        this->_bandwidth = bandwidth;
        this->_inter_node_latency = inter_node_latency;
        this->curTimeStamp = 0;
        #ifndef GEM5_MODE
        this->omp_lock = new omp_lock_t();
        this->stack_stats = new StackStats();
        omp_init_lock(omp_lock);
        #endif
    }


    void UDMem::tick(uint64_t timestamp) {
        this->curTimeStamp += timestamp;
        this->output_limit = (timestamp * this->_bandwidth) / 2; // 2 is because of 2GHz
        this->output_count = 0;     
    }

    bool UDMem::isIdle() {
        return this->_message_time_stamp.empty();
    }

    void UDMem::pushMessage(std::unique_ptr<MMessage> m) {
        #ifndef GEM5_MODE
        omp_set_lock(this->omp_lock);
        this->_message_time_stamp.push(this->curTimeStamp);
        this->_message.push(std::move(m));
        omp_unset_lock(this->omp_lock);
        #else
        this->_message_time_stamp.push(this->curTimeStamp);
        this->_message.push(std::move(m));
        #endif
    }

    void UDMem::pushDelayedMessage(std::unique_ptr<MMessage> m) {
        this->_remote_message_time_stamp.push(this->curTimeStamp);
        this->_remote_message.push(std::move(m));
    }

    std::unique_ptr<MMessage> UDMem::popMessage() {
        std::unique_ptr<MMessage> m;
        if (!(this->_message_time_stamp.empty()) && \
            this->output_count < this->output_limit && \
            (this->_message_time_stamp.front() + this->_latency) <= this->curTimeStamp) {
            this->output_count += 64;
            m = this->peekMessage();
            if (m->isStore()) {
                this->output_count += 64;
                this->stack_stats->dram_store_count++;
                this->stack_stats->dram_store_bytes += m->getLen() * WORDSIZE;
            }else{
                this->stack_stats->dram_load_count++;
                this->stack_stats->dram_load_bytes += m->getLen() * WORDSIZE;
            }
            BASIM_WARNING_IF((m->getdestaddr() & 0x003f) + m->getLen() * 8 > 64, "Warning: Message is crossing the boundary\n");
            this->_message_time_stamp.pop();
            this->_message.pop();
        } else {
            m.reset();
        }
        return m;
    }

    std::unique_ptr<MMessage> UDMem::popDelayedMessage() {
        std::unique_ptr<MMessage> m;
        if(!(this->_remote_message_time_stamp.empty()) && (this->_remote_message_time_stamp.front() + this->_inter_node_latency) <= this->curTimeStamp){
            m = std::move(this->_remote_message.front());
            this->_remote_message.pop();
            this->_remote_message_time_stamp.pop();
        } else {
            m.reset();
        }
        return m;
    }

    std::unique_ptr<MMessage> UDMem::peekMessage() {
        return std::move(this->_message.front());
    }

    void UDMem::updateStats() {
        this->stack_stats->peak_dram_load_bytes = std::max(this->stack_stats->peak_dram_load_bytes, (this->stack_stats->dram_load_bytes - this->stack_stats->dram_load_bytes_prev));
        this->stack_stats->peak_dram_store_bytes = std::max(this->stack_stats->peak_dram_store_bytes, (this->stack_stats->dram_store_bytes - this->stack_stats->dram_store_bytes_prev));
        this->stack_stats->peak_dram_load_count = std::max(this->stack_stats->peak_dram_load_count, (this->stack_stats->dram_load_count - this->stack_stats->dram_load_count_prev));
        this->stack_stats->peak_dram_store_count = std::max(this->stack_stats->peak_dram_store_count, (this->stack_stats->dram_store_count - this->stack_stats->dram_store_count_prev));
        this->stack_stats->peak_dram_load_store_count = std::max(this->stack_stats->peak_dram_load_store_count, (this->stack_stats->dram_load_count - this->stack_stats->dram_load_count_prev + this->stack_stats->dram_store_count - this->stack_stats->dram_store_count_prev));
        
        this->stack_stats->dram_load_bytes_prev = this->stack_stats->dram_load_bytes;
        this->stack_stats->dram_store_bytes_prev = this->stack_stats->dram_store_bytes;
        this->stack_stats->dram_load_count_prev = this->stack_stats->dram_load_count;
        this->stack_stats->dram_store_count_prev = this->stack_stats->dram_store_count;
    }

    UDMem::~UDMem() {
        delete omp_lock;
        delete stack_stats;
    }

} // namespace basim
