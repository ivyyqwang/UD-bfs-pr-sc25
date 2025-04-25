#include "int_arith_inst.hh"
#include "archstate.hh"
#include "debug.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include <cstdint>
#include "isa_cycles.hh"

namespace basim {

/* addi Instruction */
Cycles exeInstAddi(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstAddiXs(inst)));
  auto imm_val = extrInstAddiImm(inst);
  regval_t result = src_data + imm_val;
  tst->writeReg(extrInstAddiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::ADDI)]++;
#endif
  return Cycles(INT_ARITH_ADDSUB_CYCLES);
}

std::string disasmInstAddi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "ADDI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAddiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAddiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstAddiImm(inst));
  return disasm_str;
}

EncInst constrInstAddi(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::ADDI);
  embdInstAddiXs(inst, Xs);
  embdInstAddiXd(inst, Xd);
  embdInstAddiImm(inst, imm);
  return inst;
}


/* subi Instruction */
Cycles exeInstSubi(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstSubiXs(inst)));
  auto imm_val = extrInstSubiImm(inst);
  regval_t result = src_data - imm_val;
  tst->writeReg(extrInstSubiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SUBI)]++;
#endif
  return Cycles(INT_ARITH_ADDSUB_CYCLES);
}

std::string disasmInstSubi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SUBI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSubiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSubiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSubiImm(inst));
  return disasm_str;
}

EncInst constrInstSubi(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SUBI);
  embdInstSubiXs(inst, Xs);
  embdInstSubiXd(inst, Xd);
  embdInstSubiImm(inst, imm);
  return inst;
}


/* muli Instruction */
Cycles exeInstMuli(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstMuliXs(inst)));
  auto imm_val = extrInstMuliImm(inst);
  regval_t result = static_cast<uint64_t>(src_data * imm_val);
  tst->writeReg(extrInstMuliXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MULI)]++;
#endif
  return Cycles(INT_ARITH_MULDIV_CYCLES);
}

std::string disasmInstMuli(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MULI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMuliXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMuliXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMuliImm(inst));
  return disasm_str;
}

EncInst constrInstMuli(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MULI);
  embdInstMuliXs(inst, Xs);
  embdInstMuliXd(inst, Xd);
  embdInstMuliImm(inst, imm);
  return inst;
}


/* divi Instruction */
Cycles exeInstDivi(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstDiviXs(inst)));
  auto imm_val = extrInstDiviImm(inst);
  if (imm_val == 0) {
    BASIM_ERROR("Divide by zero");
  }
  regval_t result = static_cast<uint64_t>(src_data / imm_val);
  tst->writeReg(extrInstDiviXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::DIVI)]++;
#endif
  return Cycles(INT_ARITH_MULDIV_CYCLES);
}

std::string disasmInstDivi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "DIVI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstDiviXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstDiviXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstDiviImm(inst));
  return disasm_str;
}

EncInst constrInstDivi(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::DIVI);
  embdInstDiviXs(inst, Xs);
  embdInstDiviXd(inst, Xd);
  embdInstDiviImm(inst, imm);
  return inst;
}


/* modi Instruction */
Cycles exeInstModi(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstModiXs(inst)));
  auto imm_val = extrInstModiImm(inst);
  if (imm_val == 0) {
    BASIM_ERROR("Mod by zero");
  }
  regval_t result = static_cast<uint64_t>(src_data % imm_val);
  tst->writeReg(extrInstModiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MODI)]++;
#endif
  return Cycles(INT_ARITH_MULDIV_CYCLES);
}

std::string disasmInstModi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MODI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstModiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstModiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstModiImm(inst));
  return disasm_str;
}

EncInst constrInstModi(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MODI);
  embdInstModiXs(inst, Xs);
  embdInstModiXd(inst, Xd);
  embdInstModiImm(inst, imm);
  return inst;
}


/* add, sub, mul, div, mod Instruction */
Cycles exeInstAddSubMulDivMod(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src1_data = static_cast<int64_t>(tst->readReg(extrInstAddXs(inst)));
  auto src2_data = static_cast<int64_t>(tst->readReg(extrInstAddXt(inst)));
  int64_t result;
  Cycles cycles;
  switch (extrInstAddFunc(inst)) {
  case 0: // add
    result = src1_data + src2_data;
    cycles = Cycles(INT_ARITH_ADDSUB_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::ADD)]++;
#endif
    break;
  case 1: // sub
    result = src1_data - src2_data;
    cycles = Cycles(INT_ARITH_ADDSUB_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SUB)]++;
#endif
    break;
  case 2: // mul
    result = src1_data * src2_data;
    cycles = Cycles(INT_ARITH_MULDIV_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MUL)]++;
#endif
    break;
  case 3: // div
    if (src2_data == 0) {
      BASIM_ERROR("Divide by zero");
    }
    result = src1_data / src2_data;
    cycles = Cycles(INT_ARITH_MULDIV_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::DIV)]++;
#endif
    break;
  case 4: // mod
    if (src2_data == 0) {
      BASIM_ERROR("Mod by zero");
    }
    result = src1_data % src2_data;
    cycles = Cycles(INT_ARITH_MULDIV_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOD)]++;
#endif
    break;
  default:
    BASIM_ERROR("EXECUTING add, sub, mul, div, mod WITH UNKNOWN FUNC");
  }
  tst->writeReg(extrInstAddXd(inst), static_cast<uint64_t>(result));
    ast.uip += 4;
  return cycles;
}

std::string disasmInstAddSubMulDivMod(EncInst inst) {
  std::string disasm_str;
  switch (extrInstAddFunc(inst)) {
  case 0:
    disasm_str += "ADD";
    break;
  case 1:
    disasm_str += "SUB";
    break;
  case 2:
    disasm_str += "MUL";
    break;
  case 3:
    disasm_str += "DIV";
    break;
  case 4:
    disasm_str += "MOD";
    break;
  default:
    BASIM_ERROR("DISASM add, sub, mul, div, mod WITH UNKNOWN FUNC");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAddXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAddXt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstAddXd(inst))];
  return disasm_str;
}

EncInst constrInstAddSubMulDivMod(uint64_t func, RegId Xs, RegId Xt, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::ADD);
  embdInstAddFunc(inst, func);
  embdInstAddXs(inst, Xs);
  embdInstAddXt(inst, Xt);
  embdInstAddXd(inst, Xd);
  return inst;
}


/* sladdii Instruction */
Cycles exeInstSladdii(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstSladdiiXs(inst)));
  auto imm_val = extrInstSladdiiImm(inst);
  auto shift_val = extrInstSladdiiShift(inst);
  regval_t result = (src_data << shift_val) + imm_val;
  tst->writeReg(extrInstSladdiiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SLADDII)]++;
#endif
  return Cycles(INT_ARITH_ADDSUB_CYCLES);
}

std::string disasmInstSladdii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SLADDII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSladdiiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSladdiiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSladdiiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSladdiiImm(inst));
  return disasm_str;
}

EncInst constrInstSladdii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SLADDII);
  embdInstSladdiiXs(inst, Xs);
  embdInstSladdiiXd(inst, Xd);
  embdInstSladdiiShift(inst, shift);
  embdInstSladdiiImm(inst, imm);
  return inst;
}


/* slsubii Instruction */
Cycles exeInstSlsubii(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstSlsubiiXs(inst)));
  auto imm_val = extrInstSlsubiiImm(inst);
  auto shift_val = extrInstSlsubiiShift(inst);
  regval_t result = (src_data << shift_val) - imm_val;
  tst->writeReg(extrInstSlsubiiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SLSUBII)]++;
#endif
  return Cycles(INT_ARITH_ADDSUB_CYCLES);
}

std::string disasmInstSlsubii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SLSUBII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlsubiiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSlsubiiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSlsubiiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSlsubiiImm(inst));
  return disasm_str;
}

EncInst constrInstSlsubii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SLSUBII);
  embdInstSlsubiiXs(inst, Xs);
  embdInstSlsubiiXd(inst, Xd);
  embdInstSlsubiiShift(inst, shift);
  embdInstSlsubiiImm(inst, imm);
  return inst;
}


/* sraddii Instruction */
Cycles exeInstSraddii(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSraddiiXs(inst));
  auto imm_val = extrInstSraddiiImm(inst);
  auto shift_val = extrInstSraddiiShift(inst);
  regval_t result = (src_data >> shift_val) + imm_val;
  tst->writeReg(extrInstSraddiiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SRADDII)]++;
#endif
  return Cycles(INT_ARITH_ADDSUB_CYCLES);
}

std::string disasmInstSraddii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SRADDII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSraddiiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSraddiiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSraddiiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSraddiiImm(inst));
  return disasm_str;
}

EncInst constrInstSraddii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SRADDII);
  embdInstSraddiiXs(inst, Xs);
  embdInstSraddiiXd(inst, Xd);
  embdInstSraddiiShift(inst, shift);
  embdInstSraddiiImm(inst, imm);
  return inst;
}


/* srsubii Instruction */
Cycles exeInstSrsubii(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = tst->readReg(extrInstSrsubiiXs(inst));
  auto imm_val = extrInstSrsubiiImm(inst);
  auto shift_val = extrInstSrsubiiShift(inst);
  regval_t result = (src_data >> shift_val) - imm_val;
  tst->writeReg(extrInstSrsubiiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intarith++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::SRSUBII)]++;
#endif
  return Cycles(INT_ARITH_ADDSUB_CYCLES);
}

std::string disasmInstSrsubii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "SRSUBII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSrsubiiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstSrsubiiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstSrsubiiShift(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstSrsubiiImm(inst));
  return disasm_str;
}

EncInst constrInstSrsubii(RegId Xs, RegId Xd, uint64_t shift, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::SRSUBII);
  embdInstSrsubiiXs(inst, Xs);
  embdInstSrsubiiXd(inst, Xd);
  embdInstSrsubiiShift(inst, shift);
  embdInstSrsubiiImm(inst, imm);
  return inst;
}

}; // namespace basim
