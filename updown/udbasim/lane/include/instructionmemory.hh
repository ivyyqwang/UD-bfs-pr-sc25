/**
**********************************************************************************************************************************************************************************************************************************
* @file:	instructionmemory.hh
* @author:	Andronicus
* @date:
* @brief:   Simple Instruction Memory for UpDown Accelerator
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __INSTRUCTION_MEMORY__H__
#define __INSTRUCTION_MEMORY__H__
#include "encodings.hh"
#include "types.hh"
#include "debug.hh"
#include <cstdint>
#include <iostream>
#include <vector>
#include <unordered_map>
#include "inst_decode.hh"

namespace basim {
class InstructionMemory {
private:
  /* Instruction Map */
  std::vector<EncInst> insts;
  std::unordered_map<Addr, uint32_t> debug_rodata;  // this is not an actual hardware memory, just for debug info
  std::unordered_map<uint32_t, std::string> debug_symbols;  // this is not an actual hardware memory, just for debug info

  /* base address of instruction memory*/
  Addr baseaddr;

  Addr binStartofEventSymbols;
  Addr binStartofProgram;
  Addr binStartofData;
  Addr binStartofDebugSymbols;
  Addr binEndofFile;

public:
  /* Constructors */
  InstructionMemory() : baseaddr(0) { insts.resize(INSTMEM_SIZE, 0xFFFFFFFF); };
  InstructionMemory(Addr progbase) : baseaddr(progbase){};

  /* set progbaseaddr*/
  void setPGBase(Addr progbase) { baseaddr = progbase; }

  /* get progbaseaddr*/
  Addr getPGBase() { return baseaddr; }

  /* Load Program into Instruction Memory*/
  void loadProgBinary(std::string progfile);
  
  /* Load Program into Instruction Memory*/
  void loadProg(std::string progfile){};

  /* get next instruction based on UIP*/
  EncInst getNextInst(Addr uip) { return insts[uip - baseaddr]; }

  EncInst getDataOffset(Addr addr) {
    //std::cout << "addr:" << addr << "return:" << insts[addr * 4 + baseaddr + startofData] << std::endl;
    return debug_rodata[addr * 4];
  }

  EncInst getData(Addr addr) {
    //std::cout << "addr:" << addr << "return:" << insts[addr + baseaddr] << std::endl;
    return debug_rodata[addr - binStartofData];  // TODO: this should be simplified from the assmebler side!
  }

  std::string getSymbolName(uint32_t enc_event_label) {
    auto it = debug_symbols.find(enc_event_label);
    if (it == debug_symbols.end()) {
      return "Unknown";
    }
    return it->second;
  }

  const std::unordered_map<uint32_t, std::string> & getSymbolNameMap() {
    return debug_symbols;
  }

  std::unordered_map<uint32_t, std::string> extractSymbolNameMap(const std::string& progfile);

  void dumpInstructionMemory(){
    BASIM_INFOMSG("========== Start Instruction Memory Dump ==========");
    uint64_t offset = 0;
    for (auto &it : insts) {
      if (it == 0xFFFFFFFF)
        continue;
      // BASIM_INFOMSG("[0x%lx]: 0x%08x", it.first, it.second);
      BASIM_INFOMSG("[0x%lx]: 0x%08x -\t%s", baseaddr+offset, it, decodeInst(it).disasm(it).c_str());
      offset += 4;
    }
    BASIM_INFOMSG("========== End Instruction Memory Dump ==========");
  }

  //~InstructionMemory(){
  //    delete insts;
  //}
};

typedef InstructionMemory *InstructionMemoryPtr;
} // namespace basim

#endif //!__INSTRUCTION_MEMORY__H__
