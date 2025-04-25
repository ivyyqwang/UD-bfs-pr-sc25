#include "compatibility.h"
#include "dramalloc.hpp"
#include "networkid.h"
#include "operands.h"
#include "updown_config.h"
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <sys/types.h>

#define IGNORE_CONTINUATION 0x7FFFFFFFFFFFFFFF
#define ROUND_UP_ALLOCATION

namespace dramalloc {

#ifdef GEM5_MODE
DramAllocator::DramAllocator(UpDown::UDRuntime_t *runtime_, uint64_t eventLabel, uint64_t defaultBlockSize)
    : DramAllocator(runtime_, runtime_->getMachineConfig(), eventLabel, defaultBlockSize) {}
#else
DramAllocator::DramAllocator(UpDown::UDRuntime_t *runtime_, uint64_t eventLabel) : DramAllocator(runtime_, runtime_->getMachineConfig(), eventLabel) {}
#endif

#ifdef GEM5_MODE
DramAllocator::DramAllocator(UpDown::UDRuntime_t *runtime_, UpDown::ud_machine_t machineConfig, uint64_t eventLabel, uint64_t defaultBlockSize)
    : eventLabel(eventLabel), defaultBlockSize(defaultBlockSize) {
#else
DramAllocator::DramAllocator() {}
DramAllocator::DramAllocator(UpDown::UDRuntime_t *runtime_, UpDown::ud_machine_t machineConfig, uint64_t eventLabel) : eventLabel(eventLabel) {
#endif

  /* check if the number of nodes is a power of 2 */
  BASIM_ERROR_IF((machineConfig.NumNodes & (machineConfig.NumNodes - 1)) != 0,
                 "The machine has to have a number of nodes that is a power of 2. Current number of nodes: %ld\n", machineConfig.NumNodes);

  /* node id of the start node */
  this->startNode = 0;

  /* address of the start of the global memory physical allocation space */
#ifdef GEM5_MODE
  this->phyStart = reinterpret_cast<UpDown::word_t *>(machineConfig.MapMemBase + machineConfig.MapMemSize / machineConfig.NumStacks);
#else
  this->phyStart = reinterpret_cast<UpDown::word_t *>(this->startNode << 37 | 0x0);
#endif

  /* address of the start of virtual base for global memory */
  this->virtStart = reinterpret_cast<UpDown::word_t *>(machineConfig.GMapMemBase);

  /* UpDown runtime instance*/
  this->runtime = runtime_;

  /* size of simulated memory per node */
  this->memPerNode = machineConfig.GMapMemSize / machineConfig.NumNodes;

  BASIM_INFOMSG("DramAllocator: physical base = %p, virtual base = %p\n", phyStart, virtStart);

  /* create our allocator:
   * a 2d, rtree based allocator that can keep track of physical allocations*/
  this->allocator = new Allocator(this->startNode << 37 | 0x0, machineConfig.GMapMemSize, machineConfig.NumNodes);

#ifdef GEM5_MODE
  printf("DramAllocator: default block size = %ld\n", defaultBlockSize);
#endif

#ifdef FASTSIM
  uint64_t reqSize = sizeof(DRAMRequest) * machineConfig.NumNodes;
#elif GEM5_MODE
  uint64_t reqSize = std::max(sizeof(DRAMRequest), defaultBlockSize) * machineConfig.NumNodes;
#endif

  if (machineConfig.NumNodes == 1) {
    /* need a small allocation in global virtual memory for the request arguments
     * to exists in.
     * This is a sizeof(DRAMRequest) in virtual, and we don't even try to
     * partition it
     */
    UpDown::word_t *req = this->virtStart;
    BASIM_INFOMSG("DramAllocator: req = %p\n", req);
    uint64_t phy = (uint64_t)this->phyStart;
    BASIM_INFOMSG("DramAllocator: machine has only one node, use local memory instead.\n");

    this->args = reinterpret_cast<DRAMRequest *>(machineConfig.PhysGMapMemBase);
    BASIM_INFOMSG("DramAllocator: args = %p\n", this->args);

    installTranslationEntries(req, phy, reqSize, sizeof(DRAMRequest), this->runtime->getMachineConfig().NumNodes, 0, IGNORE_CONTINUATION);

    /* we're ready, reset the arguments */
    resetArgs();
    BASIM_INFOMSG("DramAllocator: Initialized\n");
    return;
  }

  /* need a small allocation in global virtual memory for the request arguments
   * to exists in.
   * This is a sizeof(DRAMRequest) in virtual, and we don't even try to
   * partition it
   */
  this->args = reinterpret_cast<DRAMRequest *>(machineConfig.PhysGMapMemBase);
  BASIM_INFOMSG("DramAllocator: args = %p\n", this->args);

#ifdef FASTSIM
  UpDown::word_t *req = reinterpret_cast<UpDown::word_t *>(runtime->mm_malloc_global(reqSize));
  BASIM_INFOMSG("DramAllocator: req = %p\n", req);
  BASIM_ERROR_IF(req != this->virtStart, "DramAllocator: failed to allocate DRAM allocator internal data at %p, address already allocated.\n", this->virtStart);

  uint64_t phy_offset = this->allocator->allocate(reqSize, sizeof(DRAMRequest), machineConfig.NumNodes, 0);
  BASIM_ERROR_IF(phy_offset == UINT64_MAX,
                 "DramAllocator: failed to allocate DRAM allocator internal data: size = %ld, blockSize = %ld, numNodes = %ld, startNode = %d\n",
                 sizeof(DRAMRequest), sizeof(DRAMRequest), machineConfig.NumNodes, 0);
  uint64_t phy_base = startNode << 37 | phy_offset & (~0ULL >> 37);

  /* install the mapping for this alloc */
  installTranslationEntries(req, phy_base, reqSize, sizeof(DRAMRequest), machineConfig.NumNodes, 0, IGNORE_CONTINUATION);
#elif GEM5_MODE
  UpDown::word_t *req = reinterpret_cast<UpDown::word_t *>(runtime->mm_malloc_global(reqSize));
  BASIM_INFOMSG("DramAllocator: request pointer = %p\n", req);
  BASIM_ERROR_IF(req != this->virtStart, "DramAllocator: failed to allocate DRAM allocator internal data at %p, address already allocated.\n", this->virtStart);

  uint64_t phy_offset = this->allocator->allocate(reqSize, defaultBlockSize, machineConfig.NumNodes, 0);
  BASIM_ERROR_IF(phy_offset == UINT64_MAX,
                 "DramAllocator: failed to allocate DRAM allocator internal data: size = %ld, blockSize = %ld, numNodes = %ld, startNode = %d\n", reqSize,
                 defaultBlockSize, machineConfig.NumNodes, 0);
  uint64_t phy_base = startNode << 37 | phy_offset & ~(~0ULL >> 37);

  /* install the mapping for this alloc */
  installTranslationEntries(req, phy_base, reqSize, defaultBlockSize, machineConfig.NumNodes, 0, IGNORE_CONTINUATION);
#endif

  /* we're ready, reset the arguments */
  resetArgs();
  BASIM_INFOMSG("DramAllocator: Initialized\n");
}

OPTNONE void DramAllocator::run() {
  while (args->reqType != DRAMallocRequestType::FINISH) {
    BASIM_INFOMSG("Allocator(run): Waiting for next request at args %p\n", args);
    if (args->reqType == DRAMallocRequestType::ALLOCATE_MEMORY) {
      BASIM_INFOMSG("Allocator(run): Current args: reqType=%ld, size=%ld, blockSize=%ld, nrNodes=%ld, startNode=%ld\n", args->reqType, args->allocArgs.size,
                    args->allocArgs.blockSize, args->allocArgs.nrNodes, args->allocArgs.startNode);
#ifdef GEM5_MODE
      args->allocArgs.blockSize = defaultBlockSize;
      printf("DramAllocator: Input block size is ignored on GEM5, set to default block size = %ld\n", args->allocArgs.blockSize);
      fflush(stdout);
#endif
      allocate_memory(args->allocArgs.size, args->allocArgs.blockSize, args->allocArgs.nrNodes, args->allocArgs.startNode, args->continuation);
      resetArgs();
    } else if (args->reqType == DRAMallocRequestType::FREE_MEMORY) {
      /* TODO: missing free */
      resetArgs();
      writeFreeResponse();
    }
    UpDown::networkid_t nwid(0, false, 0);
    runtime->start_exec(nwid);
  }
  printf("Allocator: Terminated\n");
}

void *DramAllocator::allocate_memory(size_t size, size_t blockSize, uint64_t numNodes, uint64_t startNode, UpDown::word_t continuation) {
  // Check if the allocation parameter is valid
  BASIM_ERROR_IF(((blockSize & (blockSize - 1)) != 0), "DramAllocator error: block size must be a power of 2.\n");
  BASIM_ERROR_IF((blockSize >= this->memPerNode), "DramAllocator error: block size is greater than available memory per node.\n");
  BASIM_ERROR_IF((blockSize <= 64), "DramAllocator error: block size must be greater than 64 Bytes.\n");
  BASIM_ERROR_IF((numNodes > this->runtime->getMachineConfig().NumNodes),
                 "DramAllocator error: number of nodes is greater than the number of nodes in the system.\n");
  BASIM_ERROR_IF(((numNodes & (numNodes - 1)) != 0), "DramAllocator error: number of nodes must be a power of 2.\n");
  BASIM_ERROR_IF((startNode >= this->runtime->getMachineConfig().NumNodes), "DramAllocator error: Invalid starting node id.\n");

  if (numNodes == 1) {
    void *virt = reinterpret_cast<UpDown::word_t *>(runtime->mm_malloc(size));
    printf("NumNodes = 1 use local memory, allocate memory: VA base = %p, request size = %ld\n", virt, size);

    // install the translation for this allocation
    this->translation_table.push_back({(uint64_t)virt, (uint64_t)virt, size, blockSize, numNodes, startNode});
    installTranslationEntries(virt, (uint64_t)virt, size, blockSize, numNodes, startNode, continuation);

    return virt;
  }

  size_t alloc_size = size;

#ifdef ROUND_UP_ALLOCATION
  /* For now we round up the allocation size to the next multiple of the block size * numNodes (rectangle size)
      and align the block to 8 word boundary*/
  blockSize = std::ceil(blockSize / 8.0) * 8;
  alloc_size = std::ceil(size / (blockSize * numNodes + 0.0)) * (blockSize * numNodes);
#endif

  /* allocation in global virtual memory */
  void *virt = reinterpret_cast<UpDown::word_t *>(runtime->mm_malloc_global(alloc_size));
  /* split alloc in physical memory */
  uint64_t phy = this->allocator->allocate(alloc_size, blockSize, numNodes, startNode);
  BASIM_ERROR_IF((phy == UINT64_MAX), "DramAllocator: failed to allocate memory: size = %ld, blockSize = %ld, numNodes = %ld, startNode = %ld\n", size,
                 blockSize, numNodes, startNode);

  printf("DramAllocator: allocate memory: VA base = %p, PA base = 0x%lX, request size = %ld, allocated size = %ld, block size = %ld, number of nodes = %ld, "
         "start node id = %ld\n",
         virt, phy, size, alloc_size, blockSize, numNodes, startNode);

  /* install the mapping for this allocation */
  this->translation_table.push_back({(uint64_t)virt, (uint64_t)phy, size, blockSize, numNodes, startNode});
  installTranslationEntries(virt, phy, size, blockSize, numNodes, startNode, continuation);

  return virt;
}

DRAMRequest *DramAllocator::getArgAddr() { return this->args; }

void DramAllocator::printMemoryState() { this->allocator->printStats(); }

void DramAllocator::installTranslationEntries(void *virt, uint64_t phy, size_t size, size_t blockSize, uint64_t numNodes, uint64_t startNode,
                                              UpDown::word_t continuation) {
  BASIM_INFOMSG("DramAllocator: install translation entries\n");
  BASIM_INFOMSG("args->allocArgs.virt: %p\n", virt);
  BASIM_INFOMSG("args->allocArgs.phy: 0x%lx\n", phy);
  BASIM_INFOMSG("args->allocArgs.size: %ld\n", size);
  BASIM_INFOMSG("args->allocArgs.blockSize: %ld\n", blockSize);
  BASIM_INFOMSG("args->allocArgs.nrNodes: %ld\n", numNodes);
  BASIM_INFOMSG("args->allocArgs.startNode: %ld\n", startNode);

  // Calculate the swizzle mask for the translation
  uint64_t mask;
  if (numNodes == 1) {
    printf("DramAllocator: single node allocation in local memory, virtual address = physical address = 0x%lX\n", (uint64_t)virt);
    mask = 0;
  } else {
    uint64_t nrC = log2(blockSize);
    uint64_t nrB = log2(numNodes);
    uint64_t nrF = 37 - nrC;
    mask = 0 | (uint64_t(pow(2, nrF)) - 1) << (nrC + nrB) | (uint64_t(pow(2, nrC)) - 1);
    BASIM_INFOMSG("swizzle mask = %ld (0x%lx)\n", mask, mask);

    runtime->lock();

    UpDown::word_t opsData[7];
    UpDown::operands_t ops(7, opsData);
    ops.set_operand(0, reinterpret_cast<UpDown::word_t>(virt));
    ops.set_operand(1, size);
    ops.set_operand(2, mask);
    ops.set_operand(3, phy);
    ops.set_operand(4, this->runtime->getMachineConfig().NumNodes);
    ops.set_operand(5, 1 ? phy != UINT64_MAX : 0);
    ops.set_operand(6, continuation);
    // Install translation to the nodes that can access this memory
    uint64_t nwid = 0;
    UpDown::event_t eventOps(eventLabel, nwid, UpDown::CREATE_THREAD, &ops);

    // Init top flag to 0
    uint64_t val = 0;
    if (continuation == IGNORE_CONTINUATION)
      runtime->t2ud_memcpy(&val, sizeof(uint64_t), nwid, 0 /*Offset*/);

    runtime->send_event(eventOps);
    BASIM_INFOMSG("DramAllocator: send translation for va_base=%p pa_base=0x%lx to nwid [%ld,%ld)\n", virt, phy, 0l,
           this->runtime->getMachineConfig().NumNodes * 64 * 32);
    runtime->start_exec(nwid);
    runtime->unlock();

    if (continuation == IGNORE_CONTINUATION)
      runtime->test_wait_addr(nwid, 0, -1);
  }
}

void DramAllocator::writeFreeResponse() {}

void DramAllocator::resetArgs() {
  this->args->freeArgs.address = 0;

  this->args->allocArgs.size = 0;
  this->args->allocArgs.blockSize = 0;
  this->args->allocArgs.nrNodes = 0;
  this->args->allocArgs.startNode = 0;

  this->args->reqType = DRAMallocRequestType::NO_REQUEST;
}

void *DramAllocator::mm_malloc_global(size_t size, size_t blockSize, uint64_t numNodes, uint64_t startNode) {
  return this->allocate_memory(size, blockSize, numNodes, startNode, IGNORE_CONTINUATION);
}

uint64_t DramAllocator::get_swizzle_mask(size_t blockSize, uint64_t nrNodes) {
  uint64_t nrC = log2(blockSize);
  uint64_t nrB = log2(nrNodes);
  uint64_t nrF = 37 - nrC;
  uint64_t mask = 0 | (uint64_t(pow(2, nrF)) - 1) << (nrC + nrB) | (uint64_t(pow(2, nrC)) - 1);
  return mask;
}

void *DramAllocator::translate_udva2sa(uint64_t virt) {
  BASIM_INFOMSG("Getting physical address for virtual address 0x%lX", (uint64_t)virt);
  for (auto &entry : this->translation_table) {
    if (entry.virt_base <= virt && virt < entry.virt_base + entry.size) {
      BASIM_INFOMSG("Translation entry found: virt_base = 0x%lX, phy_base = 0x%lX, size = %lu, blockSize = %lu, numNodes = %lu, startNode = %lu",
                    entry.virt_base, entry.phy_base, entry.size, entry.blockSize, entry.numNodes, entry.startNode);

      // Check for single node allocation
      if (entry.numNodes == 1) {
        BASIM_INFOMSG("Single node allocation in local memory, virtual address = physical address = 0x%lX", (uint64_t)virt);
        return (void *)(virt);
      }

      // Check for bounds
      UpDown::word_t offset = virt - entry.virt_base;

      // Convert the swizzle mask to the parameters
      uint64_t C = log2(entry.blockSize);
      uint64_t B = log2(entry.numNodes);
      uint64_t F = 37 - C;
      uint64_t P = 64 - C - B - F;

      BASIM_INFOMSG("Swizzle parameters P = %lu, F = %lu, B = %lu, C = %lu", P, F, B, C);

      // Calculate the physical address
      uint64_t blockNumber = (offset >> C) & ((1ULL << (B + F)) - 1);
      uint64_t nodeOffset = blockNumber % entry.numNodes;
      uint64_t blockNumberInNode = blockNumber / entry.numNodes;
      uint64_t blockOffset = offset & ((1ULL << C) - 1);
      BASIM_INFOMSG("Block number %lu, node offset %lu, block number in node %lu, block offset %lu", blockNumber, nodeOffset, blockNumberInNode, blockOffset);

      // Calculate the simulated address
      uint64_t simulatedAddress = this->runtime->getMachineConfig().PhysGMapMemBase + this->memPerNode * (nodeOffset + entry.startNode) +
                                  blockNumberInNode * entry.blockSize + blockOffset + ((entry.phy_base << 27) >> 27);

      BASIM_INFOMSG("Simulated address 0x%lX, memory per node 0x%lX, physGMapMemBase 0x%lX\n", simulatedAddress, memPerNode,
                    this->runtime->getMachineConfig().PhysGMapMemBase);

// #define DEBUG_TRANSLATION
#ifdef DEBUG_TRANSLATION
      uint64_t swizzledAddress = (offset & ~(~0ULL >> P)) | nodeOffset << 37 | blockNumberInNode * entry.blockSize + blockOffset;
      BASIM_INFOMSG("Swizzled address 0x%lX", swizzledAddress);
      uint64_t physicalAddress = ((uint64_t)entry.phy_base) + swizzledAddress;
      BASIM_INFOMSG("Physical address 0x%lX, entry.phy_base 0x%lX, physGMapMemBase 0x%lX", physicalAddress, entry.phy_base,
                    this->runtime->getMachineConfig().PhysGMapMemBase);
      uint64_t pa2sa = ((UpDown::BASimUDRuntime_t *)(this->runtime))->mapPA2SA((basim::Addr)physicalAddress, 1).addr;
      physicalAddress += this->runtime->getMachineConfig().PhysGMapMemBase;
      BASIM_INFOMSG("Calculated simulated address 0x%lX pa2sa return address 0x%lx", physicalAddress, pa2sa);
      BASIM_ERROR_IF(simulatedAddress != physicalAddress, "Translation error! Translation mismatch directly calculated = 0x%lx, from swizzled address = 0x%lx",
                     simulatedAddress, physicalAddress);
#endif

      return (void *)(simulatedAddress);
    }
  }

  BASIM_ERROR("Translation error! Virtual address 0x%lX not exist in translation table\n", (uint64_t)virt);
  // Translation failed
  return nullptr;
}

} // namespace dramalloc
