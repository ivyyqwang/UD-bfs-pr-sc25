#include "thread_ctrl_inst.hh"
#include "archstate.hh"
#include "lanetypes.hh"
#include "debug.hh"
#include "transition.hh"
#include "isa_cycles.hh"

namespace basim {

/* yield Instruction */
Cycles exeInstYield(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;


#ifdef DETAIL_STATS
  uint64_t curr_local_stat = 0;
  if(ast.curr_event_inst_count > MAX_BINS-1){
    lnstats->inst_per_event[MAX_BINS-1]++;
  } else{
    lnstats->inst_per_event[ast.curr_event_inst_count]++;
  }
  if(ast.curr_event_inst_count > lnstats->max_inst_per_event) {
    lnstats->max_inst_per_event = ast.curr_event_inst_count;
  }
  if(ast.curr_tx_inst_count > MAX_BINS-1){
    lnstats->inst_per_tx[MAX_BINS-1]++;
  } else{
    lnstats->inst_per_tx[ast.curr_tx_inst_count]++;
  }
  if (ast.curr_tx_inst_count > lnstats->max_inst_per_tx) {
    lnstats->max_inst_per_tx = ast.curr_tx_inst_count;
  }
  // LM_LOAD_COUNT
  curr_local_stat = lnstats->lm_load_count - ast.prev_event_lm_load_count;
  if(curr_local_stat > MAX_COUNT_BINS-1){
    lnstats->lm_load_count_per_event[MAX_COUNT_BINS-1]++;
  } else{
    lnstats->lm_load_count_per_event[curr_local_stat]++;
  }
  //printf("Debug: lm_load_count total:%lu, prev:%lu, curr:%lu\n", lnstats->lm_load_count, ast.prev_event_lm_load_count, curr_local_stat);
  ast.prev_event_lm_load_count = lnstats->lm_load_count;
  // LM_STORE_COUNT
  curr_local_stat = lnstats->lm_store_count - ast.prev_event_lm_store_count;
  if(curr_local_stat > MAX_COUNT_BINS-1){
    lnstats->lm_store_count_per_event[MAX_COUNT_BINS-1]++;
  } else{
    lnstats->lm_store_count_per_event[curr_local_stat]++;
  }
  //printf("Debug: lm_store_count total:%lu, prev:%lu, curr:%lu\n", lnstats->lm_store_count, ast.prev_event_lm_store_count, curr_local_stat);
  ast.prev_event_lm_store_count = lnstats->lm_store_count;

  // DRAM_LOAD_COUNT
  curr_local_stat = lnstats->dram_load_count - ast.prev_event_dram_load_count;
  if(curr_local_stat > MAX_COUNT_BINS-1){
    lnstats->dram_load_count_per_event[MAX_COUNT_BINS-1]++;
  } else{
    lnstats->dram_load_count_per_event[curr_local_stat]++;
  }
  //printf("Debug: dram_load_count total:%lu, prev:%lu, curr:%lu\n", lnstats->dram_load_count, ast.prev_event_dram_load_count, curr_local_stat);
  ast.prev_event_dram_load_count = lnstats->dram_load_count;

  // DRAM_STORE_COUNT
  curr_local_stat = lnstats->dram_store_count - ast.prev_event_dram_store_count;
  if(curr_local_stat > MAX_COUNT_BINS-1){
    lnstats->dram_store_count_per_event[MAX_COUNT_BINS-1]++;
  } else{
    lnstats->dram_store_count_per_event[curr_local_stat]++;
  }
  //printf("Debug: dram_store_count total:%lu, prev:%lu, curr:%lu\n", lnstats->dram_store_count, ast.prev_event_dram_store_count, curr_local_stat);
  ast.prev_event_dram_store_count = lnstats->dram_store_count;

  // DRAM_STORE_BYTES
  curr_local_stat = lnstats->dram_store_bytes - ast.prev_event_dram_store_bytes;
  if(curr_local_stat > MAX_BYTES_BINS-1){
    lnstats->dram_store_bytes_per_event[MAX_BYTES_BINS-1]++;
  } else{
    lnstats->dram_store_bytes_per_event[curr_local_stat]++;
  }
  //printf("Debug: dram_store_bytes total:%lu, prev:%lu, curr:%lu\n", lnstats->dram_store_bytes, ast.prev_event_dram_store_bytes, curr_local_stat);
  ast.prev_event_dram_store_bytes = lnstats->dram_store_bytes;

  // DRAM_LOAD_BYTES
  curr_local_stat = lnstats->dram_load_bytes - ast.prev_event_dram_load_bytes;
  if(curr_local_stat > MAX_BYTES_BINS-1){
    lnstats->dram_load_bytes_per_event[MAX_BYTES_BINS-1]++;
  } else{
    lnstats->dram_load_bytes_per_event[curr_local_stat]++;
  }
  //printf("Debug: dram_load_bytes total:%lu, prev:%lu, curr:%lu\n", lnstats->dram_load_bytes, ast.prev_event_dram_load_bytes, curr_local_stat);
  ast.prev_event_dram_load_bytes = lnstats->dram_load_bytes;

  // LM_LOAD_BYTES
  curr_local_stat = lnstats->lm_load_bytes - ast.prev_event_lm_load_bytes;
  if(curr_local_stat > MAX_BYTES_BINS-1){
    lnstats->lm_load_bytes_per_event[MAX_BYTES_BINS-1]++;
  } else{
    lnstats->lm_load_bytes_per_event[curr_local_stat]++;
  }
  ast.prev_event_lm_load_bytes = lnstats->lm_load_bytes;

  // LM_STORE_BYTES
  curr_local_stat = lnstats->lm_store_bytes - ast.prev_event_lm_store_bytes;
  if(curr_local_stat > MAX_BYTES_BINS-1){
    lnstats->lm_store_bytes_per_event[MAX_BYTES_BINS-1]++;
  } else{
    lnstats->lm_store_bytes_per_event[curr_local_stat]++;
  }
  ast.prev_event_lm_store_bytes = lnstats->lm_store_bytes;
  
#endif

  //update SBP if the stateproperty type was input consuming
  stateproperty_t sp = tst->getStateProperty();
  SBCR sbcr = tst->getSBCR();
  if(*ast.lanestate != LaneState::SBREFILL_TERM && *ast.lanestate != LaneState::SBREFILL_TERM_ACTION){
    // if condition added to allow action execution in SBREFILL state
    uint64_t curr_sbp = tst->readReg(RegId::X5);
    switch(sp.getType()){
        case StateProperty::COMMON:
        case StateProperty::BASIC:
        //case StateProperty::REFILL:
        case StateProperty::MAJORITY:
        case StateProperty::DEFAULT:
          if  (ast.currtrans.getType() != TransitionType::EVENT){
            curr_sbp += sbcr.getAdvanceWidth();
            if(((ast.currtrans).getType() == TransitionType::REFILL_WITH_ACTION) ||((ast.currtrans).getType() == TransitionType::REFILL))
              curr_sbp = curr_sbp - ast.currtrans.getAttachModeRefill(); 

            BASIM_INFOMSG("NWID:%u, TID:%u, Updated SBP after yield to (%ld)", tst->getNWIDbits(), tst->getTID(),tst->readReg(RegId::X5));
            tst->writeReg(RegId::X5, curr_sbp);
          }
          break;
        case StateProperty::FLAG:
        case StateProperty::EPSILON:
        case StateProperty::FLAG_DEFAULT:
        case StateProperty::FLAG_MAJORITY:
          default:
          // Nothing to be done for these
          break;
    }
  }

  // Adding Transition relevant updates to State_Property
  if(ast.currtrans.getType() != TransitionType::EVENT){
    //Set the State_property to EVENT
    tst->setStateProperty(ast.currtrans.getNextSp());
    stateproperty_t sp = (tst->getStateProperty());
    BASIM_INFOMSG("NWID:%u, TID:%u, Updated StateProperty after yield to (%s,stateID:%ld,value:%ld)", 
          tst->getNWIDbits(), tst->getTID(), sp.print_type(sp.getType()),sp.getState(),sp.getValue());
  }

  *ast.lanestate = LaneState::NULLSTATE;
  eventword_t ev = EventWord(tst->readReg(RegId::X2));
  auto numOp = ev.getNumOperands() + 2;
  (ast.eventq)->pop();
  (ast.opbuff)->clear(1);
  
  // This may not be necessary
  ast.uip += 4;
  lnstats->inst_count_threadctrl++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::YIELD)]++;
#endif
  return Cycles(THREAD_CTRL_CYCLES);
}

std::string disasmInstYield(EncInst inst) {
  std::string disasm_str;
  disasm_str += "YIELD";
  return disasm_str;
}

EncInst constrInstYield() {
  EncInst inst;
  embdInstOpcode(inst, Opcode::YIELD);
  return inst;
}


/* yieldt Instruction */
Cycles exeInstYieldt(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  *ast.lanestate = LaneState::NULLSTATE;
  eventword_t ev = EventWord(tst->readReg(RegId::X2));
  auto numOp = ev.getNumOperands() + 2;
  auto tid = ev.getThreadID();
  (ast.eventq)->pop();
  (ast.opbuff)->clear(1);
  (ast.tstable)->remfromTST(tid);
  if((lnstats->start_gt128th != -1) && ((ast.tstable)->numActiveThreads() < 128)){
    lnstats->cycles_gt128th += (ast.timestamp - lnstats->start_gt128th);
    lnstats->start_gt128th = -1;
  }
  
  // This may not be necessary
  ast.uip += 4;
  lnstats->inst_count_threadctrl++;

#ifdef DETAIL_STATS
  uint64_t curr_local_stat = 0;
  if(ast.curr_event_inst_count > MAX_BINS-1){
    lnstats->inst_per_event[MAX_BINS-1]++;
  } else{
    lnstats->inst_per_event[ast.curr_event_inst_count]++;
  }
  if(ast.curr_event_inst_count > lnstats->max_inst_per_event) {
    lnstats->max_inst_per_event = ast.curr_event_inst_count;
  }
  if(ast.curr_tx_inst_count > MAX_BINS-1){
    lnstats->inst_per_tx[MAX_BINS-1]++;
  } else{
    lnstats->inst_per_tx[ast.curr_tx_inst_count]++;
  }
  if (ast.curr_tx_inst_count > lnstats->max_inst_per_tx) {
    lnstats->max_inst_per_tx = ast.curr_tx_inst_count;
  }
  // LM_LOAD_COUNT
  curr_local_stat = lnstats->lm_load_count - ast.prev_event_lm_load_count;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->lm_load_count_per_event[MAX_BINS-1]++;
  } else{
    lnstats->lm_load_count_per_event[curr_local_stat]++;
  }
  ast.prev_event_lm_load_count = lnstats->lm_load_count;

  // LM_STORE_COUNT
  curr_local_stat = lnstats->lm_store_count - ast.prev_event_lm_store_count;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->lm_store_count_per_event[MAX_BINS-1]++;
  } else{
    lnstats->lm_store_count_per_event[curr_local_stat]++;
  }
  ast.prev_event_lm_store_count = lnstats->lm_store_count;

  // DRAM_LOAD_COUNT
  curr_local_stat = lnstats->dram_load_count - ast.prev_event_dram_load_count;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->dram_load_count_per_event[MAX_BINS-1]++;
  } else{
    lnstats->dram_load_count_per_event[curr_local_stat]++;
  }
  ast.prev_event_dram_load_count = lnstats->dram_load_count;

  // DRAM_STORE_COUNT
  curr_local_stat = lnstats->dram_store_count - ast.prev_event_dram_store_count;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->dram_store_count_per_event[MAX_BINS-1]++;
  } else{
    lnstats->dram_store_count_per_event[curr_local_stat]++;
  }
  ast.prev_event_dram_store_count = lnstats->dram_store_count;

  // DRAM_STORE_BYTES
  curr_local_stat = lnstats->dram_store_bytes - ast.prev_event_dram_store_bytes;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->dram_store_bytes_per_event[MAX_BINS-1]++;
  } else{
    lnstats->dram_store_bytes_per_event[curr_local_stat]++;
  }
  ast.prev_event_dram_store_bytes = lnstats->dram_store_bytes;

  // DRAM_LOAD_BYTES
  curr_local_stat = lnstats->dram_load_bytes - ast.prev_event_dram_load_bytes;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->dram_load_bytes_per_event[MAX_BINS-1]++;
  } else{
    lnstats->dram_load_bytes_per_event[curr_local_stat]++;
  }
  ast.prev_event_dram_load_bytes = lnstats->dram_load_bytes;

  // LM_LOAD_BYTES
  curr_local_stat = lnstats->lm_load_bytes - ast.prev_event_lm_load_bytes;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->lm_load_bytes_per_event[MAX_BINS-1]++;
  } else{
    lnstats->lm_load_bytes_per_event[curr_local_stat]++;
  }
  ast.prev_event_lm_load_bytes = lnstats->lm_load_bytes;

  // LM_STORE_BYTES
  curr_local_stat = lnstats->lm_store_bytes - ast.prev_event_lm_store_bytes;
  if(curr_local_stat > MAX_BINS-1){
    lnstats->lm_store_bytes_per_event[MAX_BINS-1]++;
  } else{
    lnstats->lm_store_bytes_per_event[curr_local_stat]++;
  }
  ast.prev_event_lm_store_bytes = lnstats->lm_store_bytes;
  
#endif

#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::YIELDT)]++;
#endif
  return Cycles(THREAD_CTRL_CYCLES);
}

std::string disasmInstYieldt(EncInst inst) {
  std::string disasm_str;
  disasm_str += "YIELDT";
  return disasm_str;
}

EncInst constrInstYieldt() {
  EncInst inst;
  embdInstOpcode(inst, Opcode::YIELDT);
  return inst;
}


}; // namespace basim
