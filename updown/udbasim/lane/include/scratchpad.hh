/**
**********************************************************************************************************************************************************************************************************************************
* @file:	scratchpad.hh
* @author:	Andronicus
* @date:
* @brief:   Class file for UpDown Scratch Pad
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __SCRATCHPAD__H__
#define __SCRATCHPAD__H__
#include "lanetypes.hh"
#include "scratchpadbank.hh"
#include "types.hh"
#include "util.hh"
#include <cstdlib>
#include <iostream>
#include <memory>
#include <vector>

namespace basim {

class ScratchPad {
  /** @brief ScratchPad Bank per Lane
   *
   */
private:
  /* numBanks = numLanes */
  const unsigned numBanks;

  /* vector of spdbanks*/
  std::vector<ScratchPadBankPtr> spdbanks;

  /* Base Address of the ScratchPad */
  Addr spdBaseAddr;

  /* banksize */
  uint32_t bankSize;

public:
  /* default constructor */
  ScratchPad() : numBanks(0), spdBaseAddr(0){};

  /* allocate space equal to number of Bytes in Bank */
  ScratchPad(size_t _numBanks, Addr base = 0, uint32_t banksize = 65536) : numBanks(_numBanks), spdBaseAddr(base), bankSize(banksize) {
    for (auto i = 0; i < numBanks; i++) {
      ScratchPadBankPtr spdbank = new ScratchPadBank(banksize, base); // Base to be set based on LM Mode

      spdbanks.emplace_back(spdbank);
    }
  }

  /* Bank access functions */
  void setBase(Addr base) { spdBaseAddr = base; }

  /* Read N Bytes into ptr based on endianness */
  void readBytes(uint32_t nbytes, Addr addr, uint8_t *data) {
    uint32_t read_bytes = 0, offset = 0;
    int curr_bytes = 0;
    int laneid;
    uint64_t saddr;
    while(read_bytes < nbytes){
      laneid = (addr - spdBaseAddr) / bankSize;
      //if(((addr + (uint64_t)(nbytes - read_bytes) - spdBaseAddr) / bankSize) > laneid){
      if((nbytes - read_bytes) > SCRATCHPADBANK_SIZE){
        // strides across lanes - read bank by bank?
        //curr_bytes = (((laneid + 1) * bankSize) - addr);
        curr_bytes = SCRATCHPADBANK_SIZE;
      }else{
        curr_bytes = nbytes;
      }
      saddr = (addr - spdBaseAddr) % bankSize;
      spdbanks[laneid]->readBytes(curr_bytes, saddr, &data[offset]);
      read_bytes += curr_bytes;
      addr += curr_bytes;
      offset += curr_bytes;
      //nbytes -= curr_bytes;
    }

    //int laneid = (addr - spdBaseAddr) / bankSize;
    //uint64_t saddr = (addr - spdBaseAddr) % bankSize;
    //spdbanks[laneid]->readBytes(nbytes, saddr, data);
  }

  /* Write N Bytes in same order as received */
  void writeBytes(uint8_t nbytes, Addr addr, uint8_t *data) {
    uint32_t write_bytes = 0, offset = 0;
    int curr_bytes = 0;
    int laneid;
    uint64_t saddr;
    while(write_bytes < nbytes){
      laneid = (addr - spdBaseAddr) / bankSize;
      //if(((addr + (uint64_t)(nbytes - read_bytes) - spdBaseAddr) / bankSize) > laneid){
      if((nbytes - write_bytes) > SCRATCHPADBANK_SIZE){
        // strides across lanes - read bank by bank?
        //curr_bytes = (((laneid + 1) * bankSize) - addr);
        curr_bytes = SCRATCHPADBANK_SIZE;
      }else{
        curr_bytes = nbytes;
      }
      saddr = (addr - spdBaseAddr) % bankSize;
      spdbanks[laneid]->writeBytes(nbytes, saddr, data);
    //spdbanks[laneid]->readBytes(curr_bytes, saddr, &data[offset]);
      write_bytes += curr_bytes;
      addr += curr_bytes;
      offset += curr_bytes;
      //nbytes -= curr_bytes;
    }

    //int laneid = (addr - spdBaseAddr) / bankSize;
    //uint64_t saddr = (addr - spdBaseAddr) % bankSize;
    //spdbanks[laneid]->writeBytes(nbytes, saddr, data);
  }

  void readScratchpadBank(uint8_t laneid, uint8_t *data){
    spdbanks[laneid]->readAllBank(data);
  }

  void readAllScratchpad(uint8_t *data){
    uint32_t offset = 0;
    for (auto i = 0; i < numBanks; i++) {
      spdbanks[i]->readAllBank(&data[offset]);
      offset += SCRATCHPADBANK_SIZE;
    }
  }

  void writeScratchpadBank(uint8_t laneid, const uint8_t *data){
    spdbanks[laneid]->writeAllBank(data);
  }

  void writeAllScratchpad(const uint8_t *data){
    uint32_t offset = 0;
    for (auto i = 0; i < numBanks; i++) {
      spdbanks[i]->writeAllBank(&data[offset]);
      offset += SCRATCHPADBANK_SIZE;
    }
  }

  /* Read word in the right endian order (little) */
  word_t readWord(Addr addr) {
    int laneid = (addr - spdBaseAddr) / bankSize;
    uint64_t saddr = (addr - spdBaseAddr) % bankSize;
    return spdbanks[laneid]->readWord(saddr);
  }

  /* Write word */
  void writeWord(Addr addr, word_t worddata) {
    int laneid = (addr - spdBaseAddr) / bankSize;
    uint64_t saddr = (addr - spdBaseAddr) % bankSize;
    spdbanks[laneid]->writeWord(saddr, worddata);
  }

  ~ScratchPad(){
    for (auto spdb: spdbanks){
      delete spdb;
    }
    spdbanks.clear();
  }
};

typedef ScratchPad *ScratchPadPtr;

} // namespace basim

#endif //!__SCRATCHPAD__H__
