/**
**********************************************************************************************************************************************************************************************************************************
* @file:	archstate.hh
* @author:	Andronicus
* @date:
* @brief:   Combined Archtecture state to be passed to Instruction execution
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __ARCHSTATE__H__
#define __ARCHSTATE__H__
#include "threadstate.hh"
#include "tstable.hh"
#include <iostream>
#include "translationmemory.hh"
#include "eventq.hh"
#include "scratchpadbank.hh"
#include "scratchpad.hh"
#include "instructionmemory.hh"
#include "opbuffer.hh"
#include "sendbuffer.hh"
#include "streambuffer.hh"
#include "stats.hh"

namespace basim {

struct ArchState {
  InstructionMemoryPtr instmem;
  OpBufferPtr opbuff;
  EventQPtr eventq;
  //ScratchPadBankPtr spdbank;
  ScratchPadPtr spd;
  ThreadStatePtr threadstate;
  TSTablePtr tstable;
  Addr uip;
  lanestateptr lanestate;
  BufferPtr sendbuffer;
  StreamBufferPtr streambuffer;
  TranslationMemoryPtr transmem;
  LaneStats *lanestats;
  CurrentTrans currtrans;
  Addr pgbase;
  uint64_t timestamp;
#ifdef DETAIL_STATS
  uint64_t curr_event_inst_count;
  uint64_t curr_tx_inst_count;
  uint64_t prev_event_lm_load_count;
  uint64_t prev_event_lm_store_count;
  uint64_t prev_event_dram_load_count;
  uint64_t prev_event_dram_store_count;
  uint64_t prev_event_lm_load_bytes;
  uint64_t prev_event_lm_store_bytes;
  uint64_t prev_event_dram_load_bytes;
  uint64_t prev_event_dram_store_bytes;
#endif

#ifdef INST_HIST
  uint32_t instCount[static_cast<size_t>(InstMap::COUNT)];
#endif
  // add transaction memory as well

  // ~ArchState(){
  //  delete transmem;
  // }
};

typedef ArchState *ArchStatePtr;

} // namespace basim

#endif //!__ARCHSTATE__H__
