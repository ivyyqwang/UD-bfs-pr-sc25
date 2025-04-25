#include "hash_inst.hh"
#include "archstate.hh"
#include "lanetypes.hh"
#include "debug.hh"
#include <cstdint>
#include "isa_cycles.hh"

namespace basim {

/* hash helper */
/* CRC64-ECMA-182 Little Endian Implementation */
static const uint64_t POLY64REV = 0xC96C5795D7870F42;
static const uint64_t INITIALCRC = 0xFFFFFFFFFFFFFFFF;
static uint64_t crc64_tab[256];

static void init_crc64_tab() {
    int i, j;
    uint64_t part;
    for (i = 0; i < 256; i++) {
        part = i;
        for (j = 0; j < 8; j++) {
            if (part & 1)
                part = (part >> 1) ^ POLY64REV;
            else
                part >>= 1;
        }
        crc64_tab[i] = part;
    }
}

static uint64_t crc64(uint64_t crc, const uint8_t *seq, size_t len) {
  while (len-- > 0)
      crc = crc64_tab[(crc ^ *seq++) & 0xFF] ^ (crc >> 8);
  return crc;
}

static bool crc64_init = false;

static uint64_t crc16(uint64_t input) {
  uint64_t poly = 0xA6BC;
  uint64_t crc = (input & 0x00000000FFFFFFFF) ^ 0x00000000FFFFFFFF;
  for (int i = 0; i < 32; i++) {
      if (crc & 1) {
          crc = (crc >> 1) ^ poly;
      } else {
          crc = (crc >> 1);
      }
  }
  return crc ^ 0x000000000000FFFF;
}


/* hashsb32 Instruction */
Cycles exeInstHashsb32(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto x5_addr = tst->readReg(RegId::X5);
  auto ht_base = extrInstHashsb32Htbase(inst);
  regval_t x5_data = 0;
  regval_t result = 0;

  if (tst->readReg(RegId::X2) & 0x0000000000800000) {
    uint64_t issue_width = 32; // Extract issue width
    StreamBufferPtr stbuff = ast.streambuffer;
    x5_data = (stbuff->getVarSymbol(x5_addr, 8) << 0) | (stbuff->getVarSymbol(x5_addr+8, 8) << 8) | (stbuff->getVarSymbol(x5_addr+16, 8) << 16) | (stbuff->getVarSymbol(x5_addr+24, 8) << 24);
    result = crc16(x5_data) * 2 + ht_base;
  } else {
    ScratchPadPtr spd = ast.spd;
    uint32_t x5_tmp = 0;
    spd->readBytes(4, x5_addr, reinterpret_cast<uint8_t *>(&x5_tmp));
    x5_data = x5_tmp;
    lnstats->lm_load_bytes += 4;
    lnstats->lm_load_count++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::HASHSB32)]++;
#endif
    result = crc16(x5_data) + ht_base;
  }

  tst->writeReg(extrInstHashsb32Xd(inst), result);
  ast.uip += 4;
  lnstats->inst_count_hash++;
  return Cycles(HASH_CYCLES);
}

std::string disasmInstHashsb32(EncInst inst) {
  std::string disasm_str;
  disasm_str += "HASHSB32";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashsb32Xd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstHashsb32Htbase(inst));
  return disasm_str;
}

EncInst constrInstHashsb32(RegId Xd, uint64_t htbase) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::HASHSB32);
  embdInstHashsb32Xd(inst, Xd);
  embdInstHashsb32Htbase(inst, htbase);
  return inst;
}


/* hashsb64 Instruction */
Cycles exeInstHashsb64(ArchState& ast, EncInst inst) {
  if (!crc64_init) {
    init_crc64_tab();
    crc64_init = true;
  }
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto x5_addr = tst->readReg(RegId::X5);
  auto xs_data = tst->readReg(extrInstHashsb64Xs(inst));

  uint64_t issue_width = 64; // Extract issue width
  StreamBufferPtr stbuff = ast.streambuffer;
  regval_t x5_data = (stbuff->getVarSymbol(x5_addr, 8) << 0) | (stbuff->getVarSymbol(x5_addr+8, 8) << 8) | (stbuff->getVarSymbol(x5_addr+16, 8) << 16) | (stbuff->getVarSymbol(x5_addr+24, 8) << 24) | (stbuff->getVarSymbol(x5_addr+32, 8) << 32) | (stbuff->getVarSymbol(x5_addr+40, 8) << 40) | (stbuff->getVarSymbol(x5_addr+48, 8) << 48) | (stbuff->getVarSymbol(x5_addr+56, 8) << 56);

  uint64_t crc = INITIALCRC;
  regval_t result = (crc64(crc, reinterpret_cast<uint8_t *>(&x5_data), 8) ^ INITIALCRC) + xs_data;
  tst->writeReg(extrInstHashsb64Xd(inst), result);
    ast.uip += 4;
  lnstats->inst_count_hash++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::HASHSB64)]++;
#endif
  return Cycles(HASH_CYCLES);
}

std::string disasmInstHashsb64(EncInst inst) {
  std::string disasm_str;
  disasm_str += "HASHSB64";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashsb64Xs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashsb64Xd(inst))];
  return disasm_str;
}

EncInst constrInstHashsb64(RegId Xs, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::HASHSB64);
  embdInstHashsb64Xs(inst, Xs);
  embdInstHashsb64Xd(inst, Xd);
  return inst;
}


/* hashl64 Instruction */
Cycles exeInstHashl64(ArchState& ast, EncInst inst) {
  if (!crc64_init) {
    init_crc64_tab();
    crc64_init = true;
  }
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  auto x5_addr = tst->readReg(RegId::X5);
  auto x5_data = spd->readWord(x5_addr);
  lnstats->lm_load_bytes += 8;
  lnstats->lm_load_count++;
  auto xs_data = tst->readReg(extrInstHashl64Xs(inst));
  uint64_t crc = INITIALCRC;
  regval_t result = (crc64(crc, reinterpret_cast<uint8_t *>(&x5_data), 8) ^ INITIALCRC) + xs_data;
  tst->writeReg(extrInstHashl64Xd(inst), result);
  ast.uip += 4;
  lnstats->inst_count_hash++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::HASHL64)]++;
#endif
  return Cycles(HASH_CYCLES);
}

std::string disasmInstHashl64(EncInst inst) {
  std::string disasm_str;
  disasm_str += "HASHL64";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashl64Xs(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashl64Xd(inst))];
  return disasm_str;
}

EncInst constrInstHashl64(RegId Xs, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::HASHL64);
  embdInstHashl64Xs(inst, Xs);
  embdInstHashl64Xd(inst, Xd);
  return inst;
}


/* hash Instruction */
Cycles exeInstHash(ArchState& ast, EncInst inst) {
  if (!crc64_init) {
    init_crc64_tab();
    crc64_init = true;
  }
  ThreadStatePtr tst = ast.threadstate;
  auto lnstats = ast.lanestats;
  auto xe_data = tst->readReg(extrInstHashXe(inst));
  auto xd_data = tst->readReg(extrInstHashXd(inst));
  regval_t result = xe_data + xd_data;
  uint64_t crc = INITIALCRC;
  uint64_t crc_result = crc64(crc, reinterpret_cast<uint8_t *>(&result), 8) ^ INITIALCRC;
  tst->writeReg(extrInstHashXd(inst), crc_result);
  ast.uip += 4;
  lnstats->inst_count_hash++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::HASH)]++;
#endif
  return Cycles(HASH_CYCLES);
}

std::string disasmInstHash(EncInst inst) {
  std::string disasm_str;
  disasm_str += "HASH";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashXe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashXd(inst))];
  return disasm_str;
}

EncInst constrInstHash(RegId Xe, RegId Xd) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::HASH);
  embdInstHashXe(inst, Xe);
  embdInstHashXd(inst, Xd);
  return inst;
}


/* hashl Instruction */
Cycles exeInstHashl(ArchState& ast, EncInst inst) {
  if (!crc64_init) {
    init_crc64_tab();
    crc64_init = true;
  }
  ThreadStatePtr tst = ast.threadstate;
  ScratchPadPtr spd = ast.spd;
  auto lnstats = ast.lanestats;
  auto xe_addr = tst->readReg(extrInstHashlXe(inst));
  auto wordstohash = extrInstHashlLenw(inst) + 1;
  if(wordstohash > 0) {
    regval_t result = spd->readWord(xe_addr) + tst->readReg(extrInstHashlXd(inst));
    xe_addr += 8;
    lnstats->lm_load_bytes += 8;
    lnstats->lm_load_count++;
    result = crc64(INITIALCRC, reinterpret_cast<uint8_t *>(&result), 8);
    result ^= INITIALCRC;
    for (int i = 0; i < wordstohash - 1; i++) {
      result += spd->readWord(xe_addr);
      xe_addr += 8;
      lnstats->lm_load_bytes += 8;
      lnstats->lm_load_count++;
      result = crc64(INITIALCRC, reinterpret_cast<uint8_t *>(&result), 8);
      // result = crc64(result, reinterpret_cast<uint8_t *>(&result), 8);
      result ^= INITIALCRC;
    }
    // result ^= INITIALCRC;
    tst->writeReg(extrInstHashlXd(inst), result);
    tst->writeReg(extrInstHashlXe(inst), xe_addr);
  }
  ast.uip += 4;
  lnstats->inst_count_hash++;
#ifdef INST_HIST
    ast.instCount[static_cast<size_t>(InstMap::HASHL)]++;
#endif
  return Cycles(HASH_CYCLES);
}

std::string disasmInstHashl(EncInst inst) {
  std::string disasm_str;
  disasm_str += "HASHL";
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashlXe(inst))];
  disasm_str += std::string(" ") + REG_NAMES[static_cast<uint8_t>(extrInstHashlXd(inst))];
  disasm_str += std::string(" ") + std::to_string(extrInstHashlLenw(inst) + 1);
  return disasm_str;
}

EncInst constrInstHashl(RegId Xe, RegId Xd, uint64_t lenw) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::HASHL);
  embdInstHashlXe(inst, Xe);
  embdInstHashlXd(inst, Xd);
  embdInstHashlLenw(inst, lenw);
  return inst;
}


}; // namespace basim
