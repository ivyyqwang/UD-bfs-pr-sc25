#include "networkid.h"
#include "simupdown.h"
#include "updown.h"
#include "updown_config.h"
#include <cstdint>
#include <cstdio>
#include <sys/types.h>
#include <updown.h>
#include <vector>

// #ifdef FASTSIM
// #include <simupdown.h>
// // #elif ASST
// // #include <updown.h>
// #else
// #include <gem5/m5ops.h>
// #include <updown.h>
// #endif

// #ifdef BASIM
// #include <basimupdown.h>
// #endif

#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#else
#include "basimupdown.h"
#endif

#include "alloc.h"

namespace dramalloc {

/* Request: in-memory mailbox for a malloc request, defined as:
 *  - total alloc size
 *  - size of blocks to split the alloc into
 *  - nb of nodes to split the request across (contiguous)
 *  - first node of the alloc
 */
enum DRAMallocRequestType : UpDown::word_t { NO_REQUEST, ALLOCATE_MEMORY, FREE_MEMORY, FINISH };

struct AllocationRequestArgs {
  UpDown::word_t size = 0;
  UpDown::word_t blockSize = 0;
  UpDown::word_t nrNodes = 0;
  UpDown::word_t startNode = 0;
};

struct FreeRequestArgs {
  UpDown::word_t address = 0;
};

struct DRAMRequest {
  DRAMallocRequestType reqType = NO_REQUEST;
  // UpDown::word_t networkId = -1;
  UpDown::word_t continuation = -1;
  union {
    AllocationRequestArgs allocArgs;
    FreeRequestArgs freeArgs;
  };
  uint64_t padding[2];
};

/**
 * @class DramAllocator
 * @brief A class that provides memory allocation and management functionality for DRAM.
 *
 * The DramAllocator class is responsible for allocating and managing memory in DRAM. It provides
 * methods for allocating memory, translating virtual addresses to physical addresses, printing
 * the memory state, and more.
 */
class DramAllocator {
public:
#ifdef GEM5_MODE
  /**
   * \brief Constructs a DramAllocator object.
   *
   * \param runtime A pointer to the UDRuntime_t object.
   * \param eventLabel The event label from the linker output header file ended with DRAMalloc__global_broadcast.
   * \param defaultBlockSize The default block size.
   */
  DramAllocator(UpDown::UDRuntime_t *runtime, uint64_t eventLabel, uint64_t defaultBlockSize);

  /**
   * \brief Constructs a DramAllocator object. (Deprecated, use the constructor without machineConfig.)
   *
   * \param runtime A pointer to the UDRuntime_t object.
   * \param machineConfig The machine configuration.
   * \param eventLabel The event label from the linker output header file ended with DRAMalloc__global_broadcast.
   * \param defaultBlockSize The default block size.
   */
  DramAllocator(UpDown::UDRuntime_t *runtime, UpDown::ud_machine_t machineConfig, uint64_t eventLabel, uint64_t defaultBlockSize);
#else
  /**
   * \brief Constructs a DramAllocator object. 
   *
   * \param runtime A pointer to the UDRuntime_t object.
   * \param eventLabel The event label from the linker output header file ended with DRAMalloc__global_broadcast.
   */
  DramAllocator(UpDown::UDRuntime_t *runtime, uint64_t eventLabel);

  /**
   * \brief Constructs a DramAllocator object. (Deprecated, use the constructor without machineConfig.)
   *
   * \param runtime A pointer to the UDRuntime_t object.
   * \param machineConfig The machine configuration. Note that use the runtime to get the machine configuration.
   * \param eventLabel The event label from the linker output header file ended with DRAMalloc__global_broadcast.
   */
  DramAllocator(UpDown::UDRuntime_t *runtime, UpDown::ud_machine_t machineConfig, uint64_t eventLabel);
  DramAllocator(); // now ASST-Fastsim will call it to link library
#endif
  /**
   * \brief Runs the allocator to handle calls from UpDown. Optional if only to allocate memory from the top.
   */
  void run();

  /**
   * \brief Print allocator states.
   */
  void printMemoryState();

  /**
   * \brief Allocates memory in global virtual memory.
   *
   * \param size The size of the memory to allocate (in Bytes).
   * \param blockSize The size of the block for DRAM alloc (in Bytes).
   * \param numNodes The number of nodes which the segment spans. Note that this number should be a power of 2.
   * \param startNode The starting node ID where the segment to be allocated is located.
   * \return A pointer to the allocated memory. Null if the allocation fails.
   */
  void *mm_malloc_global(size_t size, size_t blockSize, uint64_t numNodes, uint64_t startNode);

  /**
   * \brief Translates a virtual address to a physical address.
   *
   * \param virt The virtual address.
   * \return The physical address. Null if the translation fails.
   */
  void *translate_udva2sa(uint64_t virt);

private:
  struct GTranslateEntry {
    uint64_t virt_base;
    uint64_t phy_base;
    size_t size;
    size_t blockSize;
    uint64_t numNodes;
    uint64_t startNode;
  };

  UpDown::UDRuntime_t *runtime;
  DRAMRequest *args;
  UpDown::word_t *virtStart;
  UpDown::word_t *phyStart;
  Allocator *allocator;
  uint64_t eventLabel;
  uint64_t startNode;
  uint64_t memPerNode;
  std::vector<GTranslateEntry> translation_table;

#ifdef GEM5_MODE
  uint64_t defaultBlockSize;
#endif

  DRAMRequest *getArgAddr();
  void *allocate_memory(size_t size, size_t blockSize, uint64_t numNodes, uint64_t startNode, UpDown::word_t nwid);
  void installTranslationEntries(void *virt, uint64_t phy, size_t size, size_t blockSize, uint64_t numNodes, uint64_t startNode,
                                 UpDown::word_t continuation);
  void writeAllocationResponse(UpDown::word_t *addr);
  void writeFreeResponse();
  void resetArgs();
  uint64_t get_swizzle_mask(size_t blockSize, uint64_t nrNodes);
};

inline uint64_t getNodeId(uint64_t id) { return (id >> 11) & 0xffff; }

}; // namespace dramalloc
