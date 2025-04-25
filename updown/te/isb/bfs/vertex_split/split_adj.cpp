#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <sys/types.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>

#define USAGE "USAGE: ./split_adj -f <graph_file> -m <max_degree> -s(stats) -l (line offset) -n(no split)"

// #define DEBUG

struct Edge {
  uint64_t src;
  uint64_t dst;

  Edge() = default;
  Edge(uint64_t s, uint64_t d) : src(s), dst(d) {}

  bool operator<(const Edge &e) const { return src < e.src || (src == e.src && dst < e.dst); }
};

struct Vertex {
  uint64_t degree;
  uint64_t orig_vid;
  uint64_t vid;
  uint64_t *neighbors;
  uint64_t distance;
  uint64_t parent;
  uint64_t split_range;
  uint64_t offset;
};

class InputParser {
public:
  InputParser(int &argc, char **argv) {
    for (int i = 1; i < argc; ++i)
      this->tokens.push_back(std::string(argv[i]));
  }
  const std::string &getCmdOption(const std::string &option) const {
    std::vector<std::string>::const_iterator itr;
    itr = std::find(this->tokens.begin(), this->tokens.end(), option);
    if (itr != this->tokens.end() && ++itr != this->tokens.end()) {
      return *itr;
    }
    static const std::string empty_string("");
    return empty_string;
  }
  bool cmdOptionExists(const std::string &option) const { return std::find(this->tokens.begin(), this->tokens.end(), option) != this->tokens.end(); }

private:
  std::vector<std::string> tokens;
};

int main(int argc, char *argv[]) {

  if (argc < 2) {
    printf("Insufficient Input Params\n");
    printf("%s\n", USAGE);
    exit(1);
  }

  InputParser input(argc, argv);

  std::string graph_file_path = input.getCmdOption("-f");
  int max_degree = std::stoi(input.getCmdOption("-m"));
  bool directed = input.cmdOptionExists("-d");
  bool stats = input.cmdOptionExists("-s");
  bool no_split = input.cmdOptionExists("-n");
  bool split = !no_split;
  if (no_split) max_degree = 0;

  std::ifstream inputFile(graph_file_path);
  std::string line;

  printf("===========Input Parameters===========\n");
  printf("Graph file: %s\n", graph_file_path.c_str());
  printf("Max degree: %d\n", max_degree);
  printf("Directed: %s\n", directed ? "true" : "false");
  printf("Stats: %s\n", stats ? "true" : "false");
  printf("No split: %s\n", no_split ? "true" : "false");
  fflush(stdout);

  printf("\n===========Reading graph file %s===========\n", graph_file_path.c_str());

  // Skip the first n lines
  if (input.cmdOptionExists("-l")) {
    int line_offset = std::stoi(input.getCmdOption("-l"));
    std::string line;
    while (line_offset > 0) {
      std::getline(inputFile, line);
      line_offset--;
    }
  }

  uint64_t num_orig_vertices;
  std::getline(inputFile, line);
  num_orig_vertices = std::stoull(line);
  printf("Number of original vertices: %ld\n", num_orig_vertices);

  uint64_t num_edges;
  std::getline(inputFile, line);
  num_edges = std::stoull(line);
  printf("Number of edges: %ld\n", num_edges);

  // Read the number of vertices and edges
  if (num_orig_vertices == 0 || num_edges == 0) {
    printf("Error: Number of vertices or edges is zero\n");
    exit(1);
  }

  // Allocate memory for the vertices
  Vertex *orig_vertices = reinterpret_cast<Vertex *>(malloc(sizeof(Vertex) * num_orig_vertices));
  uint64_t *edge_bins = reinterpret_cast<uint64_t *>(malloc(sizeof(uint64_t) * num_edges));
  uint64_t vid = 0, new_vid = 0, offset = 0;
  Vertex *tmp_v, temp_vertex;
  uint64_t num_split = 0;
  uint64_t max_orig_degree = 0, avg_orig_degree = 0;
  std::unordered_map<uint64_t, uint64_t> split_bases;
  std::unordered_map<uint64_t, uint64_t> num_split_vids;
  std::unordered_map<uint64_t, uint64_t> reverse_map;
  std::unordered_map<uint64_t, uint64_t> updated_degree_map;

  uint64_t previous_offset = 0;

  // Read the graph file
  while (std::getline(inputFile, line)) {
    tmp_v = orig_vertices + vid;
    tmp_v->degree = std::stoull(line) - previous_offset;
    previous_offset = std::stoull(line);
    tmp_v->vid = vid;
    tmp_v->orig_vid = vid;
    tmp_v->neighbors = edge_bins + offset;
    tmp_v->distance = 0xffffffffffffffff;
    tmp_v->parent = 0;
    tmp_v->split_range = (vid << 32) | (vid + 1);

    if (split) {

      num_split = (tmp_v->degree / max_degree) + 1;
      if (num_split == 1) {
        split_bases[vid] = new_vid;
        num_split_vids[vid] = num_split;
        reverse_map[new_vid] = vid;
        updated_degree_map[new_vid] = tmp_v->degree;
        new_vid++;
      } else {
        split_bases[vid] = new_vid;
        num_split_vids[vid] = num_split;
        uint64_t deg_per_split = std::ceil(tmp_v->degree / num_split);
        for (uint64_t i = 0; i < num_split; i++) {
          if (i == num_split - 1) {
            updated_degree_map[new_vid + i] = tmp_v->degree - (deg_per_split * (num_split - 1));
          } else {
            updated_degree_map[new_vid + i] = deg_per_split;
          }
          reverse_map[new_vid + i] = vid;
        }
#ifdef DEBUG
        printf("Original vertex %ld - degree %ld - split into %ld vertices [%ld, %ld)\n", tmp_v->vid, tmp_v->degree, num_split, new_vid, new_vid + num_split);
#endif
        new_vid += num_split;
      }
    } else {
#ifdef DEBUG
        printf("Original vertex %ld - degree %ld nlist %p\n", tmp_v->vid, tmp_v->degree, tmp_v->neighbors);
#endif
    }

    vid++;
    offset += tmp_v->degree;
    if (vid >= num_orig_vertices) break;
    if (stats) {
      max_orig_degree = std::max(max_orig_degree, tmp_v->degree);
    }
  }
  if (stats) {
    avg_orig_degree = offset / num_orig_vertices;
  }

  printf("Read in %ld vertices at %p and %ld edges at %p\n", num_orig_vertices, orig_vertices, num_edges, edge_bins);

  printf("===========Finished reading graph file %s===========\n\n", graph_file_path.c_str());

  // Split the vertices
  printf("===========Splitting the vertices===========\n");

  uint64_t num_split_vertices = new_vid;
  uint64_t max_split_degree = 0;

  // Allocate memory for the split vertices
  Vertex *vertices;
#ifdef DEBUG
  uint64_t *orig_edge_bins = reinterpret_cast<uint64_t *>(malloc(sizeof(uint64_t) * num_edges));
#endif

  if (no_split) {
    vertices = orig_vertices;
    num_split_vertices = num_orig_vertices;
    max_split_degree = max_orig_degree;
    offset = 0;
    while (std::getline(inputFile, line)) {
        edge_bins[offset] = std::stoull(line);
#ifdef DEBUG
        orig_edge_bins[offset] = edge_bins[offset];
#endif
        offset++;
    }
  } else {
    vertices = reinterpret_cast<Vertex *>(malloc(sizeof(Vertex) * num_split_vertices));

    offset = 0;
    for (uint64_t i = 0; i < num_split_vertices; i++) {
      Vertex *v = vertices + i;
      v->vid = i;
      v->orig_vid = reverse_map[i];
      v->degree = updated_degree_map[i];
      v->neighbors = edge_bins + offset;
      v->distance = UINT64_MAX;
      v->parent = UINT64_MAX;
      v->split_range = (split_bases[reverse_map[i]] << 32) | (split_bases[reverse_map[i]] + num_split_vids[reverse_map[i]]);

#ifdef DEBUG
      printf("Split vertex %ld - degree %ld, nlsit_offset %ld (%p) - orig_vid %ld - split_range [%ld,%ld)\n", v->vid, v->degree, offset, edge_bins + offset,
             v->orig_vid, split_bases[reverse_map[i]], split_bases[reverse_map[i]] + num_split_vids[reverse_map[i]]);
#endif
      offset += updated_degree_map[i];

      if (stats)
        max_split_degree = std::max(max_split_degree, v->degree);
    }
  }
  printf("Total number of split vertices: %ld\n", num_split_vertices);
  printf("Construct vertices array %p and neighbor list %p\n", vertices, edge_bins);

  printf("===========Finished splitting and shuffling the vertices===========\n\n");

  printf("===========Remapping the edges===========\n");

  uint64_t dst, dst_split;
  uint64_t NUM_SPLIT_MASK = 0xffffffff;
  uint64_t num_dst_split;

  int i = 0;
  srand(time(0));
  if (split) {
    while (std::getline(inputFile, line)) {
      dst = std::stoull(line);
#ifdef DEBUG
      orig_edge_bins[i] = dst;
#endif
      num_dst_split = rand() % num_split_vids[dst];
      dst_split = split_bases[dst] + num_dst_split;
      edge_bins[i] = dst_split;
#ifdef DEBUG
      printf("Edge %d (%p): %ld -> %ld\n", i, edge_bins + i, dst, edge_bins[i]);
#endif
      i++;
    }
  }
  printf("===========Finished remapping the edges===========\n\n");

  if (stats) {
    // Print stats
    printf("===========Printing graph stats===========\n");
#ifdef DEBUG
    Vertex *v;
    for (int i = 0; i < num_split_vertices; i++) {
      v = vertices + i;
      printf("Vertex %ld - degree %ld\n\tNeighbors %p: [", v->vid, v->degree, v->neighbors);
      // for (uint64_t i = 0; i < v->degree; i++) {
      //   printf("%ld ", v->neighbors[i]);
      // }
      printf("]\n");
    }
#endif
    printf("Number of original vertices: %ld\n", num_orig_vertices);
    printf("Max degree in original graph: %ld\n", max_orig_degree);
    printf("Avg degree in original graph: %ld\n", avg_orig_degree);
    printf("Number of split vertices: %ld\n", num_split_vertices);
    printf("Max degree after split: %ld\n", max_split_degree);
    printf("Avg degree after split: %ld\n", num_edges / num_split_vertices);
    printf("Number of edges: %ld\n", num_edges);

    printf("===========Finished printing graph stats===========\n\n");
  }

  // Write the split graph to binary files
  printf("===========Writing the split graph to binary files===========\n");

  std::string output_prefix;
  if (no_split) {
    max_degree = 0;
    output_prefix = graph_file_path.substr(0, graph_file_path.find_last_of('.')) + "_no_split_shuffle";
  } else {
    output_prefix = graph_file_path.substr(0, graph_file_path.find_last_of('.')) + "_shuffle_max_deg_" + std::to_string(max_degree);
  }

  FILE *graph_file = std::fopen((output_prefix + ".bin").c_str(), "wb");
  if (!graph_file) {
    printf("Error when openning file %s, exiting.\n", (output_prefix + ".bin").c_str());
    exit(EXIT_FAILURE);
  }

  printf("Writing to %s\n", output_prefix.c_str());
  int n;

  fseek(graph_file, 0, SEEK_SET);
  n = fwrite(&num_orig_vertices, sizeof(uint64_t), 1, graph_file);
  printf("Writing number of original vertices = %ld\n", num_orig_vertices);
  n = fwrite(&num_split_vertices, sizeof(uint64_t), 1, graph_file);
  printf("Writing number of split vertices = %ld\n", num_split_vertices);

  n = fwrite(&num_edges, sizeof(uint64_t), 1, graph_file);
  printf("Writing number of edges = %ld\n", num_edges);

  n = fwrite(&(vertices[0]), sizeof(Vertex), num_split_vertices, graph_file);
  n = fwrite(edge_bins, sizeof(uint64_t), num_edges, graph_file);

  fclose(graph_file);

  printf("Done writing to %s\n\n", output_prefix.c_str());
  printf("===========Finished writing the split graph to binary files===========\n\n");
  fflush(stdout);

#ifdef DEBUG
  // Read the split graph
  printf("===========Reading the split graph from binary files===========\n");

  FILE *outputFile = std::fopen((output_prefix + ".bin").c_str(), "rb");
  printf("Reading from %s\n", (output_prefix + ".bin").c_str());
  if (!outputFile) {
    printf("Error when openning file %s, exiting.\n", (output_prefix + "_gv.bin").c_str());
    exit(EXIT_FAILURE);
  }

  uint64_t num_vertices;
  fseek(outputFile, 0, SEEK_SET);
  n = fread(&num_vertices, sizeof(uint64_t), 1, outputFile);
  printf("Number of original vertices: %ld\n", num_vertices);

  n = fread(&num_vertices, sizeof(uint64_t), 1, outputFile);
  printf("Number of split vertices: %ld\n", num_vertices);

  // fseek(edgeFile, 0, SEEK_SET);
  n = fread(&num_edges, sizeof(uint64_t), 1, outputFile);
  printf("Number of edges: %ld\n", num_edges);
  fflush(stdout);

  Vertex *v;
  uint64_t neighbor, num_vertices_read = 0;
  uint64_t num_edges_read = 0;

  Vertex *vertices_read = reinterpret_cast<Vertex *>(malloc(sizeof(Vertex) * num_vertices));

  while (num_vertices_read < num_vertices) {
    v = vertices_read + num_vertices_read;
    n = fread(v, sizeof(Vertex), 1, outputFile);
    num_vertices_read++;
  }
  // fread(vertices_read, sizeof(Vertex), num_vertices, vertexFile);
  printf("Read in %ld vertices\n", num_vertices_read);

  offset = 0;
  for (int i = 0; i < num_vertices; i++) {
    printf("Vertex %ld - degree %ld\n\tNeighbors: [", vertices_read[i].vid, vertices_read[i].degree);
    num_edges_read += vertices_read[i].degree;
    for (uint64_t j = 0; j < vertices_read[i].degree; j++) {
      n = fread(&neighbor, sizeof(uint64_t), 1, outputFile);
      // printf("%ld ", neighbor);
      if (reverse_map[neighbor] != orig_edge_bins[offset + j] && split) {
        printf("\nError: Edge %ld (%ld, %ld) not found in the original graph\n", offset + j, reverse_map[vertices_read[i].vid], reverse_map[neighbor]);
        printf("Expected %ld, found %ld\n", orig_edge_bins[offset + j], reverse_map[neighbor]);
        exit(1);
      }
    }
    offset += vertices_read[i].degree;
    printf("]\n");
  }

  if (num_edges != num_edges_read) {
    printf("Error: Number of edges read %ld, expected %ld\n", num_edges_read, num_edges);
    printf("Error: Number of edges mismatch\n");
    exit(1);
  }

  fclose(outputFile);

  printf("===========Successfully read the split graph from binary files===========\n\n");

#endif

  return 0;
}