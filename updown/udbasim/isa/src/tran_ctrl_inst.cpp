#include "tran_ctrl_inst.hh"
#include "archstate.hh"
#include "lanetypes.hh"
#include "debug.hh"

namespace basim {

/* lastact Instruction */
Cycles exeInstLastact(ArchState& ast, EncInst inst) {
  // Last Action needs to update the state property when not EVENT
  // Change Lanestate based on current lanestate
  // If EVENT_ACTION to TRANS 
  // If EVENT to SBREFILL_TERM 
  // if TRANS_ACTION to SBREFILL_TERM
  // update statepropeerty ot next_stateproperty
  ThreadStatePtr tst = ast.threadstate;
  
  if(*ast.lanestate == LaneState::EVENT_ACTION){
    *ast.lanestate = LaneState::TRANS;
    if(ast.currtrans.getType() != TransitionType::EVENT){
    //Set the State_property to EVENT
    tst->setStateProperty(ast.currtrans.getNextSp());
    stateproperty_t sp = (tst->getStateProperty());
    BASIM_INFOMSG("NWID:%u, TID:%u, Updated StateProperty after lastact to (%s,stateID:%ld,value:%ld)", tst->getNWIDbits(), tst->getTID(), sp.print_type(sp.getType()),sp.getState(),sp.getValue());
    }else{
      //start from where the previous transition was left off meaning before calling SBREFILL and TERM
      *ast.lanestate = LaneState::SBREFILL_TERM; 
    }
    // To keep TRANS EFA base - update uip = pgbase + curr_trans.target
    ast.uip = ast.pgbase + (ast.currtrans.getTarget());
  }
  else if(*ast.lanestate == LaneState::TRANS_ACTION)
    *ast.lanestate = LaneState::SBREFILL_TERM;
  else if(*ast.lanestate == LaneState::SBREFILL_TERM_ACTION)
    *ast.lanestate = LaneState::TRANS;
  else
    BASIM_ERROR("Encountered lastaction in invalid lanestate");
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::LASTACT)]++;
#endif
  return Cycles(1);
}

std::string disasmInstLastact(EncInst inst) {
  std::string disasm_str;
  disasm_str += "LASTACT";
  return disasm_str;
}

EncInst constrInstLastact() {
  EncInst inst;
  embdInstOpcode(inst, Opcode::LASTACT);
  return inst;
}


/* ssprop Instruction */
Cycles exeInstSsprop(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto X6_val = tst->readReg(RegId::X6);
  uint64_t type = extrInstSspropType(inst) & 0x000000000000000F;
  uint64_t val = extrInstSspropValue(inst) & 0x0000000000000FFF;
  regval_t result = (X6_val & 0xFFFFFFFFF000FFF0) | (val << 16) | type;
  tst->writeReg(RegId::X6, result);
  ast.uip += 4;
  lnstats->inst_count_tranctrl++;
  //update nextSp
   stateproperty_t nsp = ast.currtrans.getNextSp();
   nsp.setType(static_cast<StateProperty>(type));
   nsp.setValue(val);
   ast.currtrans.updateNextSp(nsp);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SSPROP)]++;
#endif
  return Cycles(1);
}

std::string disasmInstSsprop(EncInst inst) {
 stateproperty_t sp;
  std::string disasm_str;
  disasm_str += "SSPROP";
  disasm_str += std::string(" ") + std::string(sp.print_type(static_cast<StateProperty>(extrInstSspropType(inst))));
  disasm_str += std::string(" ") + std::to_string(extrInstSspropValue(inst));
  return disasm_str;
}

EncInst constrInstSsprop(uint64_t type, uint64_t value) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SSPROP);
  embdInstSspropType(inst, type);
  embdInstSspropValue(inst, value);
  return inst;
}


/* fstate Instruction */
Cycles exeInstFstate(ArchState& ast, EncInst inst) {
  BASIM_WARNING("INSTRUCTION fstate EXE NOT IMPLEMENTED");
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::FSTATE)]++;
#endif
  return Cycles(0);
}

std::string disasmInstFstate(EncInst inst) {
  std::string disasm_str;
  disasm_str += "FSTATE";
  disasm_str += std::string(" ") + std::to_string(extrInstFstateProp(inst));
  return disasm_str;
}

EncInst constrInstFstate(uint64_t prop) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::FSTATE);
  embdInstFstateProp(inst, prop);
  return inst;
}


/* siw Instruction */
Cycles exeInstSiw(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto sbcr_data = tst->readReg(RegId::X4);
  auto imm_val = extrInstSiwWidth(inst);
  regval_t result = (sbcr_data & 0xFFFFFF0FFFFFFFFF) | ((imm_val & static_cast<uint64_t>(0x000000000000000F)) << 36);
  tst->writeReg(RegId::X4, result);
    ast.uip += 4;
  lnstats->inst_count_tranctrl++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SIW)]++;
#endif
  return Cycles(1);
}

std::string disasmInstSiw(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SIW";
  disasm_str += std::string(" ") + std::to_string(extrInstSiwWidth(inst));
  return disasm_str;
}

EncInst constrInstSiw(uint64_t width) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SIW);
  embdInstSiwWidth(inst, width);
  return inst;
}


/* refill Instruction */
Cycles exeInstRefill(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto sbp_data = tst->readReg(RegId::X5);
  auto sbcr_data = tst->readReg(RegId::X4);
  auto imm_val = extrInstRefillImm(inst);
  regval_t result = sbp_data + ((sbcr_data & 0x0000000F00000000) >> 32) - imm_val;
  tst->writeReg(RegId::X5, result);
    ast.uip += 4;
  lnstats->inst_count_tranctrl++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::REFILL)]++;
#endif
  return Cycles(1);
}

std::string disasmInstRefill(EncInst inst) {
  std::string disasm_str;
  disasm_str += "REFILL";
  disasm_str += std::string(" ") + std::to_string(extrInstRefillImm(inst));
  return disasm_str;
}

EncInst constrInstRefill(uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::REFILL);
  embdInstRefillImm(inst, imm);
  return inst;
}


}; // namespace basim
