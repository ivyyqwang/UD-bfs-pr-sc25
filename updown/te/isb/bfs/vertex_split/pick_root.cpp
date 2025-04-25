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

#define USAGE "USAGE: ./pick_root -f <graph_file> -d <root_degree> -v <original_vid> -s(stats)"

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

    std::string graph_file = input.getCmdOption("-f");
    uint64_t root_degree, orig_vid;
    bool root_degree_set = false;
    if (input.cmdOptionExists("-d")) {
        root_degree_set = true;
        root_degree = std::stoull(input.getCmdOption("-d"));
    } else if (input.cmdOptionExists("-v")) {
        root_degree_set = false;
        orig_vid = std::stoull(input.getCmdOption("-v"));
    } else {
        printf("Please provide a criteria to pick root vertex using -d or -v option.\n");
        exit(EXIT_FAILURE);
    }
    bool stats = input.cmdOptionExists("-s");
    
    
    printf("===========Reading the split graph from binary files===========\n");

    FILE *outputFile = std::fopen((graph_file).c_str(), "rb");
    if (!outputFile) {
        printf("Error when openning file %s, exiting.\n", (graph_file).c_str());
        exit(EXIT_FAILURE);
    }

    uint64_t num_vertices, n, num_edges, num_orig_vertices;
    fseek(outputFile, 0, SEEK_SET);
    n = fread(&num_orig_vertices, sizeof(uint64_t), 1, outputFile);
    printf("Number of original vertices: %ld\n", num_orig_vertices);

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
        if (root_degree_set && v->degree == root_degree) {
            printf("Root vertex: %ld\n", v->vid);
            printf("Root vertex original id: %ld\n", v->orig_vid);
            printf("Root vertex degree: %ld\n", v->degree);
            return 0;
        } else if (v->orig_vid == orig_vid) {
            printf("Root vertex: %ld\n", v->vid);
            printf("Root vertex original id: %ld\n", v->orig_vid);
            printf("Root vertex degree: %ld\n", v->degree);
            return 0;
        }
        num_vertices_read++;
    }
    printf("Read in %ld vertices\n", num_vertices_read);
    if (root_degree_set) {
        printf("Root vertex with degree %ld not found.\n", root_degree);
    } else {
        printf("Root vertex with original id %ld not found.\n", orig_vid);
    }
    exit(0);

    for (int i = 0; i < num_vertices; i++) {
        printf("Vertex %ld - degree %ld\n\tNeighbors: [", vertices_read[i].vid, vertices_read[i].degree);
        num_edges_read += vertices_read[i].degree;
        for (uint64_t j = 0; j < vertices_read[i].degree; j++) {
            n = fread(&neighbor, sizeof(uint64_t), 1, outputFile);
        }
        printf("]\n");
    }
    
    fclose(outputFile);
    
    printf("===========Successfully read the split graph from binary files===========\n\n");

    if (stats) {
        // Print stats
        printf("===========Printing graph stats===========\n");
        double avg_degree = 0;
        uint64_t max_degree = 0;
        Vertex v;

        for (int i = 0; i < num_vertices; i++) {
            v = vertices_read[i];
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
        printf("Number of split vertices: %ld\n", num_vertices);
        printf("Number of edges: %ld\n", num_edges);
        printf("Max degree: %ld\n", max_degree);
        printf("Average degree: %f\n", avg_degree / num_vertices);

        printf("===========Finished printing graph stats===========\n\n");
    }



    return 0;
}