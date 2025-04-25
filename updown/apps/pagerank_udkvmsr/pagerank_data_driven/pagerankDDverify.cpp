
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

// #define VALIDATE_RESULT
// #define DEBUG
// #define STATS
// #define DEBUG_GRAPH

#ifdef VALIDATE_RESULT
#include <fstream>
#include <iostream>
#endif

#define USAGE                                                                                                                                                  \
  "USAGE: ./pagerankDDverify <graph_file_path> <epsilon>\n\
  graph_file_path: \tpath to the graph file.\n"

#define NUM_PR_ITERATIONS 4

#define ALPHA 0.85
// #define EPSILON (0.001)

struct Vertex {
  uint64_t id;
  uint64_t deg;
  uint64_t *neigh;
  double val;
  uint64_t active_flag;
  uint64_t padding[3]; // Padding to 64 bytes
};

int main(int argc, char *argv[]) {

  if (argc < 2) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }

  std::string filename(argv[1]);
//   double epsilon = std::atof(argv[2]);

  char *graph_file = strdup(filename.c_str());
  char *path = strtok(graph_file, "/");
  while (path != NULL) {
    graph_file = path;
    path = strtok(NULL, "/");
  }
  graph_file = strtok(graph_file, ".");

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
  Vertex *g_v_bin_0 = reinterpret_cast<Vertex *>(malloc(num_vertices * sizeof(Vertex)));
  Vertex *g_v_bin_1 = reinterpret_cast<Vertex *>(malloc(num_vertices * sizeof(Vertex)));

  uint64_t *nlist_bin = reinterpret_cast<uint64_t *>(malloc((num_edges + num_vertices * 8) * sizeof(uint64_t)));

  // calculate size of neighbour list and assign values to each member value
  printf("Build the graph now\n");
  fflush(stdout);

  uint64_t curr_base = 0;
  Vertex *temp_vertex_0, *temp_vertex_1;
  uint64_t *temp_neigh;
  double val = (1.0 - ALPHA) / num_vertices;
  for (int i = 0; i < num_vertices; i++) {
    temp_vertex_0 = g_v_bin_0 + i;
    n = fread(temp_vertex_0, sizeof(Vertex) / 2, 1, in_file_gv);
    temp_vertex_0->neigh = nlist_bin + curr_base;
    temp_vertex_0->val = val;
    temp_vertex_0->active_flag = 1;

    temp_neigh = temp_vertex_0->neigh;
    n = fread(temp_neigh, sizeof(uint64_t), temp_vertex_0->deg, in_file_nl);

    temp_vertex_1 = g_v_bin_1 + i;
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

  double epsilon = 1.0 / num_vertices;
  printf("Epsilon = %.10lf\n", epsilon);
  fclose(in_file_gv);
  fclose(in_file_nl);
  printf("Finish building the graph, start running PageRank.\n");
  fflush(stdout);

  uint64_t iter = 0;

  while (iter < NUM_PR_ITERATIONS) {
    printf("PageRank iteration %ld\n", iter);
    fflush(stdout);

    uint64_t active_set_size = 0, active_count = 0;
    // Initialize active set size and count
    for (int i = 0; i < num_vertices; i++) {
      if (g_v_bin_0[i].active_flag == 0 || g_v_bin_0[i].deg == 0) {
        g_v_bin_1[i].val = g_v_bin_0[i].val;
        g_v_bin_0[i].active_flag = 0;
        continue;
      }
      active_set_size ++;
      double new_value = 0.0;
      for (int j = 0; j < g_v_bin_0[i].deg; j++) {
        uint64_t neigh_id = g_v_bin_0[i].neigh[j];
        new_value += g_v_bin_0[neigh_id].val / g_v_bin_0[neigh_id].deg;
      }
      new_value = ((1.0 - ALPHA) / num_vertices) + (ALPHA * new_value);
      double diff = std::abs(new_value - g_v_bin_0[i].val);

      if (diff >= epsilon) {
        active_count += 1;
        for (int j = 0; j < g_v_bin_0[i].deg; j++) {
          uint64_t neigh_id = g_v_bin_0[i].neigh[j];
          g_v_bin_1[neigh_id].active_flag = 1;
        }
      } 
    //   else {
    //     printf("Vertex %d: old value = %lf, new value = %lf, diff = %lf\n", i, g_v_bin_0[i].val, new_value, diff);
    //   }
      g_v_bin_1[i].val = new_value;
      g_v_bin_0[i].active_flag = 0;
    }
    printf("Iteration %ld: Number of vertices above epsilon = %lu, active set size before iteration = %lu\n", iter, active_count, active_set_size);

    active_set_size = 0, active_count = 0;
    for (int i = 0; i < num_vertices; i++) {
      temp_vertex_0 = g_v_bin_0 + i;
      temp_vertex_1 = g_v_bin_1 + i;

      temp_vertex_0->active_flag = 0; // Reset active flag for next iteration
      if (temp_vertex_1->deg == 0)
        continue;

      if (temp_vertex_1->active_flag == 1) {
        active_count++;
        active_set_size += temp_vertex_1->deg;
      }

    }
    printf("Iteration %ld: Number of active vertices after iteration = %lu, active set volumn for next iteration = %lu\n", iter, active_count, active_set_size);

    // Swap arrays
    Vertex *temp = g_v_bin_0;
    g_v_bin_0 = g_v_bin_1;
    g_v_bin_1 = temp;
    printf("Finish PageRank iteration %ld\n", iter);
    fflush(stdout);
    iter++;
  }

  printf("PageRank program finishes.\n");

  return 0;
}