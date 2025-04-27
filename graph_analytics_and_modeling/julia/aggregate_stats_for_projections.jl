using StatsBase
include("shared.jl")


function load_and_parse_all_files()

    println("BFS RMAT:")
    bfs_stats(RESULTS_LOC*"BFS_RMAT_percentileRanges:[(0.001,1.0)]_samples:100_sizes:[256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576,2097152,4194304,8388608,16777216]_startSeed:453923_trials:10.json")
    println("\nBFS ER:")
    bfs_stats(RESULTS_LOC*"BFS_erdosReyni_avgDegree:[10,35]_percentileRanges:[(0.001,1.0)]_sizes:[256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576,2097152,4194304,8388608,16777216]_startSeed:98423_trials:10.json")
    println("\nBFS Forest Fire:")
    bfs_stats(RESULTS_LOC*"BFS_forestFires_p:[0.4]_percentileRanges:[(0.001,1.0)]_samples:100_sizes:[256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576,2097152,4194304,8388608,16777216]_startSeed:453923_trials:10.json")
    println()

    println("PageRank RMAT:")
    pagerank_stats(RESULTS_LOC*"PR_v2_RMAT_epsilons:[-1.0]_sizes:[256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576,2097152,4194304,8388608,16777216]_startSeed:453923_trials:10.json")
    println("\nPageRank ER:")
    pagerank_stats(RESULTS_LOC*"PR_v2_erdosReyni_avgDegree:[10,35]_epsilons:[-1.0]_sizes:[256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576,2097152,4194304,8388608,16777216]_startSeed:98423_trials:10.json")
    println("\nPageRank Forest Fire:")
    pagerank_stats(RESULTS_LOC*"PR_v2_forestFire_epsilons:[-1.0]_p:[0.4]_sizes:[256,512,1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576,2097152,4194304,8388608,16777216]_startSeed:453923_trials:10.json")

end 


function bfs_stats(output_file)

    output = load_output_from_json(output_file)
    println("graph_sizes:$(output["graph_sizes"]')")

    # get median over graph trials median over uniformly selected starting vertices
    frontier_counts = dropdims(median(median(length.(output["forward_frontier_edgecount"][1,:,:,:,end]),dims=(1)),dims=(2)),dims=(1,2))
    println("frontier sizes:$(frontier_counts')")                                                 #using `end` here to make sure the ER results
                                                                                                  # displayed are for d_avg = 35.


end 

function pagerank_stats(output_file)

    output = load_output_from_json(output_file)
    println("graph_sizes:$(output["graph_sizes"]')")

    # Push Based Pagerank is idx 1 
    active_set_volume_sums = median(sum.(output["active_set_volumes"][1,:,1,:,end]),dims=1)
    println("Push PR active set volume sums:$(active_set_volume_sums)")
    iterations = median(length.(output["active_set_volumes"][1,:,1,:,end]),dims=1)
    println("Push PR iteratons:$(iterations)")

    # Data Driven Pagerank is idx 2 
    active_set_volume_sums = median(sum.(output["active_set_volumes"][2,:,1,:,end]),dims=1)
    println("Data Driven PR active set volume sums:$(active_set_volume_sums)")

    iterations = median(length.(output["active_set_volumes"][2,:,1,:,end]),dims=1)
    println("Data Driven PR iteratons:$(iterations)")

end 

function graph_stats(output_file)

    output = load_output_from_json(output_file)
    println("graph_sizes:$(output["graph_sizes"]')")


    median_max_degree = dropdims(median(output["max_degrees"],dims=1),dims=(1,3))
    println("median degrees:$( median_max_degree)")

end 