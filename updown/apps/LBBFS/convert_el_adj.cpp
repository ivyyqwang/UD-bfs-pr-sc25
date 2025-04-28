
#include <fstream>
#include <vector>
#include <iostream>


std::vector<std::vector<uint32_t>>
readGraphintoSym(const std::string &filename) {
  std::ifstream infile(filename);

  if (!infile.is_open()) {
    std::cerr << "Error opening file: " << filename << std::endl;
    return {};
  }

  std::vector<std::vector<uint32_t>> adjacencyList;

  uint64_t src, dest;

  // int limit = 0;
  while (infile >> src >> dest) {
    // if (src == dest) {
    //   continue;
    // }
    if (std::max(src, dest) >= adjacencyList.size()) {
      adjacencyList.resize(std::max(src, dest) + 1);
    }
    adjacencyList[src].push_back(dest);
    adjacencyList[dest].push_back(src);
    //
    // if (limit > 10000000) {
    //   break;
    // }
    // limit += 1;
  }

  infile.close();

  std::cout << "done reading in the graph\n";

  for (auto &edges : adjacencyList) {
    {
      std::sort(edges.begin(), edges.end());
      auto last = std::unique(edges.begin(), edges.end());
      edges.erase(last, edges.end());
    }
  }
  return adjacencyList;
}


bool write_sym_graph(const std::vector<std::vector<uint32_t>> &graph,
                     const std::string &filename, bool pack = false) {
  size_t M = 0;
  std::vector<size_t> prefix_sum;
  size_t num_nodes = 0;
  std::vector<uint32_t> relabel(graph.size());
  bool source_vertec_found = false;
  for (size_t i = 0; i < graph.size(); i++) {
    if (pack && graph[i].size() == 0) {
      continue;
    }
    if (graph[i].size() >= 2 && source_vertec_found == false) {
      std::cout << "source vertex should be " << num_nodes << "\n";
      source_vertec_found = true;
    }
    relabel[i] = num_nodes;
    num_nodes += 1;
    prefix_sum.push_back(M);
    M += graph[i].size();
  }
  std::cout << "starting to write the graph\n";

  std::ofstream myfile;
  myfile.open(filename);
  myfile << "AdjacencyGraph\n";

  myfile << num_nodes << "\n";

  myfile << M << "\n";
  for (uint64_t i = 0; i < prefix_sum.size(); i++) {
    myfile << prefix_sum[i] << "\n";
  }
  for (uint64_t i = 0; i < graph.size(); i++) {
    for (const auto &dest : graph[i]) {
      myfile << relabel[dest] << "\n";
    }
  }
  myfile.close();
  return true;
}

int main([[maybe_unused]] int32_t argc, char *argv[]) {

  auto graph = readGraphintoSym(argv[1]);
  write_sym_graph(graph, argv[2], true);
}