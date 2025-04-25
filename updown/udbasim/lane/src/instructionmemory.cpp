#include "instructionmemory.hh"
#include "debug.hh"
#include "encodings.hh"
#include "fstream"
#include "inst_decode.hh"
#include "types.hh"
#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace basim {

/* Load Program into Instruction Memory*/
void InstructionMemory::loadProgBinary(std::string progfile) {
  Addr addr;
  uint64_t numinst;
  uint32_t insword;
  uint32_t numEventSymbols;
  uint64_t cur_pos = 0;
  std::ifstream instream(progfile.c_str(), std::ios::binary);
  BASIM_ERROR_IF(!instream, "Could not load binary: %s\n", progfile.c_str());

  instream.seekg(0, instream.end);
  int file_len = instream.tellg();
  instream.seekg(0, instream.beg);

  /* LOAD HEADER */
  instream.read(reinterpret_cast<char *>(&binStartofEventSymbols), sizeof(binStartofEventSymbols));
  if(binStartofEventSymbols == 24) {
    // TODO ALEX remove in december 2024
    BASIM_WARNING("The binary file has been linked and assembled using an old version. It is marked as deprecated and will be removed in the future. Please relink your binary program file.");
    instream.read(reinterpret_cast<char *>(&binStartofProgram), sizeof(binStartofProgram));
    instream.read(reinterpret_cast<char *>(&binStartofData), sizeof(binStartofData));

    /* LOAD EVENT SYMBOL TABLE*/
    // skip, only used by Top runtime
    // instream.read(reinterpret_cast<char *>(&numEventSymbols), sizeof(numEventSymbols));

    /* LOAD INSTRUCTIONS */
    // Skip the symbols and head to the program
    instream.seekg(binStartofProgram, instream.beg);
    cur_pos = binStartofProgram;
    while (cur_pos < binStartofData) {
      // Addr (8), num_inst(8), trans(4), ins0(4), ins1(4)...
      instream.read(reinterpret_cast<char *>(&addr), sizeof(addr));
      cur_pos += sizeof(addr);
      instream.read(reinterpret_cast<char *>(&numinst), sizeof(numinst));
      cur_pos += sizeof(numinst);
      instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
      cur_pos += sizeof(insword);
      EncInst binst = static_cast<EncInst>(insword);
      insts[addr] = binst;
      addr += 4;
      numinst--;
      for (int i = numinst; i > 0; i--) {
        instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
        EncInst binst = static_cast<EncInst>(insword);
        insts[addr] = binst;
        addr += 4;
        cur_pos += sizeof(insword);
      }
    }

    /* LOAD DEBUG RODATA */
    // loading into separate debug rodata region
    instream.seekg(binStartofData, instream.beg);
    cur_pos = binStartofData;
    addr = 0;
    while (cur_pos < file_len) {
      instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
      uint32_t binst = static_cast<uint32_t>(insword);
      debug_rodata[addr] = binst;
      addr += 4;
      cur_pos += sizeof(insword);
    }
  } else {
    instream.read(reinterpret_cast<char *>(&binStartofProgram), sizeof(binStartofProgram));
    instream.read(reinterpret_cast<char *>(&binStartofData), sizeof(binStartofData));
    instream.read(reinterpret_cast<char *>(&binStartofDebugSymbols), sizeof(binStartofDebugSymbols));
    instream.read(reinterpret_cast<char *>(&binEndofFile), sizeof(binEndofFile));

    /* LOAD EVENT SYMBOL TABLE*/
    // skip, only used by Top runtime
    // instream.read(reinterpret_cast<char *>(&numEventSymbols), sizeof(numEventSymbols));

    /* LOAD INSTRUCTIONS */
    // Skip the symbols and head to the program
    instream.seekg(binStartofProgram, instream.beg);
    cur_pos = binStartofProgram;
    while (cur_pos < binStartofData) {
      // Addr (8), num_inst(8), trans(4), ins0(4), ins1(4)...
      instream.read(reinterpret_cast<char *>(&addr), sizeof(addr));
      cur_pos += sizeof(addr);
      instream.read(reinterpret_cast<char *>(&numinst), sizeof(numinst));
      cur_pos += sizeof(numinst);
      instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
      cur_pos += sizeof(insword);
      EncInst binst = static_cast<EncInst>(insword);
      insts[addr] = binst;
      addr += 4;
      numinst--;
      for (int i = numinst; i > 0; i--) {
        instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
        EncInst binst = static_cast<EncInst>(insword);
        insts[addr] = binst;
        addr += 4;
        cur_pos += sizeof(insword);
      }
    }

    /* LOAD DEBUG RODATA */
    // loading into separate debug rodata region
    instream.seekg(binStartofData, instream.beg);
    cur_pos = binStartofData;
    addr = 0;
    while (cur_pos < binStartofDebugSymbols) {
      instream.read(reinterpret_cast<char *>(&insword), sizeof(insword));
      uint32_t binst = static_cast<uint32_t>(insword);
      debug_rodata[addr] = binst;
      addr += 4;
      cur_pos += sizeof(insword);
    }

    /* LOAD DEBUG SYMBOLS */
    instream.seekg(binStartofDebugSymbols, instream.beg);
    cur_pos = binStartofData;
    uint32_t num_sym;
    instream.read(reinterpret_cast<char *>(&num_sym), 4);
    // while (cur_pos < file_len) {
    for (int i = 0; i < num_sym; i++) {
      uint32_t sym_addr;
      uint32_t sym_name_len;
      instream.read(reinterpret_cast<char *>(&sym_addr), 4);
      instream.read(reinterpret_cast<char *>(&sym_name_len), 4);
      std::string sym(sym_name_len, '\0');
      instream.read(&sym[0], sym_name_len);
      debug_symbols[sym_addr] = sym;
      cur_pos += 4 + 4 + sym_name_len;
      // BASIM_PRINT("Symbol: %s at 0x%x, len = %u\n", sym.c_str(), sym_addr, sym_name_len);
    }
  }
  instream.close();
  // dumpInstructionMemory();
}

// ID : Name Map extractor
std::unordered_map<uint32_t, std::string> InstructionMemory::extractSymbolNameMap(const std::string& progfile) {
    std::unordered_map<uint32_t, std::string> nameMap;
    std::ifstream instream(progfile.c_str(), std::ifstream::binary);
    uint64_t offset;
    uint32_t numEventSymbols, id, nameSize;
    BASIM_ERROR_IF(!instream, "Could not load the binary: %s", progfile.c_str());
    
    instream.read(reinterpret_cast<char *>(&offset), sizeof(offset));
    // return, if the file does not contain the event names table (old format)
    // ALEX TODO remove this if in december 2024
    if(offset == 24) {
        return nameMap;
    }
    instream.seekg(16, instream.cur);
    instream.read(reinterpret_cast<char *>(&offset), sizeof(offset));
    instream.seekg(offset, instream.beg);

    // read the numEventSymbols var
    instream.read(reinterpret_cast<char *>(&numEventSymbols), sizeof(numEventSymbols));
    BASIM_INFOMSG("\nnumEventSymbols read as: %i", numEventSymbols);

    // Should be at the start of the name/id dict
    for (auto i = 0; i < numEventSymbols; i++){
        BASIM_INFOMSG("\nStart of iteration %u of name/id dict reading loop:", i);
        instream.read(reinterpret_cast<char *>(&id), sizeof(id));
        instream.read(reinterpret_cast<char *>(&nameSize), sizeof(nameSize));
        char* name = new char[nameSize + 1];
        instream.read(reinterpret_cast<char *>(name), nameSize);

        name[nameSize] = '\0';
        nameMap.insert(std::make_pair(id, std::string(name)));

        BASIM_INFOMSG("ID: %u,  Name: %s", id, name);
        BASIM_INFOMSG("ID: %u Maps to: %s", id, nameMap[id].c_str());
        delete[] name;
    }
    instream.close();

    return nameMap;
}

} // namespace basim
