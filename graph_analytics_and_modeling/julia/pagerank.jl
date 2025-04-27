using Distributed 
@everywhere include("graph_generators.jl") # loads "shared.jl"
@everywhere using StatsBase: sample, fit, Histogram, percentile,  median 
@everywhere using LinearAlgebra: norm, normalize, normalize!
using Base.Iterators: product


GRAPH_SIZES = [2^scale for scale in 8:24]
TRIALS = 10
EPSILONS = [-1.0]
            # negative numbers scale epsilon by the size of the graph
            # so -1 corresponds to ε = 1/n .

ONLY_GENERATE_GRAPHS = false
    # NOTE: setting this to true allows the routines to generate and save the random 
    #       graphs, and then they can be loaded again for additional experiments.



#  --  TLDR Driver  --  #

function run_all_pagerank_experiments(only_test=true, save_output=true)

    if only_test
        modes_to_run = (true)
    else
        modes_to_run = (true,false)
    end

    # run test trials to make sure that results will run & save 
    for (testing) in modes_to_run
        erdos_renyi_pagerank(testing,save_output,false)
        RMAT_pagerank(testing,save_output)
        network_file_pagerank(testing,save_output)
        forest_fire_pagerank(testing,save_output)
    
    end
end 



#
#    Experiment Drivers 
# 

function network_file_pagerank(testing::Bool, save_output::Bool)

    if testing 
        files = [SNAP_GRAPHS*"web-Google.txt"]
        #files = ["/p/mnt/data/kloster-graphs/hollywood-2009.mat"]
        file_abbreviations = ["web-Google"]
        epsilons = [-1.0]
	else
        #= 
        files = SNAP_GRAPHS .* readdir(SNAP_GRAPHS)    
        append!(files,UDSNAP_GRAPHS .* readdir(UDSNAP_GRAPHS))
        =#
        files = UDSNAP_GRAPHS .* [
			"cit-Patents.txt",	
			"com-lj.ungraph.txt",
			"com-youtube.ungraph.txt",
			"flickrEdges.txt",
			"web-Google.txt",
		]

        file_abbreviations = first.(split.(replace.(last.(split.(files,"/")),"_"=>":"),"."))
		push!(files,RANDOM_GRAPHS*"er_dAvg:35_n:1048576_seed:98674.smat")
        push!(file_abbreviations, "ER (n=2^20 dAvg=35)")
		push!(files,RANDOM_GRAPHS*"rmat_n:1048576_seed:454044.smat")
        push!(file_abbreviations, "RMAT (n=2^20)")
		push!(files,RANDOM_GRAPHS*"forestFire_burnP:0.4_n:1048576_seed:16755.smat")
        push!(file_abbreviations, "FF (n=2^20 p=.4)")

        #file_abbreviations = first.(split.(replace.(last.(split.(files,"/")),"_"=>":"),"."))
        epsilons = EPSILONS
	end
    @assert length(file_abbreviations) == length(files)
	
    result_dict = Dict{String,Any}([
        # experiment params 
		("graph_files",files),
		("file_abbreviations",file_abbreviations),
        ("epsilons",epsilons),
    ])

    parameters = product(epsilons,files) # varying parameters
    parallel_pagerank_analysis!(FileIOGraph(), result_dict, parameters)

    if save_output
        filename = filter(x->!isspace(x),"PR_v2_savedGraphs_epsilons:$(epsilons)_numGraphs:$(length(files)).json")
        save_output_to_json(testing, filename, result_dict)
    end

    return result_dict

end 


function erdos_renyi_pagerank(testing::Bool, save_output::Bool, scale_ps::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [2^8,2^10,2^12]
        if !scale_ps 
            #edge_ps = [.4]
            avg_degree = Int[10,35]
        end
		# -- new params 
        #TODO: add in alphas? 
		epsilons = [-1.0]
		#percentile_ranges = [(.8,.9),(.9,1.0)]

	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES
        if !scale_ps 
            #edge_ps = [.3,.4,.5,.6,.7]
            avg_degree = Int[10,35]
        end
        epsilons = EPSILONS
	end 
    start_seed = 98423
 

    #return parallel_forest_fire_stats(testing, save_output, graph_sizes, burn_ps, percentiles_to_measure, trials, start_seed)

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("trials",trials),
		("epsilons",epsilons),
    ])
    if !scale_ps 
        #result_dict["edge_ps"] = edge_ps
        result_dict["average_degree"] = avg_degree
    end

    if scale_ps 
        parameters = enumerate(product( # constant parameters
								repeat([(start_seed)],trials),
                                       epsilons, graph_sizes)) # varying parameters
    else
        parameters = enumerate(product( # constant parameters
                                repeat([(start_seed)],trials),
                                        epsilons, graph_sizes, avg_degree)) # varying parameters
    end


    if ONLY_GENERATE_GRAPHS
        pmap(curried_pagerank_graph_generation(ErdosRenyi()), parameters)
    else 
        parallel_pagerank_analysis!(ErdosRenyi(),result_dict, parameters)
        
        if save_output
            if scale_ps 
                filename = filter(x->!isspace(x),"PR_v2_erdosReyni_epsilons:$(epsilons)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            else 
                filename = filter(x->!isspace(x),"PR_v2_erdosReyni_avgDegree:$(avg_degree)_epsilons:$(epsilons)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            end 
            save_output_to_json(testing, filename, result_dict)
        end
    end
    return result_dict
end

function forest_fire_pagerank(testing::Bool, save_output::Bool)
    
    if testing 
        trials = 1
        graph_sizes = [2^8,2^10,2^12]
        burn_ps = [.4,.5]
		# -- new params 
        #TODO: add in alphas? 
		epsilons = [-1.0]
		#percentile_ranges = [(.8,.9),(.9,1.0)]

	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES  
        burn_ps = [.4]
        epsilons = EPSILONS
	end 
    start_seed = 453923
 

    #return parallel_forest_fire_stats(testing, save_output, graph_sizes, burn_ps, percentiles_to_measure, trials, start_seed)

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
        ("burn_ps",burn_ps),
		("trials",trials),
		("epsilons",epsilons),
    ])

    #parameters = enumerate(product( # constant parameters
    #                        repeat([(ForestFire(), start_seed, percentiles_to_measure)],trials),
    #                               graph_sizes, burn_ps)) # varying parameters
   
    parameters = enumerate(product( # constant parameters
                                  repeat([(start_seed)],trials),
                                          epsilons, graph_sizes, burn_ps)) # varying parameters

    if ONLY_GENERATE_GRAPHS
        pmap(curried_pagerank_graph_generation(ForestFire()), parameters)
    else 
        parallel_pagerank_analysis!(ForestFire(),result_dict, parameters)
        
        if save_output
            filename = filter(x->!isspace(x),"PR_v2_forestFire_epsilons:$(epsilons)_p:$(burn_ps)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            save_output_to_json(testing, filename, result_dict)
        end
    end
    return result_dict
end

function RMAT_pagerank(testing::Bool, save_output::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [2^8,2^10,2^12]
		# -- new params 
        #TODO: add in alphas? 
		epsilons = [-1.0]
	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES  
        epsilons = EPSILONS
	end 
    #graph_sizes = [nextpow(2,size) for size in graph_sizes]
    start_seed = 453923
 

    #return parallel_forest_fire_stats(testing, save_output, graph_sizes, burn_ps, percentiles_to_measure, trials, start_seed)

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("trials",trials),
		("epsilons",epsilons),
    ])

    parameters = enumerate(product( # constant parameters
                                  repeat([(start_seed)],trials),
                                          epsilons, graph_sizes)) # varying parameters


    if ONLY_GENERATE_GRAPHS
        pmap(curried_pagerank_graph_generation(RMAT()), parameters)
    else 
        parallel_pagerank_analysis!(RMAT(),result_dict, parameters)
        
        if save_output
            filename = filter(x->!isspace(x),"PR_v2_RMAT_epsilons:$(epsilons)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
            save_output_to_json(testing, filename, result_dict)
        end
    end
    return result_dict
end


#  -- Shared Drivers -- # 

function parallel_pagerank_analysis!(graph_type::Graph, result_dict, parameters)



    num_algorithms = 6

    x_read_sums = Array{Int}(undef,num_algorithms,size(parameters)...)
    r_read_sums = Array{Int}(undef,num_algorithms,size(parameters)...)
    d_read_sums = Array{Int}(undef,num_algorithms,size(parameters)...)
    x_write_sums  = Array{Int}(undef,num_algorithms,size(parameters)...)
    r_write_sums  = Array{Int}(undef,num_algorithms,size(parameters)...)
                    #matrices contain all vertex level counts for each algorithm
    
    seeds =  Array{Int}(undef,size(parameters)...)
    mat_gen_times = Array{Float64}(undef,size(parameters)...)
    runtime_output = Array{Float64}(undef,num_algorithms, size(parameters)...)
    active_set_sizes_output  = Array{Vector{Int}}(undef,num_algorithms,size(parameters)...)
    active_set_volumes_output  = Array{Vector{Int}}(undef,num_algorithms,size(parameters)...)

    data_output = zip(
        eachslice(x_read_sums,dims=Tuple(2:length(size(parameters))+1)),
        eachslice(r_read_sums,dims=Tuple(2:length(size(parameters))+1)),
        eachslice(d_read_sums,dims=Tuple(2:length(size(parameters))+1)),
        eachslice(x_write_sums,dims=Tuple(2:length(size(parameters))+1)),
        eachslice(r_write_sums,dims=Tuple(2:length(size(parameters))+1)),
        eachslice(runtime_output,dims=Tuple(2:length(size(parameters))+1)),
        eachslice(active_set_sizes_output,dims=Tuple(2:length(size(parameters))+1)),
        eachslice(active_set_volumes_output,dims=Tuple(2:length(size(parameters))+1)),
    )
    
	exp_output = pmap(curried_pagerank_analysis(graph_type), parameters)
    
	for (i,((x_reads_output, r_reads_output, d_reads_output, x_writes_output, r_writes_output, runtime_output, active_set_size_output, active_set_volumes_output),
		    (seed_used, mat_gen_time, x_reads, r_reads, d_reads, x_writes, r_writes, runtimes, active_set_sizes,active_set_volumes))) in enumerate(zip(data_output,exp_output))

            seeds[i] = seed_used
			mat_gen_times[i] = mat_gen_time

            x_reads_output .= x_reads
            r_reads_output .= r_reads
            d_reads_output .= d_reads
            x_writes_output .= x_writes
            r_writes_output .= r_writes
            runtime_output .= runtimes 
            active_set_size_output .= active_set_sizes
            active_set_volumes_output .= active_set_volumes
	end 

	# -- add computed values to output dictionary. 
	result_dict["seeds"] = seeds
	result_dict["x_read_sums"] = x_read_sums
	result_dict["r_read_sums"] = r_read_sums
	result_dict["d_read_sums"] = d_read_sums
	result_dict["x_write_sums"] = x_write_sums
    result_dict["r_write_sums"] = r_write_sums  
	result_dict["mat_gen_times"] =  mat_gen_times
    result_dict["active_set_sizes"] =  active_set_sizes_output
    result_dict["active_set_volumes"] =  active_set_volumes_output
    result_dict["runtimes"] = runtime_output
    result_dict["algorithms"] = ["Topological", "Data-Driven", "Push Based","Pull Push Based","Adaptive Data-Driven","Adaptive Push"]
end 

# curried function for spawner
function curried_pagerank_analysis(graph_type::Graph)
	return args->curried_pagerank_analysis(graph_type, args) 
end 

# curried function for workers
@everywhere function curried_pagerank_analysis(graph_type::RandomGraph, args)
	(seed_offset,((seed_start), ε, graph_args...)) = args

	return pagerank_analysis(ε, graph_type, seed_start + seed_offset, graph_args...)
end 

@everywhere function curried_pagerank_analysis(graph_type::FileIOGraph, args)
	(ε,file) = args
    
    A,load_t = @timed load_graph(file)
    if ε == -1.0 #TODO: not a great solution. Need to rethink how the graphs are
        #      seeded so seed it tied to the experiment parameter and maybe process id (% NPROCS)?
        ε = 1.0/size(A,1)
    end
	return -1, load_t, pagerank_analysis(A,MatrixNetwork(A),ε)...
end 

@everywhere function pagerank_analysis(ε::Float64, graph_args...)
	(A, seed_used), mat_gen_t = @timed generate_random_graph(graph_args...)

    if ε == -1.0 #TODO: not a great solution. Need to rethink how the graphs are
        #      seeded so seed it tied to the experiment parameter and maybe process id (% NPROCS)?
        ε = 1.0/size(A,1)
    end
	return seed_used, mat_gen_t, pagerank_analysis(sparse(A),A,ε)...
end 

@everywhere function pagerank_analysis(A_col::SparseMatrixCSC, A_row::MatrixNetwork, ε::Float64)
    α = .85 #TODO: make variable? 

    num_algorithms = 6 #TODO: is there a better way of updating the number of algorithms reported?
    x_read_sums = Vector{Int}(undef,num_algorithms)
    d_read_sums = Vector{Int}(undef,num_algorithms)
    r_read_sums = Vector{Int}(undef,num_algorithms)
    x_write_sums = Vector{Int}(undef,num_algorithms)
    r_write_sums = Vector{Int}(undef,num_algorithms)

    all_active_set_sizes = Vector{Vector{Int}}(undef,num_algorithms)
    all_active_set_volumes = Vector{Vector{Int}}(undef,num_algorithms)
    runtimes = Vector{Float64}(undef,num_algorithms)


    for algo_idx = 1:num_algorithms
        # all experiments have `data_tracking` and `runtime` functions. 
        #    data_tracking _ -> (x_read, r_read_sum, d_read_sum, x_write_sum, r_write_sum, active_set_sizes, active_set_volumes)

        # TODO: does julia have a case statement
        if algo_idx == 1 # Topological (standard) P.R.
            data_tracking_experiment = ()->begin 
                    _, x_reads, d_reads, x_write_s,active_set_sizes, active_set_volumes = topology_driven_pagerank_tracked(A_col,α, ε);
                    return sum(x_reads), 0, sum(d_reads), sum(x_write_s), 0 ,active_set_sizes, active_set_volumes;
                end                    # r_read_sum                     # r_write_sum
            runtime_experiment = ()->(@timed topology_driven_pagerank(A_col,α, ε)).time
        elseif algo_idx == 2 # Data Driven (active sets) P.R.
            data_tracking_experiment = ()->begin 
                    _, x_reads, d_reads, x_write_s, active_set_sizes, active_set_volumes = data_driven_pagerank_tracked(A_col,α, ε);
                    return sum(x_reads), 0, sum(d_reads), sum(x_write_s), 0, active_set_sizes, active_set_volumes;
                end                    # r_read_sum                     # r_write_sum
            runtime_experiment = ()->(@timed data_driven_pagerank(A_col,α, ε)).time
        elseif algo_idx == 3 #  -- Push Based Data-Driven
            data_tracking_experiment = ()->begin 
                    _, x_reads, r_reads, d_reads, x_writes, r_writes, active_set_sizes, active_set_volumes = push_based_pagerank_tracked(A_col,A_row,α, ε);
                    return sum(x_reads), sum(r_reads), sum(d_reads), sum(x_writes), sum(r_writes), active_set_sizes, active_set_volumes;
                end
            runtime_experiment = ()->(@timed push_based_pagerank(A_col,A_row,α, ε)).time
        elseif algo_idx == 4 #  -- Pull Push Based Data-Driven
            data_tracking_experiment = ()->begin 
                    _, x_reads, r_reads, d_reads, x_writes, r_writes, active_set_sizes, active_set_volumes = pull_push_based_pagerank_tracked(A_col,A_row,α, ε);
                    return sum(x_reads), sum(r_reads), sum(d_reads), sum(x_writes), sum(r_writes), active_set_sizes, active_set_volumes;
                end 
            runtime_experiment = ()->(@timed pull_push_based_pagerank(A_col,A_row,α, ε)).time
        elseif algo_idx == 5 #  -- Adaptive Data-Driven (Sharp P.R.)
            data_tracking_experiment = ()->begin 
                    _, x_reads, d_reads, x_write_s, active_set_sizes, active_set_volumes= adaptive_data_driven_pagerank_tracked(A_col, α, ε)
                    return sum(x_reads), 0, sum(d_reads), sum(x_write_s), 0, active_set_sizes, active_set_volumes
                end                    # r_read_sum                     # r_write_sum
            runtime_experiment = ()->(@timed adaptive_data_driven_pagerank(A_col,α, ε)).time
        elseif algo_idx == 6 #   -- Adaptive Push Data-Driven
            data_tracking_experiment = ()->begin 
                    _, x_reads, r_reads, d_reads, x_writes, r_writes, active_set_sizes, active_set_volumes = adaptive_push_based_pagerank_tracked(A_col,A_row,α, ε)
                    return sum(x_reads), sum(r_reads), sum(d_reads), sum(x_writes), sum(r_writes), active_set_sizes, active_set_volumes;
                end
            runtime_experiment = ()->(@timed adaptive_push_based_pagerank(A_col,A_row,α, ε)).time
        end 
        # -- run the experiment drivers
        x_read_sums[algo_idx], d_read_sums[algo_idx], r_read_sums[algo_idx], 
           x_write_sums[algo_idx], r_write_sums[algo_idx], all_active_set_sizes[algo_idx], 
           all_active_set_volumes[algo_idx] = data_tracking_experiment()
        runtimes[algo_idx] = runtime_experiment()

    end 

    return x_read_sums, r_read_sums, d_read_sums, x_write_sums, r_write_sums, runtimes, all_active_set_sizes, all_active_set_volumes
end 

# 
#  -- drivers for just generating graphs 

# curried function for spawner
function curried_pagerank_graph_generation(graph_type::Graph)
	return args->curried_pagerank_graph_generation(graph_type, args) 
end 


# curried function for workers
@everywhere function curried_pagerank_graph_generation(graph_type::RandomGraph, args)
	(seed_offset,((seed_start), ε, graph_args...)) = args
    filename = RANDOM_GRAPHS*file_name(graph_type, seed_start + seed_offset, graph_args...)
    if !isfile(filename)
        generate_random_graph(graph_type, seed_start + seed_offset, graph_args...)
    else
        println("file:$(filename) already exists.")
    end
end 


#
#   Vanilla PageRank Routines 
#

# ---------------------------------------------------------------------------- #
#    Within the Pagerank Routines are some additional versions of pagerank that
#  were tested, but the functions relevant to results are 
#
#    - 'topology_driven_pagerank': a standard pagerank algorithm 
#    - 'data_driven_pagerank': pagerank which tracks an active set of vertices.
#
#  These functions are included so that the data included with our submission 
#  is able to be matched to the routines, though some experiment results were 
#  not used for our submission. 
# ---------------------------------------------------------------------------- #


@everywhere function topology_driven_pagerank(A, α::Float64, ε::Float64; verbose=false)

    n = size(A,1)
    x = Vector{Float64}(undef,n)
    x_new = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    iteration = 1
    while true 
        break_check = -Inf 
        for i = 1:n

            update = 0.0
            for j in get_undirected_neighbors(A,i)
                update += x[j]/get_undirected_degree(A,j)
            end
            update *= α
            update += (1-α)/n
            x_new[i] = update

            cur_check = abs(x[i] - update)
            if break_check < cur_check
                break_check = cur_check 
            end 
        end 
        
        #break_check = maximum(abs.(x_new .- x)) # NOTE: maximum is making allocations :/
        verbose && println("iter $(iteration): ||xₖ₊₁ - xₖ||∞ = $(break_check)")

        if break_check < ε
            break 
        else 
            x .= x_new
            iteration += 1 
        end 

    end 
    #normalize!(x_new,1)
    
    return x_new 
end 

@everywhere function data_driven_pagerank(A, α::Float64, ε::Float64; verbose=false)
    n = size(A,1)
    x = Vector{Float64}(undef,n)
    #x_new = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)
    vertices_still_active = true
    work_list = Vector{Bool}(undef,n); fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n); fill!(new_work_list,false);
    
    while vertices_still_active
        vertices_still_active = false  # reactivate when adding
                                       # node to next work_list 

        for i in filter(i->work_list[i], 1:n)
            update = 0.0
            for j in get_undirected_neighbors(A,i)
                update += x[j]/get_undirected_degree(A,j)
            end
            update *= α
            update += (1-α)/n

            update_check = abs(update - x[i])
            verbose && println("vᵢ = $(i): |xₖ₊₁[i] - xₖ[i]| = $(update_check) |work_list| = $(sum(work_list))")

            if update_check ≥ ε
                x[i] = update 
                for j in get_undirected_neighbors(A,i)
                    new_work_list[j] = true 
                    vertices_still_active = true 
                end     
            end 

        end 

        work_list .= new_work_list
        fill!(new_work_list,false)
    end 

    #=
    for each split
        # coalesce neighbors
        3 add (1-alpha)/n too... 
    end 
    =#

    return x 
end 

@everywhere function adaptive_data_driven_pagerank(A, α::Float64, ε::Float64; verbose=false)
    n = size(A,1)
    x = Vector{Float64}(undef,n)
    #x_new = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    work_list = Vector{Bool}(undef,n); #fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n); fill(new_work_list,false)
    cur_ε = 1e-1
    while cur_ε > ε
        vertices_still_active = true
        fill!(work_list,true)
        while vertices_still_active
            vertices_still_active = false  # reactivate when adding
                                        # node to next work_list 

            for i in filter(i->work_list[i], 1:n)
                
                update = 0.0
                for j in get_undirected_neighbors(A,i)
                    update += x[j]/get_undirected_degree(A,j)
                end
                update *= α
                update += (1-α)/n

                update_check = abs(update - x[i])
                verbose && println("vᵢ = $(i): |xₖ₊₁[i] - xₖ[i]| = $(update_check) |work_list| = $(length(work_list))")

                if update_check ≥ cur_ε
                    x[i] = update 
                    for j in get_undirected_neighbors(A,i) # TODO: add in neighbor reads?
                        new_work_list[j] = true 
                        vertices_still_active = true 
                    end     
                end 

            end 

            work_list .= new_work_list
            fill!(new_work_list,false)
        end 

        cur_ε /= 10 
    end
    #normalize!(x,1)
    return x
end 


@everywhere function push_based_pagerank(A::SparseMatrixCSC{T,Int}, α::Float64, ε::Float64; kwargs...) where T 
    push_based_pagerank(A, MatrixNetwork(A), α, ε; kwargs...)
end 

@everywhere function push_based_pagerank(A::MatrixNetwork{T}, α::Float64, ε::Float64; kwargs...) where T 
    push_based_pagerank(sparse(A), A, α, ε; kwargs...)
end 

@everywhere function push_based_pagerank(A_col::SparseMatrixCSC{T,Int},A_row::MatrixNetwork{T}, α::Float64, ε::Float64) where T 
                             #use both a SparseCSC and MatrixNetwork for fast row and column access. 
    n = size(A_col,1)
    x = Vector{Float64}(undef,n)
    r = Vector{Float64}(undef,n)
    
    connected_nodes = n
    fill!(x, (1-α)/connected_nodes)
    fill!(r, 0.0)

    work_list = Vector{Bool}(undef,n); fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n); fill!(new_work_list,false)
    

    #  -- Initialize residual vector
    
    for i = 1:n 
        for j in get_undirected_neighbors(A_col,i)
            r[i] += 1/get_undirected_degree(A_row,j)
        end 
        r[i] *= ((1-α)*α/connected_nodes)
    end 

    #println("zero residual values:$(sum(r .== 0.0)) isolated nodes:$(n - connected_nodes)")

    # -- Iterate over active set
    vertices_still_active = true
    while vertices_still_active
        vertices_still_active = false  # reactivate when adding
                                       # node to next work_list 

        for i in filter(i->work_list[i], 1:n)

            x[i] += r[i] #NOTE: line 14 in paper isn't being used as written
            for j in get_undirected_neighbors(A_row,i)
                r_old = r[j]
                r[j] += (r[i]*α) / get_undirected_degree(A_row,i)
                if r[j] ≥ ε && r_old < ε 
                    new_work_list[j] = true 
                    vertices_still_active = true 
                end 
            end
            r[i] = 0 
        end 
        work_list .= new_work_list
        fill!(new_work_list,false)
    end
    #normalize!(x,1)
    return x
end 

@everywhere function adaptive_push_based_pagerank(A::SparseMatrixCSC{T,Int}, α::Float64, ε::Float64; kwargs...) where T 
    adaptive_push_based_pagerank(A, MatrixNetwork(A), α, ε; kwargs...)
end 

@everywhere function adaptive_push_based_pagerank(A::MatrixNetwork{T}, α::Float64, ε::Float64; kwargs...) where T 
    adaptive_push_based_pagerank(sparse(A), A, α, ε; kwargs...)
end 

@everywhere function adaptive_push_based_pagerank(A_col::SparseMatrixCSC{T,Int},A_row::MatrixNetwork{T}, α::Float64, ε::Float64) where T 
                             #use both a SparseCSC and MatrixNetwork for fast row and column access. 
    n = size(A_col,1)
    x = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)
    r = Vector{Float64}(undef,n)
    

    all_εs = Vector{Float64}(undef,n)
    fill!(all_εs,1e-1)

    work_list = Vector{Bool}(undef,n); # <-- initilized in ε loop
    new_work_list = Vector{Bool}(undef,n); fill(new_work_list,false)
    
    #  -- Initialize residual vector
    fill!(r,0.0)
    for i = 1:n 
        for j in get_undirected_neighbors(A_col,i)
            r[i] += 1.0/get_undirected_degree(A_row,j)
        end 
        r[i] *= ((1-α) * α / n)
    end 

    # -- Iterate over active set

    while maximum(r) > ε # iterate over ε's 

        fill!(work_list,true)

        vertices_still_active = true
        while vertices_still_active
            vertices_still_active = false  # reactivate when adding
                                        # node to next work_list 

            for i in filter(i->work_list[i], 1:n)

                x[i] += r[i] #NOTE: line 14 in paper isn't being used as written
                for j in get_undirected_neighbors(A_row,i)
                    r_old = r[j]
                    r[j] += (r[i]*α) / get_undirected_degree(A_row,i)
                    
                    if r[j] ≥ all_εs[j]  && r_old < all_εs[j] 
                        new_work_list[j] = true 
                        vertices_still_active = true 
                    end 
                end
                r[i] = 0 
            end 
            work_list .= new_work_list
            fill!(new_work_list,false)
        end

        percentile_ε = percentile(r,10)
        fill!(all_εs, max(percentile_ε,ε))
    end 
    #normalize!(x,1)# normalize by L1 
    return x 
end 

@everywhere function pull_push_based_pagerank(A::SparseMatrixCSC{T,Int}, α::Float64, ε::Float64; kwargs...) where T 
    pull_push_based_pagerank(A, MatrixNetwork(A), α, ε; kwargs...)
end 

@everywhere function pull_push_based_pagerank(A::MatrixNetwork{T}, α::Float64, ε::Float64; kwargs...) where T 
    pull_push_based_pagerank(sparse(A), A, α, ε; kwargs...)
end 

@everywhere function pull_push_based_pagerank(A_col::SparseMatrixCSC{T,Int},A_row::MatrixNetwork{T}, α::Float64, ε::Float64) where T 
                             #use both a SparseCSC and MatrixNetwork for fast row and column access. 
    n::Int = size(A_col,1)
    x = Vector{Float64}(undef,n)
    r = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    work_list = Vector{Bool}(undef,n); fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n); fill!(new_work_list,false)
    

    #  -- Initialize residual vector
    fill!(r,0.0)
    for i = 1:n 
        for j in get_undirected_neighbors(A_col,i)
            r[i] += 1/get_undirected_degree(A_row,j)
        end 
        r[i] *= (1-α)*α/n
    end 

    # -- Iterate over active set
    vertices_still_active = true
    while vertices_still_active
        vertices_still_active = false  # reactivate when adding
                                       # node to next work_list 

        for i in filter(i->work_list[i], 1:n)
            update = 0.0
            for j in get_undirected_neighbors(A_col,i)        
                update += x[j] / get_undirected_degree(A_col,j)
            end
            update *= α 
            x[i] = update + (1 - α)/n
            
            for j in get_undirected_neighbors(A_row,i)
                r_j_old = r[j]
                r[j] += (r[i]*α)/get_undirected_degree(A_row,i)
                if r[j] ≥ ε && r_j_old < ε 
                    new_work_list[j] = true 
                    vertices_still_active = true
                end 
            end 
            r[i] = 0 
        end 

        work_list .= new_work_list
        fill!(new_work_list,false)
    end 
    #normalize!(x,1)
    return x
end 


function test_methods() 

    #=
    n = 1000
    seed!(1310)
    A = sprand(n,n,.1)
    A = max.(A,A')
    fill!(A.nzval,1.0);
    =#

    n = 2^10
    A = sparse(first(generate_random_graph(RMAT(),131231,n)))
    fill!(A.nzval,1.0)
    println("size(A,1):$(size(A,1)) -- A nnz:$(nnz(A))")

    ε = 1e-10
    α = .9999999

    # compare against MatrixNetwork's version 
    mn_A = MatrixNetwork(A)
    mn_x = MatrixNetworks.pagerank(mn_A, α, 1e-16)
    println("finished MatrixNetwork version")
    num_algos = 6
    pagerank_output = Matrix{Float64}(undef,size(A,1),num_algos)

    #TODO: replace current manual indexing with symbols?
    @time pagerank_output[:,1] = topology_driven_pagerank(A, α, ε)

    @time pagerank_output[:,2] = data_driven_pagerank(A, α, ε)
    @time pagerank_output[:,3] = adaptive_data_driven_pagerank(A, α, ε)
    
    @time pagerank_output[:,4] = push_based_pagerank(A, α, ε)
    @time pagerank_output[:,5] = adaptive_push_based_pagerank(A, α, ε)

    @time pagerank_output[:,6] = pull_push_based_pagerank(A, α, ε)
    #@time pagerank_output[:,7] = adaptive_pull_push_based_pagerank(A, α, ε)
    
    for (i,x) in enumerate(eachcol(pagerank_output))
        
        println("|--method $(i):$(norm(mn_x - x,1) <= ((n*ε)/(1-α)))")
        println("norm(mn_x - x,1):$(norm(mn_x - x,1))   sum(x):$(sum(x))")
        println("norm(mn_x - normalize(x,1),1):$(norm(mn_x - normalize(x,1),1))   sum(x):$(sum(x))")
        println("       norm(r,∞):$(maximum(abs.(compute_residual(A,x,α))))  --  norm(r,1):$(norm(compute_residual(A,x,α),1))")
        println("     (n*ε)/(1-α):$((n*ε)/(1-α)) -- n:$(n) - ε:$ε - α:$α")
        #@assert norm(mn_x - x,1) <= ((n*ε)/(1-α))
        @assert sum(x) <= 1 
        #println("method $(i) passed")
    end 

                                                                                            # output must be the same
    @assert norm(pagerank_output[:,1] - first(topology_driven_pagerank_tracked(A, α, ε)),1) == 0.0
    @assert norm(pagerank_output[:,2] - first(data_driven_pagerank_tracked(A, α, ε)),1) == 0.0
    @assert norm(pagerank_output[:,3] - first(adaptive_data_driven_pagerank_tracked(A, α, ε)),1) == 0.0
    @assert norm(pagerank_output[:,4] - first(push_based_pagerank_tracked(A, mn_A, α, ε)),1) == 0.0
    @assert norm(pagerank_output[:,5] - first(adaptive_push_based_pagerank_tracked(A,mn_A, α, ε)),1) == 0.0
    @assert norm(pagerank_output[:,6] - first(pull_push_based_pagerank_tracked(A,mn_A, α, ε)),1) == 0.0

    #tracked_pagerank_output = Matrix{Float64}(undef,size(A,1),4)
        
    #@assert norm(mn_x - x_topology) < n*ε/(1-α)
    #@assert norm(mn_x - x_data) < n*ε/(1-α)
    #@assert norm(mn_x - x_push) < n*ε/(1-α)
    #@assert norm(mn_x - x_pull_push) < n*ε/(1-α)




end 

function test_for_allocations() 

    n = 1000 
    A = sprand(n,n,.1)
    A = max.(A,A')
    mn_A = MatrixNetwork(A)
    ε = 1e-6
    α = .85

    topology_driven_pagerank(A, α, ε)
    data_driven_pagerank(A, α, ε)
    push_based_pagerank(A,mn_A, α, ε)
    pull_push_based_pagerank(A, mn_A, α, ε)
    adaptive_push_based_pagerank(A, mn_A, α, ε)
    
end 



#
#   Tracked PageRank Routines 
#


@everywhere function topology_driven_pagerank_tracked(A, α::Float64, ε::Float64; verbose=false)

    n = size(A,1)
    x = Vector{Float64}(undef,n)
    x_new = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    x_reads = zeros(Int,n)
    d_reads = zeros(Int,n)
    x_writes = zeros(Int,n)

    active_set_sizes = Int[n]
    active_set_volumes = Int[nnz(A)]

    iteration = 1
    while true 
        break_check = -Inf 
        for i = 1:n
            update = 0.0
            for j in get_undirected_neighbors(A,i)
                update += x[j]/get_undirected_degree(A,j)
                x_reads[j] += 1 
                d_reads[j] += 1 
            end
            update *= α
            update += (1-α)/n
            x_new[i] = update
            x_writes[i] += 1 
            cur_check = abs(x[i] - update)
            x_reads[i] + 1 
            if break_check < cur_check
                break_check = cur_check 
            end 
        end 
        
        #break_check = maximum(abs.(x_new .- x)) # NOTE: maximum is making allocations :/
        verbose && println("iter $(iteration): ||xₖ₊₁ - xₖ||∞ = $(break_check)")

        if break_check < ε
            break 
        else 
            x .= x_new
            x_writes .+= 1
            iteration += 1
            push!(active_set_sizes,n) # Every loop touches every node. Included 
                                      # here for data formatting consistency
            push!(active_set_volumes, nnz(A))
        end 

    end 
    return x_new, x_reads, d_reads, x_writes, active_set_sizes, active_set_volumes
end 

@everywhere function data_driven_pagerank_tracked(A, α::Float64, ε::Float64; verbose=false)
    n = size(A,1)
    x = Vector{Float64}(undef,n)
    #x_new = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    x_reads = zeros(Int,n)
    d_reads = zeros(Int,n)
    x_writes = zeros(Int,n)

    active_set_sizes = Int[n]
    active_set_volumes = Int[nnz(A)]

    vertices_still_active = true
    work_list = Vector{Bool}(undef,n); fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n); fill!(new_work_list,false)
    
    while vertices_still_active
        vertices_still_active = false  # reactivate when adding
                                       # node to next work_list 

        for i in filter(i->work_list[i], 1:n)
            
            update = 0.0
            for j in get_undirected_neighbors(A,i)
                update += x[j]/get_undirected_degree(A,j)
                x_reads[j] += 1
                d_reads[j] += 1  
            end
            update *= α
            update += (1-α)/n

            update_check = abs(update - x[i])
            x_reads[i] += 1
            verbose && println("vᵢ = $(i): |xₖ₊₁[i] - xₖ[i]| = $(update_check) |work_list| = $(length(work_list))")

            if update_check ≥ ε
                x[i] = update 
                x_writes[i] += 1 
                for j in get_undirected_neighbors(A,i) # TODO: add in neighbor reads?
                    new_work_list[j] = true 
                    vertices_still_active = true 
                end     
            end 

        end 

        work_list .= new_work_list
        fill!(new_work_list,false)
        active_vertices = sum(work_list)
        push!(active_set_sizes, active_vertices)
        push!(active_set_volumes, active_vertices > 0 ? sum(get_undirected_degree(A,i) for i in filter(i->work_list[i],1:n)) : 0)
        
    end 
    
    return x, x_reads, d_reads, x_writes, active_set_sizes, active_set_volumes
end 

@everywhere function push_based_pagerank_tracked(A_col::SparseMatrixCSC{T,Int},A_row::MatrixNetwork{T}, α::Float64, ε::Float64) where T 
                             #use both a SparseCSC and MatrixNetwork for fast row and column access. 
    n = size(A_col,1)
    x = Vector{Float64}(undef,n)
    r = Vector{Float64}(undef,n)

    fill!(x, (1-α)/n)
    fill!(r,0.0)

    x_reads = zeros(Int,n)
    r_reads = zeros(Int,n)
    d_reads = zeros(Int,n)
    x_writes = zeros(Int,n)
    r_writes = zeros(Int,n)

    active_set_sizes = Int[n]
    active_set_volumes = Int[nnz(A_col)]

    work_list = Vector{Bool}(undef,n); fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n); fill!(new_work_list,false)
    
    #  -- Initialize residual vector
    for i = 1:n 
        for j in get_undirected_neighbors(A_col,i)
            r[i] += 1/get_undirected_degree(A_row,j)
            d_reads[j] += 1 
        end 
        r[i] *= (1-α)*α/n
        r_writes[i] += 1  # NOTE: aggregating all writes as 1 bc we 
                          #       could use a accumulation variable
    end 

    # -- Iterate over active set
    vertices_still_active = true
    while vertices_still_active
        vertices_still_active = false  # reactivate when adding
                                       # node to next work_list 

        for i in filter(i->work_list[i], 1:n)

            x[i] += r[i] #NOTE: line 14 in paper isn't being used as written
            for j in get_undirected_neighbors(A_row,i)
                r_old = r[j]
                r[j] += (r[i]*α) / get_undirected_degree(A_row,i)
                
                r_reads[j] += 1 
                r_reads[i] += 1 
                d_reads[i] += 1 
                r_writes[j] += 1 
                if r[j] ≥ ε && r_old < ε 
                    new_work_list[j] = true 
                    vertices_still_active = true 
                end 
            end
            r[i] = 0 
            r_writes[i] += 1 
        end 
        work_list .= new_work_list
        fill!(new_work_list,false)
        active_vertices = sum(work_list)
        push!(active_set_sizes, active_vertices)
        push!(active_set_volumes, active_vertices > 0 ? sum(get_undirected_degree(A_col,i) for i in filter(i->work_list[i],1:n)) : 0)

    end
    return x, x_reads, r_reads, d_reads, x_writes, r_writes, active_set_sizes, active_set_volumes
end 

@everywhere function pull_push_based_pagerank_tracked(A_col::SparseMatrixCSC{T,Int},A_row::MatrixNetwork{T}, α::Float64, ε::Float64) where T 
                             #use both a SparseCSC and MatrixNetwork for fast row and column access. 
    n::Int = size(A_col,1)
    x = Vector{Float64}(undef,n)
    r = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    work_list = Vector{Bool}(undef,n); fill!(work_list,true);
    new_work_list = Vector{Bool}(undef,n); fill!(new_work_list,false);
    
    r_reads = zeros(Int,n)
    x_reads = zeros(Int,n)
    d_reads = zeros(Int,n)
    x_writes = zeros(Int,n)
    r_writes = zeros(Int,n)

    active_set_sizes = Int[n]
    active_set_volumes = Int[nnz(A_col)]

    #  -- Initialize residual vector
    fill!(r,0.0)
    for i = 1:n 
        for j in get_undirected_neighbors(A_col,i)
            r[i] += 1/get_undirected_degree(A_row,j)
            d_reads[j] += 1 
        end 
        r[i] *= (1-α)*α/n
        r_writes[i] += 1  # NOTE: aggregating all writes as 1 bc we 
                        #       could use a accumulation variable
    end 

    # -- Iterate over active set
    vertices_still_active = true
    while vertices_still_active
        vertices_still_active = false  # reactivate when adding
                                       # node to next work_list 

        for i in filter(i->work_list[i], 1:n)
            update = 0.0
            for j in get_undirected_neighbors(A_col,i)        
                update += x[j] / get_undirected_degree(A_col,j)
                x_reads[j] += 1
                d_reads[i] += 1 
            end
            update *= α 
            x[i] = update + (1 - α)/n
            x_writes[i] += 1 

            for j in get_undirected_neighbors(A_row,i)
                r_j_old = r[j]
                r_reads[j] += 1 
                r[j] += (r[i]*α)/get_undirected_degree(A_row,i)
                r_reads[i] += 1 
                r_writes[j] += 1 
                if r[j] ≥ ε && r_j_old < ε 
                    new_work_list[j] = true 
                    vertices_still_active = true
                end 
            end 
            r[i] = 0 
            r_writes[i] += 1 
        end 

        work_list .= new_work_list
        fill!(new_work_list,false)
        active_vertices = sum(work_list)
        push!(active_set_sizes, active_vertices)
        push!(active_set_volumes, active_vertices > 0 ? sum(get_undirected_degree(A_col,i) for i in filter(i->work_list[i],1:n)) : 0)
    end 
    return x, x_reads, r_reads, d_reads, x_writes, r_writes, active_set_sizes, active_set_volumes
end 

#  -- Adaptive Pagerank 
@everywhere function adaptive_data_driven_pagerank_tracked(A, α::Float64, ε::Float64; verbose=false)
    n = size(A,1)
    x = Vector{Float64}(undef,n)
    #x_new = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    x_reads = zeros(Int,n)
    d_reads = zeros(Int,n)
    x_writes = zeros(Int,n)

    active_set_sizes = Int[n]
    active_set_volumes = Int[nnz(A)]

    work_list = Vector{Bool}(undef,n); #fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n); fill(new_work_list,false)
    cur_ε = 1e-1
    while cur_ε > ε
        vertices_still_active = true
        fill!(work_list,true)
        while vertices_still_active
            vertices_still_active = false  # reactivate when adding
                                        # node to next work_list 

            for i in filter(i->work_list[i], 1:n)
                
                update = 0.0
                for j in get_undirected_neighbors(A,i)
                    update += x[j]/get_undirected_degree(A,j)
                    x_reads[j] += 1
                    d_reads[j] += 1  
                end
                update *= α
                update += (1-α)/n

                update_check = abs(update - x[i])
                x_reads[i] += 1
                verbose && println("vᵢ = $(i): |xₖ₊₁[i] - xₖ[i]| = $(update_check) |work_list| = $(length(work_list))")

                if update_check ≥ cur_ε
                    x[i] = update 
                    x_writes[i] += 1 
                    for j in get_undirected_neighbors(A,i) # TODO: add in neighbor reads?
                        new_work_list[j] = true 
                        vertices_still_active = true 
                    end     
                end 

            end 

            work_list .= new_work_list
            fill!(new_work_list,false)
            active_vertices = sum(work_list)
            push!(active_set_sizes, active_vertices)
            push!(active_set_volumes, active_vertices > 0 ? sum(get_undirected_degree(A,i) for i in filter(i->work_list[i],1:n)) : 0)
        end 

        cur_ε /= 10 
    end
    #normalize!(x,1)
    #x_reads .+= 1 
    #x_writes .+= 1 
    return x, x_reads, d_reads, x_writes, active_set_sizes, active_set_volumes
end 


@everywhere function adaptive_push_based_pagerank_tracked(A_col::SparseMatrixCSC{T,Int},A_row::MatrixNetwork{T}, α::Float64, ε::Float64) where T 
                             #use both a SparseCSC and MatrixNetwork for fast row and column access. 
    n = size(A_col,1)
    x = Vector{Float64}(undef,n)
    r = Vector{Float64}(undef,n)
    fill!(x, (1-α)/n)

    all_εs = Vector{Float64}(undef,n)
    fill!(all_εs,1e-1)

    x_reads = zeros(Int,n)
    r_reads = zeros(Int,n)
    d_reads = zeros(Int,n)
    x_writes = zeros(Int,n)
    r_writes = zeros(Int,n)

    active_set_sizes = Int[n]
    active_set_volumes = Int[nnz(A_col)]

    #cur_ε = 1e-1

    work_list = Vector{Bool}(undef,n); #fill!(work_list,true)
    new_work_list = Vector{Bool}(undef,n);fill!(new_work_list,false);
    
    #  -- Initialize residual vector
    fill!(r,0.0)
    for i = 1:n 
        for j in get_undirected_neighbors(A_col,i)
            r[i] += 1/get_undirected_degree(A_row,j)
            d_reads[j] += 1 
        end 
        r[i] *= ((1-α)*α/n)
        r_writes[i] += 1  # NOTE: aggregating all writes as 1 bc we 
                          #       could use a accumulation variable
    end 

    # -- Iterate over active set

    while maximum(r) > ε # iterate over ε's 

        fill!(work_list,true)

        vertices_still_active = true
        while vertices_still_active
            vertices_still_active = false  # reactivate when adding
                                        # node to next work_list 

            for i in filter(i->work_list[i], 1:n)

                x[i] += r[i] #NOTE: line 14 in paper isn't being used as written
                r_reads[i] += 1 
                x_writes[i] +=1 

                for j in get_undirected_neighbors(A_row,i)
                    r_old = r[j]
                    r[j] += (r[i]*α) / get_undirected_degree(A_row,i)
                    
                    d_reads[i] += 1 
                    r_reads[i] += 1 
                    r_reads[j] += 1 
                    r_writes[j] += 1 
                    
                    if r[j] ≥ all_εs[j]  && r_old < all_εs[j] 
                        new_work_list[j] = true 
                        vertices_still_active = true 
                    end 
                end
                r[i] = 0 
                r_writes[i] += 1 
            end 
            work_list .= new_work_list
            fill!(new_work_list,false)
            active_vertices = sum(work_list)
            push!(active_set_sizes, active_vertices)
            push!(active_set_volumes, active_vertices > 0 ? sum(get_undirected_degree(A_col,i) for i in filter(i->work_list[i],1:n)) : 0)
        end

        #cur_ε /= 10

        #println("med resid: $(median(r))")
        #println("25th percentile resid: $(percentile(r,25))")
        #println("total_active nodes:$(sum(work_list))")
        fill!(all_εs, max(percentile(r,10),ε))

    end 
    return x,  x_reads, r_reads, d_reads, x_writes, r_writes, active_set_sizes, active_set_volumes
end 



function compute_residual(A, x, α)
    r = x .- α .* A*[get_undirected_degree(A,i) > 1e-16 ? xᵢ/get_undirected_degree(A,i) : xᵢ for (i,xᵢ) in enumerate(x)]
        #(I - α⋅Pᵀ)x  = x - α⋅(AᵀD⁻¹)x  
    return (1-α)/size(A,1) .- r 
        # (1-α)/n⋅e - (I - α⋅Pᵀ)x 
end 