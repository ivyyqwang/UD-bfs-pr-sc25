#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <vector>

#include "alloc.h"

Allocator::Allocator(uint64_t start, uint64_t memSize, uint64_t nbNodes) : start{start, 0}, len{memSize, nbNodes}, freeBlocks(start,0, memSize, nbNodes) {}

uint64_t Allocator::allocate(size_t size, size_t blockSize, uint64_t nbNodes, uint64_t startNode) {
  /* transform the request for a search query */
  Rect req;
  req.start[MEMDIM] = 0;
  req.start[NODEDIM] = startNode;

  if (size == 0 || blockSize == 0 || nbNodes == 0) {
    printf("Invalid allocation request, size = %lu, block size = %lu. Size and block size cannot be zero.\n", size, blockSize);
    return UINT64_MAX;
  }

  if (nbNodes <= 1) {
    printf("Invalid allocation request, number of nodes = %ld. The number of nodes need to be greater than 1.\n", nbNodes);
    return UINT64_MAX;
  }
  if ((nbNodes & (nbNodes - 1)) != 0) {
    printf("Invalid allocation request, number of nodes = %ld. The number of nodes must be a power of 2.", nbNodes);
    return UINT64_MAX;
  }

  /* length of the memory allocation on the first node */
  size_t sizeInBlocks = (size / blockSize);
  if (size % blockSize)
    sizeInBlocks++;
  bool isFullRect = sizeInBlocks % nbNodes == 0;
  uint64_t memLength = ((sizeInBlocks / nbNodes) + (isFullRect ? 0 : 1)) * blockSize;
  uint64_t nodeLength = nbNodes;

  /* sanity check: no alloc if we're being asked for less than one block
   * per node
   */
  if (sizeInBlocks < nodeLength) {
    printf("Invalid allocation request. Less than 1 block requested per node, allocation size = %lu, block size = %lu.\n", size, blockSize); 
    return UINT64_MAX;
  }

  /* search for free position */
  std::vector<Block> blocks = this->freeBlocks.search(startNode, memLength, nodeLength);
  if (blocks.empty()) {
    printf("Failed to allocate. No free block found on nodes [%ld, %ld) \n", startNode, startNode + nodeLength);
    return UINT64_MAX;
  }

  /* select one:
   * TODO: better than the first one
   */
  Block selectedBlock = blocks[0];
  this->freeBlocks.remove(selectedBlock);

  /* split the leftovers into nice pieces:
   * we can always start the alloc at the top, but startNode dictates
   * where we start on the y axis. We have maximum 4 blocks to
   * create :
   *      |d|x|x|x|x|a|a|a|     |x|x|x|x|a|a|a|       |x|x|x|x|a|a|a|
   *      |d|x|x|x|x|a|a|a|     |x|x|x|x|a|a|a|       |x|x|x|x|a|a|a|
   *      |d|x|x|b|b|b|b|b| or  |x|x|b|b|b|b|b|  or   |x|x|x|x|a|a|a|
   *      |c|c|c|c|c|c|c|c|     |c|c|c|c|c|c|c|       |c|c|c|c|c|c|c|
   *
   * (mem is vert axis, nodes is horizontal axis)
   * Note that this scheme favors creating allocations across nodes, but
   * makes for more holes.
   **/
  Rect a, b, c, d;
  /* ease our code by computing a few coordinates */
  uint64_t sx1, sx2, sy1, sy2;
  sx1 = selectedBlock.rect.start[MEMDIM];
  sx2 = sx1 + selectedBlock.rect.len[MEMDIM];
  sy1 = selectedBlock.rect.start[NODEDIM];
  sy2 = sy1 + selectedBlock.rect.len[NODEDIM];
  // do we have a block in top right?
  if (startNode + nodeLength < sy2) {
    a.start[MEMDIM] = sx1;
    a.start[NODEDIM] = startNode + nodeLength;
    a.len[MEMDIM] = memLength;
    // there's a b, so a is less tall
    if (!isFullRect)
      a.len[MEMDIM] -= blockSize;
    a.len[NODEDIM] = sy2 - a.start[NODEDIM];
    Block newb = {a, blockSize};
    this->freeBlocks.add(newb);
  }
  // do we have a b?
  if (!isFullRect) {
    b = selectedBlock.rect;
    b.start[MEMDIM] += (sizeInBlocks / nbNodes) * blockSize;
    b.start[NODEDIM] += startNode + sizeInBlocks % nbNodes;
    b.len[MEMDIM] = blockSize;
    b.len[NODEDIM] = sy2 - b.start[NODEDIM];
    Block newb = {b, blockSize};
    this->freeBlocks.add(newb);
  }
  // c can also not be there
  if (memLength != selectedBlock.rect.len[MEMDIM]) {
    c = selectedBlock.rect;
    c.start[MEMDIM] += memLength;
    c.len[MEMDIM] -= memLength;
    Block newb = {c, blockSize};
    this->freeBlocks.add(newb);
  }
  // do we have a block in top left?
  if (startNode != sy1) {
    d = selectedBlock.rect;
    d.len[MEMDIM] = memLength;
    d.len[NODEDIM] = startNode - sy1;
    Block newb = {d, blockSize};
    this->freeBlocks.add(newb);
  }
  /* return the request */
  uint64_t ret = selectedBlock.rect.start[MEMDIM];
  return ret;
}

void Allocator::free(uint64_t start, size_t size, size_t blockSize, uint64_t nbNodes, uint64_t startNode) {
  if (size == 0 || blockSize == 0 || nbNodes == 0)
    return;

  /* transform the request for a search query */
  Rect req;
  req.start[MEMDIM] = start;
  req.start[NODEDIM] = startNode;

  /* length of the memory allocation on the first node */
  size_t sizeInBlocks = (size / blockSize);
  bool isFullRect = sizeInBlocks % nbNodes == 0;
  req.len[MEMDIM] = ((sizeInBlocks / nbNodes) + (isFullRect ? 0 : 1)) * blockSize;
  req.len[NODEDIM] = nbNodes;

  /* insert it in the rtree */
  Block newb = {req, blockSize};
  this->freeBlocks.add(newb);
}
