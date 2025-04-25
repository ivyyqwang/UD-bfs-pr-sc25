#include "dramalloc.hpp"
#include "bfs_udweave_exe.hpp"
#include <basim_stats.hh>
#include <basimupdown.h>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sys/types.h>
#include <queue>
#include <vector>
#include <cmath>

using namespace std;

// #define DEBUG
#define VALIDATE_RESULT

#ifdef GEM5_MODE
#include <gem5/m5ops.h>
#endif

#ifdef VALIDATE_RESULT
#include <fstream>
#include <iostream>
#endif

#define USAGE "USAGE: ./bfs_udweave <graph_file> <num_lanes> <num_control_lanes_per_level> <root_vid> "

#define TOP_FLAG_OFFSET 0

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

int cpu_bfs(UpDown::UDRuntime_t *rt, dramalloc::DramAllocator *allocator, Vertex *g_v, uint64_t root_id, uint64_t n_vertices){
  queue<uint64_t> q;
  vector<uint64_t> cpu_distance(n_vertices, -1);
  Vertex *vertex = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v + root_id));
  uint64_t distance = vertex->distance;
  root_id = vertex->orig_vid;
  if(distance != 0){
    return 1;
  }
  cpu_distance[root_id] = 0;
  q.push(root_id);

  uint64_t access_v = 1;

  uint64_t distance_level = 0;

  while (!q.empty()) {
    uint64_t vid = q.front();
    access_v++;
    // printf("vid = %lu, %lu\n", vid, n_vertices);
    // fflush(stdout);
    q.pop();
    vertex = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v + vid));
    distance = vertex->distance;
    if(distance_level  < distance){
      // printf("distance = %lu\n", distance);
      // fflush(stdout);
      distance_level = distance;
    }
    // printf("distance = %lu\n", distance);
    // fflush(stdout);
    if(distance != cpu_distance[vid]){
      printf("vid = %lu, updown distance = %lu, updown parent = %lu, cpu distenace = %lu\n", vid, distance, vertex->parent, cpu_distance[vid]);
      return 1;
    }
    if(vertex->split_range == 0){
      uint64_t *neighbors = vertex->neighbors;
      for (int j = 0; j < vertex->degree; j++) {
        uint64_t *temp_neigh = (uint64_t *)allocator->translate_udva2sa((uint64_t)(neighbors + j));
        uint64_t new_vid = temp_neigh[0];
        Vertex * new_vertex = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v + new_vid));
        new_vid = new_vertex->orig_vid;
        // printf("new_vid = %lu\n", new_vid);
        // fflush(stdout);
        if(cpu_distance[new_vid] == -1){
          cpu_distance[new_vid] = distance + 1;
          q.push(new_vid);
          // if(new_vid == 862245){
          //   printf("push new_vid = %lu, parent = %lu\n", new_vid, vid);
          //   fflush(stdout);
          // }
          // printf("push new_vid = %lu\n", new_vid);
          // fflush(stdout);
        }
        // else{
        //   printf("not push new_vid = %lu\n", new_vid);
        //   fflush(stdout);
        // }
      }
    }
    else{
      uint64_t split_vid = vertex->split_range >> 32;
      uint64_t split_bound = vertex->split_range & 0xffffffff;
      // printf("[%lu,%lu]\n", split_vid, split_bound);
      fflush(stdout);
      for(unsigned vid = split_vid; vid < split_bound; vid++){
        vertex = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v + vid));
        uint64_t *neighbors = vertex->neighbors;
        // printf("vertex->degree = %lu\n", vertex->degree);
        // fflush(stdout);
        for (int j = 0; j < vertex->degree; j++) {
          uint64_t *temp_neigh = (uint64_t *)allocator->translate_udva2sa((uint64_t)(neighbors + j));
          uint64_t new_vid = temp_neigh[0];
          Vertex * new_vertex = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v + new_vid));
          new_vid = new_vertex->orig_vid;
          // printf("new_vid = %lu\n", new_vid);
          // fflush(stdout);
          if(cpu_distance[new_vid] == -1){
            cpu_distance[new_vid] = distance + 1;
            q.push(new_vid);

            // if(new_vid == 862245){
            // printf("push 2 new_vid = %lu, parent = %lu\n", new_vid, vid);
            // fflush(stdout);
            // }
            // printf("push new_vid = %lu\n", new_vid);
            // fflush(stdout);
            }
          // else{
          //   printf("not push new_vid = %lu\n", new_vid);
          //   fflush(stdout);
          // }
        }
      }
    }
  }
  printf("Access num of v = %lu\n", access_v);
  return 0;
}



uint64_t bfs_main_updown_iter(UpDown::UDRuntime_t *rt, Vertex* gv, uint64_t* queue, uint64_t queue_length, uint64_t num_lanes, uint64_t num_control_lanes_per_level) {

  UpDown::word_t ops_data[8];
  UpDown::operands_t ops(8, ops_data);

  uint64_t log2_num_control_lanes_per_level = std::log2(num_control_lanes_per_level);

  ops.set_operand(0, (uint64_t)num_lanes);
  ops.set_operand(1, (uint64_t)gv);
  ops.set_operand(2, (uint64_t)queue);
  ops.set_operand(3, (uint64_t)queue_length);
  ops.set_operand(4, (uint64_t)0);
  ops.set_operand(5, (uint64_t)num_lanes);
  ops.set_operand(6, (uint64_t)log2_num_control_lanes_per_level);
  ops.set_operand(7, (uint64_t)0);


  UpDown::networkid_t nwid(0, false, 0);
  UpDown::event_t event_ops(bfs_udweave_exe::main_master__init /*Event Label*/, nwid, UpDown::CREATE_THREAD /*Thread ID*/, &ops /*Operands*/);
  rt->send_event(event_ops);
  uint64_t val = 0;
  rt->t2ud_memcpy(&val, sizeof(uint64_t), nwid, TOP_FLAG_OFFSET);

#ifdef GEM5_MODE
  m5_reset_stats(0, 0);
#else
  ((UpDown::BASimUDRuntime_t *)rt)->reset_all_stats();
  ((UpDown::BASimUDRuntime_t *)rt)->reset_sim_ticks();
#endif

  rt->start_exec(nwid);

  rt->test_wait_addr(nwid, TOP_FLAG_OFFSET, 1);

#ifdef GEM5_MODE
  m5_dump_reset_stats(0, 0);
#endif

  // rt->ud2t_memcpy(&val, sizeof(uint64_t), nwid, TOP_VAL_OFFSET /*Offset*/);

  return val;
}

int main(int argc, char *argv[]) {

  char *graph_file_path;
  char *output_file;
  if (argc < 5) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }
  graph_file_path = argv[1];
  uint64_t num_lanes = atoi(argv[2]);
  uint64_t num_control_lanes_per_level = atoi(argv[3]);
  uint64_t root_vertex_id = atoi(argv[4]);
  uint64_t network_latency = 1100;
  uint64_t network_bandwidth = 0;
  
  if (argc >= 6) {
    network_latency = atoi(argv[5]);
  }

  if (argc >= 7) {
    network_bandwidth = atoi(argv[6]);
  }

  printf("network_latency = %lu, network_bandwidth = %lu\n", network_latency, network_bandwidth);
  fflush(stdout);

  // Set up machine parameters
  UpDown::ud_machine_t machine;
  if(num_lanes <= 2048){
     machine.MapMemSize = 1UL << 39; // 512GB
     machine.GMapMemSize = 1UL << 32; // 4GB
  }else{
    machine.MapMemSize = 1UL << 38; // 256GB
    machine.GMapMemSize = 1UL << 37; // 128GB
  }
  machine.LocalMemAddrMode = 1;
  machine.NumLanes = num_lanes > 64 ? 64 : num_lanes;
  machine.NumUDs = std::ceil(num_lanes / 64.0) > 4 ? 4 : std::ceil(num_lanes / 64.0);
  machine.NumStacks = std::ceil(num_lanes / (64.0 * 4)) > 8 ? 8 : std::ceil(num_lanes / (64.0 * 4));
  machine.NumNodes = std::ceil(num_lanes / (64.0 * 4 * 8));
  machine.InterNodeLatency = network_latency;
  machine.InterNodeBandwidth = network_bandwidth;

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
  bfs_rt = new UpDown::BASimUDRuntime_t(machine, "bfs_udweave_exe.bin", 0, 100, std::string(graph_file) + "_" + std::to_string(num_lanes) + "nds");
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

  // printf("Number of UpDown nodes:%ld\n", num_nodes);

  printf("Initialize DRAMalloc\n");
  uint64_t blockSize = 4 * 1024;
#ifdef GEM5_MODE
  dramalloc::DramAllocator *allocator = new dramalloc::DramAllocator(bfs_rt, bfs_udweave_exe::DRAMalloc__global_broadcast /*eventlabel*/, blockSize);
#else
  dramalloc::DramAllocator *allocator = new dramalloc::DramAllocator(bfs_rt, bfs_udweave_exe::DRAMalloc__global_broadcast /*eventlabel*/);
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

  vector<uint64_t> map_org2id(num_vertices, -1);

  printf("Graph of Size :\n\tnum_vertices=%ld\n\tnum_split_vertices=%ld\n\tnum_edges=%ld\n", num_vertices, num_split_vertices, num_edges);

  printf("Allocating memmory for Vertices...\n");
  Vertex *g_v_bin = reinterpret_cast<Vertex *>(allocator->mm_malloc_global(2 * num_split_vertices * sizeof(Vertex), blockSize, machine.NumNodes, 0));

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
  uint64_t root_id_tmp = -1;
  uint64_t root_id_tmp_orig = -1;
  uint64_t root_id_orig = -1;
  bool new_version = true;
  uint64_t total_vertices = num_split_vertices;
  for (int i = 0; i < num_split_vertices; i++) {
    temp_vertex = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin + i));
    n = fread(temp_vertex, sizeof(Vertex), 1, in_file);
    temp_vertex->vid = i;
    temp_vertex->distance = -1;
    uint64_t orig_vid = temp_vertex->orig_vid;
    uint64_t split_vid = temp_vertex->split_range >> 32;
    uint64_t split_bound = temp_vertex->split_range & 0xffffffff;
    if((root_id_tmp == -1) && (temp_vertex->degree != 0)){
      root_id_tmp = temp_vertex->vid;
      root_id_tmp_orig = orig_vid;
    }
    if(i == root_vertex_id){
      root_id_orig = orig_vid;
    }
    // printf("vid = %lu, split_vid = %lu, split_bound = %lu\n",i,split_vid, split_bound);
    // fflush(stdout);
    // printf("Vertex vid=%ld addr=%lu(0x%p) - deg %ld, dist %ld, "
    //       "ori_vid %ld, split_range [%ld, %ld], neigh_list %p\n",
    //       temp_vertex->vid, (unsigned long)(g_v_bin + i), (void *)(g_v_bin + i), temp_vertex->degree, temp_vertex->distance, temp_vertex->orig_vid,
    //       temp_vertex->split_range >> 32, temp_vertex->split_range & 0xffffffff, temp_vertex->neighbors);
    // fflush(stdout);
    if(new_version){
      if(temp_vertex->split_range == 0){
        new_version = false;
      }else if((split_vid == i) && (split_bound == i+1)){
        map_org2id[orig_vid] = i;
        temp_vertex->split_range = 0;
      }else{
        if(map_org2id[orig_vid] == -1){
          map_org2id[orig_vid] = total_vertices;
          Vertex * temp_vertex_org = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin + total_vertices));
          temp_vertex_org->vid = total_vertices;
          temp_vertex_org->orig_vid = total_vertices;
          temp_vertex_org->distance = -1;
          temp_vertex_org->degree = 0;
          temp_vertex_org->split_range = temp_vertex->split_range;
          total_vertices++;
        }

          // printf("vid = %lu, orig_vid = %lu, new_orig_vid = %lu\n",i,orig_vid, map_org2id[orig_vid]);
          // fflush(stdout);
          // printf("Vertex vid=%ld addr=%lu(0x%p) - deg %ld, dist %ld, "
          //   "ori_vid %ld, split_range [%ld, %ld], neigh_list %p\n",
          //   temp_vertex->vid, (unsigned long)(g_v_bin + i), (void *)(g_v_bin + i), temp_vertex->degree, temp_vertex->distance, temp_vertex->orig_vid,
          //   temp_vertex->split_range >> 32, temp_vertex->split_range & 0xffffffff, temp_vertex->neighbors);

          // fflush(stdout);
      }
    }
  }

  printf("total_vertices = %lu\n", total_vertices);

  for (int i = 0; i < num_split_vertices; i++) {
    temp_vertex = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin + i));
    
    if(new_version)
    {
      uint64_t orig_vid = temp_vertex->orig_vid;
      temp_vertex->orig_vid = map_org2id[orig_vid];
    }

    neighbors = nlist_bin + curr_base;
    
    for (int j = 0; j <  std::ceil(temp_vertex->degree / 8.0) * 8; j++) {
      temp_neigh = (uint64_t *)allocator->translate_udva2sa((uint64_t)(neighbors + j));
      if(j < temp_vertex->degree){
        n = fread(temp_neigh, sizeof(uint64_t), 1, in_file);
        // uint64_t new_vid = temp_neigh[0];
        // Vertex * new_vertex = (Vertex *) allocator->translate_udva2sa((uint64_t) (g_v_bin + new_vid));
        // new_vid = new_vertex->orig_vid;
        // temp_neigh[0] = new_vid;
      }
      else{
        temp_neigh[0] = -1;
      }
    }
    temp_vertex->neighbors = neighbors;

#ifdef DEBUG
    printf("Vertex vid=%ld addr=%lu(0x%p) - deg %ld, dist %ld, "
           "ori_vid %ld, split_range [%ld, %ld], neigh_list %p\nNeighbors: [",
           temp_vertex->vid, (unsigned long)(g_v_bin + i), (void *)(g_v_bin + i), temp_vertex->degree, temp_vertex->distance, temp_vertex->orig_vid,
           temp_vertex->split_range >> 32, temp_vertex->split_range & 0xffffffff, temp_vertex->neighbors);

    for (int j = 0; j < temp_vertex->degree; j++) {
      // printf("(%ld, %ld) \t", temp_vertex->orig_vid, nlist_bin[curr_base + j]);
      uint64_t *temp_neigh = (uint64_t *)allocator->translate_udva2sa((uint64_t)(temp_vertex->neighbors + j));
      printf("%ld, ", *temp_neigh);
    }
    printf("]\n");
#endif

    curr_base += std::ceil(temp_vertex->degree / 8.0) * 8;
  }
  printf("Finished reading the graph, number of edges read = %ld.\n", curr_base);

  printf("Vertices build done.\n");

  printf("Graph Built. Will do BFS now\n");
  printf("Graph: NumEdges:%ld\n", num_edges);
  printf("Graph: NumVertices:%ld\n", num_split_vertices);

  temp_vertex = (Vertex *)allocator->translate_udva2sa((uint64_t)(g_v_bin + root_vertex_id));
  if (temp_vertex->split_range == 0 && temp_vertex->degree == 0) {
    printf("Root vertex %ld is not in the graph, degree = 0.\n", root_vertex_id);
    printf("Will use root vertex %ld.\n", root_id_tmp);
    root_vertex_id = root_id_tmp;
    root_id_orig = root_id_tmp_orig;
  }

  printf("Root vertex %lu, original vertex id %lu\n", root_vertex_id, root_id_orig);

  uint64_t avg_deg = num_edges / num_split_vertices * 1.8;
  uint64_t queue_length = (num_split_vertices * avg_deg / num_lanes);
  if(queue_length < 1024)
    queue_length = 1024;
  uint64_t queue_size = (queue_length * 2 + 2) * num_lanes * sizeof(uint64_t);
  uint64_t *frontier = reinterpret_cast<uint64_t *>(bfs_rt->mm_malloc(queue_size));
  printf("frontier addr = 0x%lx, len = %lu\n", frontier, queue_length);
  frontier[0] = 2;
  frontier[1] = 0;
  frontier[2] = root_vertex_id;
  frontier[3] = root_vertex_id;
  for(uint64_t i=1; i<num_lanes; i++){
    uint64_t len = queue_length * 2 + 2;
    frontier[i*len] = 0;
    frontier[i*len+1] = 0;
  }

fflush(stdout);
#ifdef GEM5_MODE
m5_switch_cpu();
#else
bfs_rt->reset_all_stats();
#endif

uint64_t num_iters = bfs_main_updown_iter(bfs_rt, g_v_bin, frontier, queue_length, num_lanes, num_control_lanes_per_level);

// #ifdef DEBUG
//   for (int i = 0; i < num_split_vertices; i++) {
//     temp_vertex = g_v_bin + i;
//     if (i == num_vertices) {
//       printf("--------------------\nSplit vertices:\n--------------------\n");
//     }
//     if (temp_vertex->distance == 0 && temp_vertex->degree == 0) continue;
//     printf("Vertex %ld (addr %p) - deg %ld, dist %ld, parent %ld, "
//             "ori_vid %ld, split_range [%ld, %ld], neigh_list %p\n",
//             temp_vertex->vid, (g_v_bin + i), temp_vertex->degree, temp_vertex->distance, temp_vertex->parent, temp_vertex->orig_vid,
//             temp_vertex->split_range >> 32, temp_vertex->split_range & 0xffffffff, temp_vertex->neighbors);
//   }
// #endif


#if not defined GEM5_MODE
  for(int j=0; j<num_lanes; j++)
  {
    printf("UD = %d, Lane = %d\n",(j / 64) , j%64);
    bfs_rt->print_stats((j / 64) , j%64);
    #ifdef DETAIL_STATS
      bfs_rt->print_histograms(j / 64 , j%64);
    #endif
  }
  for(unsigned int node=0; node<machine.NumNodes; ++node) {
    bfs_rt->print_node_stats(node);
  }
#endif

if(new_version){
  num_vertices = total_vertices;
}


#ifdef VALIDATE_RESULT
  if(cpu_bfs(bfs_rt, allocator, g_v_bin, root_vertex_id, num_vertices) == 0)
    printf("Validate Pass\n");
  else
    printf("Validate Fail\n");
#endif

  delete bfs_rt;
}
