#include "bitwise_inst.hh"
#include "archstate.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include "debug.hh"
#include <cstdint>
#include "isa_cycles.hh"

namespace basim {

/* sli Instruction */
Cycles exeInstSli(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSliXs(inst));
  auto shift_val = extrInstSliShift(inst);
  regval_t result = src_data << shift_val;
  tst->writeReg(extrInstSliXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SLI)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSli(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SLI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSliXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSliXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSliShift(inst));
  return disasm_str;
}

EncInst constrInstSli(RegId Xs, RegId Xd, uint64_t shift) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SLI);
  embdInstSliXs(inst, Xs);
  embdInstSliXd(inst, Xd);
  embdInstSliShift(inst, shift);
  return inst;
}


/* sri Instruction */
Cycles exeInstSri(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSriXs(inst));
  auto shift_val = extrInstSriShift(inst);
  regval_t result = src_data >> shift_val;
  tst->writeReg(extrInstSriXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SRI)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSri(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SRI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSriXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSriXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSriShift(inst));
  return disasm_str;
}

EncInst constrInstSri(RegId Xs, RegId Xd, uint64_t shift) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SRI);
  embdInstSriXs(inst, Xs);
  embdInstSriXd(inst, Xd);
  embdInstSriShift(inst, shift);
  return inst;
}


/* slori Instruction */
Cycles exeInstSlori(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSloriXs(inst));
  auto dst_data = tst->readReg(extrInstSloriXd(inst));
  auto imm_val = extrInstSloriShift(inst);
  regval_t result = dst_data | (src_data << imm_val);
  tst->writeReg(extrInstSloriXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SLORI)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSlori(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SLORI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSloriXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSloriXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSloriShift(inst));
  return disasm_str;
}

EncInst constrInstSlori(RegId Xs, RegId Xd, uint64_t shift) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SLORI);
  embdInstSloriXs(inst, Xs);
  embdInstSloriXd(inst, Xd);
  embdInstSloriShift(inst, shift);
  return inst;
}


/* srori Instruction */
Cycles exeInstSrori(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSroriXs(inst));
  auto dst_data = tst->readReg(extrInstSroriXd(inst));
  auto imm_val = extrInstSroriShift(inst);
  regval_t result = dst_data | (src_data >> imm_val);
  tst->writeReg(extrInstSroriXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SRORI)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSrori(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SRORI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSroriXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSroriXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSroriShift(inst));
  return disasm_str;
}

EncInst constrInstSrori(RegId Xs, RegId Xd, uint64_t shift) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SRORI);
  embdInstSroriXs(inst, Xs);
  embdInstSroriXd(inst, Xd);
  embdInstSroriShift(inst, shift);
  return inst;
}


/* slandi Instruction */
Cycles exeInstSlandi(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSlandiXs(inst));
  auto dst_data = tst->readReg(extrInstSlandiXd(inst));
  auto imm_val = extrInstSlandiShift(inst);
  regval_t result = dst_data & (src_data << imm_val);
  tst->writeReg(extrInstSlandiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SLANDI)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSlandi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SLANDI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlandiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlandiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSlandiShift(inst));
  return disasm_str;
}

EncInst constrInstSlandi(RegId Xs, RegId Xd, uint64_t shift) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SLANDI);
  embdInstSlandiXs(inst, Xs);
  embdInstSlandiXd(inst, Xd);
  embdInstSlandiShift(inst, shift);
  return inst;
}


/* srandi Instruction */
Cycles exeInstSrandi(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSrandiXs(inst));
  auto dst_data = tst->readReg(extrInstSrandiXd(inst));
  auto imm_val = extrInstSrandiShift(inst);
  regval_t result = dst_data & (src_data >> imm_val);
  tst->writeReg(extrInstSrandiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SRANDI)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSrandi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SRANDI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSrandiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSrandiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSrandiShift(inst));
  return disasm_str;
}

EncInst constrInstSrandi(RegId Xs, RegId Xd, uint64_t shift) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SRANDI);
  embdInstSrandiXs(inst, Xs);
  embdInstSrandiXd(inst, Xd);
  embdInstSrandiShift(inst, shift);
  return inst;
}


/* slorii Instruction */
Cycles exeInstSlorii(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSloriiXs(inst));
  auto imm_val = extrInstSloriiImm(inst);
  auto shift_val = extrInstSloriiShift(inst);
  regval_t result = imm_val | (src_data << shift_val);
  tst->writeReg(extrInstSloriiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SLORII)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSlorii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SLORII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSloriiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSloriiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSloriiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSloriiImm(inst));
  return disasm_str;
}

EncInst constrInstSlorii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SLORII);
  embdInstSloriiXs(inst, Xs);
  embdInstSloriiXd(inst, Xd);
  embdInstSloriiShift(inst, shift);
  embdInstSloriiImm(inst, imm);
  return inst;
}


/* srorii Instruction */
Cycles exeInstSrorii(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSroriiXs(inst));
  auto imm_val = extrInstSroriiImm(inst);
  auto shift_val = extrInstSroriiShift(inst);
  regval_t result = imm_val | (src_data >> shift_val);
  tst->writeReg(extrInstSroriiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SRORII)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSrorii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SRORII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSroriiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSroriiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSroriiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSroriiImm(inst));
  return disasm_str;
}

EncInst constrInstSrorii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SRORII);
  embdInstSroriiXs(inst, Xs);
  embdInstSroriiXd(inst, Xd);
  embdInstSroriiShift(inst, shift);
  embdInstSroriiImm(inst, imm);
  return inst;
}


/* slandii Instruction */
Cycles exeInstSlandii(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSlandiiXs(inst));
  auto imm_val = extrInstSlandiiImm(inst);
  auto shift_val = extrInstSlandiiShift(inst);
  regval_t result = imm_val & (src_data << shift_val);
  tst->writeReg(extrInstSlandiiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SLANDII)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSlandii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SLANDII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlandiiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlandiiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSlandiiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSlandiiImm(inst));
  return disasm_str;
}

EncInst constrInstSlandii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SLANDII);
  embdInstSlandiiXs(inst, Xs);
  embdInstSlandiiXd(inst, Xd);
  embdInstSlandiiShift(inst, shift);
  embdInstSlandiiImm(inst, imm);
  return inst;
}


/* srandii Instruction */
Cycles exeInstSrandii(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSrandiiXs(inst));
  auto imm_val = extrInstSrandiiImm(inst);
  auto shift_val = extrInstSrandiiShift(inst);
  regval_t result = imm_val & (src_data >> shift_val);
  tst->writeReg(extrInstSrandiiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SRANDII)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSrandii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SRANDII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSrandiiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSrandiiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSrandiiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSrandiiImm(inst));
  return disasm_str;
}

EncInst constrInstSrandii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SRANDII);
  embdInstSrandiiXs(inst, Xs);
  embdInstSrandiiXd(inst, Xd);
  embdInstSrandiiShift(inst, shift);
  embdInstSrandiiImm(inst, imm);
  return inst;
}


/* sari Instruction */
Cycles exeInstSari(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSariXs(inst));
  auto imm_val = extrInstSariShift(inst);
  int64_t tmp_result = (*((int64_t *)&src_data)) >> imm_val;
  regval_t result = *((regval_t *)&tmp_result);
  tst->writeReg(extrInstSariXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::SARI)]++;
#endif
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSari(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SARI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSariXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSariXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSariShift(inst));
  return disasm_str;
}

EncInst constrInstSari(RegId Xs, RegId Xd, uint64_t shift) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SARI);
  embdInstSariXs(inst, Xs);
  embdInstSariXd(inst, Xd);
  embdInstSariShift(inst, shift);
  return inst;
}


/* sr, sl, sar Instruction */
Cycles exeInstSrSlSar(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  regval_t src_data = tst->readReg(extrInstSrXs(inst));
  regval_t tmp_data = tst->readReg(extrInstSrXt(inst));
  regval_t tmp_result;
  regval_t result;

  switch (extrInstSrFunc(inst)) {
  case 0:
    BASIM_INFOMSG("NWID:%u, TID:%u,Executing SR", tst->getNWIDbits(), tst->getTID());
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SR)]++;
#endif
    if (tmp_data > 63) 
      result = 0;
    else
      result = src_data >> tmp_data;
    break;
  case 1:
    BASIM_INFOMSG("NWID:%u, TID:%u,Executing SL", tst->getNWIDbits(), tst->getTID());
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SL)]++;
#endif
    if (tmp_data > 63) 
      result = 0;
    else
      result = src_data << tmp_data;
    break;
  case 2:
    BASIM_INFOMSG("NWID:%u, TID:%u,Executing SAR", tst->getNWIDbits(), tst->getTID());
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SAR)]++;
#endif
    if (tmp_data > 63) 
      if (src_data & 0x8000000000000000)
        tmp_result = 0xFFFFFFFFFFFFFFFF;
      else
        tmp_result = 0;
    else
      tmp_result = (*((int64_t *)&src_data)) >> tmp_data;
    result = *((regval_t *)&tmp_result);
    break;
  default:
    BASIM_ERROR("NWID:%u, TID:%u,EXECUTING sr, sl, sar WITH UNKNOWN FUNC", tst->getNWIDbits(), tst->getTID());
    return Cycles(ZERO_CYCLES);
  }
  tst->writeReg(extrInstSrXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
  return Cycles(BITWISE_CYCLES);
}

std::string disasmInstSrSlSar(EncInst inst) {
  std::string disasm_str;
  switch (extrInstSrFunc(inst)) {
  case 0:
    disasm_str += "SR";
    break;
  case 1:
    disasm_str += "SL";
    break;
  case 2:
    disasm_str += "SAR";
    break;
  default:
    BASIM_ERROR("DISASM sr, sl, sar WITH UNKNOWN FUNC");
    break;
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlXt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlXd(inst))];
  return disasm_str;
}

EncInst constrInstSrSlSar(uint64_t func, RegId Xs, RegId Xt, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SL);
  embdInstSlFunc(inst, func);
  embdInstSlXs(inst, Xs);
  embdInstSlXt(inst, Xt);
  embdInstSlXd(inst, Xd);
  return inst;
}


/* andi Instruction */
Cycles exeInstAndi(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstAndiXs(inst));
  uint64_t imm_val = extrInstAndiImm(inst);
  regval_t result = src_data & imm_val;
  tst->writeReg(extrInstAndiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::ANDI)]++;
#endif
  return Cycles(1);
}

std::string disasmInstAndi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "ANDI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAndiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAndiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstAndiImm(inst));
  return disasm_str;
}

EncInst constrInstAndi(RegId Xs, RegId Xd, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::ANDI);
  embdInstAndiXs(inst, Xs);
  embdInstAndiXd(inst, Xd);
  embdInstAndiImm(inst, imm);
  return inst;
}


/* and, or, xor Instruction */
Cycles exeInstAndOrXor(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  regval_t src_data = tst->readReg(extrInstAndXs(inst));
  regval_t tmp_data = tst->readReg(extrInstAndXt(inst));
  regval_t result;

  switch (extrInstAndFunc(inst)) {
  case 0:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::AND)]++;
#endif
    result = src_data & tmp_data;
    break;
  case 1:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::OR)]++;
#endif
    result = src_data | tmp_data;
    break;
  case 2:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::XOR)]++;
#endif
    result = src_data ^ tmp_data;
    break;
  default:
    BASIM_ERROR("NWID:%u, TID:%u, EXECUTING sr, sl, sar WITH UNKNOWN FUNC", tst->getNWIDbits(), tst->getTID());
    return Cycles(0);
  }
  tst->writeReg(extrInstAndXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
  return Cycles(1);
}

std::string disasmInstAndOrXor(EncInst inst) {
  std::string disasm_str;
  switch (extrInstAndFunc(inst)) {
  case 0:
    disasm_str += "AND";
    break;
  case 1:
    disasm_str += "OR";
    break;
  case 2:
    disasm_str += "XOR";
    break;
  default:
    BASIM_ERROR("DISASM and, or, xor WITH UNKNOWN FUNC");
    break;
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAndXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAndXt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAndXd(inst))];
  return disasm_str;
}

EncInst constrInstAndOrXor(uint64_t func, RegId Xs, RegId Xt, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::AND);
  embdInstAndFunc(inst, func);
  embdInstAndXs(inst, Xs);
  embdInstAndXt(inst, Xt);
  embdInstAndXd(inst, Xd);
  return inst;
}


/* ori Instruction */
Cycles exeInstOri(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstOriXs(inst));
  uint64_t imm_val = extrInstOriImm(inst);
  regval_t result = src_data | imm_val;
  tst->writeReg(extrInstOriXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::ORI)]++;
#endif
  return Cycles(1);
}

std::string disasmInstOri(EncInst inst) {
  std::string disasm_str;
  disasm_str += "ORI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstOriXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstOriXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstOriImm(inst));
  return disasm_str;
}

EncInst constrInstOri(RegId Xs, RegId Xd, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::ORI);
  embdInstOriXs(inst, Xs);
  embdInstOriXd(inst, Xd);
  embdInstOriImm(inst, imm);
  return inst;
}


/* xori Instruction */
Cycles exeInstXori(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstXoriXs(inst));
  uint64_t imm_val = extrInstXoriImm(inst);
  regval_t result = src_data ^ imm_val;
  tst->writeReg(extrInstXoriXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::XORI)]++;
#endif
  return Cycles(1);
}

std::string disasmInstXori(EncInst inst) {
  std::string disasm_str;
  disasm_str += "XORI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstXoriXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstXoriXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstXoriImm(inst));
  return disasm_str;
}

EncInst constrInstXori(RegId Xs, RegId Xd, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::XORI);
  embdInstXoriXs(inst, Xs);
  embdInstXoriXd(inst, Xd);
  embdInstXoriImm(inst, imm);
  return inst;
}

/* swiz Instruction */
Cycles exeInstSwiz(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto mask = tst->readReg(extrInstSwizXs(inst));
  regval_t result = tst->readReg(extrInstSwizXd(inst));

  uint64_t prev_bit_val = 1; 
  uint64_t st_bit = 0, end_bit = 0;
  uint8_t one_seg_num_bits = 0, zero_seg_num_bits = 0;

  for (uint64_t i = 0; i < 64; i++) {
    uint64_t cur_bit = 1ull << i;
    uint64_t cur_bit_val = cur_bit & mask;
    if (cur_bit_val && !prev_bit_val) { // 0 -> 1
      // mark end (middle of the two adjacent swizzle segments)
      end_bit = cur_bit;
      one_seg_num_bits = 1;
    } else if (!cur_bit_val && prev_bit_val) { // 1 -> 0
      // perform swizzle
      uint64_t tmp = ((end_bit - st_bit) & result) << one_seg_num_bits;
      result = (result & ~(cur_bit - st_bit)) | tmp | (((cur_bit - end_bit) & result) >> zero_seg_num_bits);
      // mark start (start of the two adjacent swizzle segments)
      st_bit = cur_bit;
      zero_seg_num_bits = 1;
    } else if (!cur_bit_val && !prev_bit_val) { // 0 -> 0
      zero_seg_num_bits++;
    } else { // 1 -> 1
      one_seg_num_bits++;
    }
    prev_bit_val = cur_bit_val;
  }
  // last swizzle segment
  if (prev_bit_val) {
    // perform swizzle
    uint64_t tmp = ((end_bit - st_bit) & result) << one_seg_num_bits;
    result = (result & ~(0xFFFFFFFFFFFFFFFF - st_bit + 1)) | tmp | (((0xFFFFFFFFFFFFFFFF - end_bit + 1) & result) >> zero_seg_num_bits);
  }
  tst->writeReg(extrInstSwizXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_bitwise++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SWIZ)]++;
#endif
  return Cycles(1);
}

std::string disasmInstSwiz(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SWIZ";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSwizXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSwizXd(inst))];
  return disasm_str;
}

EncInst constrInstSwiz(RegId Xs, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SWIZ);
  embdInstSwizXs(inst, Xs);
  embdInstSwizXd(inst, Xd);
  return inst;
}


}; // namespace basim
