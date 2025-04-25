#include "int_cmp_inst.hh"
#include "archstate.hh"
#include "debug.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include "isa_cycles.hh"

namespace basim {

/* clti Instruction */
Cycles exeInstClti(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstCltiXs(inst)));
  auto imm_val = extrInstCltiImm(inst);
  regval_t result = src_data < imm_val ? 1 : 0;
  tst->writeReg(extrInstCltiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intcmp++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::CLTI)]++;
#endif
  return Cycles(CMP_WORD_CYCLES);
}

std::string disasmInstClti(EncInst inst) {
  std::string disasm_str;
  disasm_str += "CLTI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCltiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCltiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstCltiImm(inst));
  return disasm_str;
}

EncInst constrInstClti(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::CLTI);
  embdInstCltiXs(inst, Xs);
  embdInstCltiXd(inst, Xd);
  embdInstCltiImm(inst, imm);
  return inst;
}


/* cgti Instruction */
Cycles exeInstCgti(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstCgtiXs(inst)));
  auto imm_val = extrInstCgtiImm(inst);
  regval_t result = src_data > imm_val ? 1 : 0;
  tst->writeReg(extrInstCgtiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intcmp++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::CGTI)]++;
#endif
  return Cycles(CMP_WORD_CYCLES);
}

std::string disasmInstCgti(EncInst inst) {
  std::string disasm_str;
  disasm_str += "CGTI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCgtiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCgtiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstCgtiImm(inst));
  return disasm_str;
}

EncInst constrInstCgti(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::CGTI);
  embdInstCgtiXs(inst, Xs);
  embdInstCgtiXd(inst, Xd);
  embdInstCgtiImm(inst, imm);
  return inst;
}


/* ceqi Instruction */
Cycles exeInstCeqi(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto src_data = static_cast<int64_t>(tst->readReg(extrInstCeqiXs(inst)));
  auto imm_val = extrInstCeqiImm(inst);
  regval_t result = src_data == imm_val ? 1 : 0;
  tst->writeReg(extrInstCeqiXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_intcmp++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::CEQI)]++;
#endif
  return Cycles(CMP_WORD_CYCLES);
}

std::string disasmInstCeqi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "CEQI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCeqiXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCeqiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstCeqiImm(inst));
  return disasm_str;
}

EncInst constrInstCeqi(RegId Xs, RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::CEQI);
  embdInstCeqiXs(inst, Xs);
  embdInstCeqiXd(inst, Xd);
  embdInstCeqiImm(inst, imm);
  return inst;
}


/* clt, cgt, ceq, cstr Instruction */
Cycles exeInstCltCgtCeqCstr(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  int numbytes = 0;
  uint8_t data1, data2;
  auto lnstats = ast.lanestats;
  auto xs_data = static_cast<int64_t>(tst->readReg(extrInstCltXs(inst)));
  auto xt_data = static_cast<int64_t>(tst->readReg(extrInstCltXt(inst)));
  regval_t result;
  Cycles cycles;
  switch (extrInstCltFunc(inst)) {
  case 0: // CLT
    result = xs_data < xt_data ? 1 : 0;
    cycles = Cycles(CMP_WORD_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::CLT)]++;
#endif
    break;
  case 1: // CGT
    result = xs_data > xt_data ? 1 : 0;
    cycles = Cycles(CMP_WORD_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::CGT)]++;
#endif
    break;
  case 2: // CEQ
    result = xs_data == xt_data ? 1 : 0;
    cycles = Cycles(CMP_WORD_CYCLES);
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::CEQ)]++;
#endif
    break;
  case 3: // CSTR
    spd->readBytes(1, static_cast<Addr>(xs_data++), &data1);
    spd->readBytes(1, static_cast<Addr>(xt_data++), &data2);
    numbytes++;
    for(; (numbytes < 255) && (data1 == data2); numbytes++){
      spd->readBytes(1, static_cast<Addr>(xs_data++), &data1);
      spd->readBytes(1, static_cast<Addr>(xt_data++), &data2);
    }
    //tst->writeReg(extrInstCstrXd(inst), numbytes-1);
    result = numbytes - 1;
    cycles = Cycles((numbytes / WORDSIZE) * CMP_WORD_CYCLES); // FIXME: cycles
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::CSTR)]++;
#endif
    break;
  default:
    BASIM_ERROR("EXECUTING clt, cgt, ceq, cstr WITH UNKNOWN FUNC");
    break;
  }
  tst->writeReg(extrInstCltXd(inst), result);
  ast.uip += 4;
  lnstats->inst_count_intcmp++;
  return cycles;
}

std::string disasmInstCltCgtCeqCstr(EncInst inst) {
  std::string disasm_str;
  switch (extrInstCltFunc(inst)) {
  case 0:
    disasm_str += "CLT";
    break;
  case 1:
    disasm_str += "CGT";
    break;
  case 2:
    disasm_str += "CEQ";
    break;
  case 3:
    disasm_str += "CSTR";
    break;
  default:
    BASIM_ERROR("DISASM clt, cgt, ceq, cstr WITH UNKNOWN FUNC");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCltXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCltXt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCltXd(inst))];
  return disasm_str;
}

EncInst constrInstCltCgtCeqCstr(uint64_t func, RegId Xs, RegId Xt, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::CLT);
  embdInstCltFunc(inst, func);
  embdInstCltXs(inst, Xs);
  embdInstCltXt(inst, Xt);
  embdInstCltXd(inst, Xd);
  return inst;
}

}; // namespace basim
