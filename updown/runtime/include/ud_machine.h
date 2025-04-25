#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <utility>
#include <getopt.h>
#include <string>

#include "debug.h"

namespace UpDown {
/**
 * @brief Structure containing the machine configuration.
 *
 * This structure can be used to change the parameters of the runtime, during
 * runtime construction.
 */

struct ud_machine_t {
  // Offsets for addrs space
  uint64_t MapMemBase = BASE_MAPPED_ADDR;         // Base address for memory map
  uint64_t GMapMemBase = BASE_MAPPED_GLOBAL_ADDR; // Base address for memory map
  uint64_t UDbase = BASE_SPMEM_ADDR;              // Base address for upstream
  uint64_t SPMemBase = BASE_SPMEM_ADDR;           // ScratchPad Base address
  uint64_t ControlBase = BASE_CTRL_ADDR;          // Base for control operands
  uint64_t ProgBase = BASE_PROG_ADDR;          // Base for control operands
  uint64_t EventQueueOffset = EVENT_QUEUE_OFFSET; // Offset for Event Queues
  uint64_t OperandQueueOffset =
      OPERAND_QUEUE_OFFSET;                     // Offset for Operands Queues
  uint64_t StartExecOffset = START_EXEC_OFFSET; // Offset for Start Exec signal
  uint64_t LockOffset = LOCK_OFFSET;            // Offset for Lock signal

  uint64_t PhysGMapMemBase = BASE_MAPPED_GLOBAL_ADDR;

  // Machine config and capacities
  uint64_t CapNumNodes = NUM_NODES_CAPACITY;          // Max number of UpDowns
  uint64_t CapNumStacks = NUM_STACKS_CAPACITY;        // Max number of UpDowns
  uint64_t CapNumUDs = NUM_UDS_CAPACITY;              // Max number of UpDowns
  uint64_t CapNumLanes = NUM_LANES_CAPACITY;          // Max number of UpDowns
  uint64_t CapSPmemPerLane = SPMEM_CAPACITY_PER_LANE; // Max bank size per lane
  uint64_t CapControlPerLane =
      CONTROL_CAPACITY_PER_LANE;       // Max Control Sigs and regs per lane
  uint64_t NumUDs = DEF_NUM_UDS;       // Number of UpDowns
  uint64_t NumLanes = DEF_NUM_LANES;   // Number of lanes
  uint32_t LocalMemAddrMode = 1;       // Local Memory Mode
  uint64_t NumStacks = DEF_NUM_STACKS; // Number of lanes
  uint64_t NumNodes = DEF_NUM_NODES;   // Number of lanes

  // Sizes for memories
  uint64_t MapMemSize = DEF_MAPPED_SIZE;   // Mapped Memory size
  uint64_t GMapMemSize = DEF_GMAPPED_SIZE; // Mapped Memory size
  uint64_t SPBankSize =
      DEF_SPMEM_BANK_SIZE; // Local Momory (scratchpad) Bank Size
  uint64_t SPBankSizeWords =
      DEF_SPMEM_BANK_SIZE * DEF_WORD_SIZE; // LocalMemorySize in Words
  uint64_t MemISegBlockSize = DEF_MEM_ISEG_BLOCK_SIZE; // Local Memory Segment Size (B)
  uint64_t MemLatency = DEF_MEM_LATENCY;      // Memory Latency
  uint64_t FarMemExtraLatency = DEF_FAR_MEM_EXTRA_LATENCY; // Extra Latency for Far Memory
  uint64_t MemBandwidth = DEF_MEM_BANDWIDTH;  // Memory Bandwidth
  uint64_t InterNodeLatency = DEF_INTER_NODE_LATENCY; // Inter Node Latency
  uint64_t InterNodeBandwidth = DEF_INTER_NODE_BANDWIDTH; // Inter Node Bandwidth (GB/s per node)
  
  private:
    uint64_t convertStr2Long(char *c) {
      std::string str(c);
      std::size_t npos = str.find('x');
      if(npos == std::string::npos) {
        return std::stol(str);
      } else {
        str = str.substr(npos+1);
        return std::stol(str, nullptr, 16);
      }
    }

  public:
  // Constructors
  ud_machine_t() {}
  ud_machine_t(int argc, char* argv[]) {
    int c;

    static struct option long_options[] = {
      {"memSize", required_argument, NULL, 'm'},
      {"gMemSize", required_argument, NULL, 'g'},
      {NULL, 0, NULL, 0}
    };

    while((c = getopt_long(argc, argv, "m:g:", long_options, NULL)) != -1) {
      switch(c) {
        case 'm':
          MapMemSize = convertStr2Long(optarg);
          break;
        case 'g':
          GMapMemSize = convertStr2Long(optarg);
          break;
      }
    }
  }

  // Scratchpad Memory Size
  uint64_t SPSize() {
    return this->CapNumNodes * this->CapNumStacks * this->CapNumUDs *
           this->CapNumLanes * this->CapSPmemPerLane;
  }
};
} // namespace UpDown