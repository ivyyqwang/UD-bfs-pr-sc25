
#include "dramalloc.hpp"
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>

#ifdef BASIM
#include <basimupdown.h>
#endif

#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif

// #define VALIDATE_RESULT
// #define DEBUG
#define STATS
// #define DEBUG_GRAPH

#ifdef VALIDATE_RESULT
#include <fstream>
#include <iostream>
#endif

#include "out/pagerank_pull_dd.hpp"

#define USAGE                                                                                                                                                  \
  "USAGE: ./pagerankPullMSR <graph_file_path> <num_nodes> <num_uds> <partition_per_lane> (<output_file_path>)\n\
  graph_file_path: \tpath to the graph file.\n\
  num_nodes: \tnumber of nodes, minimum is 1.\n\
  num_uds: \tnumber of UDs per node, default = 32 if greater than 1 node is used.\n\
  partition_per_lane: \tnumber of partitions per lane.\n"

#define NUM_LANE_PER_UD 64
#define NUM_UD_PER_CLUSTER 4
#define NUM_CLUSTER_PER_NODE 8
#define TOP_FLAG_OFFSET 0

#define NUM_PR_ITERATIONS 5

#define ALPHA 0.85
// #define EPSILON (0.000001)

// #define PART_PARM 1

struct Vertex {
  uint64_t id;
  uint64_t deg;
  uint64_t *neigh;
  double val;
  uint64_t active_flag;
  uint64_t padding[3]; // Padding to 64 bytes
};


struct Iterator {
  Vertex *begin;
  Vertex *end;
};

int main(int argc, char *argv[]) {

  if (argc < 5) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }

  std::string filename(argv[1]);
  uint64_t num_nodes = atoi(argv[2]);
  uint64_t num_uds_per_node = NUM_UD_PER_CLUSTER * NUM_CLUSTER_PER_NODE;
  uint64_t num_lanes_per_ud = NUM_LANE_PER_UD;
  int PART_PARM = atoi(argv[4]);

  if (num_nodes < 2) {
    num_nodes = 1;
    num_uds_per_node = atoi(argv[3]);
  }

  // Split path name and file name (last token)
  char *graph_file = strdup(filename.c_str());
  char *path = strtok(graph_file, "/");
  while (path != NULL) {
    graph_file = path;
    path = strtok(NULL, "/");
  }
  graph_file = strtok(graph_file, ".");

  printf("Test configurations: \n\tnum_nodes = %ld, \n\tnum_uds_per_node = %ld, \n\tnum_lanes_per_ud = %ld, ", num_nodes, num_uds_per_node, num_lanes_per_ud);

  uint64_t num_lanes = num_nodes * num_uds_per_node * num_lanes_per_ud;

  printf("\n\ttotal_num_lanes = %ld\n", num_lanes);

  // Set up machine parameters
  UpDown::ud_machine_t machine;
  machine.NumLanes = num_lanes_per_ud;
  machine.NumUDs = std::min((int)num_uds_per_node, NUM_UD_PER_CLUSTER);
  machine.NumStacks = std::ceil((double)num_uds_per_node / NUM_UD_PER_CLUSTER);
  machine.NumNodes = num_nodes;
  machine.LocalMemAddrMode = 1;

#ifdef GEM5_MODE
  UpDown::UDRuntime_t *pagerank_rt = new UpDown::UDRuntime_t(machine);
#elif BASIM
  UpDown::BASimUDRuntime_t *pagerank_rt =
      new UpDown::BASimUDRuntime_t(machine, "pagerank_pull_dd.bin", 0, 100, std::string(graph_file) + "_" + argv[2] + "nds");
#endif

#ifdef DEBUG
  printf("=== Base Addresses ===\n");
  pagerank_rt->dumpBaseAddrs();
  printf("\n=== Machine Config ===\n");
  pagerank_rt->dumpMachineConfig();
#endif

  printf("Initialize DRAMalloc\n");
  uint64_t blockSize = 4 * 1024;
#ifdef GEM5_MODE
  dramalloc::DramAllocator *allocator = new dramalloc::DramAllocator(pagerank_rt pagerank_pull_dd::DRAMalloc__global_broadcast /*eventlabel*/, blockSize);
#else
  dramalloc::DramAllocator *allocator = new dramalloc::DramAllocator(pagerank_rt, pagerank_pull_dd::DRAMalloc__global_broadcast /*eventlabel*/);
#endif
  printf("Finish initialize DRAMalloc\n");

  FILE *in_file_gv = fopen((filename + "_gv.bin").c_str(), "rb");
  if (!in_file_gv) {
    printf("Error when openning file %s, exiting.\n", (filename + "_gv.bin").c_str());
    exit(EXIT_FAILURE);
  }

  FILE *in_file_nl = fopen((filename + "_nl.bin").c_str(), "rb");
  if (!in_file_nl) {
    printf("Error when openning file %s, exiting.\n", (filename + "_nl.bin").c_str());
    exit(EXIT_FAILURE);
  }

  uint64_t num_vertices, num_edges;
  std::size_t n;

  fseek(in_file_gv, 0, SEEK_SET);
  n = fread(&num_vertices, sizeof(num_vertices), 1, in_file_gv);
  n = fread(&num_edges, sizeof(num_edges), 1, in_file_nl);
  printf("Input graph: Number of vertices = %ld\t Number of edges = %ld\n", num_vertices, num_edges);
  fflush(stdout);

  // Allocate the array where the top and updown can see it:
  Vertex *g_v_bin_0 = reinterpret_cast<Vertex *>(allocator->mm_malloc_global(num_vertices * sizeof(Vertex), blockSize, num_nodes, 0));
  Vertex *g_v_bin_1 = reinterpret_cast<Vertex *>(allocator->mm_malloc_global(num_vertices * sizeof(Vertex), blockSize, num_nodes, 0));

  uint64_t *nlist_bin = reinterpret_cast<uint64_t *>(allocator->mm_malloc_global((num_edges + num_vertices * 8) * sizeof(uint64_t), blockSize, num_nodes, 0));

  uint64_t num_partitions = num_lanes * PART_PARM;
  uint64_t num_pairs_per_part = ceil((num_vertices + 0.0) / num_partitions);
  printf("Number of partitions per lane = %d\t Number of partitions = %ld\t Number of vertices per partition = %ld\n", PART_PARM, num_partitions,
         num_pairs_per_part);

  Iterator *partitions_0 = reinterpret_cast<Iterator *>(allocator->mm_malloc_global((num_partitions) * sizeof(Iterator), blockSize, num_nodes, 0));
  Iterator *partitions_1 = reinterpret_cast<Iterator *>(allocator->mm_malloc_global((num_partitions) * sizeof(Iterator), blockSize, num_nodes, 0));

#ifdef DEBUG
  printf("Vertax array 0 = %p\n", g_v_bin_0);
  printf("Vertax array 1 = %p\n", g_v_bin_1);
  printf("Edge array = %p\n", nlist_bin);
#endif

  // calculate size of neighbour list and assign values to each member value
  printf("Build the graph now\n");
  fflush(stdout);

  uint64_t curr_base = 0;
  Vertex *temp_vertex_0, *temp_vertex_1;
  uint64_t *temp_neigh;
  double val = (1.0 - ALPHA) / num_vertices;
  for (int i = 0; i < num_vertices; i++) {
    temp_vertex_0 = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin_0 + i));
    n = fread(temp_vertex_0, sizeof(Vertex) / 2, 1, in_file_gv);
    temp_vertex_0->neigh = nlist_bin + curr_base;
    temp_vertex_0->val = val;
    temp_vertex_0->active_flag = 1;

    for (int j = 0; j < temp_vertex_0->deg; j++) {
      temp_neigh = (uint64_t *)allocator->translate_udva2sa((uint64_t)(temp_vertex_0->neigh + j));
      n = fread(temp_neigh, sizeof(uint64_t), 1, in_file_nl);
    }

    temp_vertex_1 = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin_1 + i));
    temp_vertex_1->id = temp_vertex_0->id;
    temp_vertex_1->deg = temp_vertex_0->deg;
    temp_vertex_1->neigh = nlist_bin + curr_base;
    temp_vertex_1->val = 0.0;
    temp_vertex_1->active_flag = 0;

#ifdef DEBUG_GRAPH
    printf("Vertex[0] %d (addr %p) - deg %ld, neigh_list %p\n", i, (g_v_bin_0 + i), temp_vertex_0->deg, (nlist_bin + curr_base));
    printf("Vertex[1] %d (addr %p) - deg %ld, neigh_list %p\n", i, (g_v_bin_1 + i), temp_vertex_0->deg, (nlist_bin + curr_base));
#endif
    curr_base += std::ceil(temp_vertex_0->deg / 8.0) * 8;
}

#ifdef DEBUG
  printf("-------------------\nparitions 0 = %p\n", partitions_0);
  fflush(stdout);
#endif

  // Initialize partitions
  Iterator *temp_partition;
  int offset = 0;
  for (int i = 0; i < num_partitions; i++) {
    temp_partition = (Iterator *)allocator->translate_udva2sa((uint64_t)(partitions_0 + i));
    temp_partition->begin = g_v_bin_0 + offset;
    offset = std::min((i + 1) * num_pairs_per_part, num_vertices);
    temp_partition->end = g_v_bin_0 + offset;
#ifdef DEBUG_GRAPH
    printf("Partition %d: pair_id=%d, key=%ld"
           "base_pair_addr=%p, part_entry_addr=%p\n",
           i, offset, temp_partition->begin->id, partitions_0 + i, partitions_0 + i);
#endif
  }

#ifdef DEBUG
  printf("-------------------\nparitions 1 = %p\n", partitions_1);
  fflush(stdout);
#endif
  // Initialize partitions
  offset = 0;
  for (int i = 0; i < num_partitions; i++) {
    temp_partition = (Iterator *)allocator->translate_udva2sa((uint64_t)(partitions_1 + i));
    temp_partition->begin = g_v_bin_1 + offset;
    offset = std::min((i + 1) * num_pairs_per_part, num_vertices);
    temp_partition->end = g_v_bin_1 + offset;
#ifdef DEBUG_GRAPH
    printf("Partition %d: pair_id=%d, key=%ld"
          "base_pair_addr=%p, part_entry_addr=%p\n",
           i, offset, temp_partition->begin->id, partitions_1 + i, partitions_1 + i);
#endif
  }

  double epsilon = 1.0 / num_vertices;
  printf("Epsilon = %lf\n", epsilon);
  fclose(in_file_gv);
  fclose(in_file_nl);
  printf("Finish building the graph, start running PageRank.\n");
  fflush(stdout);

  uint64_t iter = 0;
  
  while (iter < NUM_PR_ITERATIONS) {
    printf("PageRank iteration %ld\n", iter);
    fflush(stdout);
    /* operands
      X8: Pointer to partitions (64-bit DRAM address)
      X9: Number of lanes
      X10: Number of partitions per lane
      X11: Pointer to inKVSet (64-bit DRAM address)
      X12: Input KVSet length
      X13: Pointer to outKVSet (64-bit DRAM address)
      X14: Output KVSet length
      X15: Top flag offset in the scratchpad (in Bytes)
    */
    UpDown::operands_t ops(8);
    ops.set_operand(0, (uint64_t) partitions_0);
    ops.set_operand(1, (uint64_t) PART_PARM);
    ops.set_operand(2, (uint64_t) num_lanes);
    ops.set_operand(3, (uint64_t) g_v_bin_0);
    ops.set_operand(4, (uint64_t) num_vertices);
    ops.set_operand(5, (uint64_t) g_v_bin_1);
    ops.set_operand(6, (double) epsilon);
    UpDown::networkid_t nwid(0, false, 0);

    UpDown::event_t evnt_ops(pagerank_pull_dd::InitUpDown__init /*Event Label*/, nwid, UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);

    // Init top flag to 0
    uint64_t val = 0;
    pagerank_rt->ud2t_memcpy(&val, sizeof(uint64_t), nwid, TOP_FLAG_OFFSET /*Offset*/);

    pagerank_rt->send_event(evnt_ops);

    pagerank_rt->start_exec(nwid);

    pagerank_rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

    iter++;

    uint64_t active_set_size = 0, active_count = 0, active_volume = 0;
    for (int i = 0; i < num_vertices; i++) {
      temp_vertex_0 = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin_0 + i));
      temp_vertex_1 = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin_1 + i));

      if (temp_vertex_1->deg == 0) continue;

      if (abs(temp_vertex_0->val - temp_vertex_1->val) >= epsilon) {
        active_volume = active_volume + temp_vertex_1->deg;
        active_count = active_count + 1;
#ifdef VALIDATE_RESULT
        if (temp_vertex_0->active_flag != 2) {
          printf("Failed to active vertex %d: old value = %lf (%p), new value = %lf (%p)\n", i, temp_vertex_0->val, g_v_bin_0 + i, temp_vertex_1->val, g_v_bin_1 + i);
        }
#endif
      }
      if (temp_vertex_1->active_flag == 1) {
        active_set_size++;
      } 
    }
    printf("Iteration %ld: Number of vertices activated = %lu, active set size for next iteration= %lu\n", iter, active_count, active_set_size);    
    // Swap arrays
    Vertex *temp = g_v_bin_0;
    g_v_bin_0 = g_v_bin_1;
    g_v_bin_1 = temp;
    // Swap partitions
    Iterator *temp_part = partitions_0;
    partitions_0 = partitions_1;
    partitions_1 = temp_part;
#ifdef DEBUG
    printf("Switch partitions and vertex arrays: ");
    printf("g_v_bin_0 = %p\tg_v_bin_1 = %p\t", g_v_bin_0, g_v_bin_1);
    printf("partitions_0 = %p\tpartitions_1 = %p\t", partitions_0, partitions_1);
    // printf("active_set_0 = %p\tactive_set_1 = %p\n", active_set_0, active_set_1);
    fflush(stdout);
  #endif
    
    printf("Finish PageRank iteration %ld\n", iter);
    fflush(stdout);
  }

#ifdef VALIDATE_OUTPUT
  const char *output_file;
  if (argc < 6) {
    output_file = "output/pagerank_output.txt";
  } else {
    output_file = argv[5];
  }
  std::ofstream output(output_file);
#ifdef DEBUG
  printf("-------------------\nUpDown program termiantes. Verify the result output kv set.\n");
#endif
  for (int i = 0; i < num_vertices; i++) {
    temp_vertex_1 = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin_1 + i));
    if (temp_vertex_1->deg == 0) {
      continue;
    }
#ifdef DEBUG
    printf("Output pagerank value array %d: key=%ld value=%f DRAM_addr=%p\n", i, temp_vertex_1->id, temp_vertex_1->val, g_v_bin_1 + i);
#endif
    output << i << " " << temp_vertex_1->val << std::endl;
  }
#endif

#ifdef STATS
#ifdef FASTSIM
  // Dump stats and histograms
  pagerank_rt->db_write_stats(0, num_lanes, "pagerank");
#if defined(DETAIL_STATS)
  pagerank_rt->db_write_event_stats(0, num_lanes, "pagerank");
#endif

  for (int i = 0; i < machine.NumNodes; i++) {
    pagerank_rt->print_node_stats(i);
  }

  for (int i = 0; i < num_nodes * num_uds_per_node; i = i + 1) {
    for (int j = 0; j < 64; j = j + 1) {
      pagerank_rt->print_stats(i, j);

#ifdef DETAIL_STATS
      pagerank_rt->print_histograms(i, j);
#endif
    }
  }

#endif
#endif

  delete pagerank_rt;
  printf("UDKVMSR PageRank program finishes.\n");

  return 0;
}