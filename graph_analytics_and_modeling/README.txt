Before using, please set the project location with the absolute path of where the folder is downloaded to, by altering PROJECT_LOC in julia/shared.jl 


Included folders 
- julia: includes serial implemntations that the work statistics for each graph were projected off of for BFS and PageRank algorithms. 
- data: includes SNAP & random graphs used in GEM5 simulations, and data used for computing statistics used in models.
- python: includes modeling code for projecting performance for BFS and PageRank routines 

Julia Folder:
- Key experiment drivers: bfs_frontiers.jl , graph_stats.jl , pagerank.jl 
- Random Graph Generators: graph_generators.jl, randomGraphCode.jl 
- Project level parameters: shared.jl 

Data Folder:
- SNAP: snap graphs used by GEM5 simulation.
- randomGraphs: generated random graphs (only includes networks used with GEM5 simulations) 
- julia_output: location of JSON files saved from Julia experiment drivers. Includes the data files used for generating our plots. 
