#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <vector>

#include "rtree.h"

class Allocator {
public:
  Allocator(uint64_t start, size_t memSize, size_t nbNodes);
  ~Allocator() = default;

  uint64_t allocate(size_t size, size_t blockSize, uint64_t nbNodes, uint64_t startNode);
  void free(uint64_t start, size_t size, size_t blocksize, uint64_t nbNodes, uint64_t startNode);

  void printStats(void) { freeBlocks.printStats(); }

private:
  RTree freeBlocks;
  uint64_t start[2];
  size_t len[2];
};
