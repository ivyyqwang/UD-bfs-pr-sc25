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

#define USAGE "USAGE: ./split -f <graph_file> -m <max_degree> -d(directed) -s(stats) -l (line offset) -n(no split)"

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

class InputParser{
    public:
        InputParser (int &argc, char **argv){
            for (int i=1; i < argc; ++i)
                this->tokens.push_back(std::string(argv[i]));
        }
        const std::string& getCmdOption(const std::string &option) const{
            std::vector<std::string>::const_iterator itr;
            itr =  std::find(this->tokens.begin(), this->tokens.end(), option);
            if (itr != this->tokens.end() && ++itr != this->tokens.end()){
                return *itr;
            }
            static const std::string empty_string("");
            return empty_string;
        }
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
    bool no_split = input.cmdOptionExists("-n");
    if (no_split) max_degree = 0;
    
    std::ifstream inputFile(graph_file_path);
    std::string line;
    std::unordered_map<uint64_t, uint64_t> orig_vertices;
    std::set<Edge> edges;
    uint64_t max_orig_vid = 0;

    printf("===========Input Parameters===========\n");
    printf("Graph file: %s\n", graph_file_path.c_str());
    printf("Max degree: %d\n", max_degree);
    printf("Directed: %s\n", directed ? "true" : "false");
    printf("Stats: %s\n", stats ? "true" : "false");
    printf("No split: %s\n", no_split ? "true" : "false");

    printf("\n===========Reading graph file %s===========\n", graph_file_path.c_str());

    // Skip the first n lines
    if (input.cmdOptionExists("-l")) {
        int line_offset = std::stoi(input.getCmdOption("-l"));
        std::string line;
        while (std::getline(inputFile, line) && line_offset > 0) {
            line_offset--;
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

        max_orig_vid = std::max(max_orig_vid, std::max(src, dst));

#ifdef DEBUG
        // printf("Edge: (%ld, %ld)\n", src, dst);
#endif
    }
    printf("Read in %ld vertices and %ld edges\n", orig_vertices.size(), edges.size());

    printf("===========Finished reading graph file %s===========\n\n", graph_file_path.c_str());

    // Split the vertices
    printf("===========Splitting and shuffling the vertices===========\n");

    std::unordered_map<uint64_t, uint64_t> updated_degree_map;
    std::unordered_map<uint64_t, uint64_t> split_ranges;
    std::unordered_map<uint64_t, uint64_t> reverse_map;
    uint64_t split_vid = max_orig_vid + 1;

    uint64_t max_orig_degree = 0;
    if (no_split) {
        for (const std::pair<uint64_t, uint64_t> &v : orig_vertices) {
            updated_degree_map[v.first] = 0;
            split_ranges[v.first] = 0;
            reverse_map[v.first] = v.first;
        }
    } else {
        for (const std::pair<uint64_t, uint64_t> &v : orig_vertices) {
            uint64_t num_split = (v.second / max_degree) + 1;
            if (num_split == 1) {
                split_ranges[v.first] = 0;
                updated_degree_map[v.first] = 0;
                reverse_map[v.first] = v.first;
            } else {
                split_ranges[v.first] = split_vid << 32 | num_split;
                updated_degree_map[v.first] = 0;
                reverse_map[v.first] = v.first;
                for (uint64_t i = 0; i < num_split; i++) {
                    updated_degree_map[split_vid + i] = 0;
                    reverse_map[split_vid + i] = v.first;
                    split_ranges[split_vid + i] = split_vid << 32 | num_split;
                }
                split_vid += num_split;
            }

#ifdef DEBUG
            printf("Vertex %ld degree %ld split into %ld vertices, starting %ld. \n", v.first, v.second, num_split, split_vid);
#endif
            if (stats) max_orig_degree = std::max(max_orig_degree, v.second);
        }
    
    }
    uint64_t num_orig_vertices = orig_vertices.size();
    orig_vertices.clear();

#ifdef DEBUG
    for (uint64_t i = 0; i < split_vid; i++) {
        printf("reverse_map[%ld] = %ld\n", i, reverse_map[i]);
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
    if (no_split) {
        for (auto &e : edges) {
            new_edges[i] = e;
            i++;
            updated_degree_map[e.src] += 1;
        }
    } else {
    
        for (auto &e : edges) {
            src = e.src;
            dst = e.dst;
            if (split_ranges[src]) 
                src_split = (split_ranges[src] >> 32) + (rand() % (split_ranges[src] & NUM_SPLIT_MASK));
            else src_split = src;
            if (split_ranges[dst]) 
                dst_split = (split_ranges[dst] >> 32) + (rand() % (split_ranges[dst] & NUM_SPLIT_MASK));
            else dst_split = dst;
            
#ifdef DEBUG
            printf("Edge: (%ld, %ld) -> (%ld, %ld)\n", src, dst, src_split, dst_split);
#endif
            new_edges[i].src = src_split;
            new_edges[i].dst = dst_split;
            i++;
            
            updated_degree_map[src_split] += 1;
        }
    }
    // vid_map.clear();
    printf("===========Finished remapping the edges===========\n\n");

    // Create the split graph
    printf("===========Creating the split graph===========\n");

    uint64_t num_split_vertices = split_vid;
    Vertex *vertices = reinterpret_cast<Vertex *>(malloc(sizeof(Vertex) * num_split_vertices));
    printf("Number of split vertices: %ld\n", num_split_vertices);
    
    uint64_t *edge_bins = reinterpret_cast<uint64_t *>(malloc(sizeof(uint64_t) * edges.size()));
    uint64_t offset = 0;

    for (uint64_t i = 0; i < split_vid; i++) {
        vertices[i].vid = i;
        vertices[i].degree = updated_degree_map[i];
        vertices[i].orig_vid = reverse_map[i];
        vertices[i].neighbors = edge_bins + offset;
        vertices[i].distance = UINT64_MAX;
        vertices[i].parent = UINT64_MAX;
        // vertices[i].split_range = (split_ranges[reverse_map[i]] & (NUM_SPLIT_MASK << 32)) + (split_ranges[reverse_map[i]] >> 32) + (split_ranges[reverse_map[i]] & NUM_SPLIT_MASK);
        vertices[i].split_range = (split_ranges[i] & (NUM_SPLIT_MASK << 32)) + ((split_ranges[i] >> 32) + (split_ranges[i] & NUM_SPLIT_MASK));
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
            avg_degree += v.degree;
            if (v.degree > max_degree) max_degree = v.degree;
#ifdef DEBUG
            printf("Vertex %ld - degree %ld\n\tNeighbors: [", v.vid, v.degree);
            for (uint64_t i = 0; i < v.degree; i++) {
                printf("%ld ", v.neighbors[i]);
            }
            printf("]\n");
#endif
        }
        printf("Number of original vertices: %ld\n", num_orig_vertices);
        printf("Max degree in original graph: %ld\n", max_orig_degree);
        printf("Number of split vertices: %ld\n", num_split_vertices);
        printf("Number of edges: %ld\n", num_edges);
        printf("Average degree: %f\n", avg_degree / num_split_vertices);
        printf("Max degree after split: %ld\n", max_degree);

        printf("===========Finished printing graph stats===========\n\n");
    }

    // Write the split graph to binary files
    printf("===========Writing the split graph to binary files===========\n");

    std::string output_prefix;
    if (no_split) {
        max_degree = 0;
        output_prefix = graph_file_path.substr(0, graph_file_path.find_last_of('.')) + "_orig";
    } else {
        output_prefix = graph_file_path.substr(0, graph_file_path.find_last_of('.')) + "_max_deg_" + std::to_string(max_degree);
    }

    FILE* graph_file = std::fopen((output_prefix + ".bin").c_str(), "wb");
    if (!graph_file) {
        printf("Error when openning file %s, exiting.\n", (output_prefix + ".bin").c_str());
        exit(EXIT_FAILURE);
    }

    printf("Writing to %s\n", output_prefix.c_str());
    int n;

    fseek(graph_file, 0, SEEK_SET);
    num_orig_vertices = max_orig_vid + 1;
    n = fwrite(&num_orig_vertices,sizeof(uint64_t),1,graph_file);
    printf("Writing number of original vertices = %ld\n", num_orig_vertices);
    n = fwrite(&num_split_vertices,sizeof(uint64_t),1,graph_file);
    printf("Writing number of split vertices = %ld\n", num_split_vertices);

    n = fwrite(&num_edges, sizeof(uint64_t),  1,  graph_file);
    printf("Writing number of edges = %ld\n", num_edges);

    n = fwrite(&(vertices[0]), sizeof(Vertex), num_split_vertices, graph_file);
    n = fwrite(edge_bins, sizeof(uint64_t), num_edges, graph_file);

    fclose(graph_file);

    printf("Done writing to %s\n\n", output_prefix.c_str());
    printf("===========Finished writing the split graph to binary files===========\n\n");
    fflush(stdout);

#ifdef DEBUG
    // if (stats) {    
    //     printf("{");
    //     for (int i = 0; i < split_vid; i++) {
    //         Vertex v = vertices[i];
    //         printf("%ld:%ld, ", v.vid, v.degree);
    //     }
    //     printf("}");
    // }

    // Read the split graph
    printf("===========Reading the split graph from binary files===========\n");

    FILE *outputFile = std::fopen((output_prefix + ".bin").c_str(), "rb");
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
    if (num_edges != edges.size()) {
        printf("Error: Number of edges mismatch\n");
        exit(1);
    }
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

    for (int i = 0; i < num_vertices; i++) {
        printf("Vertex %ld - degree %ld\n\tNeighbors: [", vertices_read[i].vid, vertices_read[i].degree);
        num_edges_read += vertices_read[i].degree;
        for (uint64_t j = 0; j < vertices_read[i].degree; j++) {
            n = fread(&neighbor, sizeof(uint64_t), 1, outputFile);
            printf("%ld ", neighbor);
            if (edges.find(Edge(reverse_map[vertices_read[i].vid], reverse_map[neighbor])) == edges.end()) {
                printf("Error: Edge (%ld, %ld) not found in the original graph\n", reverse_map[vertices_read[i].vid], reverse_map[neighbor]);
                exit(1);
            }
        }
        printf("]\n");
    }
    
    if (num_edges_read != edges.size()) {
        printf("Error: Number of edges mismatch\n");
        exit(1);
    }

    fclose(outputFile);
    
    printf("===========Successfully read the split graph from binary files===========\n\n");

#endif

    return 0;
}