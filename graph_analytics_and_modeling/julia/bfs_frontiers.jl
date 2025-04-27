#include("shared.jl")
using Distributed 
@everywhere include("graph_generators.jl")

#using Random: seed!
@everywhere using StatsBase: sample
using Base.Iterators: product

GRAPH_SIZES = [2^scale for scale in 8:24]
TRIALS = 10 
PERCENTILE_RANGES = [(.001,1.0)]
SAMPLES = 100
ONLY_GENERATE_GRAPHS = true

#  --  TLDR Driver  --  #

function run_all_bfs_experiments(only_test=true, save_output=true)

    if only_test
        modes_to_run = (true)
    else
        modes_to_run = (true,false)
    end

    # run test trials to make sure that results will run & save 
    for (testing) in modes_to_run
        erdos_renyi_bfs(testing,save_output,false)
        RMAT_bfs(testing,save_output)
        file_with_specific_seeds_bfs(testing,save_output)
        forest_fire_bfs(testing,save_output)
    end
end 


function erdos_renyi_bfs(testing::Bool, save_output::Bool, scale_ps::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [100,1000]
        if !scale_ps 
			avg_degree = Int[10]
        end
		# -- new params 
		samples = 10
		percentile_ranges = [(.8,.9),(.9,1.0)]

	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES#,100000]
        if !scale_ps 
			avg_degree = Int[10,35]
        end
		samples = SAMPLES
		percentile_ranges = PERCENTILE_RANGES
	end 
    start_seed = 98423
 
    #return parallel_forest_fire_stats(testing, save_output, graph_sizes, burn_ps, percentiles_to_measure, trials, start_seed)

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("trials",trials),
		("samples",samples),
        ("percentile_ranges",percentile_ranges),
    ])
    if !scale_ps 
		result_dict["average_degree"] = avg_degree
    end

    #parameters = enumerate(product( # constant parameters
    #                        repeat([(ForestFire(), start_seed, percentiles_to_measure)],trials),
    #                               graph_sizes, burn_ps)) # varying parameters
   
    if scale_ps 
        parameters = enumerate(product( # constant parameters
								repeat([(start_seed, samples, percentile_ranges)],trials),
										graph_sizes)) # varying parameters

    else
        parameters = enumerate(product( # constant parameters
                                repeat([(start_seed, samples, percentile_ranges)],trials),
                                    	graph_sizes, avg_degree)) # varying parameters
    end

	if ONLY_GENERATE_GRAPHS
		pmap(curried_bfs_graph_generation(ErdosRenyi()), parameters)
	else 
		parallel_bfs_analysis!(ErdosRenyi(),result_dict, parameters)
		
		if save_output
			if scale_ps 
				filename = filter(x->!isspace(x),"BFS_erdosReyni_percentileRanges:$(percentile_ranges)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
			else 
				filename = filter(x->!isspace(x),"BFS_erdosReyni_avgDegree:$(avg_degree)_percentileRanges:$(percentile_ranges)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
			end 
			save_output_to_json(testing, filename, result_dict)
		end
	end
    return result_dict
end

function forest_fire_bfs(testing::Bool, save_output::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [100,1000]
		burn_ps = [.1,.2,.3]
		# -- new params 
		samples = 10
		percentile_ranges = [(.8,.9),(.9,1.0)]

	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES#,100000]
		burn_ps = [.4]
		samples = SAMPLES
		percentile_ranges = PERCENTILE_RANGES
	end 
    start_seed = 453923
 

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("trials",trials),
		("burn_ps",burn_ps),
		("samples",samples),
        ("percentile_ranges",percentile_ranges),
    ])

	parameters = enumerate(product( # constant parameters
							repeat([(start_seed, samples, percentile_ranges)],trials),
									graph_sizes, burn_ps)) # varying parameters

	if ONLY_GENERATE_GRAPHS
		pmap(curried_bfs_graph_generation(ForestFire()), parameters)
	else 
		parallel_bfs_analysis!(ForestFire(),result_dict, parameters)
		
		if save_output
			filename = filter(x->!isspace(x),"BFS_forestFires_p:$(burn_ps)_percentileRanges:$(percentile_ranges)_samples:$(samples)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
			save_output_to_json(testing, filename, result_dict)
		end
	end
    return result_dict
end

function RMAT_bfs(testing::Bool, save_output::Bool)
    
    if testing 
        trials = 4
        graph_sizes = [100,1000]
		# -- new params 
		samples = 10
		percentile_ranges = [(.8,.9),(.9,1.0)]

	else
        trials = TRIALS
        graph_sizes = GRAPH_SIZES#,100000]
		samples = SAMPLES
		percentile_ranges = PERCENTILE_RANGES
	end 
	graph_sizes = [nextpow(2,size) for size in graph_sizes]
    start_seed = 453923
 

    result_dict = Dict([
        # experiment params 
		("graph_sizes",graph_sizes),
		("trials",trials),
		("samples",samples),
        ("percentile_ranges",percentile_ranges),
    ])

	parameters = enumerate(product( # constant parameters
							repeat([(start_seed, samples, percentile_ranges)],trials),
									graph_sizes)) # varying parameters

	if ONLY_GENERATE_GRAPHS
		pmap(curried_bfs_graph_generation(RMAT()), parameters)
	else 
		parallel_bfs_analysis!(RMAT(),result_dict, parameters)
		
		if save_output
			filename = filter(x->!isspace(x),"BFS_RMAT_percentileRanges:$(percentile_ranges)_samples:$(samples)_sizes:$(graph_sizes)_startSeed:$(start_seed)_trials:$(trials).json")
			save_output_to_json(testing, filename, result_dict)
		end
	end
    return result_dict
end


function file_with_specific_seeds_bfs(testing::Bool,save_output::Bool)

	graph_fldr = SNAP_GRAPHS

    if testing 
        files = [graph_fldr*"web-Google.txt"]
        #files = ["/p/mnt/data/kloster-graphs/hollywood-2009.mat"]
        file_abbreviations = ["web-Google"]
		start_vertices = [10]

	else
        files = graph_fldr .* [
			"cit-Patents.txt",	
			"com-lj.ungraph.txt",
			"com-youtube.ungraph.txt",
			"flickrEdges.txt",
			"web-Google.txt",
		]
		push!(files,RANDOM_GRAPHS*"er_dAvg:35_n:1048576_seed:98674.smat")
		push!(files,RANDOM_GRAPHS*"rmat_n:1048576_seed:454044.smat")
		push!(files,RANDOM_GRAPHS*"forestFire_burnP:0.4_n:1048576_seed:16755.smat")

        file_abbreviations = [
			"cit-Patents",
			"com-lj",
			"com-youtube",
			"flickr",
			"web-Google",
			"ER",
			"RMAT",
			"FF",
		]
		
		start_vertices = [
			3858241,
			0,
			5,
			141396276,
			11342,
			1,
			1,
			1,
		]
		start_vertices .+= 1 #start vertices are incremented by 1 from what Ivy told me
							 # bc she's using Python.
			 
	end
    @assert length(file_abbreviations) == length(files)
	@assert length(start_vertices) == length(files)

	vertex_counts = Vector{Int}(undef,length(files))
	edge_counts = Vector{Int}(undef,length(files))
	unreachable_vertices = zeros(Int,length(files))
	reachability = Array{Vector{Int}}(undef,length(files))
	total_frontier_edgecount = Array{Vector{Int}}(undef,length(files))
	forward_frontier_edgecount = Array{Vector{Int}}(undef,length(files))


	for (i,(file, start_vertex)) in enumerate(zip(files, start_vertices))
		A =@time load_graph(file)

		vertex_counts[i] = size(A,1)
		edge_counts[i] = nnz(A)

		(d,_,_) = @time bfs(A,start_vertex)
		reachability[i] = zeros(Int,maximum(d))

		for v_i = 1:length(d)
			if d[v_i] == -1 
				unreachable_vertice[i] += 1 
			elseif d[v_i] == 0 
				continue
			else
				reachability[i][d[v_i]] += 1 
			end
		end 
		total_frontier_edgecount[i],forward_frontier_edgecount[i] = @time forward_vs_total(A,d)
	end 

    filename = filter(x->!isspace(x),RESULTS_LOC*"/BFS_fromSpecificSeeds_networks:$(join(file_abbreviations,"-")).json")
   
	result_dict = Dict([
		("edge_counts",edge_counts),
		("vertex_counts",vertex_counts),
		("unreachable_vertices",unreachable_vertices),
		("reachability",reachability),
		("total_frontier_edgecount",total_frontier_edgecount), 
		("forward_frontier_edgecount",forward_frontier_edgecount),
		("files",files),
		("start_vertices (indexed by 1)",start_vertices),
	])

	if save_output
        open(filename,"w") do f
            JSON.print(f,result_dict)
        end
    end

	return result_dict
end 



#  -- Shared Experiment Routines -- # 

function parallel_bfs_analysis!(graph_type::Graph,result_dict, parameters)

	#TODO: make more robust? 
	_, samples, percentile_ranges = first(last(first(parameters)))

	unreachable_nodes = zeros(Int,length(percentile_ranges),samples,size(parameters)...)
	
	#seed_nodes = zeros(Int,length(scales),trials,length(percentile_ranges),samples)
	reachability = Array{Vector{Int}}(undef,length(percentile_ranges),samples,size(parameters)...)
	total_frontier_edgecount = Array{Vector{Int}}(undef,length(percentile_ranges),samples,size(parameters)...)
	forward_frontier_edgecount = Array{Vector{Int}}(undef,length(percentile_ranges),samples,size(parameters)...)

	seeds =  Array{Int}(undef,size(parameters)...)
	vertex_counts = Array{Int}(undef,size(parameters)...)
	edge_counts = Array{Int}(undef,size(parameters)...)
	mat_gen_times = Array{Float64}(undef,size(parameters)...)

	data_output = zip(
		eachslice(unreachable_nodes,dims=Tuple(3:length(size(parameters))+2)),
		eachslice(reachability,dims=Tuple(3:length(size(parameters))+2)),
		eachslice(total_frontier_edgecount,dims=Tuple(3:length(size(parameters))+2)),
		eachslice(forward_frontier_edgecount,dims=Tuple(3:length(size(parameters))+2)),
	)
	exp_output = pmap(curried_bfs_frontier_analysis(graph_type), parameters)
    
	for (i,((unreachable_nodes_output,reachability_output,total_frontier_edgecount_output,forward_frontier_edgecount_output), 
		    (seed_used, mat_gen_time, vertices, edges, unreachable_nodes, reachability, total_frontier_edgecount, forward_frontier_edgecount))) in enumerate(zip(data_output,exp_output))
			seeds[i] = seed_used
			mat_gen_times[i] = mat_gen_time
			vertex_counts[i] = vertices
			edge_counts[i] = edges 
			unreachable_nodes_output .= unreachable_nodes
			reachability_output .= reachability
			total_frontier_edgecount_output .= total_frontier_edgecount
			forward_frontier_edgecount_output .= forward_frontier_edgecount
	end 

	# -- add computed values to output dictionary. 
	result_dict["seeds"] = seeds
	result_dict["lcc_edge_counts"] = edge_counts
	result_dict["lcc_vertex_counts"] = vertex_counts
	result_dict["unreachable_nodes"]= unreachable_nodes
	result_dict["reachability"] = reachability
	result_dict["total_frontier_edgecount"] = total_frontier_edgecount 
	result_dict["forward_frontier_edgecount"] = forward_frontier_edgecount

end 

# curried function for spawner
function curried_bfs_frontier_analysis(graph_type::Graph)
	return args->curried_bfs_frontier_analysis(graph_type, args) 
end 

# curried function for workers
@everywhere function curried_bfs_frontier_analysis(graph_type::RandomGraph, args)
	(seed_offset,((seed_start, samples, percentile_ranges), graph_args...)) = args
	return bfs_frontier_analysis(samples, percentile_ranges,
							     graph_type, seed_start + seed_offset, graph_args...
	)
end 

@everywhere function bfs_frontier_analysis(samples, percentile_ranges, graph_args...)
	(A, seed_used),mat_gen_t = @timed generate_random_graph(graph_args...)
	A, _ = largest_component(sparse(A))
	return seed_used, mat_gen_t, size(A,1), nnz(A), bfs_frontier_analysis(MatrixNetwork(A),percentile_ranges,samples)...
end 

@everywhere function curried_bfs_frontier_analysis(graph_type::FileIOGraph, args)
	((samples, percentile_ranges),file) = args
    A,load_t = @timed load_graph(file)
	return -1, load_t, bfs_frontier_analysis(A,percentile_ranges,samples)...
end 

@everywhere function bfs_frontier_analysis(A,percentile_ranges,samples)

    sampled_vertices = sample_degree_percentiles(A,percentile_ranges,samples)

    unreachable_nodes = zeros(Int,length(percentile_ranges),samples)
	reachability = Array{Vector{Int}}(undef,length(percentile_ranges),samples)
	total_frontier_edgecount = Array{Vector{Int}}(undef,length(percentile_ranges),samples)
	forward_frontier_edgecount = Array{Vector{Int}}(undef,length(percentile_ranges),samples)

	#
	for (j,sampled_vertex) in enumerate(sampled_vertices)

        for (k,v0) in enumerate(sampled_vertex)

			(d,_,_) = bfs(A,v0)
			reachability[j,k] = zeros(Int,maximum(d))

            for i = 1:length(d)
                if d[i] == -1 
                    unreachable_nodes[j,k] += 1 
                elseif d[i] == 0 
                    continue
                else
					reachability[j,k][d[i]] += 1 
                end
            end 


            total_frontier_edgecount[j,k], forward_frontier_edgecount[j,k] = forward_vs_total(A,d)
        end
    end 

    return unreachable_nodes, reachability, total_frontier_edgecount, forward_frontier_edgecount
end 

@everywhere function forward_vs_total(A,d)
	dmax = maximum(d)
	forwardcount = zeros(dmax+1)
	totalcount = zeros(dmax+1)

	for i = 1:size(A,1)
		for j in get_undirected_neighbors(A,i)
			#j = A.rowval[offset]
			
			if i > j # make sure we only count each edge once

				di = d[i]
				dj = d[j]
				if di == -1 || dj == -1 
					continue 
				end 
				totalcount[di+1] += 1
				totalcount[dj+1] += 1
				if di < dj
					forwardcount[di+1] += 1
				else
					forwardcount[dj+1] += 1
				end 
			end 
		end
	end 
	return totalcount, forwardcount
end



# curried function for spawner
function curried_bfs_graph_generation(graph_type::Graph)
	return args->curried_bfs_graph_generation(graph_type, args) 
end 


# curried function for workers
@everywhere function curried_bfs_graph_generation(graph_type::RandomGraph, args)
	(seed_offset,((seed_start, samples, percentile_ranges), graph_args...)) = args
    filename = RANDOM_GRAPHS*file_name(graph_type, seed_start + seed_offset, graph_args...)
    if !isfile(filename)
        generate_random_graph(graph_type, seed_start + seed_offset, graph_args...)
    else
        println("file:$(filename) already exists.")
    end
end 





#
#    Helpers 
# 


function get_undirected_neighbors(A::MatrixNetwork,i::Int)
	return @view A.ci[A.rp[i]:A.rp[i+1]-1]
end 

function get_undirected_degree(A::MatrixNetwork,i::Int)
	return A.rp[i+1]-A.rp[i]
end 


@everywhere function sample_degree_percentiles(A,percentile_ranges,samples)

	deg = [get_undirected_degree(A,i) for i = 1:size(A,1)]
	perm = sortperm(deg)

	n = size(A,1)

	sampled_vertices = []

	for (lower_p, upper_p) in percentile_ranges
		vert_range = @view perm[Int(ceil(lower_p*n)):Int(ceil(upper_p*n))]

		if length(vert_range) <= samples 
			push!(sampled_vertices,vert_range)
		else 
			push!(sampled_vertices,sample(vert_range,samples))
		end 
	end 
	return sampled_vertices
end 


