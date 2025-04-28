function test_matrix()

    A =  Matrix{Float64}(undef,10,10)
    A .= 1.0 
    for i = 1:size(A,1)
        A[i,i] = 0.0 
    end 
    return sparse(A)
end 


function create_nodemap_from_num_compute_nodes_randomly(node_assignment_rng::LehmerRNG,numnodes::Int32,max_nodes_per_router::Int,numrouters::Int32)
    @assert numnodes <= max_nodes_per_router*numrouters

    node_to_router_map = Vector{typeof(numnodes)}(undef,numnodes)
    assigned_compute_nodes = zeros(numrouters)

    for compute_node_idx = 1:numnodes
        router_idx = rand(node_assignment_rng,1:numrouters)
        while assigned_compute_nodes[router_idx] >= max_nodes_per_router
            router_idx = rand(node_assignment_rng,1:numrouters)
        end # sample again if router is full 
        node_to_router_map[compute_node_idx] = numnodes + router_idx
        assigned_compute_nodes[router_idx] += 1 
    end 
    @assert all(assigned_compute_nodes .<= max_nodes_per_router)
    return node_to_router_map
end


function create_nodemap_from_num_compute_nodes(numnodes::Int32, max_nodes_per_router::Int32,router_network_size::Int)
    @assert numnodes <= max_nodes_per_router*router_network_size

    node_to_router_map = Vector{typeof(numnodes)}(undef,numnodes)
    router_idx = numnodes + 1
    for compute_node_idx = 1:numnodes
        node_to_router_map[compute_node_idx] = router_idx
        if compute_node_idx % max_nodes_per_router == 0 
            router_idx += 1
        end 
    end 
    return node_to_router_map
end
#create_nodemap_from_num_routers(number_of_routers::Int32) = create_nodemap_from_num_compute_nodes(Int32(number_of_routers*NUM_NODES_PER_ROUTER))
create_nodemap_from_num_routers(number_of_routers::Integer) = create_nodemap_from_num_routers(Int32(number_of_routers))



function create_router2node_map(node2router_map::Vector{Int32}, num_routers)
    
    numnodes = length(node2router_map) 
    r2n_map = Vector{Vector{Int32}}(undef,num_routers)

    for r = 1:length(r2n_map)
        r2n_map[r] = Int32[]
    end

    for (compute_node,router) in enumerate(node2router_map)
        push!(r2n_map[router - numnodes],compute_node)
    end 

    return r2n_map
end 
                
#
#  Validating the enumerated paths 
#

function verify_found_paths(A,all_paths)
    D,_ = @time floydwarshall(A)
    verify_found_paths(D,A,all_paths, )
    return D
end 

function verify_found_paths(D,A,all_paths)

    #check all the entries in D to make sure that the paths a
    for i = 1:size(A,1)
        for j = 1:size(A,2)
            if isinf(D[i,j])
                @assert !haskey((i,j),all_paths)
            elseif D[i,j] == 0 
                continue 
            else
                
                paths = all_paths[(i,j)]

                @assert all(length(p)==length(first(paths)) for p in paths)
                @assert D[i,j] == (length(first(paths)) - 1)

                for path in paths 

                    @assert first(path) == i 
                    @assert last(path) == j
        
                    for i= 1:(length(path)-1)
                        @assert A[path[i],path[i+1]] != 0
                    end 
                end 

            end 
        end 
    end 
end 


function convert_paths_to_distance_matrix(routes::Dict{Tuple{Int64, Int64}, Vector{Vector{Int64}}})
    
    n = max(maximum(keys(routes))...) # assuming from a symetric graph.
    D = zeros(Int,n,n)

    for ((i,j),alt_paths) in routes 
                        # all paths are the same length
        D[i,j] = length(first(alt_paths))-1 
    end                                 # the paths start and 
                                        # end with i and j .

    return D
end 

