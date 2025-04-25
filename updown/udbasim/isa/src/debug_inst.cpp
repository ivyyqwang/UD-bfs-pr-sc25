#include "debug_inst.hh"
#include "archstate.hh"
#include "lanetypes.hh"
#include "debug.hh"
#include "isa_cycles.hh"
#include "logging.hh"
#include <cstdint>
#include <iostream>
#include <unordered_map>
#include <sstream>
#include <string>

namespace basim {

#ifndef __REG_NAMES_MAP__
#define __REG_NAMES_MAP__
/* Register Encodings Map */
std::unordered_map<std::string, RegId> REG_NAMES_MAP = {
  {"X0", RegId::X0},
  {"X1", RegId::X1},
  {"X2", RegId::X2},
  {"X3", RegId::X3},
  {"X4", RegId::X4},
  {"X5", RegId::X5},
  {"X6", RegId::X6},
  {"X7", RegId::X7},
  {"X8", RegId::X8},
  {"X9", RegId::X9},
  {"X10", RegId::X10},
  {"X11", RegId::X11},
  {"X12", RegId::X12},
  {"X13", RegId::X13},
  {"X14", RegId::X14},
  {"X15", RegId::X15},
  {"X16", RegId::X16},
  {"X17", RegId::X17},
  {"X18", RegId::X18},
  {"X19", RegId::X19},
  {"X20", RegId::X20},
  {"X21", RegId::X21},
  {"X22", RegId::X22},
  {"X23", RegId::X23},
  {"X24", RegId::X24},
  {"X25", RegId::X25},
  {"X26", RegId::X26},
  {"X27", RegId::X27},
  {"X28", RegId::X28},
  {"X29", RegId::X29},
  {"X30", RegId::X30},
  {"X31", RegId::X31},
  {"NWID", RegId::NWID},
  {"CONT", RegId::CONT},
  {"EQT", RegId::EQT},
  {"FSCR", RegId::FSCR},
  {"STATE_PROPERTY", RegId::STATE_PROPERTY},
  {"LMBASE", RegId::LMBASE},
  {"OB_0", RegId::OB_0},
  {"OB_1", RegId::OB_1},
  {"OB_2", RegId::OB_2},
  {"OB_3", RegId::OB_3},
  {"OB_4", RegId::OB_4},
  {"OB_5", RegId::OB_5},
  {"OB_6", RegId::OB_6},
  {"OB_7", RegId::OB_7},
  {"UDPR_0", RegId::UDPR_0},
  {"UDPR_1", RegId::UDPR_1},
  {"UDPR_2", RegId::UDPR_2},
  {"UDPR_3", RegId::UDPR_3},
  {"UDPR_4", RegId::UDPR_4},
  {"UDPR_5", RegId::UDPR_5},
  {"UDPR_6", RegId::UDPR_6},
  {"UDPR_7", RegId::UDPR_7},
  {"UDPR_8", RegId::UDPR_8},
  {"UDPR_9", RegId::UDPR_9},
  {"UDPR_10", RegId::UDPR_10},
  {"UDPR_11", RegId::UDPR_11},
  {"UDPR_12", RegId::UDPR_12},
  {"UDPR_13", RegId::UDPR_13},
  {"UDPR_14", RegId::UDPR_14},
  {"UDPR_15", RegId::UDPR_15},
};
#endif // __REG_NAMES_MAP__


/* print, perflog Instruction */
Cycles exeInstPrintPerflog(ArchState& ast, EncInst inst) {
  ThreadStatePtr tst = ast.threadstate;
  InstructionMemoryPtr instmem = ast.instmem;
  auto network_id = tst->readReg(RegId::NWID);
  auto thread_id = tst->getTID();
  if (extrInstPrintFunc(inst) == 0) {
    // print
  } else if (extrInstPrintFunc(inst) == 1) {
    // perflog
    if(!globalLogs.perflog.isOpen()) {
      ast.uip += 4;
      return Cycles(0);
    }
  } else {
    BASIM_ERROR("[NWID:%lu][TID: %d] Invalid printperflog function", network_id, +thread_id);
  }

  auto lnstats = ast.lanestats;
  // inst count increments in lane tick
  lnstats->inst_count--; 
  uint32_t offset = extrInstPrintOffset(inst);
  offset = instmem->getDataOffset(offset);
  uint64_t fmt_len = instmem->getData(offset);
  uint64_t reglist_len = instmem->getData(offset + 4);
  offset += 8;

  char *fmt = new char[fmt_len + 1];
  char *reglist = new char[reglist_len + 1];
  char *fmt_start = &(fmt[fmt_len]);
  char *reglist_start = &(reglist[reglist_len]);
  *fmt_start = '\0';
  *reglist_start = '\0';
  for (uint32_t i = fmt_len; i > 0; ) {
    uint32_t word = instmem->getData(offset);
    offset += 4;
    for (int j = 0; j < 4; j++) {
      if ((char)word == '\0') {
        i = 0;
        break;
      }
      fmt[--i] = (char)word;
      word >>= 8;
      fmt_start = &(fmt[i]);
    }
  }

  std::string f = fmt_start;
  for (uint32_t i = reglist_len; i > 0; ) {
    uint32_t word = instmem->getData(offset);
    offset += 4;
    for (int j = 0; j < 4; j++) {
      if ((char)word == '\0') {
        i = 0;
        break;
      }
      reglist[--i] = (char)word;
      word >>= 8;
      reglist_start = &(reglist[i]);
    }
  }

  uint64_t *regvalues = new uint64_t[reglist_len];
  uint32_t regcount = 0;
  std::string *payloads = new std::string[reglist_len];
  uint32_t payloadcount = 0;

  #ifdef ACTIVATE_FP
    std::string typestr[10];
    std::string typesubstr[10];
    size_t pos = 0;
    size_t fcounter = 0;

    union regvalues {
      int i;
      float f;
      signed long ld;
      double lf;
      uint32_t u;
      uint64_t lu;
      void* p;
      unsigned int x;
      unsigned long lx;
    };

    union regvalues regval;

    //build an array of each string segment until each format specifier
    //with an additional array to hold the format specifiers themselves
    while(pos <= f.length() && (pos = f.find('%', pos)) != std::string::npos) {
      //pos finds the first '%' & pos2 finds the first valid end char of a format specifier
      int pos2 = f.find_first_of("dfuxip%", pos + 1);
      //can't find one, add all to the full string and break
      if ((pos2 == std::string::npos)) {
        typesubstr[fcounter] = f;
        fcounter++;
        break;
      } else if ((f[pos2] == '%')) {
        //for the case of "%%", take the %% into end of the previous substring
        //and decrement the counter, to prevent an empty slot, as %% doesn't format a regvalue
        if (pos == pos2 - 1) {
          typesubstr[fcounter] += std::string(f.substr(0, pos2 + 1));
          f = f.substr(pos2 + 1);
          fcounter--;
        } 
        //otherwise, the % found before a valid end means the format specifier is invalid
        //this string goes into the substring, and the typestr takes '%' to signify it's invalid
        else {
          typestr[fcounter] = std::string(f.substr(pos, pos + 1));
          typesubstr[fcounter] = std::string(f.substr(0, pos));
          f = f.substr(pos + 2);
        }
      }
      //otherwise, a valid specifier is found
      //typestr stores the specifier, typesubstr stores the string up until the specifier
      //f is redefined to not include these stored portions
      else { 
        typestr[fcounter] = std::string(f.substr(pos, pos2 - pos + 1));
        typesubstr[fcounter] += std::string(f.substr(0, pos));
        f = f.substr(pos + typestr[fcounter].length());
      }
      fcounter++;
      pos = 0;
    }
  #endif

  if (extrInstPrintFunc(inst) == 0) {
    // print
    std::string regs = reglist_start;
    std::stringstream ssin(regs);
    std::string temp_s;

    auto network_id = tst->readReg(RegId::NWID);
    auto thread_id = tst->getTID();

    #ifdef ACTIVATE_FP
      printf("[BASIM_PRINT] %lu: [NWID %u] ][TID %u][%s] ", ast.timestamp, network_id, thread_id, instmem->getSymbolName(tst->getEventWord().getEventLabel()).c_str());

      //printf the original format string for up until each reg value, for all reg values
      while (std::getline(ssin, temp_s, ',')) {
        regval.lu = tst->readReg(REG_NAMES_MAP[temp_s]);

        if (typestr[regcount] == "%d" ||typestr[regcount] == "%i") {
          printf((typesubstr[regcount] + "%d").c_str(), regval.i);
        } else if (typestr[regcount] == "%lu") {
          printf((typesubstr[regcount] + "%lu").c_str(), regval.lu);
        } else if (typestr[regcount] == "%f") {
          printf((typesubstr[regcount] + "%f").c_str(), regval.f);
        } else if (typestr[regcount] == "%ld") {
          printf((typesubstr[regcount] + "%ld").c_str(), regval.ld);
        } else if (typestr[regcount] == "%lf") {
          printf((typesubstr[regcount] + "%lf").c_str(), regval.lf);
        } else if (typestr[regcount] == "%u") {
          printf((typesubstr[regcount] + "%u").c_str(), regval.u);
        } else if (typestr[regcount] == "%p") {
          printf((typesubstr[regcount] + "%p").c_str(), regval.p);
        } else if (typestr[regcount] == "%x") {
          printf((typesubstr[regcount] + "0x%x").c_str(), regval.x);
        } else if (typestr[regcount] == "%lx") {
          printf((typesubstr[regcount] + "0x%x").c_str(), regval.lx);
        } else {
          printf(" (Invalid format specifier \"%s\" for: 0x%x) ", typestr[regcount].c_str(),  regval.x);
        }
        regcount++;
      }

      printf("\n");                                                             
      fflush(stderr);                                                           
      fflush(stdout);  

    #else

      while (std::getline(ssin, temp_s, ',')) {
        regvalues[regcount++] = tst->readReg(REG_NAMES_MAP[temp_s]);
      }
      f = std::to_string(ast.timestamp) + ": " + "[NWID " + std::to_string(network_id) + "][TID " + std::to_string(thread_id) + "][" + instmem->getSymbolName(tst->getEventWord().getEventLabel()) + "] " + f;

      if (regcount == 0) { BASIM_PRINT(f.c_str(), ' '); }
      else if (regcount == 1) { BASIM_PRINT(f.c_str(), regvalues[0]); }
      else if (regcount == 2) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1]); }
      else if (regcount == 3) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1], regvalues[2]); }
      else if (regcount == 4) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3]); }
      else if (regcount == 5) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4]); }
      else if (regcount == 6) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5]); }
      else if (regcount == 7) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5], regvalues[6]); }
      else if (regcount == 8) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5], regvalues[6], regvalues[7]); }
      else if (regcount == 9) { BASIM_PRINT(f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5], regvalues[6], regvalues[7], regvalues[8]); }
      else { BASIM_ERROR("Invalid number of registers to print (currently 0~9 is supported)"); }

    #endif 
    

  } else if (extrInstPrintFunc(inst) == 1) {
    // perflog
    std::string regs = reglist_start;
    std::stringstream ssin(regs);
    std::string temp_s;

    std::getline(ssin, temp_s, ';');
    uint32_t perflog_mode = std::stoi(temp_s);
    std::getline(ssin, temp_s, ';');
    uint32_t perflog_msg_id = std::stoi(temp_s);

    if (perflog_mode == 0 or perflog_mode == 2) {
      std::string payload_list = "";
      std::getline(ssin, payload_list, ';');

      ssin.str(payload_list);
      // class PerfLogPayload(Enum):
      // '''
      // Payload selection enum for perflog
      // '''
      //   UD_CYCLE_STATS = auto()
      //   UD_ACTION_STATS = auto()
      //   UD_TRANS_STATS = auto()
      //   UD_QUEUE_STATS = auto()
      //   UD_LOCAL_MEM_STATS = auto()
      //   UD_MEM_INTF_STATS = auto()
      //   SYS_MEM_INTF_STATS = auto()
      bool en_msg = false;
      bool en_cycle = false;
      bool en_action = false;
      bool en_trans = false;
      bool en_queue = false;
      bool en_lm = false;
      bool en_dram = false;
      bool en_sys_dram = false;
      while (std::getline(ssin, temp_s, ',')) {
        payloads[payloadcount++] = temp_s;
        int pl = std::stoi(temp_s);
        if (pl == 0) { en_cycle = true; }
        else if (pl == 1) { en_action = true; }
        else if (pl == 2) { en_trans = true; }
        else if (pl == 3) { en_queue = true; }
        else if (pl == 4) { en_lm = true; }
        else if (pl == 5) { en_dram = true; }
        else if (pl == 6) { en_sys_dram = true; }
        else { BASIM_ERROR("Invalid payload selection for perflog"); }
      }
    }

    char str_buf[1024];

    #ifdef ACTIVATE_FP
      while (std::getline(ssin, temp_s, ',')) {
        regval.lu = tst->readReg(REG_NAMES_MAP[temp_s]);
        if (typestr[regcount] == "%d" ||typestr[regcount] == "%i") {
          std::sprintf(str_buf, (typesubstr[regcount] + "%d").c_str(), regval.i);
        } else if (typestr[regcount] == "%f") {
          std::sprintf(str_buf, (typesubstr[regcount] + "%f").c_str(), regval.f);
        } else if (typestr[regcount] == "%ld") {
          std::sprintf(str_buf, (typesubstr[regcount] + "%ld").c_str(), regval.ld);
        } else if (typestr[regcount] == "%lf") {
          std::sprintf(str_buf, (typesubstr[regcount] + "%lf").c_str(), regval.lf);
        } else if (typestr[regcount] == "%u") {
          std::sprintf(str_buf, (typesubstr[regcount] + "%u").c_str(), regval.u);
        } else if (typestr[regcount] == "%lu") {
          std::sprintf(str_buf, (typesubstr[regcount] + "%lu").c_str(), regval.lu);
        } else if (typestr[regcount] == "%p") {
          std::sprintf(str_buf, (typesubstr[regcount] + "%p").c_str(), regval.p);
        } else if (typestr[regcount] == "%x") {
          std::sprintf(str_buf, (typesubstr[regcount] + "0x%x").c_str(), regval.x);
        } else {
          printf(" (Invalid format specifier \"%s\" for: 0x%x) ", regval.x);
        }
        regcount++;
      }
    #else

      while (std::getline(ssin, temp_s, ',')) {
        regvalues[regcount++] = tst->readReg(REG_NAMES_MAP[temp_s]);
      }

      if (regcount == 0) { std::sprintf(str_buf, f.c_str(), ' '); }
      else if (regcount == 1) { std::sprintf(str_buf, f.c_str(), regvalues[0]); }
      else if (regcount == 2) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1]); }
      else if (regcount == 3) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1], regvalues[2]); }
      else if (regcount == 4) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3]); }
      else if (regcount == 5) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4]); }
      else if (regcount == 6) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5]); }
      else if (regcount == 7) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5], regvalues[6]); }
      else if (regcount == 8) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5], regvalues[6], regvalues[7]); }
      else if (regcount == 9) { std::sprintf(str_buf, f.c_str(), regvalues[0], regvalues[1], regvalues[2], regvalues[3], regvalues[4], regvalues[5], regvalues[6], regvalues[7], regvalues[8]); }
      else { BASIM_ERROR("Invalid number of registers to perflog (currently 0~9 is supported)"); }
    
    #endif

    std::string msg_str(str_buf);
    Cycles inc_exec_cycles = lnstats->cur_activation_cycle_count;
    Cycles total_exec_cycles = lnstats->cycle_count;

    // auto network_id = tst->readReg(RegId::NWID);
    // auto thread_id = (tst->readReg(RegId::X1) >> 23) & 0xFF;
    // auto event_label = tst->readReg(RegId::X1) & 0xFFFFF;

    auto network_id = tst->readReg(RegId::NWID);
    auto thread_id = tst->getTID();
    auto event_label = tst->getEventWord().getEventLabel();

    globalLogs.perflog.perflogCallback(
        static_cast<uint32_t>(network_id),
        static_cast<uint32_t>(thread_id),  // IDs
        static_cast<uint32_t>(event_label),  // event
        // cycles
        uint64_t(inc_exec_cycles),
        uint64_t(total_exec_cycles),
        // message
        perflog_msg_id,
        msg_str
    );
  }

  delete[] fmt;
  delete[] reglist;
  delete[] regvalues;
  delete[] payloads;
  ast.uip += 4;
  return Cycles(PRINT_CYCLES);
}

std::string disasmInstPrintPerflog(EncInst inst) {
  std::string disasm_str;
  switch (extrInstPrintFunc(inst)) {
  case 0:
    disasm_str += "PRINT";
    break;
  case 1:
    disasm_str += "PERFLOG";
    break;
  default:
    BASIM_ERROR("DISASM print, perflog WITH UNKNOWN FUNC");
  }
  disasm_str += std::string(" ") + std::to_string(extrInstPrintOffset(inst));
  return disasm_str;
}

EncInst constrInstPrintPerflog(uint64_t offset, uint64_t func) {
  EncInst inst;
  embdInstOpcode(inst, Opcode::PRINT);
  embdInstPrintOffset(inst, offset);
  embdInstPrintFunc(inst, func);
  return inst;
}

}; // namespace basim
