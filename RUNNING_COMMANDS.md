# UpDown Artifact — Detailed Reproduction Commands

This file contains the full installation, execution, and output-parsing
instructions for artifacts $A_1$–$A_4$. The AD/AE appendix (`sc26_ad_ae_main.tex`)
gives a one-page summary for each artifact and points here for exact commands.

Repository: https://github.com/ivyyqwang/UD-bfs-pr-sc26
Graphs: https://drive.google.com/drive/u/1/folders/1nEn_-90V3UCVSEdvIgV06by0yvvkdQjb

---

## A1 — `updown` (UpDown simulator + application programs)

### Software dependencies

Operating System: Ubuntu 20.04

UpDown simulator build dependencies:
- **git** — version control
- **gcc** — compiles the simulator
- **Clang** — Clang 7–16 also supported
- **SCons** — 3.0 or greater
- **Python 3.6+** — simulator relies on Python dev libraries
- **OpenMP** — parallelizes simulator execution

Python dependencies:
- `pip install perflog==2017.8.7`
- `pip install bitstring==4.1.4`

### Datasets

Inputs: https://drive.google.com/drive/folders/18CI2Gi1Nth1YmNtwumVk0vdCK1jLOg8L?usp=sharing

Raw graph text files are under `randomGraphs` and `SNAP`. Each line is an edge
list entry: `<source_vertex_id> <destination_vertex_id>`. Referred to below as
`<raw_graph_file>`.

### Installation

1. Build the UpDown simulator
   1. `git clone https://github.com/ivyyqwang/UD-bfs-pr-sc26.git`
   2. `cd UD-bfs-pr-sc26/updown; source setup_env.sh`
   3. Compile the simulator, applications, and libraries:
      1. `mkdir build; cd build`
      2. ```
         cmake $UPDOWN_SOURCE_CODE \
           -DUPDOWN_ENABLE_BASIM=ON \
           -DUPDOWN_DETAIL_STATS=ON \
           -DUPDOWN_ENABLE_FASTSIM=ON \
           -DUPDOWNRT_ENABLE_LIBRARIES=ON \
           -DCMAKE_INSTALL_PREFIX=$UPDOWN_INSTALL_DIR \
           -DUPDOWNRT_ENABLE_APPS=ON \
           -DUPDOWN_ENABLE_DEBUG=OFF
         ```
      3. `make -j; make install`
2. Download the dataset from the Google Drive link above.

All commands below assume the current directory is the `updown` folder of the
repository, and that `source setup_env.sh` has already been run in the session.

### T1 — Data preparation

Download and extract the raw graph files (plain-text edge lists) from the
Google Drive link above. The preprocessing programs convert edge-list graphs
to neighbor-list/adjacency format and split high-degree vertices into
sub-vertices; the max split degree is a command-line argument.

| Algorithm | Preprocess directory | Command |
|---|---|---|
| PageRank (push, data-driven) | `$UPDOWN_SOURCE_CODE/updown/apps/pagerank/preprocess` | `make; ./preprocess <input_filename> <output_filename> <num_vertex> <max_deg>` |
| BFS (push) | `$UPDOWN_SOURCE_CODE/apps/bfs/bfs_push/preprocess` | `make; ./preprocess <input_filename> <output_filename> <num_vertex> <max_deg>` |
| BFS (push-pull) | `$UPDOWN_INSTALL_DIR/updown/apps/` | `./split_shuffle -f <raw_graph_file> -m <max_degree> -s -l <offset>` |
| BFS (load balance) | `$UPDOWN_SOURCE_CODE/apps/bfs/bfs_load_balance/preprocess` | `make; ./preprocess <input_filename> <output_filename>` |
| K-Trust | `$UPDOWN_SOURCE_CODE/apps/KTruss/preprocess` | `make; ./preprocess <input_filename> <output_filename> <num_vertex>` |
| K-Core | `$UPDOWN_SOURCE_CODE/apps/kcore/preprocess` | `make; ./preprocess <input_filename> <output_filename>` |
| Triangle Count (TC) | `$UPDOWN_SOURCE_CODE/apps/tc/preprocess` | `make; ./preprocess <input_filename> <output_filename> <num_vertex>` |
| Connected Components (CC) | `$UPDOWN_SOURCE_CODE/apps/cc/preprocess` | `make; ./preprocess <input_filename> <output_filename>` |
| Strongly Connected Components (SCC) | `$UPDOWN_SOURCE_CODE/apps/scc/preprocess` | `make; ./preprocess <input_filename> <output_filename>` |
| Louvain | `$UPDOWN_SOURCE_CODE/apps/louvain/preprocess` | `make; ./preprocess <input_filename> <output_filename>` |

Argument notes:
- `<input_filename>`: path to the edge-list graph file.
- `<output_filename>`: path to the output binary/adj graph file.
- `<num_vertex>`: number of vertices in the graph.
- `<max_deg>`: max vertex degree after splitting (paper values: 512 for
  PageRank, 4096 for push and push-pull BFS; not set for load-balancing BFS).
- BFS push-pull `-m <max_degree>`: real max degree after splitting may be
  lower than specified but never exceeds it.
- BFS push-pull `-s`: optionally print graph statistics before/after
  splitting to stdout.
- BFS push-pull `-l <offset>`: optionally skip the first `offset` lines of
  the input (default 0) — some graph files have header lines to ignore.
- BFS push-pull outputs are binary files named
  `<raw_graph_file>_shuffle_max_deg_<max_degree>.bin`, with statistics in
  `<raw_graph_file>_m<max_degree>_stats.txt`.

### T2 — Simulation

Runs the compiled UpDown programs to obtain performance statistics (run time,
work per iteration).

**PageRank**

- Push PageRank — `$UPDOWN_INSTALL_DIR/updown/apps`:
  ```
  OMP_NUM_THREADS=<omp_threads> ./pr_udweave <graph_file_gv.bin> <graph_file_nl.bin> <num_nodes> (<network_latency> <network_bandwidth>)
  ```
  - `<omp_threads>`: OpenMP thread count (recommended: 32).
  - `<graph_file_gv.bin>`, `<graph_file_nl.bin>`: neighbor-list graphs from T1.
  - `<num_nodes>`: UpDown system size (paper: 1–256 nodes).
  - `<network_latency>` (optional): max network latency, default 1100 (550 ns).
  - `<network_bandwidth>` (optional): max network bandwidth, default 4400 (4.4 TB/s).

- Data-driven PageRank — `$UPDOWN_INSTALL_DIR/updown/apps`:
  ```
  OMP_NUM_THREADS=<omp_threads> ./partialPagerankDataDriven <graph_file_path> <num_nodes> <num_top_iterations> <num_ud_iterations>
  ```
  - `<num_top_iterations>`: iterations of PageRank computed on the CPU core.
  - `<num_ud_iterations>`: iterations computed on the UpDown accelerators.

**BFS**

- Push BFS — `$UPDOWN_INSTALL_DIR/updown/apps`:
  ```
  OMP_NUM_THREADS=<omp_threads> ./bfs_udweave <graph_file_gv.bin> <graph_file_nl.bin> <num_lanes> <num_control_lanes_per_level> <root_vid> (<network_latency> <network_bandwidth>)
  ```
  - `<num_lanes>`: number of UpDown lanes. 1 node = 2048 lanes (e.g., 4096
    lanes = the 2-node data point in Figure 4). Paper range: 1–256 nodes
    (2,048–524,288 lanes).
  - `<num_control_lanes_per_level>`: lanes managed by a single control master
    per hierarchy level (paper value: 32). If control lanes at a level exceed
    this, a higher control level is introduced.
  - `<root_vid>`: root vertex ID of the BFS tree.

- Push-Pull BFS — `$UPDOWN_INSTALL_DIR/updown/te/isb`:
  ```
  OMP_NUM_THREADS=<omp_threads> ./updown_bfs_push_pull <graph_split.bin> <num_accel> <root_vid> &> <output>
  ```
  - `<num_accel>`: number of UpDown accelerators. 1 node = 32 accelerators
    (e.g., 64 = the 2-node point in Figure 4). Paper range: 32–8,192 accelerators.
  - `<output>`: path to store simulation output (unique per run).

- Load-Balancing BFS — `$UPDOWN_INSTALL_DIR/updown/apps`:
  ```
  OMP_NUM_THREADS=<omp_threads> ./LBBFS <graph_file> <num_lanes> <root_vid>
  ```
  - `<graph_file>`: adj-format graph (PBBS format, cs.cmu.edu/pbbs/benchmarks/graphIO.html) from T1.

**K-Trust** (requires ≥512 GB memory) — `$UPDOWN_INSTALL_DIR/updown/apps`:
```
OMP_NUM_THREADS=<omp_threads> ./k_truss_udweave <k> <graph_file_gv.bin> <graph_file_nl.bin> <num_lanes>
```
- `<k>`: minimum triangle-count per edge (paper: k=3 and k=kmax).

**K-Core** — `$UPDOWN_INSTALL_DIR/updown/apps`:
```
OMP_NUM_THREADS=<omp_threads> ./kcore <graph_file_gv.bin> <graph_file_nl.bin> <num_lanes> <DifferencePercentForCompaction>
```
- `<DifferencePercentForCompaction>`: compaction threshold percentage (paper: 100 = never compact).

**Triangle Count** (requires ≥512 GB memory) — `$UPDOWN_INSTALL_DIR/updown/apps`:
```
OMP_NUM_THREADS=<omp_threads> ./tc_udweave <graph_file_gv.bin> <graph_file_nl.bin> <num_lanes> (<network_latency> <network_bandwidth>)
```

**Connected Components** — `$UPDOWN_INSTALL_DIR/updown/apps`:
```
OMP_NUM_THREADS=<omp_threads> ./em <adj_graph_file> CC <num_lanes>
```

**Strongly Connected Components** — `$UPDOWN_INSTALL_DIR/updown/apps`:
```
OMP_NUM_THREADS=<omp_threads> ./scc <graph_file_gv.bin> <graph_file_nl.bin> <num_lanes>
```

**Louvain** — `$UPDOWN_INSTALL_DIR/updown/apps`:
```
OMP_NUM_THREADS=<omp_threads> ./louvain <num_nodes> <graph_file_gv.bin> <graph_file_nl.bin>
```
- `<num_nodes>`: paper simulates a 1-node system for Louvain.

For all programs above, `<omp_threads>` is recommended to be 32 unless noted
otherwise, and `<graph_file_gv.bin>`/`<graph_file_nl.bin>` are the neighbor-list
graphs output by T1.

### T3 — Post-processing (extracting metrics from simulation output)

Extracts the numbers behind paper Figures 3–6, 10 and Tables 4–6, and the
inputs consumed by artifacts $A_2$/$A_3$.

- **K-Core** (Figure 4, Table 4): output prints simTicks per iteration, e.g.
  `[BASIM_PRINT] 544703: [...][KCORE_MULTI_main__run_iter] start ... child_event = 1910402c`
  and `[BASIM_PRINT] 557502: [...][KCORE_MULTI_main__done] end ... max_delta = 31, child = 1910402c`.
  Execution time = `(end_tick - start_tick) / 2e9` seconds. Edge count comes
  from the input graph.

- **Tables 5–6**: same pattern — each program prints start/end simTicks;
  execution time = `ticks / 2e9` seconds; edges from input graph.

- **Push PageRank** (Figures 5–6): `grep "updown_terminate" <output>` →
  e.g. `[BASIM_PRINT] 187371100: [...][updown_terminate] [DEBUG][NWID 0] Finish PageRank, number of edge updates = 9395215893`.
  First number = final simulation tick, second = edges traversed.
  `GTEPS = edges / (ticks/2e9) / 1e9`.

- **Data-Driven PageRank**: `grep "PageRank MSR returns" <output>` →
  e.g. `[BASIM_PRINT] 125143800: [...][InitUpDown__terminate] PageRank MSR returns current active set volume = 9395215893.`
  Gives final tick and active-set volume for that iteration.
  `Effective GTEPS = (num_iter * edges) / (ticks/2e9) / 1e9`, where `num_iter = 5`.

- **Push BFS**: `grep "BFS finish" <output>` →
  e.g. `[BASIM_PRINT] 3945300: [...][main_master__reduce_launcher_done] BFS finish`.
  `GTEPS = edges / (ticks/2e9) / 1e9`.

- **Push-Pull BFS**: `grep "converges" <output>` →
  e.g. `[BASIM_PRINT] 408100: [...][BFS__terminate_sync] [DEBUG][NWID 0] BFS converges at iteration = 8. Return to top.`
  `GTEPS = edges / (ticks/2e9) / 1e9`.

- **Load-Balancing BFS**: standard output ends with:
  ```
  BFS is correct
  ###, iteration number, active_set_size, start_outgoing_size, sim_ticks
  ###, 0, 1, 1, 21100
  ###, 1, 1, 4, 21100
  ###, 2, 3, 3, 20400
  total ticks = 62600
  ```
  "BFS is correct" indicates verification passed. `active_set_size` = number
  of vertices in the frontier; `start_outgoing_size` = outgoing edges from
  the frontier.

- **$A_2$ input, Data-Driven PageRank**: `grep "updown_terminate" <output>`
  outputs 5 lines (one per PageRank iteration), giving the active-set volume
  per iteration.

- **$A_2$/$A_3$ input, Push BFS**: `grep "Itera" <output>` →
  e.g. `[BASIM_PRINT] 3512900: [...][main_master__reduce_launcher_done] [Itera 3]: add queue 4825707 traversed edges 105130915`.
  First number = accumulated simulation tick, second = vertices in the next
  frontier, third = forwarded edges in the current iteration.

- **$A_2$/$A_3$ input, Load-Balancing BFS**: same CSV block as above.

- **Figure 10(a)**: each lane reports `[UD0-L0] EventTransitions = 4435808`.
  Sum `EventTransitions` across all lanes for total thread invocations.

- **Figure 10(b)**: each lane reports
  ```
  [BASIM_GLOBAL]: Curr_Sim_Cycle: 309404600
  [UD0-L0] Cycles = 303340675
  ```
  `utilization = Cycles / Curr_Sim_Cycle`.

- **Figure 10(c)**: set `<network_latency>` to `{1000, 2000, 4000, 8000, 16000}`,
  rerun Push-PR, Push-BFS, and TC, and recompute `GTEPS = edges / (ticks/2e9) / 1e9`
  for each latency value.

### Estimated reproduction time (minutes)

**PageRank & BFS variants** — sum of all 9 system configurations (1–256 nodes)
per program per graph:

| Graph | Push PR | Data-Driven PR | Push BFS | Push-Pull BFS | Load Balancing BFS |
|---|---|---|---|---|---|
| Forest Fire s28 (FF) | 270 | 600 | 1080 | 810 | 720 |
| RMAT s28 (RMAT) | 780 | 1230 | 1200 | 410 | 480 |
| Erdos Renyi s28 (ER) | 1350 | 1890 | 1080 | 600 | 1200 |
| soc-LiveJournal (LJ) | 60 | 60 | 60 | 60 | 60 |
| com-orkut (Orkut) | 60 | 120 | 120 | 60 | 120 |
| Twitter | 420 | 760 | 1080 | 1080 | 480 |

**Other UpDown programs**:

| Program | Graph | Time |
|---|---|---|
| K-Truss (k=3) | cit-Patents | 5 |
| K-Truss (k=kmax) | cit-Patents | 5 |
| K-Core | RMAT s21–s27 | 12,230 |
| Triangle Count | RMAT s22, RMAT s25 | 10,142 |
| Connected Components | RMAT s23 | 5 |
| Strongly Connected Components | RMAT s22 | 5 |
| Louvain | cit-Patents | 60 |

In total, reproducing every configuration in the paper requires 240 simulation
runs (4 UpDown programs × 7 configurations, plus 2 baseline C++ programs, × 8
datasets), at roughly 14 hours per run on average — about 3,360 compute-hours
end to end. The per-graph/per-program breakdown above lets reviewers
reproduce a representative subset (e.g., one graph and one program) far more
cheaply.

---

## A2 — `gpu_scripts` (cuGraph GPU baseline)

### Software dependencies

- Python: 3.11.14 (any 3.11–3.14)
- CUDA Toolkit: 12.9.1
- NVCC: 12.9.86
- cuGraph: 26.2.0
- cuDF: 26.2.1

Install: once the correct Python/CUDA driver versions are present, install the
rest by following https://docs.rapids.ai/install/.

### Datasets

Raw inputs from GraphChallenge (https://graphchallenge.mit.edu/data-sets/) and
the SNAP dataset collection (https://snap.stanford.edu/data/). Scripts parse
inputs by file extension; larger files may need to be unzipped first.

### T1 — Prepare inputs

Place input graphs in a folder, then prepare a test list file containing one
line per graph: `<graph_file_name_without_extension> <run_parameter>`.
`<run_parameter>` is `k` for K-Truss and the start vertex for BFS (paper uses
vertex 1). Other applications ignore the parameter but still require the
column to be present for the parser. An example list file is included in the
repository.

### T2 — Run benchmarks

```
python3 <app>_batch.py <graph_dir> <graph_list>
```
- `<app>`: application to run on the GPU.
- `<graph_dir>`: directory containing the tsv/txt graph inputs.
- `<graph_list>`: list of graphs to run (graph name + run parameter pairs).

The script runs every graph in the list and reports the average execution
time of 5 runs (warm-up runs excluded).

### Output / Analysis

Example (BFS):
```
==========================================
[1/5] Graph='<graph_name>', source_vertex=1

Using file: <graph_name>.txt
Loaded edge rows: x
Number of vertices: y
Number of edges: z
BFS source vertex: 1
BFS complete.
Reached vertices: a
Max distance: b
Avg Processing Time: t ms.
```
Compare `Avg Processing Time` to the 1-node UpDown execution time to
reproduce the paper's GPU-vs-UpDown comparison (Tables 4–6).

### Estimated reproduction time

Installing dependencies: <15 minutes on a 16-core server. Running the
benchmark on a single input: <1 minute on a high-end GPU.

---

## A3 — `graph_analytics_and_modeling` (Julia/Python performance projection)

### Software dependencies

- Julia ≥ v1.9 (https://julialang.org/downloads/oldreleases/)
- Python 3

Julia packages (run inside the Pkg REPL, activated by typing `]`):
```
add LinearAlgebra, Distributed, SparseArrays, MatrixNetworks, Random, JSON, NearestNeighbors, ImageFiltering, GenericArpack
```
To use worker processes: `julia -p [number_of_workers]::Int` (drivers also run
without extra workers).

Python packages:
```
pip3 install scipy numpy pandas matplotlib
```

### Datasets

A handful of SNAP networks are included under `data/`. Pre-computed random
graphs are included under `randomGraphs/`; more can be generated with
`generate_random_graph` in `graph_generators.jl`:

- ER: `generate_random_graph(ErdosRenyi(), 98674, 2^20, 35)`
- RMAT: `generate_random_graph(RMAT(), 454044, 2^20)` — note: the generated
  RMAT graph must be reduced to its largest connected component to match the
  included file, via `MatrixNetworks.largest_component(sparse(A))`.
- FF (Forest Fire): `generate_random_graph(ForestFire(), 16755, 2^20, .4)`

Calling `generate_random_graph` with the same parameters against the
`randomGraphs/` folder loads existing graphs and generates any missing ones.

### T1–T4 pipeline

1. **T1 — generate/load networks.**
2. **T2 — run experiment drivers.** `pagerank.jl`, `bfs_frontiers.jl`, and
   `graph_stats.jl` each expose a `run_all_*_experiments` driver, using the
   global parameters at the head of each file (with some graph-type-specific
   parameters set inside each driver). Drivers load from `SNAP_GRAPHS` /
   `RANDOM_GRAPHS` or generate+save a random graph, then write a JSON file
   with measured statistics to `RESULTS_LOC` (set in `shared.jl`).
3. **T3 — compute aggregate statistics.** `aggregate_stats_for_projections.jl`
   loads driver output and computes median statistics used for projection.
4. **T4 — evaluate/render models.** `render_all_figures` renders and saves
   Figures 7–9. `make_bfs_GTEP_projection_figure` and
   `make_pr_GTEP_projection_figure` render the individual BFS/PageRank
   projections (Figures 8–9); functions ending in `_perf()` return the raw
   plotted points and fit functions used for the performance models.
   `print_[bfs/pr]_GTEPs` generates compute rates for the machine sizes used
   in Figures 11–12.

### Experiment parameters

- All experiments generate 10 random-graph instances per size from
  $2^8$ to $2^{24}$.
- ER: edge probability $p = 35/n$ (average degree 35; also ensures
  connectivity since $35/n > \log(n)/n$).
- FF: burn probability $p = 0.4$ (produces a controlled amount of degree
  skew, enough to exercise the vertex-splitting procedure).
- RMAT: no extra parameters — uses the graph500 spec (https://graph500.org/?page_id=12#sec-3_2).
- BFS driver: 100 samples of random start vertices with degree within the
  0.001–100th percentile of all vertex degrees.
- PR driver: convergence tolerance $\varepsilon = 1/n$ (so work scales
  proportionally with graph size; set `tolerance = -1` in the driver to get
  this behavior — noted in the code).

### Estimated reproduction time

Full run (10 trials, scale 8–24): ~12–18 compute-hours, dominated by graphs
above scale 20. Trends can be validated using scale 8–20 graphs alone in
~1–2 compute-hours. Pre-generated PageRank/BFS results are included in
`data/julia_output/` and can be used instead of a full re-run.

---

## A4 — `updown_fastsim3` (large-scale MPI+OpenMP simulator)

### Software dependencies

Operating System: Ubuntu 20.04

Same UpDown build dependencies as A1 (git, gcc or Clang 7–16, SCons ≥3.0,
Python 3.6+, OpenMP), plus:
- **MPI** — for distributed execution across multiple machines (accelerates
  simulation and increases available memory).

Python dependencies: same as A1 (`perflog==2017.8.7`, `bitstring==4.1.4`).

### Datasets

Inputs are RMAT graphs, generated directly by the T1 preprocessor (no
download needed) to reduce storage requirements.

### Installation

1. Build the UpDown simulator
   1. `git clone https://github.com/ivyyqwang/UD-bfs-pr-sc26.git`
   2. `cd UD-bfs-pr-sc26/updown_fastsim3; source setup_env.sh`
   3. Compile the simulator, applications, and libraries:
      1. `cd $PROJ/ext/updown`
      2. `mkdir build; cd build`
      3. ```
         cmake $UPDOWN_SOURCE_CODE \
           -DUPDOWN_ENABLE_BASIM=ON \
           -DUPDOWN_DETAIL_STATS=ON \
           -DUPDOWN_ENABLE_FASTSIM=ON \
           -DUPDOWNRT_ENABLE_LIBRARIES=ON \
           -DCMAKE_INSTALL_PREFIX=$UPDOWN_INSTALL_DIR \
           -DUPDOWNRT_ENABLE_APPS=ON \
           -DUPDOWN_ENABLE_DEBUG=OFF
         ```
      4. `make -j; make install`

All commands below assume the current directory is the `updown_fastsim3`
folder of the repository, and that `source setup_env.sh` has already been run.

### T1 — Data preparation

Generates the RMAT neighbor-list binary directly and splits high-degree
vertices into sub-vertices.

Directory: `$UPDOWN_SOURCE_CODE/apps/fastsim3/preprocess`
```
make
./preprocess <scale> <output_filename> <max_deg>
```
- `<scale>`: RMAT scale — number of vertices = $2^{scale}$.
- `<output_filename>`: path to the output binary graph file.
- `<max_deg>`: max vertex degree after splitting (paper: 512 for PageRank,
  2048 for BFS).

### T2 — Simulation

Directory (after compiling): `$UPDOWN_INSTALL_DIR/updown/apps`

- **Push-PageRank**:
  ```
  mpirun -np <mpi_ranks> --tag-output --report-bindings --bind-to core --map-by socket -x OMP_NUM_THREADS=<omp_threads> ./pr_udweave <graph_file_gv.bin> <graph_file_nl.bin> <num_nodes>
  ```
  - `<mpi_ranks>`: number of MPI ranks (default 1).
  - `<omp_threads>`: OpenMP threads per rank (recommended 32).
  - `<graph_file_gv.bin>`, `<graph_file_nl.bin>`: neighbor-list graphs from T1.
  - `<num_nodes>`: UpDown system size (paper uses up to 16,384 nodes).

- **Push-BFS**:
  ```
  mpirun -np <mpi_ranks> --tag-output --report-bindings --bind-to core --map-by socket -x OMP_NUM_THREADS ./bfs_udweave <graph_file_gv.bin> <graph_file_nl.bin> <num_lanes> <num_control_lanes_per_level> <root_vid>
  ```
  - `<num_lanes>`: 1 node = 2,048 lanes (16,384 nodes = 33,554,432 lanes).
  - `<num_control_lanes_per_level>`: control-hierarchy fan-out per level
    (paper: 32); if exceeded, an additional control level is introduced.
  - `<root_vid>`: root vertex ID of the BFS traversal.

### Post-processing (extracting metrics)

Extracts the numbers behind paper Figures 8–9, Table 7, and artifact
$A_3$'s inputs.

- **Push PageRank**: output prints simTicks, e.g.
  `[BASIM_PRINT] 14500: [...][InitUpDown__init] Top parameters: partition_array=..., num_lanes=8192, ...`
  and `[BASIM_PRINT] 8026300: [...][InitUpDown__terminate] PageRank Map Shuffle Reduce returned. Finish updown execution and return to top.`
  Execution time = `(end_tick - start_tick) / 2e9` seconds
  (example: `(8026300 - 14500)/2e9`). Edge count comes from a line such as
  `num_edges = 196331783902, nlist_size = 292285321952`.
  `GTEPS = edges / (ticks/2e9) / 1e9`.

- **Push BFS**: `grep "BFS finish" <output>` →
  e.g. `[BASIM_PRINT] 2336400: [...][main_master__reduce_launcher_done] BFS finish`.
  `GTEPS = edges / (ticks/2e9) / 1e9`.

### Estimated reproduction time

Runs performed on the Perlmutter Supercomputer, RMAT-s33, 128 machines:
Push-PR completes in ~40 minutes, Push-BFS in ~45 minutes.
