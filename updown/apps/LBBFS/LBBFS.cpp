#include "LMStaticMap.udwh"
#include "basimupdown.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <stdio.h>
#include <string>
#include <string_view>
#include <vector>

#include "LBBFS.hpp"

#define USAGE "USAGE: ./LBBFS <graph_file> lanes src"

#define SQL_DUMP 0



#ifndef DRAM_ALLOC_BLOCKSIZE
#define DRAM_ALLOC_BLOCKSIZE (1UL << 20)
#endif

#ifndef DRAM_ALLOC_STARTNODE
#define DRAM_ALLOC_STARTNODE 0UL
#endif



int main(int argc, char *argv[]) {
//-------------Set up machine parameters
//------------Read file name and number of lanes from input

  if (argc < 2) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }


  std::string fname = argv[1];

  // Configure a machine with 64 lanes
  uint64_t num_lanes = 64;

  if (argc > 2) {
    num_lanes = atol(argv[2]);
  }
  uint64_t source = 1;
  if (argc > 3) {
    source = atol(argv[3]);
  }

  UpDown::ud_machine_t machine(argc, argv);
  machine.MapMemSize = 1UL << 37; // 256GB
  machine.GMapMemSize = 1UL << 37;
  machine.LocalMemAddrMode = 1;
  machine.NumLanes = num_lanes > 64 ? 64 : num_lanes;
  machine.NumUDs =
      std::ceil(num_lanes / 64.0) > 4 ? 4 : std::ceil(num_lanes / 64.0);
  machine.NumStacks = std::ceil(num_lanes / (64.0 * 4)) > 8
                          ? 8
                          : std::ceil(num_lanes / (64.0 * 4));
  machine.NumNodes = std::ceil(num_lanes / (64.0 * 4 * 8));

  // DRAM alloc config
  uint64_t blockSize = DRAM_ALLOC_BLOCKSIZE;
  uint64_t numNodes = machine.NumNodes;
  // uint64_t numNodes = 1;
  uint64_t startNode = DRAM_ALLOC_STARTNODE;


  // Create the runtime and load the UpDown binary
  UpDown::BASimUDRuntime_t *rt =
      new UpDown::BASimUDRuntime_t(machine, "LBBFSEFA.bin", 0, 100);


  dramalloc::DramAllocator *allocator = new dramalloc::DramAllocator(
      rt, LBBFSEFA::DRAMalloc__global_broadcast /*eventlabel*/);


  Graph graph(rt, fname, allocator, blockSize, numNodes, startNode);
  std::cout << "done loading the graph: " << fname << "\n";

  bool correct = BFS_on_UpDown(graph, source, rt, num_lanes);


  if (!correct) {
    std::cerr << "something is wrong\n";
    return 1;
  }

  std::string base_name = std::filesystem::path(fname).filename();
  std::string stats_fname = std::string("logs/lane_stats_") + base_name +
                            std::string("_") + std::to_string(num_lanes) +
                            std::string(".txt");

  freopen(stats_fname.c_str(), "w", stdout);

  for (uint64_t i = 0; i < num_lanes; i++) {
    rt->print_stats(i);
  }
  for (unsigned int node = 0; node < machine.NumNodes; ++node) {
    rt->print_node_stats(node);
  }
  std::fclose(stdout);

  return 0;
}
