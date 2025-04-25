#include "msg_inst.hh"
#include "archstate.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include "mmessage.hh"
#include "debug.hh"
#include "isa_cycles.hh"
#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace basim {

/* send Instruction */
Cycles exeInstSend(ArchState& ast, EncInst inst) {
  // send - send to another lane with event and continuation words
  // Xptr - data pointer in LM length of data in words 
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t mode = extrInstSendMode(inst);
  bool cont = ((mode & 0x1));
  //uint64_t len = extrInstSendLenw(inst) + 1;
  uint64_t len = extrInstSendLenw(inst) + 2;
  EventWord contword;
  if(cont){
    // Xc is continuation label - but how? 5 bits only - should this mean the register has the contination label?
    contword = EventWord(tst->readReg(RegId::X2));
    contword.setEventLabel(tst->readReg(extrInstSendXc(inst)));
  }else{
    RegId Xc = extrInstSendXc(inst);
    contword = EventWord(tst->readReg(Xc));
  }
  RegId Xptr = extrInstSendXptr(inst);
  EventWord ev = EventWord(tst->readReg(extrInstSendXe(inst)));
  ev.setNumOperands(len - 2);
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(ev.getNWID()),
    "Translation failed for nwid %d on nwid %d tid %d, INSTR=%u SEND dest_ev_reg=X%d data_ptr_reg=X%d cont_reg=X%d", \
    ev.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendXe(inst), (int) extrInstSendXptr(inst), (int) extrInstSendXc(inst));
  std::unique_ptr<MMessage> m(new MMessage(contword, ev, MType::M1Type));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  m->setLen(len);
  Addr spdAddr = tst->readReg(Xptr);
  BASIM_ERROR_IF(!ast.transmem->validate_sp_addr(spdAddr, len << 3),
    "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u SEND src_reg=X%d cont_reg=X%d", \
    spdAddr, spdAddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendXptr(inst), (int) extrInstSendXc(inst));

  word_t* dataptr = new word_t[len];
  for(auto i = 0; i < len; i++){
    dataptr[i] = spd->readWord(spdAddr + 8 * i); 
    lnstats->lm_load_bytes += 8;
    lnstats->lm_load_count++;
  }
  m->setMode(mode);
  #ifdef SENDPOLICY
    int policy = (ev.getNWID()).getSendPolicy();
    if(policy == 7) {
      Addr virtual_addr = static_cast<Addr>(dataptr[0]);
      Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
      BASIM_ERROR_IF(physical_addr == ast.transmem->INVALID_ADDR,
        "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u Send src_reg=X%d cont_reg=X%d", \
        virtual_addr, virtual_addr, tst->getNWIDbits(), tst->getTID(), inst, (int)extrInstSendXptr(inst), (int)extrInstSendopsXc(inst));
      m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
      dataptr[0] = physical_addr;
    }
  #endif
  m->addpayload(dataptr);
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  delete[] dataptr;
  // Cycles to be adjusted later
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_lane++;
  lnstats->message_bytes += len * 8;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SEND)]++;
#endif
  // Add 2 cycles for event word and cont word - 2 cycles we don't need this
  // Revised Feb23 - 2 cycles 
  return Cycles(SPD_SEND_CYCLES);
}

std::string disasmInstSend(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SEND";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendXe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendXptr(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSendLenw(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSendMode(inst));
  return disasm_str;
}

EncInst constrInstSend(RegId Xe, RegId Xc, RegId Xptr, uint64_t lenw, uint64_t mode) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SEND);
  embdInstSendXe(inst, Xe);
  embdInstSendXc(inst, Xc);
  embdInstSendXptr(inst, Xptr);
  embdInstSendLenw(inst, lenw);
  embdInstSendMode(inst, mode);
  return inst;
}


/* sendb Instruction */
Cycles exeInstSendb(ArchState& ast, EncInst inst) {
  BASIM_WARNING("INSTRUCTION sendb EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmInstSendb(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDB";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendbXe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendbXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendbXptr(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSendbLenw(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSendbMode(inst));
  return disasm_str;
}

EncInst constrInstSendb(RegId Xe, RegId Xc, RegId Xptr, uint64_t lenw, uint64_t mode) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDB);
  embdInstSendbXe(inst, Xe);
  embdInstSendbXc(inst, Xc);
  embdInstSendbXptr(inst, Xptr);
  embdInstSendbLenw(inst, lenw);
  embdInstSendbMode(inst, mode);
  return inst;
}


/* sendm Instruction */
Cycles exeInstSendm(ArchState& ast, EncInst inst) {
  // sendm - send to memory with continuation word or use continuation label to create a continuation word
  // Xptr - data pointer in LM length of data in words 
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t mode = extrInstSendmMode(inst);
  bool ldst = mode & 0x1;
  bool cont = ((mode & 0x2) >> 1);
  uint64_t len = extrInstSendmLenw(inst) + 1;
  EventWord contword;
  if(cont){
    // Xc is continuation label - but how? 5 bits only - should this mean the register has the contination label?
    contword = EventWord(tst->readReg(RegId::X2));
    contword.setEventLabel(tst->readReg(extrInstSendmXc(inst)));
  }else{
    RegId Xc = extrInstSendmXc(inst);
    contword = EventWord(tst->readReg(Xc));
  }
    contword.setNumOperands(len - 1);
  // Verify the NWID
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(contword.getNWID()),
    "Translation failed for continuation nwid %d on nwid %d tid %d, INSTR=%u SENDM src_reg=X%d cont_reg=X%d", \
    contword.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendmXptr(inst), (int) extrInstSendmXc(inst));
  RegId Xptr = extrInstSendmXptr(inst);
  std::unique_ptr<MMessage> m(new MMessage(contword, EventWord(0), MType::M2Type));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  m->setLen(len);
  if(ldst){ // if store
    Addr spdAddr = tst->readReg(Xptr);
    BASIM_ERROR_IF(!ast.transmem->validate_sp_addr(spdAddr, len << 3),
      "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u SENDM (store) src_reg=X%d cont_reg=X%d len=%ld", \
      spdAddr, spdAddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendmXptr(inst), (int) extrInstSendmXc(inst), len);
    word_t* dataptr = new word_t[len];
    for(auto i = 0; i < len; i++) {
      dataptr[i] = spd->readWord(spdAddr + 8 * i); 
      lnstats->lm_load_bytes += 8;
      lnstats->lm_load_count++;
    }
    m->addpayload(dataptr);
    lnstats->dram_store_bytes += 8 * len;
    lnstats->dram_store_count++;
    // test
    delete[] dataptr;
  } else { // load

    lnstats->dram_load_bytes += 8 * len;
    lnstats->dram_load_count++;
  }
  // Translate the address 
  Addr virtual_addr = static_cast<Addr>(tst->readReg(extrInstSendmXd(inst)));
  Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
  BASIM_ERROR_IF(ast.transmem->get_enable_translation() && physical_addr == ast.transmem->INVALID_ADDR,
    "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u Sendm dest_reg=X%d cont_reg=X%d", \
    tst->readReg(extrInstSendmXd(inst)), tst->readReg(extrInstSendmXd(inst)), tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendmXd(inst), (int) extrInstSendmXc(inst));
  m->setdestaddr(physical_addr);
  m->setMode(mode);
  m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_mem++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SENDM)]++;
#endif
  // Cycles to be adjusted later
  if(ldst){
    // store
    return Cycles(SPD_SEND_CYCLES);
  }else{
    // load
    return Cycles(REG_SEND_CYCLES);
  }
}

std::string disasmInstSendm(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDM";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmXd(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmXptr(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSendmLenw(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSendmMode(inst));
  return disasm_str;
}

EncInst constrInstSendm(RegId Xd, RegId Xc, RegId Xptr, uint64_t lenw, uint64_t mode) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDM);
  embdInstSendmXd(inst, Xd);
  embdInstSendmXc(inst, Xc);
  embdInstSendmXptr(inst, Xptr);
  embdInstSendmLenw(inst, lenw);
  embdInstSendmMode(inst, mode);
  return inst;
}


/* sendmb Instruction */
Cycles exeInstSendmb(ArchState& ast, EncInst inst) {
  BASIM_WARNING("INSTRUCTION sendmb EXE NOT IMPLEMENTED");
  return Cycles(0);
}

std::string disasmInstSendmb(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDMB";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmbXd(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmbXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmbXptr(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSendmbLenw(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSendmbMode(inst));
  return disasm_str;
}

EncInst constrInstSendmb(RegId Xd, RegId Xc, RegId Xptr, uint64_t lenw, uint64_t mode) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDMB);
  embdInstSendmbXd(inst, Xd);
  embdInstSendmbXc(inst, Xc);
  embdInstSendmbXptr(inst, Xptr);
  embdInstSendmbLenw(inst, lenw);
  embdInstSendmbMode(inst, mode);
  return inst;
}


/* sendr Instruction */
Cycles exeInstSendr(ArchState& ast, EncInst inst) {
  // send - send to another lane with event and continuation words
  // Xptr - data pointer in LM length of data in words 
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t len = 2;
  EventWord contword;
  RegId Xc = extrInstSendrXc(inst);
  contword = EventWord(tst->readReg(Xc));
  RegId X1 = extrInstSendrX1(inst);
  RegId X2 = extrInstSendrX2(inst);
  EventWord ev = EventWord(tst->readReg(extrInstSendrXe(inst)));
  ev.setNumOperands(len - 2);
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(ev.getNWID()),
    "Translation failed for nwid %d on nwid %d tid %d, INSTR=%u SENDR dest_ev_reg=X%d data_reg=X%d X%d cont_reg=X%d", \
    ev.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendrXe(inst), (int) extrInstSendrX1(inst), (int) extrInstSendrX2(inst), (int) extrInstSendrXc(inst));
  std::unique_ptr<MMessage> m(new MMessage(contword, ev, MType::M3Type));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  m->setLen(len);
  word_t dataptr[3];
  dataptr[0] = tst->readReg(X1); 
  dataptr[1] = tst->readReg(X2); 
  m->addpayload(std::move(dataptr));
  m->setMode(1);
  #ifdef SENDPOLICY
    int policy = (ev.getNWID()).getSendPolicy();
    if(policy == 7) {
      Addr virtual_addr = static_cast<Addr>(dataptr[0]);
      Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
      BASIM_ERROR_IF(physical_addr == ast.transmem->INVALID_ADDR,
        "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u SENDR dest_ev_reg=X%d data_reg=X%d X%d cont_reg=X%d", \
        virtual_addr, virtual_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendrXe(inst), (int) extrInstSendrX1(inst), (int) extrInstSendrX2(inst), (int) extrInstSendrXc(inst));
      m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
      m->setdestaddr(physical_addr);
    }
  #endif
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_lane++;
  lnstats->message_bytes += len * 8;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SENDR)]++;
#endif
  // Cycles to be adjusted later
  return Cycles(REG_SEND_CYCLES);
}

std::string disasmInstSendr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendrXe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendrXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendrX1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendrX2(inst))];
  return disasm_str;
}

EncInst constrInstSendr(RegId Xe, RegId Xc, RegId X1, RegId X2) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDR);
  embdInstSendrXe(inst, Xe);
  embdInstSendrXc(inst, Xc);
  embdInstSendrX1(inst, X1);
  embdInstSendrX2(inst, X2);
  return inst;
}


/* sendr3 Instruction */
Cycles exeInstSendr3(ArchState& ast, EncInst inst) {
  BASIM_INFOMSG("Executing SENDR3");
  // send - send to another lane with event and continuation words
  // Xptr - data pointer in LM length of data in words 
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t len = 3;
  EventWord contword;
  RegId Xc = extrInstSendr3Xc(inst);
  contword = EventWord(tst->readReg(Xc));
  RegId X1 = extrInstSendr3X1(inst);
  RegId X2 = extrInstSendr3X2(inst);
  RegId X3 = extrInstSendr3X3(inst);
  EventWord ev = EventWord(tst->readReg(extrInstSendr3Xe(inst)));
  ev.setNumOperands(len - 2);
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(ev.getNWID()),
    "Translation failed for nwid %d on nwid %d tid %d, INSTR=%u SENDR3 dest_ev_reg=X%d data_reg=X%d X%d X%d cont_reg=X%d", \
    ev.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendr3Xe(inst), (int) extrInstSendr3X1(inst), (int) extrInstSendr3X2(inst), (int) extrInstSendr3X3(inst), (int) extrInstSendr3Xc(inst));
  std::unique_ptr<MMessage> m(new MMessage(contword, ev, MType::M3Type));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  word_t dataptr[3];
  dataptr[0] = tst->readReg(X1); 
  dataptr[1] = tst->readReg(X2); 
  dataptr[2] = tst->readReg(X3); 
  m->setLen(len);
  m->addpayload(dataptr);
  m->setMode(1);
  #ifdef SENDPOLICY
    int policy = (ev.getNWID()).getSendPolicy();
    if(policy == 7) {
      Addr virtual_addr = static_cast<Addr>(dataptr[0]);
      Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
      BASIM_ERROR_IF(physical_addr == ast.transmem->INVALID_ADDR,
        "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u Sendr3 dest_ev_reg=X%d data_reg=X%d X%d X%d cont_reg=X%d", \
        virtual_addr, virtual_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendr3Xe(inst), (int) extrInstSendr3X1(inst), (int) extrInstSendr3X2(inst), (int) extrInstSendr3X3(inst), (int) extrInstSendr3Xc(inst));
      m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
      m->setdestaddr(physical_addr);
    }
  #endif
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_lane++;
  lnstats->message_bytes += len * 8;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SENDR3)]++;
#endif
  // Cycles to be adjusted later
  return Cycles(REG_SEND_CYCLES);
}

std::string disasmInstSendr3(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDR3";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendr3Xe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendr3Xc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendr3X1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendr3X2(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendr3X3(inst))];
  return disasm_str;
}

EncInst constrInstSendr3(RegId Xe, RegId Xc, RegId X1, RegId X2, RegId X3) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDR3);
  embdInstSendr3Xe(inst, Xe);
  embdInstSendr3Xc(inst, Xc);
  embdInstSendr3X1(inst, X1);
  embdInstSendr3X2(inst, X2);
  embdInstSendr3X3(inst, X3);
  return inst;
}


/* sendmr Instruction */
Cycles exeInstSendmr(ArchState& ast, EncInst inst) {
  // send - send to memory with event and continuation words
  // registers are payload to be written
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t len = 1;
  EventWord contword;
  RegId Xc = extrInstSendmrXc(inst);
  contword = EventWord(tst->readReg(Xc));
  // Verify the NWID
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(contword.getNWID()),
    "Translation failed for cont nwid %d on nwid %d tid %d, INSTR=%u SENDMR  data_reg=X%d cont_reg=X%d", \
      contword.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendmrX1(inst), (int) extrInstSendmrXc(inst));
  RegId X1 = extrInstSendmrX1(inst);
  RegId Xd = extrInstSendmrXd(inst);
  std::unique_ptr<MMessage> m(new MMessage(contword, EventWord(), MType::M3Type_M));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  m->setLen(len);
  word_t* dataptr = new word_t[len];
  dataptr[0] = tst->readReg(X1); 
  m->addpayload(dataptr);
  m->setMode(1);
  // Translate the address
  Addr virtual_addr = static_cast<Addr>(tst->readReg(Xd));
  Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
  BASIM_ERROR_IF(physical_addr == ast.transmem->INVALID_ADDR,
    "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u Sendmr dest_reg=X%d cont_reg=X%d", \
    virtual_addr, virtual_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) Xd, (int) Xc);
  m->setdestaddr(physical_addr);
  m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
  lnstats->dram_store_bytes += 8 * len;
  lnstats->dram_store_count++;
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_mem++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SENDMR)]++;
#endif
  delete[] dataptr;
  // Cycles to be adjusted later
  return Cycles(REG_SEND_CYCLES);
}

std::string disasmInstSendmr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDMR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmrXd(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmrXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmrX1(inst))];
  return disasm_str;
}

EncInst constrInstSendmr(RegId Xd, RegId Xc, RegId X1) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDMR);
  embdInstSendmrXd(inst, Xd);
  embdInstSendmrXc(inst, Xc);
  embdInstSendmrX1(inst, X1);
  return inst;
}


/* sendmr2 Instruction */
Cycles exeInstSendmr2(ArchState& ast, EncInst inst) {
  BASIM_INFOMSG("Executing SENDMR2");
  // send - send to another lane with event and continuation words
  // Xptr - data pointer in LM length of data in words 
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t len = 2;
  EventWord contword;
  RegId Xc = extrInstSendmr2Xc(inst);
  contword = EventWord(tst->readReg(Xc));
  // Verify the NWID
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(contword.getNWID()),
    "Translation failed for cont nwid %d on nwid %d tid %d, INSTR=%u SENDMR2 dest_addr_reg=X%d data_reg=X%d cont_reg=X%d", \
    contword.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendmr2Xd(inst), (int) extrInstSendmr2X1(inst), (int) extrInstSendmr2Xc(inst));
  RegId X1 = extrInstSendmr2X1(inst);
  RegId X2 = extrInstSendmr2X2(inst);
  RegId Xd = extrInstSendmr2Xd(inst);
  std::unique_ptr<MMessage> m(new MMessage(contword, EventWord(), MType::M3Type_M));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  m->setLen(len);
  word_t dataptr[2];
  dataptr[0] = tst->readReg(X1); 
  dataptr[1] = tst->readReg(X2); 
  m->addpayload(dataptr);
  m->setMode(1);
  // Translate the address
  Addr virtual_addr = static_cast<Addr>(tst->readReg(Xd));
  Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
  BASIM_ERROR_IF(physical_addr == ast.transmem->INVALID_ADDR,
    "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u Sendmr2 dest_reg=X%d cont_reg=X%d", \
    virtual_addr, virtual_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) Xd, (int) Xc);
  m->setdestaddr(physical_addr);
  m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
  lnstats->dram_store_bytes += 8 * len;
  lnstats->dram_store_count++;
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_mem++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SENDMR2)]++;
#endif
  // Cycles to be adjusted later
  return Cycles(REG_SEND_CYCLES);
}

std::string disasmInstSendmr2(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDMR2";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmr2Xd(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmr2Xc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmr2X1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmr2X2(inst))];
  return disasm_str;
}

EncInst constrInstSendmr2(RegId Xd, RegId Xc, RegId X1, RegId X2) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDMR2);
  embdInstSendmr2Xd(inst, Xd);
  embdInstSendmr2Xc(inst, Xc);
  embdInstSendmr2X1(inst, X1);
  embdInstSendmr2X2(inst, X2);
  return inst;
}


/* sendops Instruction */
Cycles exeInstSendops(ArchState& ast, EncInst inst) {
  // send - send to another lane with event and continuation words
  // Xptr - data pointer in LM length of data in words 
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t mode = extrInstSendopsMode(inst);
  bool cont = ((mode & 0x1));
  //uint64_t len = extrInstSendopsLenw(inst) + 1;
  uint64_t len = extrInstSendopsLenw(inst) + 2;
  EventWord contword;
  if(cont){
    // Xc is continuation label - but how? 5 bits only - should this mean the register has the contination label?
    contword = EventWord(tst->readReg(RegId::X2));
    contword.setEventLabel(tst->readReg(extrInstSendopsXc(inst)));
  }else{
    RegId Xc = extrInstSendopsXc(inst);
    contword = EventWord(tst->readReg(Xc));
  }
  RegId Xop = extrInstSendopsXop(inst);
  uint8_t regid = static_cast<uint8_t>(Xop);
  //std::shared_ptr<word_t[]> dataptr(new word_t[len]);
  word_t* dataptr = new word_t[len];
  for(auto i = 0; i < len; i++){
    dataptr[i] = tst->readReg(static_cast<RegId>(regid+i));
  }
  // Handle 9th operand
  if (len == 9)
    dataptr[8] = tst->readReg(RegId::X3);

  // Verify the NWID
  EventWord ev = EventWord(tst->readReg(extrInstSendopsXe(inst)));
  ev.setNumOperands(len - 2);
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(ev.getNWID()), 
    "Translation failed for nwid %d on nwid %d tid %d, INSTR=%u SENDOPS dest_ev_reg=X%d data_reg=X%d cont_reg=X%d", \
    ev.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendopsXe(inst), (int) extrInstSendopsXop(inst), (int) extrInstSendopsXc(inst));

  std::unique_ptr<MMessage> m(new MMessage(contword, ev, MType::M4Type));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  m->setLen(len);
  m->addpayload(dataptr);
  m->setMode(mode);
  #ifdef SENDPOLICY
    int policy = (ev.getNWID()).getSendPolicy();
    if(policy == 7) {
      Addr virtual_addr = static_cast<Addr>(dataptr[0]);
      Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
      BASIM_ERROR_IF(physical_addr == ast.transmem->INVALID_ADDR,
        "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u Sendops dest_ev_reg=X%d data_reg=X%d cont_reg=X%d", \
        virtual_addr, virtual_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendopsXe(inst), (int) extrInstSendopsXop(inst), (int) extrInstSendopsXc(inst));
      m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
      m->setdestaddr(physical_addr);
    }
  #endif
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_lane++;
  lnstats->message_bytes += len * 8;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SENDOPS)]++;
#endif
  delete[] dataptr;
  // Cycles to be adjusted later // Talk to Andrew about this
  return Cycles(REG_SEND_CYCLES);
}

std::string disasmInstSendops(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDOPS";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendopsXe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendopsXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendopsXop(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSendopsLenw(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSendopsMode(inst));
  return disasm_str;
}

EncInst constrInstSendops(RegId Xe, RegId Xc, RegId Xop, uint64_t lenw, uint64_t mode) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDOPS);
  embdInstSendopsXe(inst, Xe);
  embdInstSendopsXc(inst, Xc);
  embdInstSendopsXop(inst, Xop);
  embdInstSendopsLenw(inst, lenw);
  embdInstSendopsMode(inst, mode);
  return inst;
}


/* sendmops Instruction */
Cycles exeInstSendmops(ArchState& ast, EncInst inst) {
  // send - send to another lane with event and continuation words
  // Xptr - data pointer in LM length of data in words 
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t mode = extrInstSendmopsMode(inst);
  bool cont = ((mode & 0x1));
  uint64_t len = extrInstSendmopsLenw(inst) + 1;
  EventWord contword;
  if(cont){
    // Xc is continuation label - but how? 5 bits only - should this mean the register has the contination label?
    contword = EventWord(tst->readReg(RegId::X2));
    contword.setEventLabel(tst->readReg(extrInstSendmopsXc(inst)));
  }else{
    RegId Xc = extrInstSendmopsXc(inst);
    contword = EventWord(tst->readReg(Xc));
  }
  // Verify the NWID
  BASIM_ERROR_IF(!ast.transmem->validate_nwid(contword.getNWID()),
    "Translation failed for cont nwid %d on nwid %d tid %d, INSTR=%u SENDMOPS dest_ev_reg=X%d data_reg=X%d cont_reg=X%d", \
    contword.getNWID().networkid, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstSendmopsXe(inst), (int) extrInstSendmopsXop(inst), (int) extrInstSendmopsXc(inst));
  RegId Xop = extrInstSendmopsXop(inst);
  RegId Xd = extrInstSendmopsXd(inst);
  uint8_t regid = static_cast<uint8_t>(Xop);
  //std::shared_ptr<word_t[]> dataptr(new word_t[len]);
  word_t* dataptr = new word_t[len];
  for(auto i = 0; i < len; i++) {
    dataptr[i] = tst->readReg(static_cast<RegId>(regid + i));
  }
  std::unique_ptr<MMessage> m(new MMessage(contword, EventWord(tst->readReg(extrInstSendmopsXe(inst))), MType::M4Type_M));
  m->setSrcEventWord(EventWord(tst->readReg(RegId::X2)));
  m->setLen(len);
  m->addpayload(dataptr);
  // fix to 1 for stores
  m->setMode(1);
  lnstats->dram_store_bytes += 8 * len;
  lnstats->dram_store_count++;
  // Translate the address
  Addr virtual_addr = static_cast<Addr>(tst->readReg(Xd));
  Addr physical_addr = ast.transmem->translate_va2pa(virtual_addr, len);
  BASIM_ERROR_IF(physical_addr == ast.transmem->INVALID_ADDR,
    "Translation failed for address 0x%lx (%lu) on nwid %d tid %d, INSTR=%u Sendmops dest_reg=X%d cont_reg=X%d", \
    virtual_addr, virtual_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) Xd, (int) extrInstSendmopsXc(inst));
  m->setdestaddr(physical_addr);
  m->setIsGlobal(ast.transmem->isGlobal(virtual_addr));
  ast.sendbuffer->push(std::move(m));
  ast.uip += 4;
  delete[] dataptr;
  lnstats->inst_count_msg++;
  lnstats->inst_count_msg_mem++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SENDMOPS)]++;
#endif
  // Cycles to be adjusted later // talk to Andrew
  return Cycles(REG_SEND_CYCLES);
}

std::string disasmInstSendmops(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SENDMOPS";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmopsXe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmopsXd(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmopsXc(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSendmopsXop(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSendmopsLenw(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSendmopsMode(inst));
  return disasm_str;
}

EncInst constrInstSendmops(RegId Xe, RegId Xd, RegId Xc, RegId Xop, uint64_t lenw, uint64_t mode) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SENDMOPS);
  embdInstSendmopsXe(inst, Xe);
  embdInstSendmopsXd(inst, Xd);
  embdInstSendmopsXc(inst, Xc);
  embdInstSendmopsXop(inst, Xop);
  embdInstSendmopsLenw(inst, lenw);
  embdInstSendmopsMode(inst, mode);
  return inst;
}


/* instrans Instruction */
Cycles exeInstInstrans(ArchState& ast, EncInst inst) {
  
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  Addr virtual_base   = tst->readReg(extrInstInstransX1(inst));
  Addr physical_base  = tst->readReg(extrInstInstransX2(inst));
  uint64_t size = tst->readReg(extrInstInstransX3(inst));
  uint8_t mode  = extrInstInstransMode(inst);

  if (mode == 0) {
    BASIM_INFOMSG("Lane %d inserts local translation\n", tst->getNWIDbits());
    ast.transmem->insertLocalTrans(virtual_base, physical_base, size, extrInstInstransPerm(inst));
  } else if (mode == 1) {
    BASIM_INFOMSG("Lane %d inserts global translation\n", tst->getNWIDbits());
    uint64_t swizzle = tst->readReg(extrInstInstransX4(inst));
    ast.transmem->insertGlobalTrans(virtual_base, physical_base, size, swizzle, extrInstInstransPerm(inst));
  } else {
    BASIM_ERROR("Invalid mode for instrans instruction");
  }
  ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::INSTRANS)]++;
#endif
  
  return Cycles(ONE_CYCLE);
}

std::string disasmInstInstrans(EncInst inst) {
  std::string disasm_str;
  disasm_str += "INSTRANS";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstInstransX1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstInstransX4(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstInstransX2(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstInstransX3(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstInstransPerm(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstInstransMode(inst));
  return disasm_str;
}

EncInst constrInstInstrans(RegId X1, RegId X4, RegId X2, RegId X3, uint64_t perm, uint64_t mode) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::INSTRANS);
  embdInstInstransX1(inst, X1);
  embdInstInstransX4(inst, X4);
  embdInstInstransX2(inst, X2);
  embdInstInstransX3(inst, X3);
  embdInstInstransPerm(inst, perm);
  embdInstInstransMode(inst, mode);
  return inst;
}


}; // namespace basim
