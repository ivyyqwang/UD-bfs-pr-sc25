#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <memory>
#include <set>
#include <vector>

#include "rtree.h"

size_t Branch::area() {
  if (child != nullptr) {
    return child->rect.area();
  } else {
    return block.rect.area();
  }
}

RTree::RTree(uint64_t memStart, uint64_t nodeStart, size_t memLength, size_t
	     nodeLength) {
  Rect r;
  r.start[MEMDIM] = memStart;
  r.start[NODEDIM] = nodeStart;
  r.len[MEMDIM] = memLength;
  r.len[NODEDIM] = nodeLength;
  root = new Node(0, r);
  this->space = r;
  addBlock(*root, Block{r, 64});
}

void RTree::addBlock(Node &node, Block b) {
  assert(node.count < MAXNODES);

  /* insertion sort, we want to keep it sorted per area, and
   * we know it's always sorted
   */
  node.branches[node.count] = Branch{nullptr, b};
  for (int i = 0; i < node.count; i++) {
    if (node.branches[i].area() < b.area())
      continue;

    Branch tmp;
    tmp = node.branches[i];
    node.branches[i] = node.branches[node.count];
    node.branches[node.count] = tmp;
  }
  node.count++;
}

void RTree::addChild(Node &node, Node *n) {
  assert(node.count < MAXNODES);

  /* insertion sort, we want to keep it sorted per area, and
   * we know it's always sorted
   */
  n->parent = &node;
  n->level = node.level - 1;
  node.branches[node.count] = Branch{n, Block{0}};
  for (int i = 0; i < node.count; i++) {
    if (node.branches[i].area() < n->rect.area())
      continue;

    Branch tmp;
    tmp = node.branches[i];
    node.branches[i] = node.branches[node.count];
    node.branches[node.count] = tmp;
  }
  node.count++;
}

void RTree::removeBlock(Node &node, Block b) {
  assert(node.count > 0);
  int i;
  for (i = 0; i < node.count && b != node.branches[i].block; i++)
    ;
  assert(i < node.count);
  for (; i < node.count - 1; i++) {
    node.branches[i] = node.branches[i + 1];
  }
  node.count--;
}

void RTree::removeChild(Node &node, Node *n) {
  assert(node.count > 0);
  int i;
  for (i = 0; i < node.count && n != node.branches[i].child; i++)
    ;
  assert(i < node.count);
  for (; i < node.count - 1; i++) {
    node.branches[i] = node.branches[i + 1];
  }
  node.count--;
}

void RTree::searchRecursive(Node &node, uint64_t startNode, size_t meml, size_t nodel, std::vector<Block> &ret) {
  /* Iterate over the available branches, and try to fit a good fit:
   * ideally we want in this order:
   *  - exact fit
   *  - one edge is the full length
   *  - biggest area (bigger chunks left)
   *
   * Since the branches are sorted per area, we can just select the first
   * one that actually returns something.
   */
  size_t reqarea = meml * nodel;
  if (node.isLeaf()) {
    for (int i = 0; i < node.count; i++) {
      Branch b = node.branches[i];
      if (b.area() < reqarea)
        continue;
      if (b.block.rect.fit(startNode, meml, nodel))
        ret.push_back(b.block);
    }
  } else {
    for (int i = 0; i < node.count; i++) {
      Branch b = node.branches[i];
      if (b.area() < reqarea)
        continue;
      if (!b.child->rect.fit(startNode, meml, nodel))
        continue;
      searchRecursive(*b.child, startNode, meml, nodel, ret);
    }
  }
}

std::vector<Block> RTree::search(uint64_t startNode, size_t meml, size_t nodel) {
  std::vector<Block> ret;
  searchRecursive(*this->root, startNode, meml, nodel, ret);
  return ret;
}

Node *RTree::chooseLeaf(Node *n, Block b) {
  if (n->isLeaf())
    return n;

  /* find the node with the least enlargement */
  assert(n->count > 0);
  size_t area = b.rect.boundingBox(n->branches[0].child->rect).area() - n->branches[0].child->rect.area();
  int imin = 0;
  for (int i = 1; i < n->count; i++) {
    Rect r = b.rect.boundingBox(n->branches[i].child->rect);
    size_t na = r.area() - n->branches[i].child->rect.area();
    if (na < area) {
      imin = i;
      area = na;
    }
    /* TODO: optimization: tie breakers */
  }
  return chooseLeaf(n->branches[imin].child, b);
}

void RTree::updateBB(Node &n) {
  assert(n.count > 0);
  Rect r;
  if (n.isLeaf()) {
    r = n.branches[0].block.rect;
    for (int i = 1; i < n.count; i++)
      r = r.boundingBox(n.branches[i].block.rect);
  } else {
    r = n.branches[0].child->rect;
    for (int i = 1; i < n.count; i++)
      r = r.boundingBox(n.branches[i].child->rect);
  }
  n.rect = r;
}

/* quadratic split algorithm from original paper:
 * split a node and an extra entry (branch) into two "balanced" nodes.
 */
Node *RTree::splitNode(Node *target, Node *newNode) {
  assert(target != nullptr);
  std::vector<Node *> entries;
  for (int i = 0; i < target->count; i++)
    entries.push_back(target->branches[i].child);
  entries.push_back(newNode);

  /* pick seeds for each group:
   * compute for pair each of entries the difference between their
   * boundingbox area and their respective areas, and choose the
   * most wasteful pair:
   *  max(zip(entries,entries).map(a.BB(b).area - a.area - b.area))
   */
  size_t deltaAreas[MAXNODES + 1][MAXNODES + 1];
  size_t maxd = 0;
  int imax = 0, jmax = 1;
  for (int i = 0; i < entries.size(); i++)
    for (int j = 0; j < entries.size(); j++) {
      Node *a = entries[i];
      Node *b = entries[j];
      Rect BB = a->rect.boundingBox(b->rect);
      size_t val = BB.area() - a->area() - b->area();
      deltaAreas[i][j] = val;
      if (maxd < val) {
        maxd = val;
        imax = i;
        jmax = j;
      }
    }
  std::vector<Node *> groupA, groupB;
  Node *a = entries[imax];
  Node *b = entries[jmax];
  groupA.push_back(a);
  groupB.push_back(b);
  Rect aBB = a->rect;
  Rect bBB = b->rect;

  std::set<Node *> toInsert;
  for (int i = 0; i < entries.size(); i++)
    if (i != imax && i != jmax)
      toInsert.insert(entries[i]);

  while (!toInsert.empty()) {
    /* never create a node with less than MINNODES entries */
    if (groupA.size() + toInsert.size() == MINNODES) {
      groupA.insert(groupA.end(), toInsert.begin(), toInsert.end());
      break;
    }
    if (groupB.size() + toInsert.size() == MINNODES) {
      groupB.insert(groupB.end(), toInsert.begin(), toInsert.end());
      break;
    }
    /* pick an entry to add to a group by finding the entry with
     * the most difference in area increase when added to a group
     */
    maxd = 0;
    auto max = toInsert.begin();
    size_t maxdA = 0;
    size_t maxdB = 0;
    for (auto it = toInsert.begin(); it != toInsert.end(); it++) {
      size_t dA = aBB.boundingBox((*it)->rect).area() - aBB.area();
      size_t dB = bBB.boundingBox((*it)->rect).area() - bBB.area();
      if (maxd < std::abs((long)(dA - dB))) {
        maxd = std::abs((long)(dA - dB));
        max = it;
        maxdA = dA;
        maxdB = dB;
      }
    }

    /* add the entry to the group that will enlarge the least */
    a = *max;
    if (maxdA < maxdB) {
      groupA.push_back(a);
    } else if (maxdA > maxdB) {
      groupB.push_back(a);
    } else {
      /* tie, choose smaller area */
      if (aBB.area() < bBB.area()) {
        groupA.push_back(a);
      } else if (aBB.area() > bBB.area()) {
        groupB.push_back(a);
      } else {
        /* tie, choose smaller group */
        if (groupA.size() < groupB.size())
          groupA.push_back(a);
        else
          groupB.push_back(a);
      }
    }
    toInsert.erase(max);
  }
  /* replace entries of target Node with groupA, create new node with
   * groupB
   */
  target->count = 0;
  for (int i = 0; i < groupA.size(); i++)
    addChild(*target, groupA[i]);
  updateBB(*target);
  Node *ret = new Node(target->level);
  for (int i = 0; i < groupB.size(); i++)
    addChild(*ret, groupB[i]);
  updateBB(*ret);
  return ret;
}

Node *RTree::splitNode(Node *target, Block newBlock) {
  assert(target != nullptr);
  std::vector<Block> entries;
  for (int i = 0; i < target->count; i++)
    entries.push_back(target->branches[i].block);
  entries.push_back(newBlock);

  /* pick seeds for each group:
   * compute for pair each of entries the difference between their
   * boundingbox area and their respective areas, and choose the
   * most wasteful pair:
   *  max(zip(entries,entries).map(a.BB(b).area - a.area - b.area))
   */
  size_t deltaAreas[MAXNODES + 1][MAXNODES + 1];
  size_t maxd = 0;
  int imax = 0, jmax = 1;
  for (int i = 0; i < entries.size(); i++)
    for (int j = 0; j < entries.size(); j++)
      if (i != j) {
        Block a = entries[i];
        Block b = entries[j];
        Rect BB = a.rect.boundingBox(b.rect);
        size_t val = BB.area() - a.area() - b.area();
        deltaAreas[i][j] = val;
        if (maxd < val) {
          maxd = val;
          imax = i;
          jmax = j;
        }
      }
  std::vector<Block> groupA, groupB;
  Block a = entries[imax];
  Block b = entries[jmax];
  groupA.push_back(a);
  groupB.push_back(b);
  Rect aBB = a.rect;
  Rect bBB = b.rect;

  std::vector<Block> toInsert;
  for (int i = 0; i < entries.size(); i++)
    if (i != imax && i != jmax)
      toInsert.push_back(entries[i]);

  while (!toInsert.empty()) {
    /* never create a node with less than MINNODES entries */
    if (groupA.size() + toInsert.size() == MINNODES) {
      groupA.insert(groupA.end(), toInsert.begin(), toInsert.end());
      break;
    }
    if (groupB.size() + toInsert.size() == MINNODES) {
      groupB.insert(groupB.end(), toInsert.begin(), toInsert.end());
      break;
    }
    /* pick an entry to add to a group by finding the entry with
     * the most difference in area increase when added to a group
     */
    maxd = 0;
    auto max = toInsert.begin();
    size_t maxdA = 0;
    size_t maxdB = 0;
    for (auto it = toInsert.begin(); it != toInsert.end(); it++) {
      size_t dA = aBB.boundingBox((*it).rect).area() - aBB.area();
      size_t dB = bBB.boundingBox((*it).rect).area() - bBB.area();
      if (maxd < std::abs((long)(dA - dB))) {
        maxd = std::abs((long)(dA - dB));
        max = it;
        maxdA = dA;
        maxdB = dB;
      }
    }

    /* add the entry to the group that will enlarge the least */
    a = *max;
    if (maxdA < maxdB) {
      groupA.push_back(a);
    } else if (maxdA > maxdB) {
      groupB.push_back(a);
    } else {
      /* tie, choose smaller area */
      if (aBB.area() < bBB.area()) {
        groupA.push_back(a);
      } else if (aBB.area() > bBB.area()) {
        groupB.push_back(a);
      } else {
        /* tie, choose smaller group */
        if (groupA.size() < groupB.size())
          groupA.push_back(a);
        else
          groupB.push_back(a);
      }
    }
    toInsert.erase(max);
  }
  /* replace entries of target Node with groupA, create new node with
   * groupB
   */
  target->count = 0;
  for (int i = 0; i < groupA.size(); i++)
    addBlock(*target, groupA[i]);
  updateBB(*target);
  Node *ret = new Node(target->level);
  for (int i = 0; i < groupB.size(); i++)
    addBlock(*ret, groupB[i]);
  updateBB(*ret);
  return ret;
}

void RTree::add(Block b) {
  Node *leaf = chooseLeaf(this->root, b);
  Node *newleaf = nullptr;
  if (leaf->count < MAXNODES) {
    addBlock(*leaf, b);
    updateBB(*leaf);
  } else {
    /* TODO: optimization: merge blocks instead of split */
    newleaf = splitNode(leaf, b);
  }
  /* AdjustTree */
  while (leaf != this->root) {
    /* adjust boundingbox in parent */
    Node *p = leaf->parent;
    Node *pp = nullptr;
    updateBB(*p);
    if (newleaf != nullptr) {
      /* add newleaf to parent, or split parent */
      if (p->count < MAXNODES) {
        addChild(*p, newleaf);
        updateBB(*p);
      } else {
        pp = splitNode(p, newleaf);
      }
    }
    leaf = p;
    newleaf = pp;
  }
  /* if root split, create new root */
  if (newleaf != nullptr) {
    Node *newr = new Node(leaf->level + 1);
    addChild(*newr, leaf);
    addChild(*newr, newleaf);
    updateBB(*newr);
    this->root = newr;
  }
}

Node *RTree::chooseNode(Node *root, Node *n) {
  if (root->level == n->level)
    return root;
  std::vector<size_t> newareas;
  for (int i = 0; i < root->count; i++) {
    Rect r = n->rect.boundingBox(root->branches[i].child->rect);
    newareas.push_back(r.area() - root->branches[i].child->rect.area());
  }
  int i = std::max_element(newareas.begin(), newareas.end()) - newareas.end();
  assert(i < root->count);
  return chooseNode(root->branches[i].child, n);
}

void RTree::reinsert(Node *n) {
  Node *node = chooseNode(this->root, n);
  Node *newnode = nullptr;
  if (node->count < MAXNODES) {
    addChild(*node, n);
    updateBB(*node);
  } else {
    newnode = splitNode(node, n);
  }
  /* AdjustTree */
  while (node != this->root) {
    /* adjust boundingbox in parent */
    Node *p = node->parent;
    Node *pp = nullptr;
    updateBB(*p);
    if (newnode != nullptr) {
      /* add newnode to parent, or split parent */
      if (p->count < MAXNODES) {
        addChild(*p, newnode);
        updateBB(*p);
      } else {
        pp = splitNode(p, newnode);
      }
    }
    node = p;
    newnode = pp;
  }
  /* if root split, create new root */
  if (newnode != nullptr) {
    Node *newr = new Node(node->level + 1);
    addChild(*newr, node);
    addChild(*newr, newnode);
    updateBB(*newr);
    this->root = newr;
  }
}

Node *RTree::findLeaf(Node *node, Block b) {
  if (node->isLeaf()) {
    for (int i = 0; i < node->count; i++)
      if (node->branches[i].block == b)
        return node;
    return nullptr;
  }
  for (int i = 0; i < node->count; i++) {
    Node *c = node->branches[i].child;
    if (c->rect.overlap(b.rect)) {
      Node *ret = findLeaf(c, b);
      if (ret != nullptr)
        return ret;
    }
  }
  return nullptr;
}

void RTree::remove(Block b) {
  Node *leaf = findLeaf(this->root, b);
  if (leaf == nullptr)
    return;

  removeBlock(*leaf, b);
  /* condenseTree */
  std::vector<Node *> removedNodes;
  while (leaf != this->root) {
    Node *p = leaf->parent;
    if (leaf->count < MINNODES) {
      removeChild(*p, leaf);
      removedNodes.push_back(leaf);
    } else {
      updateBB(*leaf);
    }
    leaf = p;
  }
  for (int i = 0; i < removedNodes.size(); i++) {
    Node *n = removedNodes[i];
    if (n->isLeaf()) {
      for (int j = 0; j < n->count; j++) {
        add(n->branches[j].block);
      }
      delete n;
    } else
      reinsert(n);
  }
  /* shorten the tree if the root contains a single child */
  if (this->root->count == 1 && this->root->branches[0].child != nullptr) {
    Node *oldr = this->root;
    this->root = this->root->branches[0].child;
    this->root->level--;
    this->root->parent = nullptr;
    delete oldr;
  }
}

void RTree::printRecursive(Node *n) {
  if (n == nullptr)
    return;

  std::cout << "n:" << n << " "
            << "count: " << n->count << ", "
            << "level: " << n->level << ", "
            << "rect: {" << n->rect.start[0] << ", " << n->rect.start[1] << ", " << n->rect.len[0] << ", " << n->rect.len[1] << "}\n";

  for (int i = 0; i < n->count; i++) {
    if (n->isLeaf()) {
      Block b = n->branches[i].block;
      std::cout << "i:" << i << " "
                << "blockSize: " << b.blockSize << ", "
                << "rect: {" << b.rect.start[0] << ", " << b.rect.start[1] << ", " << b.rect.len[0] << ", " << b.rect.len[1] << "}\n";
    } else
      printRecursive(n->branches[i].child);
  }
}
