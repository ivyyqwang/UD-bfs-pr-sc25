#include "ctrl_flow_inst.hh"
#include "archstate.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include "stats.hh"
#include "debug.hh"
#include <cstdint>
#include "isa_cycles.hh"

namespace basim {

/* bne, beq, bgt, ble Instruction */
Cycles exeInstBneBeqBgtBle(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto xs1_data = static_cast<int64_t>(tst->readReg(extrInstBneX1(inst)));
  auto xs2_data = static_cast<int64_t>(tst->readReg(extrInstBneX2(inst)));
  auto offset = static_cast<int64_t>(extrInstBneTargeta(inst) | (extrInstBneTargetb(inst) << BF_BNE_TARGETA_NBITS));
  
  switch (extrInstBneFunc(inst)) {
  case 0:
    if (xs1_data != xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
      ast.uip += 4;
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 1:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BEQ)]++;
#endif
    if (xs1_data == xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 2:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BGT)]++;
#endif
    if (xs1_data > xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 3:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BLE)]++;
#endif
    if (xs1_data <= xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  default:
    BASIM_ERROR("EXECUTING bne, beq, bgt, ble WITH UNKNOWN FUNC");
    return Cycles(0);
  }
}

std::string disasmInstBneBeqBgtBle(EncInst inst) {
  std::string disasm_str;
  switch (extrInstBneFunc(inst)) {
  case 0:
    disasm_str += "BNE";
    break;
  case 1:
    disasm_str += "BEQ";
    break;
  case 2:
    disasm_str += "BGT";
    break;
  case 3:
    disasm_str += "BLE";
    break;
  default:
    BASIM_ERROR("DISASM bne, beq, bgt, ble WITH UNKNOWN FUNC");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBneX1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBneX2(inst))];
  disasm_str += std::string(" ") + std::to_string(static_cast<int64_t>(extrInstBneTargeta(inst) | (extrInstBneTargetb(inst) << BF_BNE_TARGETA_NBITS)));
  return disasm_str;
}

EncInst constrInstBneBeqBgtBle(uint64_t func, RegId X1, RegId X2, uint64_t targeta, int64_t targetb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BNE);
  embdInstBneFunc(inst, func);
  embdInstBneX1(inst, X1);
  embdInstBneX2(inst, X2);
  embdInstBneTargeta(inst, targeta);
  embdInstBneTargetb(inst, targetb);
  return inst;
}


/* bneu, bequ, bgtu, bleu Instruction */
Cycles exeInstBneuBequBgtuBleu(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto xs1_data = static_cast<uint64_t>(tst->readReg(extrInstBneuX1(inst)));
  auto xs2_data = static_cast<uint64_t>(tst->readReg(extrInstBneuX2(inst)));
  auto offset = static_cast<int64_t>(extrInstBneuTargeta(inst) | (extrInstBneuTargetb(inst) << BF_BNEU_TARGETA_NBITS));
  
  switch (extrInstBneuFunc(inst)) {
  case 0:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNEU)]++;
#endif
    if (xs1_data != xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 1:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BEQU)]++;
#endif
    if (xs1_data == xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 2:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BGTU)]++;
#endif
    if (xs1_data > xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 3:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BLEU)]++;
#endif
    if (xs1_data <= xs2_data) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  default:
    BASIM_ERROR("EXECUTING bneu, bequ, bgtu, bleu WITH UNKNOWN FUNC");
    return Cycles(0);
  }
}

std::string disasmInstBneuBequBgtuBleu(EncInst inst) {
  std::string disasm_str;
  switch (extrInstBneuFunc(inst)) {
  case 0:
    disasm_str += "BNEU";
    break;
  case 1:
    disasm_str += "BEQU";
    break;
  case 2:
    disasm_str += "BGTU";
    break;
  case 3:
    disasm_str += "BLEU";
    break;
  default:
    BASIM_ERROR("DISASM bneu, bequ, bgtu, bleu WITH UNKNOWN FUNC");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBneuX1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBneuX2(inst))];
  disasm_str += std::string(" ") + std::to_string(static_cast<int64_t>(extrInstBneuTargeta(inst) | (extrInstBneuTargetb(inst) << BF_BNEU_TARGETA_NBITS)));
  return disasm_str;
}

EncInst constrInstBneuBequBgtuBleu(uint64_t func, RegId X1, RegId X2, uint64_t targeta, int64_t targetb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BNEU);
  embdInstBneuFunc(inst, func);
  embdInstBneuX1(inst, X1);
  embdInstBneuX2(inst, X2);
  embdInstBneuTargeta(inst, targeta);
  embdInstBneuTargetb(inst, targetb);
  return inst;
}


/* bnei, beqi, bgti, blei, blti, bgei Instruction */
Cycles exeInstBneiBeqiBgtiBleiBltiBgei(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto xs_data = static_cast<int64_t>(tst->readReg(extrInstBneiX1(inst)));
  auto imm = extrInstBneiImm(inst);
  auto offset = static_cast<int64_t>(extrInstBneiTargeta(inst) | (extrInstBneiTargetb(inst) << BF_BNEI_TARGETA_NBITS));
  
  switch (extrInstBneiFunc(inst)) {
  case 0:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNEI)]++;
#endif
    if (xs_data != imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 1:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BEQI)]++;
#endif
    if (xs_data == imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 2:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BGTI)]++;
#endif
    if (xs_data > imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 3:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BLEI)]++;
#endif
    if (xs_data <= imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 4:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BLTI)]++;
#endif
    if (xs_data < imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 5:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BGEI)]++;
#endif
    if (xs_data >= imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  default:
    BASIM_ERROR("EXECUTING bnei, beqi, bgti, blei, blti, bgei WITH UNKNOWN FUNC");
    return Cycles(0);
  }
}

std::string disasmInstBneiBeqiBgtiBleiBltiBgei(EncInst inst) {
  std::string disasm_str;
  switch (extrInstBneiFunc(inst)) {
  case 0:
    disasm_str += "BNEI";
    break;
  case 1:
    disasm_str += "BEQI";
    break;
  case 2:
    disasm_str += "BGTI";
    break;
  case 3:
    disasm_str += "BLEI";
    break;
  case 4:
    disasm_str += "BLTI";
    break;
  case 5:
    disasm_str += "BGEI";
    break;
  default:
    BASIM_ERROR("DISASM bnei, beqi, bgti, blei, blti, bgei WITH UNKNOWN FUNC");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBneiX1(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstBneiImm(inst));
  disasm_str += std::string(" ") + std::to_string(static_cast<int64_t>(extrInstBneiTargeta(inst) | (extrInstBneiTargetb(inst) << BF_BNEI_TARGETA_NBITS)));
  return disasm_str;
}

EncInst constrInstBneiBeqiBgtiBleiBltiBgei(uint64_t func, RegId X1, int64_t imm, uint64_t targeta, int64_t targetb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BNEI);
  embdInstBneiFunc(inst, func);
  embdInstBneiX1(inst, X1);
  embdInstBneiImm(inst, imm);
  embdInstBneiTargeta(inst, targeta);
  embdInstBneiTargetb(inst, targetb);
  return inst;
}


/* bneiu, beqiu, bgtiu, bleiu, bltiu, bgeiu Instruction */
Cycles exeInstBneiuBeqiuBgtiuBleiuBltiuBgeiu(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto xs_data = static_cast<uint64_t>(tst->readReg(extrInstBneiuX1(inst)));
  auto imm = extrInstBneiuImm(inst);
  auto offset = static_cast<int64_t>(extrInstBneiuTargeta(inst) | (extrInstBneiuTargetb(inst) << BF_BNEIU_TARGETA_NBITS));
  
  switch (extrInstBneiuFunc(inst)) {
  case 0:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNEIU)]++;
#endif
    if (xs_data != imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 1:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BEQIU)]++;
#endif
    if (xs_data == imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 2:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BGTIU)]++;
#endif
    if (xs_data > imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 3:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BLEIU)]++;
#endif
    if (xs_data <= imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 4:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BLTIU)]++;
#endif
    if (xs_data < imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  case 5:
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BGEIU)]++;
#endif
    if (xs_data >= imm) {
      ast.uip += offset;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BTAKEN)]++;
#endif
    } else {
      ast.uip += 4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BNTAKEN)]++;
#endif
    }
    lnstats->inst_count_ctrlflow++;
    return Cycles(CTRL_FLOW_CYCLES);
  default:
    BASIM_ERROR("EXECUTING bneiu, beqiu, bgtiu, bleiu, bltiu, bgeiu WITH UNKNOWN FUNC");
    return Cycles(0);
  }
}

std::string disasmInstBneiuBeqiuBgtiuBleiuBltiuBgeiu(EncInst inst) {
  std::string disasm_str;
  switch (extrInstBneiFunc(inst)) {
  case 0:
    disasm_str += "BNEIU";
    break;
  case 1:
    disasm_str += "BEQIU";
    break;
  case 2:
    disasm_str += "BGTIU";
    break;
  case 3:
    disasm_str += "BLEIU";
    break;
  case 4:
    disasm_str += "BLTIU";
    break;
  case 5:
    disasm_str += "BGEIU";
    break;
  default:
    BASIM_ERROR("DISASM bneiu, beqiu, bgtiu, bleiu, bltiu, bgeiu WITH UNKNOWN FUNC");
  }
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBneiuX1(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstBneiuImm(inst));
  disasm_str += std::string(" ") + std::to_string(static_cast<int64_t>(extrInstBneiuTargeta(inst) | (extrInstBneiuTargetb(inst) << BF_BNEIU_TARGETA_NBITS)));
  return disasm_str;
}

EncInst constrInstBneiuBeqiuBgtiuBleiuBltiuBgeiu(uint64_t func, RegId X1, uint64_t imm, uint64_t targeta, int64_t targetb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BNEIU);
  embdInstBneiuFunc(inst, func);
  embdInstBneiuX1(inst, X1);
  embdInstBneiuImm(inst, imm);
  embdInstBneiuTargeta(inst, targeta);
  embdInstBneiuTargetb(inst, targetb);
  return inst;
}


/* jmp Instruction */
Cycles exeInstJmp(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto offset = extrInstJmpImm(inst);
    ast.uip += offset;
  lnstats->inst_count_ctrlflow++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::JMP)]++;
#endif
  return Cycles(CTRL_FLOW_CYCLES);
}

std::string disasmInstJmp(EncInst inst) {
  std::string disasm_str;
  disasm_str += "JMP";
  disasm_str += std::string(" ") + std::to_string(extrInstJmpImm(inst));
  return disasm_str;
}

EncInst constrInstJmp(int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::JMP);
  embdInstJmpImm(inst, imm);
  return inst;
}


}; // namespace basim
