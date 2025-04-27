using Distributed

@everywhere include("graph_generators.jl")
@everywhere using GenericArpack: symeigs
@everywhere using StatsBase: fit, Histogram, percentile

using Base.Iterators: product

PERCENTILES_TO_MEASURE = [0,20,40,50,60,100]
GRAPH_SIZES = [2^scale for scale in 8:24]
TRIALS = 10
ONLY_GENERATE_GRAPHS = false
    # NOTE: setting this to true allows the routines to generate and save the random 
    #       graphs, and then they can be loaded again for additional experiments.

#  --  TLDR Driver  --  #

function run_all_graph_stats_experiments(only_test=true)

    if only_test
        modes_to_run = (true)
    else
        modes_to_run = (true,false)
    end

    # run test trials to make sure that results will run & save 
    for (testing) in modes_to_run
        parallel_RMAT_stats(testing,true)
        parallel_erdos_renyi_stats(testing,true,false)
        network_file_stats(testing,true)
        parallel_forest_fire_stats(testing,true) 
    end
end 


#
#    Experiment Drivers
# 
function network_file_stats(testing::Bool, save_output::Bool)
    
    if testing 
        files = [
            SNAP_GRAPHS*"as_caida.smat",
            SNAP_GRAPHS*"ca_astroph.smat"
        ]
        #files = ["/p/mnt/data/kloster-graphs/hollywood-2009.mat"]
        #file_abbreviations = ["caida","caAstroph"]
        percentiles_to_measure = PERCENTILES_TO_MEASURE
	else
        files = SNAP_GRAPHS .* readdir(SNAP_GRAPHS)    
        append!(files,UDSNAP_GRAPHS .* readdir(UDSNAP_GRAPHS))
		percentiles_to_measure = PERCENTILES_TO_MEASURE
	end
    file_abbreviations = first.(split.(replace.(last.(split.(files,"/")),"_"=>":"),"."))
    #@assert length(file_abbreviations) == length(files)
	
    # find the largest n for all graphs 
    max_graph_size = maximum(size.(load_graph.(files),1))


    result_dict = Dict{String,Any}([
        # experiment params 
		("graph_files",files),
        ("degree_bins",log_iter_bins(max_graph_size)),
		("file_abbreviations",file_abbreviations),
        ("percentiles_to_measure",percentiles_to_measure),
    ])

    parameters = enumerate(product( # constant parameters
                            repeat([(percentiles_to_measure,max_graph_size)],1),
                                    files)) # varying parameters

    parallel_graph_stats!(FileIOGraph(),percentiles_to_measure, max_graph_size, result_dict, parameters)

    if save_output
        #filename = filter(x->!isspace(x),"savedGraphs_prefixes:$(join(file_abbreviations,"+"))_percentiles:$(percentiles_to_measure).json")
        filename = filter(x->!isspace(x),"savedGraphsStats_numGraphs:$(length(files))_percentiles:$(percentiles_to_measure).json")
        
        save_output_to_json(testing, filename, result_dict)
    end

    return result_dict
end


# -- Graph Specific Drivers 
function parallel_forest_fire_stats(testing::Bool, save_output::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [10,100,1000]
        burn_ps = [.4]
        percentiles_to_measure = [0,50,100]
	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES#[10,100,1000,10000]#,100000]
        burn_ps = [.4]
        percentiles_to_measure = PERCENTILES_TO_MEASURE
	end 
    start_seed = 453923
 
    #return parallel_forest_fire_stats(testing, save_output, graph_sizes, burn_ps, percentiles_to_measure, trials, start_seed)

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("burn_ps",burn_ps),
        ("degree_bins",log_iter_bins(maximum(graph_sizes))),
		("trials",trials),
        ("percentiles_to_measure",percentiles_to_measure),
    ])

    parameters = enumerate(product( # constant parameters
                            repeat([(start_seed, percentiles_to_measure, maximum(graph_sizes))],trials),
                                   graph_sizes, burn_ps)) # varying parameters

    if ONLY_GENERATE_GRAPHS
        pmap(curried_stats_graph_generation(ForestFire()), parameters)
    else 
        parallel_graph_stats!(ForestFire(),percentiles_to_measure,maximum(graph_sizes),result_dict, parameters)

        if save_output
            filename = filter(x->!isspace(x),"forestFire_maxDegRun_p:$(burn_ps)_percentiles:$(percentiles_to_measure)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            save_output_to_json(testing, filename, result_dict)
        end
    end
    return result_dict
end

function parallel_erdos_renyi_stats(testing::Bool, save_output::Bool, scale_ps::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [10,100,1000]
        if !scale_ps 
            #edge_ps = Float64[.4]
            avg_degree = Int[10]
        end
        percentiles_to_measure = [0,50,100]
	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES
        if !scale_ps 
            avg_degree = Int[10,35]
        end
        percentiles_to_measure = PERCENTILES_TO_MEASURE
	end 
    start_seed = 98423
 

    #return parallel_forest_fire_stats(testing, save_output, graph_sizes, burn_ps, percentiles_to_measure, trials, start_seed)

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("trials",trials),
        ("degree_bins",log_iter_bins(maximum(graph_sizes))),
        ("percentiles_to_measure",percentiles_to_measure),
    ])
    if !scale_ps 
        result_dict["average_degree"] = avg_degree
    end

    if scale_ps 
        parameters = enumerate(product( # constant parameters
        repeat([(start_seed, percentiles_to_measure,maximum(graph_sizes))],trials),
                graph_sizes)) # varying parameters

    else
        parameters = enumerate(product( # constant parameters
                                repeat([(start_seed, percentiles_to_measure,maximum(graph_sizes))],trials),
                                    graph_sizes, avg_degree)) # varying parameters
    end

    if ONLY_GENERATE_GRAPHS
        pmap(curried_stats_graph_generation(ErdosRenyi()), parameters)
    else 
        parallel_graph_stats!(ErdosRenyi(),percentiles_to_measure,maximum(graph_sizes), result_dict, parameters)

        if save_output
            if !scale_ps 
                filename = filter(x->!isspace(x),"erdosReyni_avgDegree:$(avg_degree)_percentiles:$(percentiles_to_measure)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            else 
                filename = filter(x->!isspace(x),"erdosReyni_percentiles:$(percentiles_to_measure)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            end 
            save_output_to_json(testing, filename, result_dict)
        end
    end
    return result_dict
end

function parallel_RMAT_stats(testing::Bool, save_output::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [10,100,1000]
        percentiles_to_measure = [0,50,100]
	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES
        percentiles_to_measure = PERCENTILES_TO_MEASURE
	end 
    graph_sizes = [nextpow(2,size) for size in graph_sizes]
    start_seed = 453923
 

    #return parallel_forest_fire_stats(testing, save_output, graph_sizes, burn_ps, percentiles_to_measure, trials, start_seed)

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("trials",trials),
        ("degree_bins",log_iter_bins(maximum(graph_sizes))),
        ("percentiles_to_measure",percentiles_to_measure),
    ])

    parameters = enumerate(product( 
                           repeat([(start_seed, percentiles_to_measure,maximum(graph_sizes))],trials), # constant parameters
                                    graph_sizes)) # varying parameters

    if ONLY_GENERATE_GRAPHS
        pmap(curried_stats_graph_generation(RMAT()), parameters)
    else 
        parallel_graph_stats!(RMAT(),percentiles_to_measure,maximum(graph_sizes),result_dict, parameters)

        if save_output
            filename = filter(x->!isspace(x),"RMAT_maxDegRun_percentiles:$(percentiles_to_measure)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            save_output_to_json(testing, filename, result_dict)
        end
    end

    return result_dict
end



function parallel_graph_stats!(graph_type::Graph,percentiles_to_measure::Vector{Int},max_bin_size,result_dict, parameters)

    seeds = Array{Int,length(size(parameters))}(undef,size(parameters)...)
    lcc_sizes = Array{Int,length(size(parameters))}(undef, size(parameters)...)
    normalized_λ₂ = Array{Float64,length(size(parameters))}(undef, size(parameters)...)
    A_non_zeros = Array{Int,length(size(parameters))}(undef, size(parameters)...)
    A²_non_zeros = Array{Int,length(size(parameters))}(undef, size(parameters)...)
    mat_gen_times = Array{Float64,length(size(parameters))}(undef, size(parameters)...)
    max_degrees = Array{Float64,length(size(parameters))}(undef, size(parameters)...)

    #                                    # TODO: make this more robust?
    #percentiles_to_measure::Vector{Int} = last(first(last(first(parameters))))
    bins = log_iter_bins(max_bin_size)
    degree_stats = Array{Float64,length(size(parameters)) + 1}(undef,length(bins)-1,size(parameters)...)
    max_bfs_dist_stats = Array{Float64,length(size(parameters)) + 1}(undef,length(percentiles_to_measure),size(parameters)...)

    data_output = zip(eachslice(degree_stats,dims=Tuple(2:length(size(parameters))+1)),
                      eachslice(max_bfs_dist_stats,dims=Tuple(2:length(size(parameters))+1)))
    exp_output = pmap(curried_graph_stats(graph_type), parameters)
    for (i,((degree_stats_output, max_bfs_dist_stats_output), (seed_used, mat_gen_time, lcc_size, λ₂, A_nnz, A²_nnz, max_degree, degree_stats,  max_bfs_stats))) in enumerate(zip(data_output,exp_output))
        seeds[i] = seed_used
        lcc_sizes[i] = lcc_size
        normalized_λ₂[i] = λ₂
        A_non_zeros[i] = A_nnz
        A²_non_zeros[i] = A²_nnz
        mat_gen_times[i] = mat_gen_time
        max_degrees[i] = max_degree
        degree_stats_output .= degree_stats
        max_bfs_dist_stats_output .= max_bfs_stats
    end 

    # -- add computed values to output dictionary. 
    if typeof(graph_type) <: RandomGraph
        result_dict["seeds"] = seeds
    end

    result_dict["largest_connected_component"] = lcc_sizes 
    result_dict["matrix_generation_times"] = mat_gen_times
    result_dict["normalized_lambda2"] = normalized_λ₂
    result_dict["non_zeros"] = A_non_zeros
    result_dict["2_hop_non_zeros"] = A²_non_zeros
    result_dict["max_degrees"] = max_degrees
    result_dict["degree_stats"] = degree_stats
    result_dict["max_bfs_dist_stats"] = max_bfs_dist_stats # TODO: Instead of percentiles on the max,
                                                           #       return percentiles of bfs dists.  
                                                           #       Cite: https://snap.stanford.edu/snappy/doc/reference/GetBfsEffDiam.html
end 


function curried_stats_graph_generation(graph_type::Graph)
	return args->curried_stats_graph_generation(graph_type, args) 
end 


# curried function for workers
@everywhere function curried_stats_graph_generation(graph_type::RandomGraph, args)
	(seed_offset,((seed_start, percentiles_to_measure, max_bin_size), graph_args...)) = args
    filename = RANDOM_GRAPHS*file_name(graph_type, seed_start + seed_offset, graph_args...)
    if !isfile(filename)
        generate_random_graph(graph_type, seed_start + seed_offset, graph_args...)
    else
        println("file:$(filename) already exists.")
    end
end 





function curried_graph_stats(graph_type::Graph)
    return args->curried_graph_stats(graph_type,args)
end 

#
#   Process Level Functions
#
@everywhere function curried_graph_stats(graph_type::FileIOGraph, args)
    (_,((percentiles_to_measure, max_bin_size), file)) = args
    graph_stats(percentiles_to_measure, max_bin_size, file)
end 

@everywhere function curried_graph_stats(graph_type::RandomGraph,args)
    (seed_offset,((seed_start, percentiles_to_measure, max_bin_size), graph_args...)) = args
    graph_stats(percentiles_to_measure, max_bin_size,
                graph_type, seed_start + seed_offset,graph_args...)
end 


@everywhere function graph_stats(percentiles_to_measure, max_bin_size,
                                 random_graph_args...)
    (A, seed_used), mat_gen_t = @timed generate_random_graph(random_graph_args...)
    A = sparse(A) # convert to sparseCSC
    return seed_used, mat_gen_t, graph_stats(percentiles_to_measure,max_bin_size, A)...

end 

@everywhere function graph_stats(percentiles_to_measure, max_bin_size, graph_file::String)
    #load in graph 
    A, load_t = @timed load_graph(graph_file)
    #(A, seed_used), mat_gen_t = @timed generate_random_graph(random_graph_args...)
    #A = sparse(A) # convert to sparseCSC
    return -1, load_t, graph_stats(percentiles_to_measure, max_bin_size, A)...
end 


@everywhere function graph_stats(percentiles_to_measure, max_bin_size, A)
    # expecting the input graph to be undirected 

    _, in_lcc_q = largest_component(A)
    lcc_size = sum(in_lcc_q)

    #vecs_n_vals = symeigs(A,2;which=:LM,maxiter=1000)
    #normalized_λ₂ = minimum(vecs_n_vals.values)/maximum(vecs_n_vals.values)
    normalized_λ₂ = Inf
    
    max_bfs_stats  = Vector{Float64}(undef,length(percentiles_to_measure))
    max_bfs_dists = [maximum(first(bfs(A,rand(1:size(A,1))))) for i = 1:2] # NOTE: lowered so i can get the max_degree estimates faster
    for (i,p) in enumerate(percentiles_to_measure)
        max_bfs_stats[i] = percentile(max_bfs_dists,p)
    end 

    bins = log_iter_bins(max_bin_size)
    degrees = [get_undirected_degree(A,i) for i = 1:size(A,1)]
    degree_stats = fit(Histogram,degrees,bins).weights

    return lcc_size, normalized_λ₂, nnz(A), nnz(A*A), maximum(degrees), degree_stats,  max_bfs_stats
end 
