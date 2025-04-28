#include "LMStaticMap.udwh"
#include "basimupdown.h"
#include "LBBFSEFA.hpp"
#include "dramalloc.hpp"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <stdio.h>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>



template <class T> class DRAM_MALLOC_ARRAY {
  dramalloc::DramAllocator *allocator;
  void *v_adr;

public:
  DRAM_MALLOC_ARRAY() : allocator(nullptr), v_adr(nullptr) {}
  DRAM_MALLOC_ARRAY(dramalloc::DramAllocator *a, size_t size, size_t blockSize,
                    uint64_t numNodes, uint64_t startNode)
      : allocator(a) {
    if (numNodes == 0) {
      numNodes = 1;
    }
    v_adr = allocator->mm_malloc_global(size * sizeof(T) + 64, blockSize,
                                        numNodes, startNode);
  }
  DRAM_MALLOC_ARRAY(DRAM_MALLOC_ARRAY &&other) {
    allocator = other.allocator;
    other.allocator = nullptr;
    v_adr = other.v_adr;
    other.v_adr = nullptr;
  }
  DRAM_MALLOC_ARRAY &operator=(DRAM_MALLOC_ARRAY &&other) {
    if (this == &other)
      return *this;
    this->allocator = other.allocator;
    other.allocator = nullptr;
    this->v_adr = other.v_adr;
    other.v_adr = nullptr;
    return *this;
  }

  T *data() const { return static_cast<T *>(v_adr); }
  T &operator[](size_t i) const {
    return *reinterpret_cast<T *>(allocator->translate_udva2sa(
        reinterpret_cast<uint64_t>(v_adr) + (i * sizeof(T))));
  }
  static T &get(dramalloc::DramAllocator *a, void *ptr, size_t i) {
    return *reinterpret_cast<T *>(a->translate_udva2sa(
        reinterpret_cast<uint64_t>(ptr) + (i * sizeof(T))));
  }
  void reset() {
    allocator = nullptr;
    v_adr = nullptr;
  }
  void set(void *v) { v_adr = v; }
};

template <class T> class DRAM_MALLOC_ELEMENT {
  dramalloc::DramAllocator *allocator;
  void *v_adr;

public:
  DRAM_MALLOC_ELEMENT(dramalloc::DramAllocator *a, uint64_t start_node)
      : allocator(a) {
    uint64_t block_size = 4096;
    while (block_size < sizeof(T)) {
      block_size *= 2;
    }
    v_adr = allocator->mm_malloc_global(sizeof(T), block_size, 1, start_node);
  }
  T *data() const { return static_cast<T *>(v_adr); }
  T &get() const {
    return *reinterpret_cast<T *>(
        allocator->translate_udva2sa(reinterpret_cast<uint64_t>(v_adr)));
  }
};

template <typename Runtime> struct Graph {

  // ideally this would stay half a cache line for some optimization, but its
  // not a big deal if it needs to become a full cache line
  class Vertex {
  public:
    uint64_t *dests = nullptr;
    uint64_t degree = 0;
    uint64_t edges_before = 0;
    uint64_t vertex_id = 0;
    // these can be used for different things
    // things like marking a reservation
    // things like current and next values, or multiple different values
    // this is intrusive but allows for different optimizations
    // required to be reset to max at the begining of each algorithm
    uint64_t scratch1 = std::numeric_limits<uint64_t>::max();
    uint64_t scratch2 = std::numeric_limits<uint64_t>::max();
    uint64_t scratch3 = std::numeric_limits<uint64_t>::max();
    uint64_t scratch4 = std::numeric_limits<uint64_t>::max();


  };
  uint64_t N = 0;
  uint64_t M = 0;
  DRAM_MALLOC_ARRAY<Vertex> vertexs = {};
  Runtime *rt = nullptr;
  dramalloc::DramAllocator *allocator = nullptr;

  DRAM_MALLOC_ARRAY<uint64_t> hidden_edges = {};
  uint64_t hidden_edges_size = 0;

  size_t blockSize;
  uint64_t numNodes;
  uint64_t startNode;

  Graph(Runtime *rt_, dramalloc::DramAllocator *a, size_t blockSize_,
        uint64_t numNodes_, uint64_t startNode_)
      : rt(rt_), allocator(a), blockSize(blockSize_), numNodes(numNodes_),
        startNode(startNode_) {
    if (numNodes == 0) {
      numNodes = 1;
    }
  }

  static Graph make_empty_for_frontier(Runtime *rt_, const Graph &g) {
    return Graph(rt_, g.allocator, g.blockSize, g.numNodes, g.startNode);
  }

  ~Graph() {
    // TODO(wheatman) when dram malloc supports free make sure to free the
    // memory
  }

  friend bool operator==(const Graph &lhs, const Graph &rhs) {
    if (lhs.N != rhs.N) {
      return false;
    }
    if (lhs.M != rhs.M) {
      return false;
    }
    if (lhs.vertexs.data() == nullptr || rhs.vertexs.data() == nullptr) {
      if (lhs.vertexs.data() != rhs.vertexs.data()) {
        return false;
      }
    }
    for (uint64_t i = 0; i < lhs.N; i++) {
      if (lhs.vertexs[i].dests == nullptr || rhs.vertexs[i].dests == nullptr) {
        if (lhs.vertexs[i].dests != rhs.vertexs[i].dests) {
          return false;
        }
      }
      if (lhs.vertexs[i].degree != rhs.vertexs[i].degree) {
        return false;
      }
      if (lhs.vertexs[i].edges_before != rhs.vertexs[i].edges_before) {
        return false;
      }
      if (lhs.vertexs[i].vertex_id != rhs.vertexs[i].vertex_id) {
        return false;
      }
      for (uint64_t i = 0; i < lhs.vertexs[i].degree; i++) {
        if (DRAM_MALLOC_ARRAY<uint64_t>::get(lhs.allocator,
                                             lhs.vertexs[i].dests, i) !=
            DRAM_MALLOC_ARRAY<uint64_t>::get(rhs.allocator,
                                             rhs.vertexs[i].dests, i)) {
          return false;
        }
      }
    }
    return true;
  }
  friend inline bool operator!=(const Graph &lhs, const Graph &rhs) {
    return !(lhs == rhs);
  }

  Graph(Graph &&other) {
    N = other.N;
    other.N = 0;
    M = other.M;
    other.M = 0;
    vertexs = std::move(other.vertexs);
    other.vertexs.reset();
    rt = other.rt;
    other.rt = nullptr;
    hidden_edges = std::move(other.hidden_edges);
    other.hidden_edges.reset();
    hidden_edges_size = other.hidden_edges_size;
    other.hidden_edges_size = 0;
    allocator = other.allocator;
    other.allocator = nullptr;

    blockSize = other.blockSize;
    numNodes = other.numNodes;
    startNode = other.startNode;
    other.blockSize = 0;
    other.numNodes = 0;
    other.startNode = 0;
  }
  Graph &operator=(Graph &&other) {
    if (this == &other)
      return *this;

    this->N = other.N;
    other.N = 0;
    this->M = other.M;
    other.M = 0;
    this->vertexs = std::move(other.vertexs);
    other.vertexs.reset();
    this->rt = other.rt;
    other.rt = nullptr;
    this->hidden_edges = std::move(other.hidden_edges);
    other.hidden_edges.reset();
    this->hidden_edges_size = other.hidden_edges_size;
    other.hidden_edges_size = 0;
    this->allocator = other.allocator;
    other.allocator = nullptr;
    this->blockSize = other.blockSize;
    this->numNodes = other.numNodes;
    this->startNode = other.startNode;
    other.blockSize = 0;
    other.numNodes = 0;
    other.startNode = 0;
    return *this;
  }
  Graph(Runtime *rt_, const std::string_view fname, dramalloc::DramAllocator *a,
        size_t blockSize_, uint64_t numNodes_, uint64_t startNode_)
      : rt(rt_), allocator(a), blockSize(blockSize_), numNodes(numNodes_),
        startNode(startNode_) {
    if (numNodes == 0) {
      numNodes = 1;
    }
    if (fname.substr(fname.size() - 4) == ".adj") {
      read_from_adj(fname);
    } else {
      std::cerr << "not implemented yet\n";
    }
  }
  uint64_t &dest(uint64_t source, uint64_t idx) const {
    return *reinterpret_cast<uint64_t *>(allocator->translate_udva2sa(
        reinterpret_cast<uint64_t>(vertexs[source].dests) +
        (idx * sizeof(uint64_t))));
  }

  void alloc_vertexs_for_frontier(uint64_t num_vertexs) {
    vertexs = DRAM_MALLOC_ARRAY<Vertex>(allocator, num_vertexs, blockSize,
                                        numNodes, startNode);
  }

  void read_from_adj(const std::string_view fname) {
    std::fstream s{fname.data(), std::ios::in};
    char buffer[30] = {0};

    s.getline(buffer, 30, '\n');
    std::string header(buffer);
    if (header != "AdjacencyGraph") {
      std::cerr << "bad input file\n";
      return;
    }
    s >> N >> M;

    vertexs =
        DRAM_MALLOC_ARRAY<Vertex>(allocator, N, blockSize, numNodes, startNode);
    hidden_edges_size = M + (8 * N);
    hidden_edges = DRAM_MALLOC_ARRAY<uint64_t>(allocator, hidden_edges_size,
                                               blockSize, numNodes, startNode);
    uint64_t hidden_edges_offset = 0;
    uint64_t last_offset = 0;
    s >> last_offset;
    for (uint64_t i = 1; i < N; i++) {
      uint64_t offset = 0;
      s >> offset;
      vertexs[i - 1].edges_before = last_offset;
      vertexs[i - 1].degree = offset - last_offset;
      vertexs[i - 1].dests = hidden_edges.data() + hidden_edges_offset;
      hidden_edges_offset += vertexs[i - 1].degree;
      if (hidden_edges_offset % 8 != 8) {
        hidden_edges_offset += 8 - (hidden_edges_offset % 8);
      }
      // alloc<uint64_t>(vertexs[i - 1].degree);
      last_offset = offset;
    }
    vertexs[N - 1].edges_before = last_offset;
    vertexs[N - 1].degree = M - last_offset;
    vertexs[N - 1].dests = hidden_edges.data() + hidden_edges_offset;
    // vertexs[N - 1].dests = alloc<uint64_t>(vertexs[N - 1].degree);

    for (uint64_t i = 0; i < N; i++) {
      for (uint64_t j = 0; j < vertexs[i].degree; j++) {
        uint64_t dst = 0;
        s >> dst;
        dest(i, j) = dst;
      }
      vertexs[i].vertex_id = i;
      vertexs[i].scratch1 = std::numeric_limits<uint64_t>::max();
      vertexs[i].scratch2 = std::numeric_limits<uint64_t>::max();
      vertexs[i].scratch3 = std::numeric_limits<uint64_t>::max();
      vertexs[i].scratch4 = std::numeric_limits<uint64_t>::max();
    }
  }

  void print() {
    std::cout << N << "\n";
    std::cout << M << "\n";
    for (uint64_t i = 0; i < N; i++) {
      std::cout << "Vertex: " << i << "\n";
      for (uint64_t j = 0; j < vertexs[i].degree; j++) {
        std::cout << dest(i, j) << ", ";
      }
      std::cout << "\n";
    }
  }




  std::pair<std::vector<uint64_t>, uint64_t>
  BFS_iter(const std::vector<uint64_t> &distances) const {
    std::vector<uint64_t> next(distances.size());
    uint64_t num_active = 0;
    for (uint64_t i = 0; i < N; i++) {
      uint64_t new_distance = distances[i];
      bool active = false;
      for (uint64_t j = 0; j < vertexs[i].degree; j++) {
        if (distances[dest(i, j)] != std::numeric_limits<uint64_t>::max() &&
            distances[dest(i, j)] + 1 < new_distance) {
          new_distance = distances[dest(i, j)] + 1;
          active = true;
        }
      }
      next[i] = new_distance;
      if (active) {
        num_active += 1;
      }
    }
    return {next, num_active};
  }

  std::vector<uint64_t> BFS(uint64_t source) const {
    std::vector<uint64_t> distances(
        N, (uint64_t)std::numeric_limits<uint64_t>::max());
    distances[source] = 0;
    std::vector<uint64_t> frontier;
    frontier.push_back(source);
    while (!frontier.empty()) {
      std::vector<uint64_t> next_frontier;
      for (auto vertex : frontier) {
        for (uint64_t j = 0; j < vertexs[vertex].degree; j++) {
          auto new_neighbor_distance = distances[vertex] + 1;
          if (new_neighbor_distance < distances[dest(vertex, j)]) {
            distances[dest(vertex, j)] = new_neighbor_distance;
            next_frontier.push_back(dest(vertex, j));
          }
        }
      }
      std::swap(frontier, next_frontier);
    }
    return distances;
  }
};


template <class Graph, class RT>
Graph EdgeMapSparseNonDeterministic(const Graph &g, Graph &frontier, RT *rt,
                                    int num_lanes, int iteration_number) {
  std::vector<uint64_t> correct_next_frontier_ids;
  uint64_t correct_M = 0;
  {
    for (uint64_t i = 0; i < frontier.N; i++) {
      auto v = frontier.vertexs[i];
      uint64_t degree = v.degree;
      uint64_t vertex_id = v.vertex_id;
      for (uint64_t j = 0; j < degree; j++) {
        auto neighbor = g.dest(vertex_id, j);
        uint64_t neighbor_distance = g.vertexs[neighbor].scratch1;
        if (neighbor_distance == std::numeric_limits<uint64_t>::max()) {
          correct_next_frontier_ids.push_back(g.dest(vertex_id, j));
        }
      }
    }
    // Remove duplicates
    std::sort(correct_next_frontier_ids.begin(),
              correct_next_frontier_ids.end());
    auto it = std::unique(correct_next_frontier_ids.begin(),
                          correct_next_frontier_ids.end());
    correct_next_frontier_ids.erase(it, correct_next_frontier_ids.end());
    for (auto vertex_id : correct_next_frontier_ids) {
      correct_M += g.vertexs[vertex_id].degree;
    }
  }

  // printf("range for input frontier = %p, %p\n", f.elements, f.elements +
  // f.N);

  UpDown::networkid_t nwid(0);
  UpDown::operands_t ops(6);
  ops.set_operand(0, frontier.N);
  ops.set_operand(1, frontier.M);
  ops.set_operand(2, frontier.vertexs.data());
  ops.set_operand(3, g.vertexs.data());
  ops.set_operand(4, num_lanes);

  // create an event
  UpDown::event_t event(LBBFSEFA::EM_SPARSE_NON_DETERMINISTIC__start, nwid,
                        UpDown::CREATE_THREAD, &ops);

  UpDown::word_t flag = 0;
  rt->t2ud_memcpy(
      &flag, sizeof(UpDown::word_t), nwid,
      TOP_FLAG_OFFSET); // copy the value of flag to the SP of NWID 0

  // start executing
  rt->send_event(event);
  rt->start_exec(nwid);

  // wait until the value at address TOP_FLAG_OFFSET in network ID 0 becomes 1
  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

  UpDown::word_t thread_id;
  UpDown::word_t frontier_N;
  UpDown::word_t frontier_M;
  rt->ud2t_memcpy(&thread_id, sizeof(UpDown::word_t), nwid, HEAP_OFFSET + 64);
  rt->ud2t_memcpy(&frontier_N, sizeof(UpDown::word_t), nwid, HEAP_OFFSET + 72);
  rt->ud2t_memcpy(&frontier_M, sizeof(UpDown::word_t), nwid, HEAP_OFFSET + 80);
  std::cout << "frontier size N = " << frontier_N << " M = " << frontier_M
            << "\n";

  if (frontier_N != correct_next_frontier_ids.size()) {
    std::cerr << "frontier_N is wrong got " << frontier_N << " expected "
              << correct_next_frontier_ids.size() << "\n";

    std::cerr << "frontier_M  got " << frontier_M << " expected " << correct_M
              << "\n";
    Graph bad_frontier = Graph::make_empty_for_frontier(rt, g);
    bad_frontier.N = 0;
    bad_frontier.M = 0;
    return bad_frontier;
  }

  if (frontier_M != correct_M) {
    std::cerr << "frontier_M is wrong got " << frontier_M << " expected "
              << correct_M << "\n";
    Graph bad_frontier = Graph::make_empty_for_frontier(rt, g);
    bad_frontier.N = 0;
    bad_frontier.M = 0;
    return bad_frontier;
  }

  auto next_frontier = Graph::make_empty_for_frontier(rt, g);
  next_frontier.alloc_vertexs_for_frontier(frontier_N);
  next_frontier.N = frontier_N;
  next_frontier.M = frontier_M;

  UpDown::operands_t ops2(2);
  ops2.set_operand(0, next_frontier.vertexs.data());
  ops2.set_operand(1, iteration_number);

  // create an event
  UpDown::event_t event2(LBBFSEFA::EM_SPARSE_NON_DETERMINISTIC__phase3, nwid,
                         thread_id, &ops2);

  flag = 0;
  rt->t2ud_memcpy(
      &flag, sizeof(UpDown::word_t), nwid,
      TOP_FLAG_OFFSET); // copy the value of flag to the SP of NWID 0

  // start executing
  rt->send_event(event2);
  rt->start_exec(nwid);

  // wait until the value at address TOP_FLAG_OFFSET in network ID 0 becomes 1
  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);
  bool correct = true;

  if (next_frontier.N != correct_next_frontier_ids.size()) {
    std::cerr << "bad size of next frontier got " << next_frontier.N
              << " expected " << correct_next_frontier_ids.size() << "\n";
    correct = false;
  }

  // first check if the degrees and prefix_sums are correct
  std::vector<uint64_t> next_frontier_ids;
  uint64_t prefix_sum = 0;
  for (uint64_t i = 0; i < next_frontier.N; i++) {
    auto v = next_frontier.vertexs[i];
    uint64_t degree = v.degree;
    uint64_t edges_before = v.edges_before;
    uint64_t vertex_id = v.vertex_id;
    if (edges_before != prefix_sum) {
      std::cerr << "bad prefix sum of edges in new frontier\n";
      correct = false;
    }
    prefix_sum += degree;
    if (degree != g.vertexs[vertex_id].degree) {
      std::cerr << "bad degree in new fontier for vertex " << vertex_id << "\n";
      std::cout << "degree was " << degree << " expected "
                << g.vertexs[vertex_id].degree << "\n";
      correct = false;
    }
    next_frontier_ids.push_back(vertex_id);
  }
  std::sort(next_frontier_ids.begin(), next_frontier_ids.end());
  auto it = std::unique(next_frontier_ids.begin(), next_frontier_ids.end());
  if (it != next_frontier_ids.end()) {
    std::cerr << "frontier has duplicates\n";
    correct = false;
  }
  if (correct_next_frontier_ids != next_frontier_ids) {
    std::cerr << "next frontier has the wrong ids in it\n";
    std::cout << "the lengths are " << next_frontier_ids.size() << " and "
              << correct_next_frontier_ids.size() << "\n";
    correct = false;

    std::vector<uint64_t> only_in_mine;
    std::vector<uint64_t> only_in_correct;

    std::set_difference(next_frontier_ids.begin(), next_frontier_ids.end(),
                        correct_next_frontier_ids.begin(),
                        correct_next_frontier_ids.end(),
                        std::inserter(only_in_mine, only_in_mine.begin()));

    std::set_difference(
        correct_next_frontier_ids.begin(), correct_next_frontier_ids.end(),
        next_frontier_ids.begin(), next_frontier_ids.end(),
        std::inserter(only_in_correct, only_in_correct.begin()));
    std::cout << "only in mine\n";
    for (auto id : only_in_mine) {
      std::cout << id << ", ";
    }
    std::cout << "\n";

    std::cout << "only in correct\n";
    for (auto id : only_in_correct) {
      std::cout << id << ", ";
    }
    std::cout << "\n";
  }

  if (!correct) {
    Graph bad_frontier = Graph::make_empty_for_frontier(rt, g);
    bad_frontier.N = 0;
    bad_frontier.M = 0;
    return bad_frontier;
  }

  return next_frontier;
}

template <class G, class RT>
bool BFS_on_UpDown(const G &graph, unsigned long source, RT *rt,
                   int num_lanes) {
  graph.vertexs[source].scratch1 = 0;
  G frontier = G::make_empty_for_frontier(rt, graph);
  frontier.alloc_vertexs_for_frontier(1);
  frontier.N = 1;
  frontier.M = graph.vertexs[source].degree;
  frontier.vertexs[0].dests = graph.vertexs[source].dests;
  frontier.vertexs[0].degree = graph.vertexs[source].degree;
  frontier.vertexs[0].edges_before = 0;
  frontier.vertexs[0].vertex_id = source;
  unsigned long num_active = frontier.N;

  uint64_t iters = 0;
  uint64_t sim_ticks = rt->getSimTicks();

  std::vector<uint64_t> sim_ticks_per_iter;
  std::vector<uint64_t> edges_per_iter;
  std::vector<uint64_t> vertices_per_iter;

  while (num_active) {
    // printf("range for graph frontier = %p, %p\n", frontier.vertexs,
    //        frontier.vertexs + frontier.N);
    auto nextFrontier = EdgeMapSparseNonDeterministic(
        graph, frontier, rt, num_lanes, iters);
    num_active = nextFrontier.N;
    sim_ticks_per_iter.push_back(rt->getSimTicks() - sim_ticks);
    edges_per_iter.push_back(frontier.M);
    vertices_per_iter.push_back(frontier.N);
    sim_ticks = rt->getSimTicks();
    frontier = std::move(nextFrontier);
    iters += 1;
  }
  std::cout << "took " << iters << " iterations\n";
  auto correct = graph.BFS(source);
  uint64_t wrong_positions = 0;
  for (uint64_t i = 0; i < graph.N; i++) {
    if (correct[i] != graph.vertexs[i].scratch1) {
      // std::cout << "incorrect BFS in position " << i << " got " << got
      //           << " expected " << correct[i] << "\n";
      wrong_positions += 1;
    }
  }
  if (wrong_positions) {
    std::cerr << "BFS was wrong in " << wrong_positions << " positions \n";
    return false;
  }
  std::cout << "BFS is correct\n";
  std::cout << "### , iteration number, active_set_size, start_outgoing_size, "
               "sim_ticks\n";
  uint64_t total_ticks = 0;
  for (uint64_t i = 0; i < sim_ticks_per_iter.size(); i++) {
    std::cout << "###, " << i << ", " << vertices_per_iter[i] << ", "
              << edges_per_iter[i] << ", " << sim_ticks_per_iter[i] << "\n";
    total_ticks += sim_ticks_per_iter[i];
  }
  std::cout << "total ticks = " << total_ticks << "\n";
  return true;
}

