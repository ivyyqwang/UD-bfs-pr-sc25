/**
**********************************************************************************************************************************************************************************************************************************
* @file:	udaccelerator.hh
* @author:	Andronicus
* @date:
* @brief:   Accelerator Definition
**********************************************************************************************************************************************************************************************************************************
**/
#ifndef __UDMEMORY__H__
#define __UDMEMORY__H__
#include "lanetypes.hh"
#include "logging.hh"
#include "stats.hh"
#include "translationmemory.hh"
#include "types.hh"
#include "udlane.hh"
#include <cstdint>
#include <iostream>
#include <omp.h>

namespace basim {

class UDMemory : public TickObject {
private:
  uint32_t udnodeid;

  uint32_t numStacks;

  std::vector<UDMemPtr> udMems;

  uint64_t curTimeStamp;

public:
  /* Null Constructor */
  UDMemory() : udnodeid(0), numStacks(8){};

  /* Accelerator Constructor with id, numStacks */
  UDMemory(uint32_t _udnodeid, uint32_t _numStacks, uint64_t latency, uint64_t bandwidth, uint64_t inter_node_latency);

  /* Idle Check */
  bool isIdle();

  /* Idle Check */
  bool isIdle(uint32_t stackID);

  /* Tick for Memory */
  void tick(uint64_t timestamp) override;

  // /* simulate API for memory runs through all stacks */
  // void simulate(uint64_t numTicks, uint64_t timestamp);

  // /* Simulate API to call per stack */
  // void simulate(uint32_t stackID, uint64_t numTicks, uint64_t timestamp);

  void pushMessage(std::unique_ptr<MMessage> m, uint32_t stackID);

  void pushDelayedMessage(std::unique_ptr<MMessage> m, uint32_t stackID);

  std::unique_ptr<MMessage> popMessage(uint32_t stackID);

  std::unique_ptr<MMessage> popDelayedMessage(uint32_t stackID);
  
  StackStats* getStackStats(uint32_t stackID);

  void resetStats(uint32_t stackID);

  void updateStats(uint32_t stackID);

  void updateStats();

  ~UDMemory();
};

typedef UDMemory* UDMemoryPtr;

} // namespace basim
#endif //!__EVENTQ__H__
