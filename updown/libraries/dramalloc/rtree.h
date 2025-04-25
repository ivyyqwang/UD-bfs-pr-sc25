#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <vector>

#ifndef RTREE_H
#define RTREE_H 1

/* R-tree style allocator: keep a balanced/sorted tree of our free slots, using
 * their bounding box for indexing. Most of the complexity is in:
 *  - deciding when to split/merge nodes of the tree
 *  - and how to convert an allocation/free into rectangles.
 */

#define MAXNODES 8
#define MINNODES 2
#define MEMDIM 0
#define NODEDIM 1

struct Rect {
  uint64_t start[2];
  size_t len[2];

  size_t area() { return len[0] * len[1]; }
  Rect boundingBox(Rect b) {
    uint64_t ax1 = start[0];
    uint64_t ax2 = ax1 + len[0];
    uint64_t ay1 = start[1];
    uint64_t ay2 = ay1 + len[1];

    uint64_t bx1 = b.start[0];
    uint64_t bx2 = bx1 + b.len[0];
    uint64_t by1 = b.start[1];
    uint64_t by2 = by1 + b.len[1];

    Rect ret;
    ret.start[0] = std::min(ax1, bx1);
    ret.start[1] = std::min(ay1, by1);
    ret.len[0] = std::max(ax2, bx2) - ret.start[0];
    ret.len[1] = std::max(ay2, by2) - ret.start[1];
    return ret;
  }

  /* checks if range fits into block */
  bool fit(size_t startNode, size_t meml, size_t nodel) {
    if (len[MEMDIM] < meml || len[NODEDIM] < nodel)
      return false;
    if (startNode < start[NODEDIM] || startNode > start[NODEDIM] + len[NODEDIM])
      return false;
    if (startNode + nodel > start[NODEDIM] + len[NODEDIM])
      return false;
    return true;
  }

  bool overlap(Rect b) {
    uint64_t ax1 = start[0];
    uint64_t ax2 = ax1 + len[0];
    uint64_t ay1 = start[1];
    uint64_t ay2 = ay1 + len[1];

    uint64_t bx1 = b.start[0];
    uint64_t bx2 = bx1 + b.len[0];
    uint64_t by1 = b.start[1];
    uint64_t by2 = by1 + b.len[1];

    return ax1 >= bx1 && ax2 >= bx2 && ay1 >= by1 && ay2 >= by2;
  }

  bool operator==(Rect r) { return start[0] == r.start[0] && start[1] == r.start[1] && len[0] == r.len[0] && len[1] == r.len[1]; }
};

struct Block {
  Rect rect;
  size_t blockSize;
  size_t area() { return rect.area(); }

  bool operator==(Block b) { return b.rect == rect; }
  bool operator!=(Block b) { return !(b.rect == rect); }
};

struct Node;

struct Branch {
  Node *child;
  Block block;
  size_t area();
};

struct Node {
  bool isLeaf() { return level == 0; }
  int level; /* (leaf is zero, others > 0) */
  int count; /* number of branches */
  Node *parent;
  Rect rect; /* bounding box for the whole node */
  Branch branches[MAXNODES];

  Node(int level) {
    this->level = level;
    this->count = 0;
    this->parent = nullptr;
    this->rect = Rect{{0, 0}, {0, 0}};
  }

  Node(int level, Rect r) {
    this->level = level;
    this->count = 0;
    this->parent = nullptr;
    this->rect = r;
  }
  size_t area() { return rect.area(); }
};

class RTree {
public:
  RTree(uint64_t memStart, uint64_t nodeStart, size_t memLength, size_t
	nodeLength);
  ~RTree() = default;

  /* return a list of Blocks that can contain a rect with given length.
   * Note that we don't provide a starting position for memory, as we
   * don't care.
   */
  std::vector<Block> search(uint64_t startNode, size_t memLenght, size_t nodeLength);

  /* add a new entry in the tree.
   * Can cause nodes of the tree to be split or move levels, including the
   * root.
   */
  void add(Block b);

  /* remove an entry in the tree.
   * Can cause nodes of the tree to be split or move levels, including the
   * root.
   */
  void remove(Block b);

  void printStats(void) { printRecursive(root); }

private:
  Node *root;
  Rect space;

  /* util methods, for internal use */
  void addBlock(Node &node, Block b);
  void removeBlock(Node &node, Block b);
  void addChild(Node &node, Node *n);
  void removeChild(Node &node, Node *n);
  void searchRecursive(Node &node, uint64_t startNode, size_t meml, size_t nodel, std::vector<Block> &ret);
  Node *splitNode(Node *node, Node *n);
  Node *splitNode(Node *node, Block b);
  Node *findLeaf(Node *root, Block b);
  Node *chooseLeaf(Node *root, Block b);
  Node *chooseNode(Node *root, Node *n);
  void reinsert(Node *n);
  void updateBB(Node &n);
  void printRecursive(Node *n);
};

#endif
