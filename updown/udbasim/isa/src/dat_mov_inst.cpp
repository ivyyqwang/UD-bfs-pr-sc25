#include "dat_mov_inst.hh"
#include "archstate.hh"
#include "debug.hh"
#include "encodings.hh"
#include "lanetypes.hh"
#include <cstdint>
#include "isa_cycles.hh"
#define IS_BIG_ENDIAN (!*(unsigned char *)&(uint16_t){1})

namespace basim {

/* movil2 Instruction */
Cycles exeInstMovil2(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  Addr addr = tst->readReg(extrInstMovil2Xs(inst)); // base_addr
  uint16_t result = extrInstMovil2Imm(inst);
  if (!transmem->validate_sp_addr(addr, 2)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVIL dest_reg=X%d data=%d", \
                addr, addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovil2Xs(inst), result);
    exit(1);
  }
  uint8_t data[2];
  data[0] = result & 0x00FF;
  data[1] = (result & 0xFF00) >> 8;
  spd->writeBytes(2, addr, data);
  lnstats->lm_store_bytes += 2;
  lnstats->lm_store_count++;
  tst->writeReg(extrInstMovil2Xs(inst), addr + 2);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVIL2)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovil2(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVIL2";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovil2Xs(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMovil2Imm(inst));
  return disasm_str;
}

EncInst constrInstMovil2(RegId Xs, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVIL2);
  embdInstMovil2Xs(inst, Xs);
  embdInstMovil2Imm(inst, imm);
  return inst;
}

/* movil1 Instruction */
Cycles exeInstMovil1(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  Addr addr = tst->readReg(extrInstMovil1Xs(inst)); // base_addr
  uint16_t result = extrInstMovil1Imm(inst);
  uint8_t data = result & 0x00FF;
  if (!transmem->validate_sp_addr(addr, 1)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVIL1 dest_reg=X%d data=%d", \
                addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovil1Xs(inst), data);
    exit(1);
  }
  spd->writeBytes(1, addr, &data);
  lnstats->lm_store_bytes += 1;
  lnstats->lm_store_count++;
  tst->writeReg(extrInstMovil1Xs(inst), addr + 1);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVIL1)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovil1(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVIL1";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovil1Xs(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMovil1Imm(inst));
  return disasm_str;
}

EncInst constrInstMovil1(RegId Xs, uint64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVIL1);
  embdInstMovil1Xs(inst, Xs);
  embdInstMovil1Imm(inst, imm);
  return inst;
}

/* movbil Instruction */
Cycles exeInstMovbil(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  auto xs = tst->readReg(extrInstMovbilXs(inst)); // bit base addr
  auto lenb = extrInstMovbilLenb(inst); // lenb
  auto bits = extrInstMovbilBits(inst); // bits
  Addr base_byte_addr = xs >> 3;
  if (!transmem->validate_sp_addr(base_byte_addr, 2)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVBIL dest_reg=X%d", \
                base_byte_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovbilXs(inst));
    exit(1);
  }
  uint64_t base_bit_offset = xs & 0x7;
  uint8_t data[2];
  spd->readBytes(2, base_byte_addr, data);
  lnstats->lm_load_bytes += 2;
  lnstats->lm_load_count++;
  data[0] = (data[0] & ((1U << base_bit_offset) - 1)) | ((bits & ((1U << lenb) - 1)) << base_bit_offset);
  if (base_bit_offset + lenb > 8) {
    data[1] = (data[1] & ~((1U << (base_bit_offset + lenb - 8)) - 1)) | ((bits & ((1U << lenb) - 1)) >> (8 - base_bit_offset));
  }
  spd->writeBytes(2, base_byte_addr, data);
  lnstats->lm_store_bytes += 2;
  lnstats->lm_store_count++;

    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVBIL)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovbil(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVBIL";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovbilXs(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMovbilLenb(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstMovbilBits(inst));
  return disasm_str;
}

EncInst constrInstMovbil(RegId Xs, uint64_t lenb, uint64_t bits) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVBIL);
  embdInstMovbilXs(inst, Xs);
  embdInstMovbilLenb(inst, lenb);
  embdInstMovbilBits(inst, bits);
  return inst;
}

/* movblr Instruction */
Cycles exeInstMovblr(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  auto xs = tst->readReg(extrInstMovblrXs(inst)); // bit base addr
  auto lenb = extrInstMovblrLenb(inst); // lenb
  Addr base_byte_addr = xs >> 3;
  if (!transmem->validate_sp_addr(base_byte_addr, 8)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVBLR scr_reg=X%d len=%ld", \
                base_byte_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovblrXs(inst), lenb);
    exit(1);
  }
  uint64_t base_bit_offset = xs & 0x7;
  auto data = spd->readWord(base_byte_addr);
  lnstats->lm_load_bytes += 8;
  lnstats->lm_load_count++;
  data >>= base_bit_offset;
  data = data & ((1U << lenb) - 1);
  tst->writeReg(extrInstMovblrXd(inst), data);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVBLR)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovblr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVBLR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovblrXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovblrXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMovblrLenb(inst));
  return disasm_str;
}

EncInst constrInstMovblr(RegId Xs, RegId Xd, uint64_t lenb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVBLR);
  embdInstMovblrXs(inst, Xs);
  embdInstMovblrXd(inst, Xd);
  embdInstMovblrLenb(inst, lenb);
  return inst;
}

/* bcpyll Instruction */
Cycles exeInstBcpyll(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  auto src_addr = tst->readReg(extrInstBcpyllXs(inst));
  auto dst_addr = tst->readReg(extrInstBcpyllXt(inst));
  // auto src_data = spd->readWord(src_addr);
  // auto dst_data = spd->readWord(dst_addr);
  auto imm_val = tst->readReg(extrInstBcpyllXd(inst));
  if (!transmem->validate_sp_addr(src_addr, imm_val)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u BCPYLL src_reg=X%d dest_reg=X%d", \
                src_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstBcpyllXs(inst), (int) extrInstBcpyllXt(inst));
    exit(1);
  }
  if (!transmem->validate_sp_addr(dst_addr, imm_val)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u BCPYLL src_reg=X%d dest_reg=X%d", \
                dst_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstBcpyllXs(inst), (int) extrInstBcpyllXt(inst));
    exit(1);
  }
  // if (imm_val > 7) {
  //   BASIM_ERROR("Invalid imm value in bcpyll");
  // }
  // regval_t result = ((src_data << 8 * (7 - imm_val)) >> 8 * (7 - imm_val)) | ((dst_data >> 8 * (imm_val + 1)) << 8 * (imm_val + 1));
  uint8_t tmp_result[1] = {0};
  for (int i = 0; i < imm_val; i++) {
    spd->readBytes(1, src_addr+i, tmp_result);
    lnstats->lm_load_bytes++;
    lnstats->lm_load_count++;
    spd->writeBytes(1, dst_addr+i, tmp_result);
    lnstats->lm_store_bytes++;
    lnstats->lm_store_count++;
  }
  // spd->writeWord(dst_addr, result);
  // tst->writeReg(extrInstBcpyllXs(inst), src_addr+imm_val+1);
  // tst->writeReg(extrInstBcpyllXt(inst), dst_addr+imm_val+1);
  tst->writeReg(extrInstBcpyllXs(inst), src_addr+imm_val);
  tst->writeReg(extrInstBcpyllXt(inst), dst_addr+imm_val);
  tst->writeReg(extrInstBcpyllXd(inst), 0);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
  // (read + write) * num_bytes / 8
  int numwords = imm_val >= 8 ? imm_val / WORDSIZE : 1;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BCPYLL)]++;
#endif
  // cycles = max(num_words/2, 1)
  return Cycles(std::max(((SPD_WORD_CYCLES * numwords) >> 1), 1));
}

std::string disasmInstBcpyll(EncInst inst) {
  std::string disasm_str;
  disasm_str += "BCPYLL";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyllXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyllXt(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyllXd(inst))];
  return disasm_str;
}

EncInst constrInstBcpyll(RegId Xs, RegId Xt, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BCPYLL);
  embdInstBcpyllXs(inst, Xs);
  embdInstBcpyllXt(inst, Xt);
  embdInstBcpyllXd(inst, Xd);
  return inst;
}

/* bcpylli Instruction */
Cycles exeInstBcpylli(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  auto src_addr = tst->readReg(extrInstBcpylliXs(inst));
  auto dst_addr = tst->readReg(extrInstBcpylliXd(inst));
  // auto src_data = spd->readWord(src_addr);
  // auto dst_data = spd->readWord(dst_addr);
  auto imm_val = extrInstBcpylliLen(inst);
  if (!transmem->validate_sp_addr(src_addr, imm_val)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u BCPYLLI src_reg=X%d dest_reg=X%d", \
                src_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstBcpylliXs(inst), (int) extrInstBcpylliXd(inst));
  }
  if (!transmem->validate_sp_addr(dst_addr, imm_val)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u BCPYLLI src_reg=X%d dest_reg=X%d", \
                dst_addr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstBcpylliXs(inst), (int) extrInstBcpylliXd(inst));
  }
  // regval_t result = ((src_data << 8 * (7 - imm_val)) >> 8 * (7 - imm_val)) | ((dst_data >> 8 * (imm_val + 1)) << 8 * (imm_val + 1));
  uint8_t tmp_result[1] = {0};
  for (int i = 0; i < imm_val; i++) {
    spd->readBytes(1, src_addr+i, tmp_result);
    lnstats->lm_load_bytes++;
    lnstats->lm_load_count++;
    spd->writeBytes(1, dst_addr+i, tmp_result);
    lnstats->lm_store_bytes++;
    lnstats->lm_store_count++;
  }
  // spd->writeWord(dst_addr, result);
  // tst->writeReg(extrInstBcpylliXs(inst), src_addr+imm_val+1);
  // tst->writeReg(extrInstBcpylliXd(inst), dst_addr+imm_val+1);
  tst->writeReg(extrInstBcpylliXs(inst), src_addr+imm_val);
  tst->writeReg(extrInstBcpylliXd(inst), dst_addr+imm_val);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
  int numwords = imm_val >= 8 ? imm_val / WORDSIZE : 1;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BCPYLLI)]++;
#endif
  return Cycles( std::max((SPD_WORD_CYCLES * (numwords)) >> 1, 1));
}

std::string disasmInstBcpylli(EncInst inst) {
  std::string disasm_str;
  disasm_str += "BCPYLLI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpylliXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpylliXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstBcpylliLen(inst));
  return disasm_str;
}

EncInst constrInstBcpylli(RegId Xs, RegId Xd, uint64_t len) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BCPYLLI);
  embdInstBcpylliXs(inst, Xs);
  embdInstBcpylliXd(inst, Xd);
  embdInstBcpylliLen(inst, len);
  return inst;
}

/* movsbr Instruction */
Cycles exeInstMovsbr(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  uint64_t issue_width = (tst->readReg(RegId::X4) >> 36) & 0xF; // Extract issue width
  uint64_t sbp = tst->readReg(RegId::X5); // Stream Buffer bit pointer
  StreamBufferPtr stbuff = ast.streambuffer;
  // Write register with value read from StreamBuffer
  tst->writeReg(extrInstMovsbrXd(inst), stbuff->getVarSymbol(sbp, issue_width));
  lnstats->inst_count_datmov++;
  ast.uip+=4;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVSBR)]++;
#endif
  return Cycles(SB_WORD_CYCLES);
}

std::string disasmInstMovsbr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVSBR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovsbrXd(inst))];
  return disasm_str;
}

EncInst constrInstMovsbr(RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVSBR);
  embdInstMovsbrXd(inst, Xd);
  return inst;
}

/* movrr Instruction */
Cycles exeInstMovrr(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  regval_t result = tst->readReg(extrInstMovrrXs(inst));
  tst->writeReg(extrInstMovrrXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVRR)]++;
#endif
  // This instruction shouldn't be used hopefully
  return Cycles(REG_WORD_CYCLES);
}

std::string disasmInstMovrr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVRR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovrrXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovrrXd(inst))];
  return disasm_str;
}

EncInst constrInstMovrr(RegId Xs, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVRR);
  embdInstMovrrXs(inst, Xs);
  embdInstMovrrXd(inst, Xd);
  return inst;
}

/* movir Instruction */
Cycles exeInstMovir(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto imm_val = extrInstMovirImm(inst);
  tst->writeReg(extrInstMovirXd(inst), imm_val);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVIR)]++;
#endif
  return Cycles(REG_WORD_CYCLES);
}

std::string disasmInstMovir(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVIR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovirXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMovirImm(inst));
  return disasm_str;
}

EncInst constrInstMovir(RegId Xd, int64_t imm) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVIR);
  embdInstMovirXd(inst, Xd);
  embdInstMovirImm(inst, imm);
  return inst;
}

/* movipr Instruction */
Cycles exeInstMovipr(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  regval_t result = ast.uip;
  tst->writeReg(extrInstMoviprXd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVIPR)]++;
#endif
  return Cycles(REG_WORD_CYCLES);
}

std::string disasmInstMovipr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVIPR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMoviprXd(inst))];
  return disasm_str;
}

EncInst constrInstMovipr(RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVIPR);
  embdInstMoviprXd(inst, Xd);
  return inst;
}

/* movlsb Instruction */
Cycles exeInstMovlsb(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  StreamBufferPtr stbuff = ast.streambuffer;
  Addr lmaddr = tst->readReg(extrInstMovlsbXs(inst));
  // Store the current SBP into the streambuffer (for accounting)
  stbuff->setSBPInternal(tst->readReg(RegId::X5));
  uint8_t databytes[SBSIZE];
  spd->readBytes(SBSIZE, lmaddr, databytes);
  lnstats->lm_load_bytes += SBSIZE;
  lnstats->lm_load_count += SBSIZE/WORDSIZE;
  for(auto i = 0; i < stbuff->getCapacity(); i++){
    stbuff->writeIntoSB(lmaddr + i, databytes[i]);
  }
  ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVLSB)]++;
#endif
  return Cycles(SB_WORD_CYCLES * SBSIZE / WORDSIZE);
}

std::string disasmInstMovlsb(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVLSB";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovlsbXs(inst))];
  return disasm_str;
}

EncInst constrInstMovlsb(RegId Xs) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVLSB);
  embdInstMovlsbXs(inst, Xs);
  return inst;
}

/* movlr Instruction */
Cycles exeInstMovlr(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  Addr saddr = tst->readReg(extrInstMovlrXs(inst)); // base_addr
  int64_t limm = static_cast<Addr>(extrInstMovlrImm(inst));
  uint8_t bytes = static_cast<uint8_t>(extrInstMovlrLenb(inst)+1);
  bool inc = static_cast<bool>(extrInstMovlrInc(inst));
  Addr effaddr = saddr + limm;  // effective address
  if (!transmem->validate_sp_addr(effaddr, 8)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVLR src_reg=X%d, offset=%d", \
                effaddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovlrXs(inst), (int) limm);
    exit(1);
  }
  word_t regdata = 0;
  if(bytes < 8){
    uint8_t regbytes[WORDSIZE];
    spd->readBytes(bytes, effaddr, regbytes);
    lnstats->lm_load_bytes += bytes;
    lnstats->lm_load_count++;
    memcpy(&regdata, regbytes, bytes);
  }else{
    regdata = spd->readWord(effaddr); // writeBytes keeps track of endianness
    lnstats->lm_load_bytes += 8;
    lnstats->lm_load_count++;
  }
  tst->writeReg(extrInstMovlrXd(inst), regdata); // Get data (what if data belongs to a different bank?)
  if (inc) {  // Update if increment
    BASIM_INFOMSG("NWID:%u, TID:%u, MOVLR: Address Incremeneted from %lx to %lx", tst->getNWIDbits(), tst->getTID(), saddr, saddr + bytes);
    saddr += bytes;
    tst->writeReg(extrInstMovlrXs(inst), saddr);
  }
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVLR)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovlr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVLR";
  disasm_str += std::string(" ") + std::to_string(extrInstMovlrImm(inst));
  disasm_str += std::string("(") + REG_NAMES[static_cast<uint8_t>(extrInstMovlrXs(inst))] + std::string(")");
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovlrXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMovlrInc(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstMovlrLenb(inst) + 1);
  return disasm_str;
}

EncInst constrInstMovlr(int64_t imm, RegId Xs, RegId Xd, uint64_t inc, uint64_t lenb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVLR);
  embdInstMovlrImm(inst, imm);
  embdInstMovlrXs(inst, Xs);
  embdInstMovlrXd(inst, Xd);
  embdInstMovlrInc(inst, inc);
  embdInstMovlrLenb(inst, lenb);
  return inst;
}

/* movrl Instruction */
Cycles exeInstMovrl(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  Addr daddr = tst->readReg(extrInstMovrlXd(inst)); // base_addr
  int64_t limm = static_cast<Addr>(extrInstMovrlImm(inst));
  uint8_t bytes = static_cast<uint8_t>(extrInstMovrlLenb(inst)+1);
  bool inc = static_cast<bool>(extrInstMovrlInc(inst));
  Addr effaddr = daddr + limm;  // Final address
  if (!transmem->validate_sp_addr(effaddr, 8)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVRL dest_reg=X%d, offset=%d", \
                effaddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovrlXd(inst), (int) limm);
    exit(1);
  }
  word_t regdata = tst->readReg(extrInstMovrlXs(inst)); // Get data (what if data belongs to a different bank?)
  if(bytes < 8){
    uint8_t regbytes[WORDSIZE];
    memcpy(regbytes, &regdata, WORDSIZE);
    spd->writeBytes(bytes, effaddr, regbytes);
    lnstats->lm_store_bytes += bytes;
    lnstats->lm_store_count++;
  }else{
    spd->writeWord(effaddr, regdata); // writeBytes keeps track of endianness
    lnstats->lm_store_bytes += 8;
    lnstats->lm_store_count++;
  }
  if (inc) {                                 // Update if increment
    daddr += bytes;
    tst->writeReg(extrInstMovrlXd(inst), daddr);
  }
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVRL)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovrl(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVRL";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovrlXs(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstMovrlImm(inst));
  disasm_str += std::string("(") + REG_NAMES[static_cast<uint8_t>(extrInstMovrlXd(inst))] + std::string(")");
  disasm_str += std::string(" ") + std::to_string(extrInstMovrlInc(inst));
  disasm_str += std::string(" ") + std::to_string(extrInstMovrlLenb(inst) + 1);
  return disasm_str;
}

EncInst constrInstMovrl(RegId Xs, int64_t imm, RegId Xd, uint64_t inc, uint64_t lenb) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVRL);
  embdInstMovrlXs(inst, Xs);
  embdInstMovrlImm(inst, imm);
  embdInstMovrlXd(inst, Xd);
  embdInstMovrlInc(inst, inc);
  embdInstMovrlLenb(inst, lenb);
  return inst;
}

/* movwlr Instruction */
Cycles exeInstMovwlr(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  Addr baddr = tst->readReg(extrInstMovwlrXb(inst)); // base_addr
  Addr saddr = tst->readReg(extrInstMovwlrXs(inst)); // base_addr
  Addr scale = static_cast<Addr>(extrInstMovwlrScale(inst));
  bool inc = static_cast<bool>(extrInstMovwlrInc(inst));
  Addr effaddr = baddr + (saddr << (scale + 3));  // Final address
  if (!transmem->validate_sp_addr(effaddr, 8)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVWLR base_reg=X%d src_reg=X%d, scale=%d", \
                effaddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovwlrXb(inst), (int) extrInstMovwlrXs(inst), (int) scale);
    exit(1);
  }
  word_t lmdata = spd->readWord(effaddr);   // Get data (what if data belongs to a different bank?)
  lnstats->lm_load_bytes += 8;
  lnstats->lm_load_count++;
  tst->writeReg(extrInstMovwlrXd(inst), lmdata);
  if (inc) { // Update if increment
    saddr += 1;  // Address should increment by 1 word
    tst->writeReg(extrInstMovwlrXs(inst), saddr);
  }
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVWLR)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovwlr(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVWLR";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovwlrXb(inst))];
  disasm_str += std::string("(") + REG_NAMES[static_cast<uint8_t>(extrInstMovwlrXs(inst))];
  disasm_str += std::string(",") + std::to_string(extrInstMovwlrInc(inst));
  disasm_str += std::string(",") + std::to_string(extrInstMovwlrScale(inst)) + std::string(")");
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovwlrXd(inst))];
  return disasm_str;
}

EncInst constrInstMovwlr(RegId Xb, RegId Xs, uint64_t inc, uint64_t scale, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVWLR);
  embdInstMovwlrXb(inst, Xb);
  embdInstMovwlrXs(inst, Xs);
  embdInstMovwlrInc(inst, inc);
  embdInstMovwlrScale(inst, scale);
  embdInstMovwlrXd(inst, Xd);
  return inst;
}

/* movwrl Instruction */
Cycles exeInstMovwrl(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  BASIM_INFOMSG("NWID:%u, TID:%u, Executing MOVWRL", tst->getNWIDbits(), tst->getTID());
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  Addr baddr = tst->readReg(extrInstMovwrlXb(inst)); // base_addr
  Addr daddr = tst->readReg(extrInstMovwrlXd(inst)); // LM addr
  Addr scale = static_cast<Addr>(extrInstMovwrlScale(inst));
  bool inc = static_cast<bool>(extrInstMovwrlInc(inst));
  Addr effaddr = baddr + (daddr << (scale + 3));  // Final address
  if (!transmem->validate_sp_addr(effaddr, 8)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u MOVWRL base_reg=X%d dest_reg=X%d, scale=%d", \
                effaddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstMovwrlXb(inst), (int) extrInstMovwrlXd(inst), (int) scale);
    exit(1);
  }
  word_t regdata = tst->readReg(extrInstMovwrlXs(inst)); // Get data (what if data belongs to a different bank?)
  spd->writeWord(effaddr, regdata);
  lnstats->lm_store_bytes += 8;
  lnstats->lm_store_count++;
  if (inc) { // Update if increment
    daddr += 1;
    tst->writeReg(extrInstMovwrlXd(inst), daddr);
  }
    ast.uip += 4;
  lnstats->inst_count_datmov++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::MOVWRL)]++;
#endif
  return Cycles(SPD_WORD_CYCLES);
}

std::string disasmInstMovwrl(EncInst inst) {
  std::string disasm_str;
  disasm_str += "MOVWRL";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovwrlXs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstMovwrlXb(inst))];
  disasm_str += std::string("(") + REG_NAMES[static_cast<uint8_t>(extrInstMovwrlXd(inst))];
  disasm_str += std::string(",") + std::to_string(extrInstMovwrlInc(inst));
  disasm_str += std::string(",") + std::to_string(extrInstMovwrlScale(inst)) + std::string(")");
  return disasm_str;
}

EncInst constrInstMovwrl(RegId Xs, RegId Xb, RegId Xd, uint64_t inc, uint64_t scale) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::MOVWRL);
  embdInstMovwrlXs(inst, Xs);
  embdInstMovwrlXb(inst, Xb);
  embdInstMovwrlXd(inst, Xd);
  embdInstMovwrlInc(inst, inc);
  embdInstMovwrlScale(inst, scale);
  return inst;
}

/* bcpyoli Instruction */
Cycles exeInstBcpyoli(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  auto lnstats = ast.lanestats;
  auto numops = extrInstBcpyoliLenw(inst);
  Addr daddr = tst->readReg(extrInstBcpyoliXd(inst)); // base_addr
  RegId raddr = extrInstBcpyoliXop(inst);
  if (!transmem->validate_sp_addr(daddr, 8 * numops)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u BCPYOLI src_reg=X%d dest_reg=X%d len=%ld", \
                daddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstBcpyoliXop(inst), (int) extrInstBcpyoliXd(inst), numops);
    exit(1);
  }
  for (uint8_t i = 0; i < numops; ++i) {
    if (i != 0) {
      daddr = daddr + 8;
      raddr = static_cast<RegId>(static_cast<uint8_t>(raddr) + 1);
    }
    regval_t regdata = tst->readReg(raddr);
    spd->writeWord(daddr, regdata);
    lnstats->lm_store_bytes += 8;
    lnstats->lm_store_count++;
  }
    ast.uip += 4;
  lnstats->inst_count_datmov++;
  int num_words = numops;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BCPYOLI)]++;
#endif
  return Cycles(std::max(((SPD_WORD_CYCLES * num_words) >> 1), 1));
}

std::string disasmInstBcpyoli(EncInst inst) {
  std::string disasm_str;
  disasm_str += "BCPYOLI";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyoliXop(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyoliXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstBcpyoliLenw(inst));
  return disasm_str;
}

EncInst constrInstBcpyoli(RegId Xop, RegId Xd, uint64_t lenw) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BCPYOLI);
  embdInstBcpyoliXop(inst, Xop);
  embdInstBcpyoliXd(inst, Xd);
  embdInstBcpyoliLenw(inst, lenw);
  return inst;
}

/* bcpyol Instruction */
Cycles exeInstBcpyol(ArchState &ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  TranslationMemoryPtr transmem = ast.transmem;
  BASIM_INFOMSG("NWID:%u, TID:%u, Translation memory = %p", tst->getNWIDbits(), tst->getTID(), transmem);
  auto lnstats = ast.lanestats;
  regval_t numops = tst->readReg(extrInstBcpyolXlenw(inst));
  Addr daddr = tst->readReg(extrInstBcpyolXd(inst)); // base_addr
  RegId raddr = extrInstBcpyolXop(inst);
  if (!transmem->validate_sp_addr(daddr, 8 * numops)) {
    BASIM_ERROR("Validation failed for address %p on nwid %d tid %d, INSTR=%u BCPYOL src_reg=X%d dest_reg=X%d len=%ld", \
                daddr, tst->getNWIDbits(), tst->getTID(), inst, (int) extrInstBcpyolXop(inst), (int) extrInstBcpyolXd(inst), numops);
    exit(1);
  }
  for (uint8_t i = 0; i < numops; ++i) {
    if (i != 0) {
      daddr = daddr + 8;
      if (raddr == RegId::X31) {
        break;
      }
      raddr = static_cast<RegId>(static_cast<uint8_t>(raddr) + 1);
    }
    regval_t regdata = tst->readReg(raddr);
    spd->writeWord(daddr, regdata);
    lnstats->lm_store_bytes += 8;
    lnstats->lm_store_count++;
  }
    ast.uip += 4;
  lnstats->inst_count_datmov++;
  int num_words = numops;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::BCPYOL)]++;
#endif
  return Cycles(std::max(((SPD_WORD_CYCLES * num_words) >> 1), 1));
  //return Cycles(SPD_WORD_CYCLES * numops);
}

std::string disasmInstBcpyol(EncInst inst) {
  std::string disasm_str;
  disasm_str += "BCPYOL";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyolXop(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyolXd(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstBcpyolXlenw(inst))];
  return disasm_str;
}

EncInst constrInstBcpyol(RegId Xop, RegId Xd, RegId Xlenw) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::BCPYOL);
  embdInstBcpyolXop(inst, Xop);
  embdInstBcpyolXd(inst, Xd);
  embdInstBcpyolXlenw(inst, Xlenw);
  return inst;
}

}; // namespace basim
