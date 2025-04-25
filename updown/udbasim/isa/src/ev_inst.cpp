#include "ev_inst.hh"
#include "archstate.hh"
#include "debug.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include "isa_cycles.hh"

namespace basim {

/* evi Instruction */
Cycles exeInstEvi(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  uint64_t src_ev = tst->readReg(extrInstEviXs(inst)); // Src Event
  auto sel = extrInstEviSel(inst);
  auto imm = extrInstEviImm(inst);
  EventWord new_ev(src_ev);
  BASIM_INFOMSG("NWID:%u, TID:%u, EVI: ev:%lx, imm:%lu, sel:%lu", tst->getNWIDbits(), tst->getTID(), new_ev.eventword, imm, sel);
  switch (sel) {
  case 1:
    new_ev.setEventLabel(imm & ELABELBITS);
    break;
  case 2:
    new_ev.setNumOperands(imm & NUMOPBITS);
    break;
  case 4:
    new_ev.setThreadID(imm & THREADIDBITS);
    break;
  case 8:
    new_ev.setNWIDbits(imm & NWIDBITS);
    break;
  default:
    BASIM_ERROR("ERROR: Incorrect Value for Select Bits in EVI: %lx\n", sel);
    break;
  }
  BASIM_INFOMSG("NWID:%u, TID:%u, EVI: new_ev:%lx", tst->getNWIDbits(), tst->getTID(), new_ev.eventword);
  tst->writeReg(extrInstEviXd(inst), new_ev.eventword);
  ast.uip += 4;
  lnstats->inst_count_ev++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::EVI)]++;
#endif
  return Cycles(EV_CYCLES);
}

std::string disasmInstEvi(EncInst inst) {
  std::string disasm_str;
  disasm_str += "EVI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEviXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEviXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstEviImm(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstEviSel(inst));
  return disasm_str;
}

EncInst constrInstEvi(RegId Xs, RegId Xd, uint64_t imm, uint64_t sel) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::EVI);
  embdInstEviXs(inst, Xs);
  embdInstEviXd(inst, Xd);
  embdInstEviImm(inst, imm);
  embdInstEviSel(inst, sel);
  return inst;
}


/* evii Instruction */
Cycles exeInstEvii(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  uint64_t src_ev = tst->readReg(RegId::X2); // current_event
  auto imm1 = extrInstEviiImm1(inst);        // Imm1
  auto sel = extrInstEviiSel(inst);          // Sel
  auto imm2 = extrInstEviiImm2(inst);        // Imm2
  EventWord new_ev(src_ev);
  bool sel_bit;
  bool use_imm2 = false;
  BASIM_INFOMSG("NWID:%u, TID:%u ,EV: evii:%lx, imm:%lu, imm2:%lu, sel:%lu", tst->getNWIDbits(), tst->getTID(), src_ev, imm1, imm2, sel);
  for (auto i = 0; i < 4; i++, sel >>= 1) {
    sel_bit = sel & 0x1;
    if (sel_bit && (i == 0)) {
      if (!use_imm2) {
        new_ev.setEventLabel(imm1 & ELABELBITS);
        use_imm2 = true;
      } else {
        new_ev.setEventLabel(imm2 & ELABELBITS);
        break;
      }
    }
    if (sel_bit && (i == 1)) {
      if (!use_imm2) {
        new_ev.setNumOperands(imm1 & NUMOPBITS);
        use_imm2 = true;
      } else {
        new_ev.setNumOperands(imm2 & NUMOPBITS);
        break;
      }
    }
    if (sel_bit && (i == 2)) {
      if (!use_imm2) {
        new_ev.setThreadID(imm1 & THREADIDBITS);
        use_imm2 = true;
      } else {
        new_ev.setThreadID(imm2 & THREADIDBITS);
        break;
      }
    }
    if (sel_bit && (i == 3)) {
      if (!use_imm2) {
        new_ev.setNWIDbits(imm1 & NWIDBITS);
        use_imm2 = true;
      } else {
        new_ev.setNWIDbits(imm2 & NWIDBITS);
        break;
      }
    }
  }
  BASIM_INFOMSG("NWID:%u, TID:%u, EVII: new_ev:%lx", tst->getNWIDbits(), tst->getTID(), new_ev.eventword);
  tst->writeReg(extrInstEviiXd(inst), new_ev.eventword);
  ast.uip += 4;
  lnstats->inst_count_ev++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::EVII)]++;
#endif
  return Cycles(EV_CYCLES);
}

std::string disasmInstEvii(EncInst inst) {
  std::string disasm_str;
  disasm_str += "EVII";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEviiXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstEviiImm1(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstEviiImm2(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstEviiSel(inst));
  return disasm_str;
}

EncInst constrInstEvii(RegId Xd, uint64_t imm1, uint64_t imm2, uint64_t sel) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::EVII);
  embdInstEviiXd(inst, Xd);
  embdInstEviiImm1(inst, imm1);
  embdInstEviiImm2(inst, imm2);
  embdInstEviiSel(inst, sel);
  return inst;
}


/* ev Instruction */
Cycles exeInstEv(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  uint64_t src_ev = tst->readReg(extrInstEvXs(inst));      // current_event
  uint8_t sel = static_cast<uint8_t>(extrInstEvSel(inst)); // Sel
  uint64_t imm1 = tst->readReg(extrInstEvXop1(inst));
  uint64_t imm2 = tst->readReg(extrInstEvXop2(inst));
  EventWord new_ev(src_ev);
  bool sel_bit;
  bool use_imm2 = false;
  BASIM_INFOMSG("NWID:%u, TID:%u, EV: ev:%lx, op1:%lu, op2:%lu, sel:%u", tst->getNWIDbits(), tst->getTID(), src_ev, imm1, imm2, sel);
  for (auto i = 0; i < 4; i++, sel >>= 1) {
    sel_bit = sel & 0x1;
    if (sel_bit && (i == 0)) {
      if (!use_imm2) {
        new_ev.setEventLabel(imm1 & ELABELBITS);
        use_imm2 = true;
      } else {
        new_ev.setEventLabel(imm2 & ELABELBITS);
        break;
      }
    }
    if (sel_bit && (i == 1)) {
      if (!use_imm2) {
        new_ev.setNumOperands(imm1 & NUMOPBITS);
        use_imm2 = true;
      } else {
        new_ev.setNumOperands(imm2 & NUMOPBITS);
        break;
      }
    }
    if (sel_bit && (i == 2)) {
      if (!use_imm2) {
        new_ev.setThreadID(imm1 & THREADIDBITS);
        use_imm2 = true;
      } else {
        new_ev.setThreadID(imm2 & THREADIDBITS);
        break;
      }
    }
    if (sel_bit && (i == 3)) {
      if (!use_imm2) {
        new_ev.setNWIDbits(imm1 & NWIDBITS);
        use_imm2 = true;
      } else {
        new_ev.setNWIDbits(imm2 & NWIDBITS);
        break;
      }
    }
  }
  BASIM_INFOMSG("NWID:%u, TID:%u, EV: new_ev:%lx", tst->getNWIDbits(), tst->getTID(), new_ev.eventword);
  tst->writeReg(extrInstEvXd(inst), new_ev.eventword);
  ast.uip += 4;
  lnstats->inst_count_ev++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::EV)]++;
#endif
  return Cycles(EV_CYCLES);
}

std::string disasmInstEv(EncInst inst) {
  std::string disasm_str;
  disasm_str += "EV";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEvXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEvXd(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEvXop1(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEvXop2(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstEvSel(inst));
  return disasm_str;
}

EncInst constrInstEv(RegId Xs, RegId Xd, RegId Xop1, RegId Xop2, uint64_t sel) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::EV);
  embdInstEvXs(inst, Xs);
  embdInstEvXd(inst, Xd);
  embdInstEvXop1(inst, Xop1);
  embdInstEvXop2(inst, Xop2);
  embdInstEvSel(inst, sel);
  return inst;
}


/* evlb Instruction */
Cycles exeInstEvlb(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  // uint64_t src_ev = tst->readReg(RegId::X2); // Src Event
  uint64_t src_ev = tst->readReg(extrInstEvlbXd(inst)); // Src Event
  auto evlabel = extrInstEvlbLabel(inst);
  EventWord new_ev(src_ev);
  new_ev.setEventLabel(evlabel & ELABELBITS);
  BASIM_INFOMSG("NWID:%u, TID:%u, EVLB: new_ev:%lx", tst->getNWIDbits(), tst->getTID(), new_ev.eventword);
  tst->writeReg(extrInstEvlbXd(inst), new_ev.eventword);
  ast.uip += 4;
  lnstats->inst_count_ev++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::EVLB)]++;
#endif
  return Cycles(EV_CYCLES);
}

std::string disasmInstEvlb(EncInst inst) {
  std::string disasm_str;
  disasm_str += "EVLB";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstEvlbXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstEvlbLabel(inst));
  return disasm_str;
}

EncInst constrInstEvlb(RegId Xd, uint64_t label) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::EVLB);
  embdInstEvlbXd(inst, Xd);
  embdInstEvlbLabel(inst, label);
  return inst;
}

}; // namespace basim
