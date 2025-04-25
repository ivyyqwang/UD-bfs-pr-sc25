#include "atomic_inst.hh"
#include "archstate.hh"
#include "lanetypes.hh"
#include "debug.hh"
#include "isa_cycles.hh"

namespace basim {

/* cswp Instruction */
Cycles exeInstCswp(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  ScratchPadPtr spd = ast.spd;
  auto src_addr = tst->readReg(extrInstCswpX1(inst));
  auto old_data = tst->readReg(extrInstCswpX3(inst));
  auto new_data = tst->readReg(extrInstCswpX4(inst));
  regval_t result = spd->readWord(src_addr);
  lnstats->lm_load_bytes += 8;
  lnstats->lm_load_count++;
  if (result == old_data) {
    spd->writeWord(src_addr, new_data);
    lnstats->lm_store_bytes += 8;
    lnstats->lm_store_count++;
  }
  tst->writeReg(extrInstCswpX2(inst), result);
    ast.uip += 4;

  lnstats->inst_count_atomic++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::CSWP)]++;
#endif
  return Cycles(ATOMIC_CYCLES);
}

std::string disasmInstCswp(EncInst inst) {
  std::string disasm_str;
  disasm_str += "CSWP";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCswpX1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCswpX2(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCswpX3(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCswpX4(inst))];
  return disasm_str;
}

EncInst constrInstCswp(RegId X1, RegId X2, RegId X3, RegId X4) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::CSWP);
  embdInstCswpX1(inst, X1);
  embdInstCswpX2(inst, X2);
  embdInstCswpX3(inst, X3);
  embdInstCswpX4(inst, X4);
  return inst;
}


/* cswpi Instruction */
Cycles exeInstCswpi(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  ScratchPadPtr spd = ast.spd;
  auto src_addr = tst->readReg(extrInstCswpX1(inst));
  auto old_data = extrInstCswpiImm1(inst);
  auto new_data = extrInstCswpiImm2(inst);
  regval_t result = spd->readWord(src_addr);
  lnstats->lm_load_bytes += 8;
  lnstats->lm_load_count++;
  if (result == old_data) {
    spd->writeWord(src_addr, new_data);
    lnstats->lm_store_bytes += 8;
    lnstats->lm_store_count++;
  }
  tst->writeReg(extrInstCswpX2(inst), result);
    ast.uip += 4;

  lnstats->inst_count_atomic++;
#ifdef INST_HIST
  ast.instCount[static_cast<size_t>(InstMap::CSWPI)]++;
#endif
  return Cycles(ATOMIC_CYCLES);
}

std::string disasmInstCswpi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "CSWPI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCswpiX1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstCswpiX2(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstCswpiImm1(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstCswpiImm2(inst));
  return disasm_str;
}

EncInst constrInstCswpi(RegId X1, RegId X2, int64_t imm1, int64_t imm2) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::CSWPI);
  embdInstCswpiX1(inst, X1);
  embdInstCswpiX2(inst, X2);
  embdInstCswpiImm1(inst, imm1);
  embdInstCswpiImm2(inst, imm2);
  return inst;
}


}; // namespace basim
