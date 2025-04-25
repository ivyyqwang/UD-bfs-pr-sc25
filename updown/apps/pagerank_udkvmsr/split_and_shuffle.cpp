#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <set>
#include <string>
#include <sys/types.h>
#include <unordered_map>
#include <sstream>
#include <cstdio>
#include <cstdlib>
#include <utility>
#include <vector>
#include <algorithm>

#define USAGE "USAGE: ./split_and_shuffle -f <graph_file> -m <max_degree> -d(directed) -s(stats) -l (line offset)"

// #define DEBUG

struct Edge {
    uint64_t src;
    uint64_t dst;

    Edge() = default;
    Edge(uint64_t s, uint64_t d) : src(s), dst(d) {}

    bool operator<(const Edge &e) const {
        return src < e.src || (src == e.src && dst < e.dst);
    }
};

struct Vertex{
  uint64_t id;
  uint64_t deg;
  uint64_t *neighbors;
  uint64_t offset;
};

class InputParser{
    public:
        InputParser (int &argc, char **argv){
            for (int i=1; i < argc; ++i)
                this->tokens.push_back(std::string(argv[i]));
        }
        /// @author iain
        const std::string& getCmdOption(const std::string &option) const{
            std::vector<std::string>::const_iterator itr;
            itr =  std::find(this->tokens.begin(), this->tokens.end(), option);
            if (itr != this->tokens.end() && ++itr != this->tokens.end()){
                return *itr;
            }
            static const std::string empty_string("");
            return empty_string;
        }
        /// @author iain
        bool cmdOptionExists(const std::string &option) const{
            return std::find(this->tokens.begin(), this->tokens.end(), option)
                   != this->tokens.end();
        }
    private:
        std::vector <std::string> tokens;
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
    
    std::ifstream inputFile(graph_file_path);
    std::string line;
    std::unordered_map<uint64_t, uint64_t> orig_vertices;
    std::set<Edge> edges;

    printf("===========Input Parameters===========\n");
    printf("Graph file: %s\n", graph_file_path.c_str());
    printf("Max degree: %d\n", max_degree);
    printf("Directed: %s\n", directed ? "true" : "false");

    printf("\n===========Reading graph file %s===========\n", graph_file_path.c_str());

    // Skip the first n lines
    if (input.cmdOptionExists("-l")) {
        int line_offset = std::stoi(input.getCmdOption("-l"));
        std::string line;
        for (int i = 0; i < line_offset; i++) {
            std::getline(inputFile, line);
        }
    }

    // Read the graph file
    while (std::getline(inputFile, line)) {
        std::istringstream iss(line);
        uint64_t src, dst;
        iss >> src >> dst;

        // add source and destination to the map
        if (orig_vertices[src]) orig_vertices[src] += 1;
        else orig_vertices[src] = 1;

        if (!directed && orig_vertices[dst]) orig_vertices[dst] += 1;
        else if (!directed && !orig_vertices[dst]) orig_vertices[dst] = 1;
        else if (directed && !orig_vertices[dst]) orig_vertices[dst] = 0;

        edges.insert(Edge(src, dst));
        if (!directed) edges.insert(Edge(dst, src));

#ifdef DEBUG
        printf("Edge: (%ld, %ld)\n", src, dst);
#endif
    }
    printf("Read in %ld vertices and %ld edges\n", orig_vertices.size(), edges.size());

    printf("===========Finished reading graph file %s===========\n\n", graph_file_path.c_str());

    // Split the vertices
    printf("===========Splitting and shuffling the vertices===========\n");

    std::unordered_map<uint64_t, uint64_t> updated_degree_map;
    std::unordered_map<uint64_t, uint64_t> split_ranges;
    uint64_t split_vid = 0;
    uint64_t max_orig_degree = 0;
#ifdef DEBUG
    std::unordered_map<uint64_t, uint64_t> reverse_map;
#endif

    for (const std::pair<uint64_t, uint64_t> &v : orig_vertices) {
        uint64_t num_split = (v.second / max_degree) + 1;
        split_ranges[v.first] = split_vid << 32 | num_split;
        for (uint64_t i = 0; i < num_split; i++) {
            updated_degree_map[split_vid + i] = 0;
#ifdef DEBUG
            reverse_map[split_vid + i] = v.first;
#endif
        }
#ifdef DEBUG
        printf("Vertex %ld degree %ld split into %ld vertices, starting %ld. \n", v.first, v.second, num_split, split_vid);
#endif
        split_vid += num_split;
        if (v.second > max_orig_degree) max_orig_degree = v.second;
    }
    uint64_t num_orig_vertices = orig_vertices.size();
    orig_vertices.clear();

    std::vector<uint64_t> vid_map(split_vid);
    for (uint64_t i = 0; i < split_vid; i++) {
        vid_map[i] = i;
    }
    std::random_shuffle(vid_map.begin(), vid_map.end());
#ifdef DEBUG
    std::unordered_map<uint64_t, uint64_t> shuffle_reverse_map;
    for (int i = 0; i < split_vid; i++) {
        shuffle_reverse_map[vid_map[i]] = reverse_map[i];
    }
#endif

    printf("Total number of split vertices: %ld\n", split_vid);
    printf("===========Finished splitting and shuffling the vertices===========\n\n");

    // Shuffle the edges
    printf("===========Remapping the edges===========\n");

    uint64_t src, dst, src_split, dst_split;
    uint64_t NUM_SPLIT_MASK = 0xffffffff;
    uint64_t num_edges = edges.size();

    Edge *new_edges = reinterpret_cast<Edge *>(malloc(sizeof(Edge) * num_edges));
    int i = 0;

    for (auto &e : edges) {
        src = e.src;
        dst = e.dst;
        src_split = vid_map[(split_ranges[src] >> 32) + (rand() % (split_ranges[src] & NUM_SPLIT_MASK))];
        dst_split = vid_map[(split_ranges[dst] >> 32) + (rand() % (split_ranges[dst] & NUM_SPLIT_MASK))];
#ifdef DEBUG
        printf("Edge: (%ld, %ld) -> (%ld, %ld)\n", src, dst, src_split, dst_split);
#endif
        new_edges[i].src = src_split;
        new_edges[i].dst = dst_split;
        i++;
        
        updated_degree_map[src_split] += 1;
    }

    vid_map.clear();
    printf("===========Finished remapping the edges===========\n\n");

    // Create the split graph
    printf("===========Creating the split graph===========\n");

    uint64_t num_split_vertices = split_vid;
    Vertex *vertices = reinterpret_cast<Vertex *>(malloc(sizeof(Vertex) * num_split_vertices));
    printf("Number of split vertices: %ld\n", num_split_vertices);
    
    uint64_t *edge_bins = reinterpret_cast<uint64_t *>(malloc(sizeof(uint64_t) * edges.size()));
    uint64_t offset = 0;

    for (uint64_t i = 0; i < split_vid; i++) {
        vertices[i].id = i;
        vertices[i].deg = updated_degree_map[i];
        vertices[i].neighbors = edge_bins + offset;
        vertices[i].offset = 0;
        offset += updated_degree_map[i];
    }

    Edge e;
    printf("\nCreate the neighbor list for each vertex\n");

    for (int i = 0; i < edges.size(); i++) {
        e = new_edges[i];
        vertices[e.src].neighbors[vertices[e.src].offset++] = e.dst;
#ifdef DEBUG
        printf("Edge (%ld, %ld) insert to vertex %ld neighbor list at offset %ld\n", e.src, e.dst, e.src, vertices[e.src].offset - 1);
#endif
    }

    printf("===========Finished creating the split graph===========\n\n");

    if (stats) {
        // Print stats
        printf("===========Printing graph stats===========\n");
        double avg_degree = 0;
        uint64_t max_degree = 0;
        Vertex v;

        for (int i = 0; i < num_split_vertices; i++) {
            v = vertices[i];
            avg_degree += v.deg;
            if (v.deg > max_degree) max_degree = v.deg;
#ifdef DEBUG
            printf("Vertex %ld - degree %ld\n\tNeighbors: [", v.id, v.deg);
            for (uint64_t i = 0; i < v.deg; i++) {
                printf("%ld ", v.neighbors[i]);
            }
            printf("]\n");
#endif
        }
        printf("Number of original vertices: %ld\n", num_orig_vertices);
        printf("Max original degree: %ld\n", max_orig_degree);
        printf("Number of split vertices: %ld\n", num_split_vertices);
        printf("Number of edges: %ld\n", num_edges);
        printf("Average degree: %f\n", avg_degree / num_split_vertices);
        printf("Max degree: %ld\n", max_degree);

        printf("===========Finished printing graph stats===========\n\n");
    }

    // Write the split graph to binary files
    printf("===========Writing the split graph to binary files===========\n");

    std::string output_prefix = graph_file_path.substr(0, graph_file_path.find_last_of('.')) + "_shuffle_max_deg_" + std::to_string(max_degree);

    FILE* gv_file = std::fopen((output_prefix + "_gv.bin").c_str(), "wb");
    FILE* nl_file = std::fopen((output_prefix + "_nl.bin").c_str(), "wb");
    if (!gv_file || !nl_file) {
        printf("Error when openning file %s or %s, exiting.\n", (output_prefix + "_gv.bin").c_str(), (output_prefix + "_nl.bin").c_str());
        exit(EXIT_FAILURE);
    }

    printf("Writing to %s\n", output_prefix.c_str());
    int n;

    fseek(gv_file, 0, SEEK_SET);
    n = fwrite(&num_split_vertices,sizeof(uint64_t),1,gv_file);
    printf("Writing number of vertices = %ld\n", num_split_vertices);

    n = fwrite(&(vertices[0]), sizeof(Vertex), num_split_vertices, gv_file);
    fclose(gv_file);
    
    fseek(nl_file, 0, SEEK_SET);
    printf("Writing number of edges = %ld\n", num_edges);
    n = fwrite(&num_edges, sizeof(uint64_t),  1,  nl_file);
    
    n = fwrite(edge_bins, sizeof(uint64_t), num_edges, nl_file);
    fclose(nl_file);

    printf("Done writing to %s\n\n", output_prefix.c_str());
    printf("===========Finished writing the split graph to binary files===========\n\n");

    if (stats) {    
        printf("{");
        for (int i = 0; i < split_vid; i++) {
            Vertex v = vertices[i];
            printf("%ld:%ld, ", v.id, v.deg);
        }
        printf("}");
    }

#ifdef DEBUG
    // Read the split graph
    printf("===========Reading the split graph from binary files===========\n");

    FILE *vertexFile = std::fopen((output_prefix + "_gv.bin").c_str(), "rb");
    FILE *edgeFile = std::fopen((output_prefix + "_nl.bin").c_str(), "rb");
    if (!vertexFile || !edgeFile) {
        printf("Error when openning file %s or %s, exiting.\n", (output_prefix + "_gv.bin").c_str(), (output_prefix + "_nl.bin").c_str());
        exit(EXIT_FAILURE);
    }

    uint64_t num_vertices;
    fseek(vertexFile, 0, SEEK_SET);
    n = fread(&num_vertices, sizeof(uint64_t), 1, vertexFile);
    printf("Number of vertices: %ld\n", num_vertices);
    
    fseek(edgeFile, 0, SEEK_SET);
    n = fread(&num_edges, sizeof(uint64_t), 1, edgeFile);
    printf("Number of edges: %ld\n", num_edges);
    if (num_edges != edges.size()) {
        printf("Error: Number of edges mismatch\n");
        exit(1);
    }

    Vertex v;
    uint64_t neighbor, num_vertices_read = 0;

    while (num_vertices_read++ < num_vertices) {
        n = fread(&v, sizeof(Vertex), 1, vertexFile);
        printf("Vertex %ld - degree %ld\n\tNeighbors: [", v.id, v.deg);
        for (uint64_t j = 0; j < v.deg; j++) {
            n = fread(&neighbor, sizeof(uint64_t), 1, edgeFile);
            printf("%ld ", neighbor);
            if (edges.find(Edge(shuffle_reverse_map[v.id], shuffle_reverse_map[neighbor])) == edges.end()) {
                printf("Error: Edge (%ld, %ld) not found in the original graph\n", shuffle_reverse_map[v.id], shuffle_reverse_map[neighbor]);
                exit(1);
            }
        }
        printf("]\n");
    }

    fclose(vertexFile);
    fclose(edgeFile);

#endif

    return 0;
}