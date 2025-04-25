#include "dramalloc.hpp"
#include "out/bfs_exe.hpp"
#include <basim_stats.hh>
#include <basimupdown.h>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sys/types.h>

// #define DEBUG
// #define VALIDATE_RESULT

#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif

#ifdef VALIDATE_RESULT
#include <fstream>
#include <iostream>
#endif

#define USAGE "USAGE: ./updown_bfs_dramalloc <graph_file> <num_uds> <root_vid> (<output_file>) "

#define NUM_UPDATES_OFFSET (3 << 3)
#define NUM_CONSUME_OFFSET (4 << 3)
#define TOP_FLAG_OFFSET (5 << 3)
#define NUM_THREAD_OFFSET (6 << 3)
#define OFRONT_SIZE_OFFSET (8 << 3)
#define NFRONT_SIZE_OFFSET (10 << 3)
#define TOP_VAL_OFFSET (11 << 3)

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define LOG2_WORD_SIZE 3

struct Vertex {
  uint64_t degree;
  uint64_t orig_vid;
  uint64_t vid;
  uint64_t *neighbors;
  uint64_t distance;
  uint64_t parent;
  uint64_t split_range;
  uint64_t padding;
};

void init_scratchpad(UpDown::UDRuntime_t *rt, Vertex *g_v, uint64_t *front_base, uint64_t num_vertices, uint64_t num_uds, uint64_t front_stride) {
  // init scratchpad, event sent to lane 0
  UpDown::word_t ops_data[7];
  UpDown::operands_t ops(7, ops_data);

  /**
    OB_0:   Updown 0's vertex array pointer.
    OB_1:   Total number of vertices.
    OB_2:   Number of UpDowns.
    OB_3:   Updown private vertex array pointer stride
    OB_4:   Nwid mask = number of lanes - 1
    OB_5:   Updown 0's frontier array pointer.
    OB_6:   Updown private frontier array pointer stride
  **/
  ops.set_operand(0, (uint64_t)g_v);
  ops.set_operand(1, (uint64_t)num_vertices);
  ops.set_operand(2, (uint64_t)num_uds);
  ops.set_operand(3, (uint64_t)0);
  ops.set_operand(4, (uint64_t)((num_uds * 64) - 1));
  ops.set_operand(5, (uint64_t)front_base);
  ops.set_operand(6, (uint64_t)front_stride);
  UpDown::networkid_t nwid(0, false, 0);

  UpDown::event_t event_ops(bfs_exe::BFS__init_node /*Event Label*/, nwid, UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);

  rt->send_event(event_ops);
  rt->start_exec(nwid);

  printf("Waiting scratchpad initialization...\n");

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET,
                     1); // UD=0, Lane_ID=0, Offset=4, expected=1
  uint64_t val = 0;
  rt->ud2t_memcpy(&val, sizeof(uint64_t), nwid, TOP_FLAG_OFFSET);
  printf("Scratchpad initialized, flag=%ld.\n", val);

  val = 0;
  rt->t2ud_memcpy(&val, sizeof(uint64_t), nwid, TOP_FLAG_OFFSET);
}

void bfs_init_itr(UpDown::UDRuntime_t *rt, Vertex *g_v, uint64_t **front_bins, uint64_t num_uds, uint64_t num_vertices, uint64_t root_id,
                  dramalloc::DramAllocator *allocator) {

  uint64_t log2_num_uds = std::log2(num_uds);

  // Initialize BFS root and send updates to its neighbors
  uint64_t rootv_udid = root_id % num_uds;
  Vertex* root = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v + root_id));
  root->distance = 0;
  if (root->degree == 0) {
    printf("Root vertex %ld is disconnected (degree = 0), pick another one an try again.\n", root_id);
    exit(1);
  }
  printf("Vertex %ld (addr %p) on bin %ld - deg %ld, dist %ld, parent %ld, "
         "ori_vid %ld, split_range [%ld, %ld], neigh_list %p\n",
         root->vid, (g_v + root_id), rootv_udid, root->degree, root->distance, root->parent, root->orig_vid, root->split_range >> 32,
         root->split_range & 0xffffffff, root->neighbors);
  fflush(stdout);
  uint64_t **frontier_bins = (uint64_t **)allocator->translate_udva2sa((uint64_t)(front_bins + ((rootv_udid) << 1) + 1));
  uint64_t *frontier = *frontier_bins;
  printf("Frontier bins %p, frontier %p\n", frontier_bins, frontier);
  uint64_t *temp_front_ptr;

  if (root->split_range != 0) {
    Vertex *split_vertex;
    uint64_t offset = 0;

    uint64_t split_vid = root->split_range >> 32;
    uint64_t split_bound = root->split_range & 0xffffffff;
    uint64_t num_split_vertices = split_bound - split_vid;
    printf("Root vid %ld is a high degree vertex, split vid range [%ld, %ld], num_split_vertices = %ld\n", root_id, split_vid, split_bound, num_split_vertices);
    fflush(stdout);
    while (split_vid < split_bound) {
      split_vertex = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v + split_vid));

      split_vertex->distance = 0;

      temp_front_ptr = (uint64_t *)allocator->translate_udva2sa((uint64_t)(frontier + offset));
      printf("frontier[offset] = %p, translated = %p\n", frontier + offset, temp_front_ptr);
      *temp_front_ptr = split_vid;
      offset += 1;
      printf("Insert split vertex %ld with degree %ld into updown %ld (nwid=%ld) frontier (%p) offset %ld.\n", split_vertex->vid, split_vertex->degree,
             rootv_udid, rootv_udid << 6, frontier, offset);
      fflush(stdout);
      split_vid++;
    }
    uint64_t *root_frontier_boundary = frontier + num_split_vertices;
    // rt->t2ud_memcpy(&(root_frontier_boundary), sizeof(uint64_t *), UpDown::networkid_t(rootv_udid << 6, false, 0), OFRONT_SIZE_OFFSET /*Offset*/);
    rt->t2ud_memcpy(&(root_frontier_boundary), sizeof(uint64_t *), UpDown::networkid_t(rootv_udid << 6, false, 0), NFRONT_SIZE_OFFSET /*Offset*/);
    printf("Insert %ld verties to updown %ld (nwid=%ld) frontier (%p) with new "
           "boundary %p\n[",
           offset, rootv_udid, rootv_udid << 6, frontier, root_frontier_boundary);
  } else {
    uint64_t *root_frontier = *frontier_bins;
    uint64_t *temp_front_ptr = (uint64_t *)allocator->translate_udva2sa((uint64_t)root_frontier);
    *temp_front_ptr = root_id;
    uint64_t *root_frontier_boundary = root_frontier + 1;

    rt->t2ud_memcpy(&(root_frontier_boundary), sizeof(uint64_t *), UpDown::networkid_t(rootv_udid << 6, false, 0), NFRONT_SIZE_OFFSET /*Offset*/);

    printf("Choose root vertex %ld with degree %ld.\n", root->vid, root->degree);
    printf("Insert vertex %ld to updown %ld (nwid=%ld) frontier (%p) with new "
           "boundary %p\n[",
           *temp_front_ptr, rootv_udid, rootv_udid << 6, root_frontier, root_frontier_boundary);
  }
}

uint64_t bfs_main_updown_iter(UpDown::UDRuntime_t *rt, uint64_t num_uds, uint64_t iter) {
  uint64_t num_node = std::ceil(num_uds / (NUM_CLUSTER_PER_NODE * NUM_UD_PER_CLUSTER + 0.0));
  uint64_t num_ud_per_node = std::min(num_uds, (uint64_t)(NUM_CLUSTER_PER_NODE * NUM_UD_PER_CLUSTER));

  printf("Number of updowns = %ld,\tnumber of nodes = %ld,\tnumber of updowns "
         "per node = %ld.\n",
         num_uds, num_node, num_ud_per_node);

  UpDown::word_t ops_data[4];
  UpDown::operands_t ops(4, ops_data);

  ops.set_operand(0, (uint64_t)num_node);
  ops.set_operand(1, (uint64_t)num_ud_per_node);
  ops.set_operand(2, (uint64_t)iter);

#ifdef DEBUG

#endif

  UpDown::networkid_t nwid(0, false, 0);
  UpDown::event_t event_ops(bfs_exe::BFS__broadcast_frontier /*Event Label*/, nwid, UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->send_event(event_ops);
  uint64_t val = 0;
  rt->t2ud_memcpy(&val, sizeof(uint64_t), nwid, TOP_FLAG_OFFSET);

#ifdef GEM5_MODE
  m5_reset_stats(0, 0);
#endif

  rt->start_exec(nwid);

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

#ifdef GEM5_MODE
  m5_dump_reset_stats(0, 0);
#endif

  rt->ud2t_memcpy(&val, sizeof(uint64_t), nwid, TOP_VAL_OFFSET /*Offset*/);

  return val;
}

int main(int argc, char *argv[]) {

  char *graph_file_path;
  char *output_file;
  if (argc < 4) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  graph_file_path = argv[1];
  uint64_t num_uds = atoi(argv[2]);
  uint64_t log2_num_uds = std::log2(num_uds);
  uint64_t num_lanes = num_uds * NUM_LANE_PER_UD;
  uint64_t root_vertex_id = atoi(argv[3]);
  bool validate_result = false;
  // uint64_t root_vertex_id = 0;
#ifdef VALIDATE_RESULT
  if (argc == 5) {
    output_file = argv[4];
    validate_result = true;
  }
#endif

  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes  = NUM_LANE_PER_UD;
  machine.NumUDs    = std::min(std::max(1, (int)num_uds), NUM_UD_PER_CLUSTER);
  machine.NumStacks = std::min(std::max(1, (int)(num_uds >> 2)), NUM_CLUSTER_PER_NODE);
  machine.NumNodes  = std::max(1, (int)num_uds >> 5);
  machine.LocalMemAddrMode = 1;
// #ifdef DEBUG
  printf("Total number of UpDowns: %ld\nmachine.NumUDs = "
         "%ld\nmachine.NumStacks = %ld\nmachine.NumNodes = %ld\n",
         num_uds, machine.NumUDs, machine.NumStacks, machine.NumNodes);
// #endif

  // Split path name and file name (last token)
  char *graph_file = strdup(graph_file_path);
  char *path = strtok(graph_file, "/");
  while (path != NULL) {
    graph_file = path;
    path = strtok(NULL, "/");
  }
  graph_file = strtok(graph_file, ".");
  printf("Graph file: %s\n", graph_file);

#ifdef GEM5_MODE
  UpDown::UDRuntime_t *bfs_rt = new UpDown::UDRuntime_t(machine);
#else
#ifdef BASIM
  UpDown::BASimUDRuntime_t *bfs_rt;
  if (((int)num_uds >> 5) >= 1)
    bfs_rt = new UpDown::BASimUDRuntime_t(machine, "bfs_exe.bin", 0, 100, std::string(graph_file) + "_" + std::to_string(((int)num_uds >> 5)) + "nds");
  else
    bfs_rt = new UpDown::BASimUDRuntime_t(machine, "bfs_exe.bin", 0, 100, std::string(graph_file) + "_" + argv[2] + "uds");
#else
  // Default configurations runtime
  UpDown::SimUDRuntime_t *bfs_rt = new UpDown::SimUDRuntime_t(machine, "GenSyncBfsEFA", "GenerateSyncBfsEFA", "./", UpDown::EmulatorLogLevel::NONE);
#endif
#endif

#ifdef DEBUG
  printf("=== Base Addresses ===\n");
  bfs_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  bfs_rt->dumpMachineConfig();
#endif

  printf("Number of UpDowns:%ld\n", num_uds);

  printf("Initialize DRAMalloc\n");
  uint64_t blockSize = 4 * 1024;
#ifdef GEM5_MODE
  dramalloc::DramAllocator *allocator = new dramalloc::DramAllocator(bfs_rt bfs_exe::DRAMalloc__global_broadcast /*eventlabel*/, blockSize);
#else
  dramalloc::DramAllocator *allocator = new dramalloc::DramAllocator(bfs_rt, bfs_exe::DRAMalloc__global_broadcast /*eventlabel*/);
#endif
  printf("Finish initialize DRAMalloc\n");

  FILE *in_file = fopen(graph_file_path, "rb");
  if (!in_file) {
    printf("Error when openning file, exiting.\n");
    exit(EXIT_FAILURE);
  }
  std::size_t n;
  uint64_t num_vertices, num_split_vertices, num_edges = 0;
  fseek(in_file, 0, SEEK_SET);
  n = fread(&num_vertices, sizeof(num_vertices), 1, in_file);
  n = fread(&num_split_vertices, sizeof(num_split_vertices), 1, in_file);
  n = fread(&num_edges, sizeof(num_edges), 1, in_file);

  printf("Graph of Size :\n\tnum_vertices=%ld\n\tnum_split_vertices=%ld\n\tnum_edges=%ld\n", num_vertices, num_split_vertices, num_edges);

  printf("Allocating memmory for Vertices...\n");
  Vertex *g_v_bin = reinterpret_cast<Vertex *>(allocator->mm_malloc_global(num_split_vertices * sizeof(Vertex), blockSize, machine.NumNodes, 0));

  printf("Vertices allocation done, allocating neighbour list...\n");
  uint64_t *nlist_bin =
      reinterpret_cast<uint64_t *>(allocator->mm_malloc_global((num_edges + num_split_vertices * 8) * sizeof(uint64_t), blockSize, machine.NumNodes, 0));

  // calculate size of neighbour list and assign values to each member value
  printf("Build the graph now\n");
  fflush(stdout);

  uint64_t curr_base = 0;
  Vertex *temp_vertex;
  uint64_t *neighbors, *temp_neigh;
  uint64_t max_degree = 0;
  for (int i = 0; i < num_split_vertices; i++) {
    temp_vertex = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin + i));
    n = fread(temp_vertex, sizeof(Vertex), 1, in_file);
    temp_vertex->vid = i;
  }
  for (int i = 0; i < num_split_vertices; i++) {
    temp_vertex = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin + i));

    neighbors = nlist_bin + curr_base;
    for (int j = 0; j < temp_vertex->degree; j++) {
      temp_neigh = (uint64_t *)allocator->translate_udva2sa((uint64_t)(neighbors + j));
      n = fread(temp_neigh, sizeof(uint64_t), 1, in_file);
    }
    temp_vertex->neighbors = neighbors;

#ifdef DEBUG
    printf("Vertex vid=%ld addr=%lu(0x%p) - deg %ld, dist %ld, "
           "ori_vid %ld, split_range [%ld, %ld], neigh_list %p\nNeighbors: [",
           temp_vertex->vid, (unsigned long)(g_v_bin + i), (void *)(g_v_bin + i), temp_vertex->degree, temp_vertex->distance, temp_vertex->orig_vid,
           temp_vertex->split_range >> 32, temp_vertex->split_range & 0xffffffff, temp_vertex->neighbors);

    for (int j = 0; j < temp_vertex->degree; j++) {
      // printf("(%ld, %ld) \t", temp_vertex->orig_vid, nlist_bin[curr_base + j]);
      printf("%ld, ", nlist_bin[curr_base + j]);
    }
    printf("]\n");
#endif

    curr_base += std::ceil(temp_vertex->degree / 8.0) * 8;
  }
  printf("Finished reading the graph, number of edges read = %ld.\n", curr_base);

  uint64_t front_stride = (num_split_vertices * 2 / num_uds) * (sizeof(uint64_t)) * 2;
#ifdef DEBUG
  printf("Allocating %ld frontiers, each with %ld vertices, stride = %ld\n", num_uds << 1, num_split_vertices * 2, front_stride);
#endif
  u_int64_t **front_bins = reinterpret_cast<uint64_t **>(allocator->mm_malloc_global(2 * num_uds * sizeof(uint64_t *), blockSize, machine.NumNodes, 0));
  u_int64_t *frontier = reinterpret_cast<uint64_t *>(allocator->mm_malloc_global(2 * front_stride * num_uds, blockSize, machine.NumNodes, 0));
  uint64_t **sa_frontier;
  for (int i = 0; i < num_uds; i++) {
    int k = i << 1;
    sa_frontier = (uint64_t **)allocator->translate_udva2sa((uint64_t)(front_bins + k));
    *sa_frontier = frontier + ((num_split_vertices * 2 / num_uds) * k * 2);
    sa_frontier = (uint64_t **)allocator->translate_udva2sa((uint64_t)(front_bins + k + 1));
    *sa_frontier = frontier + ((num_split_vertices * 2 / num_uds) * (k + 1) * 2);
#ifdef DEBUG
    printf("Allocating frontier for updown %d starting from addr %p and addr %p\n", i, front_bins + k, front_bins + k + 1);
#endif
  }
  sa_frontier = (uint64_t **)allocator->translate_udva2sa((uint64_t)(front_bins));

  printf("Vertices build done.\n");

  printf("Graph Built. Will do BFS now\n");
  printf("Graph: NumEdges:%ld\n", num_edges);
  printf("Graph: NumVertices:%ld\n", num_split_vertices);

  temp_vertex = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin + root_vertex_id));
  if (temp_vertex->split_range == 0 && temp_vertex->degree == 0) {
    printf("Root vertex %ld is not in the graph, degree = 0.\nExit the program.\n", root_vertex_id);
    exit(1);
  }

#ifdef GEM5_MODE

  fflush(stdout);
  m5_switch_cpu();

  printf("Initialize scratchpad...\n");
  // Init scratchpad
  init_scratchpad(bfs_rt, g_v_bin, *sa_frontier, num_split_vertices, num_uds, front_stride);

  printf("Scratchpad initialized.\n");
  printf("Run BFS.\n");
  // Insert the root to frontier
  bfs_init_itr(bfs_rt, g_v_bin, front_bins, num_uds, num_split_vertices, root_vertex_id, allocator);
  fflush(stdout);

  m5_dump_reset_stats(0, 0);
  uint64_t num_iters = bfs_main_updown_iter(bfs_rt, num_uds, 0);

  // m5_dump_reset_stats(0,0);

#else
  fflush(stdout);
  printf("Initialize scratchpad...\n");

  // Init scratchpad
  init_scratchpad(bfs_rt, g_v_bin, *sa_frontier, num_split_vertices, num_uds, front_stride);

  bfs_rt->db_write_stats(0, num_lanes, "INIT_FRONTIER");
#if defined(DETAIL_STATS)
  bfs_rt->db_write_event_stats(0, num_lanes, "INIT_FRONTIER");
#endif
  bfs_rt->reset_stats();
  bfs_rt->reset_sim_ticks();

  printf("Scratchpad initialized.\n");
  printf("Run BFS on root vertex %ld.\n", root_vertex_id);
  fflush(stdout);
  // Insert the root to frontier
  bfs_init_itr(bfs_rt, g_v_bin, front_bins, num_uds, num_split_vertices, root_vertex_id, allocator);

  fflush(stdout);

  uint64_t num_iters = bfs_main_updown_iter(bfs_rt, num_uds, 0);

#endif

  printf("BFS done. Number of iterations = %ld.\n", num_iters);

#ifdef FASTSIM
  // Dump stats and histograms
  bfs_rt->db_write_stats(0, num_uds * NUM_LANE_PER_UD, "bfs");
#if defined(DETAIL_STATS)
  bfs_rt->db_write_event_stats(0, num_lanes, "bfs");
#endif

  for (int i = 0; i < machine.NumNodes; i++) {
    bfs_rt->print_node_stats(i);
  }

for (int i = 0; i < num_uds; i = i + 1) {
  for (int j = 0; j < 64; j = j + 1) {
    // printf("Frontier %d %d: %ld\n", i, j, front_bins[i][j]);
    bfs_rt->print_stats(i, j);

#ifdef DETAIL_STATS
    bfs_rt->print_histograms(i, j);
#endif
  }
}
#endif

#ifdef DEBUG
  for (int i = 0; i < num_split_vertices; i++) {
    temp_vertex = g_v_bin + i;
    if (i == num_vertices) {
      printf("--------------------\nSplit vertices:\n--------------------\n");
    }
    if (temp_vertex->distance == 0 && temp_vertex->degree == 0) continue;
    printf("Vertex %ld (addr %p) - deg %ld, dist %ld, parent %ld, "
            "ori_vid %ld, split_range [%ld, %ld], neigh_list %p\n",
            temp_vertex->vid, (g_v_bin + i), temp_vertex->degree, temp_vertex->distance, temp_vertex->parent, temp_vertex->orig_vid,
            temp_vertex->split_range >> 32, temp_vertex->split_range & 0xffffffff, temp_vertex->neighbors);
  }
#endif

#ifdef VALIDATE_RESULT
  if (validate_result) {
    printf("Output the result BFS tree.\n");
    std::ofstream output(output_file);
    for (int i = 0; i < num_vertices; i++) {
      temp_vertex = g_v_bin + i;
      if (temp_vertex->distance < 0 && temp_vertex->degree == 0) continue;
      if (temp_vertex->distance == 0xffffffffffffffff) continue;
      // #ifdef DEBUG
      // printf("Vertex %ld - dist %ld\n", temp_vertex->vid, temp_vertex->distance);
      // #endif
      output << "Vertex " << temp_vertex->vid << " - dist " << temp_vertex->distance << std::endl;
    }
  }
#endif

  delete bfs_rt;
}
