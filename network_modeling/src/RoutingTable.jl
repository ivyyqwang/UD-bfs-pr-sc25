"""
    RoutingTable
   Create a routing table to tell where messages are going next. 
""" 
struct RoutingTable
#routes::Matrix{Vector{Vector{Int32}}} #TODO: change this to use a static vector once the full implementation is done. 
    routes::Dict{Tuple{Int32, Int32}, Vector{Vector{Int32}}}
    node2router_map::Vector{Int32}
end 



function RoutingTable(A::SparseMatrixCSC, node2router_map::Vector{Int32})
    return RoutingTable(reindex(all_simple_paths_up_to_p(A,3),node2router_map,Int32(size(A,1)))...)
end 

function reindex(all_paths::Dict{Tuple{Int64, Int64}, Vector{Vector{Int64}}}, node2router_map::Vector{Int32},num_routers::Int32)

    router2node_map = create_router2node_map(node2router_map,num_routers)

    #reshape(1:length(node2router_map),NUM_NODES_PER_ROUTER,:)
                
    numnodes = Int32(length(node2router_map))
    reindexed_paths = Dict{keytype(all_paths),Vector{Vector{Int32}}}()
    for ((router_i,router_j),routes) in all_paths

        paths = [[Int32(v+numnodes) for v in path] for path in routes]
        
        # update indices for routes beteen routers.
        reindexed_paths[(Int32(router_i+numnodes),Int32(router_j+numnodes))] = paths 

        # added in compute nodes connected to router_i to router_j 
        for compute_node in router2node_map[router_i]
            path_copy = deepcopy(paths) 
            foreach(path->push!(path,compute_node),path_copy)
            reindexed_paths[(compute_node,Int32(router_j+numnodes))] = paths
        end 

        # added in router_i to compute nodes connected to router_j 
        for compute_node in router2node_map[router_j]
            path_copy = deepcopy(paths) 
            foreach(path->push!(path,compute_node),path_copy)
            reindexed_paths[(Int32(router_i+numnodes),compute_node)] = paths
        end 

    end    

    # add in the router-> compute node edges, bc sometimes there may not be edges in router network 
    for router = 1:length(router2node_map)
        for compute_node in router2node_map[router]
            # add in the outgoing path from a router directly to a compute node 
            reindexed_paths[(Int32(router+numnodes), compute_node)] = Vector{Int32}[Int32[Int32(router+numnodes),compute_node]]
        end 
    end 

    # add in the outgoing compute links
    return reindexed_paths, node2router_map
                            # return this too to feed to `RoutingTable` constructor
end


function routes_from_to(t::RoutingTable, src::Int32, dst::Int32) 

    if src <= length(t.node2router_map) # this a compute_node to compute_node 
        paths = [copy(route) for route in routes_from_to(t,t.node2router_map[src],dst)]
        foreach(path->insert!(path,1,src),paths) 
        return paths 
    else # router to compute_node 
        return t.routes[(src,dst)]
    end 
end
""" 
    get_next_hop(t::RoutingTable, place::Int32, dst::Int32, choice=0)

This makes a choice for the next hop based on a nonnegeative integer choice.
choice can be used to distribute the load among the possible routes and
could be based on a for loop index or some other choice of arbitrary values.
"""
#=
function get_next_hop(t::RoutingTable, place::Int32, dst::Int32, choice::Int32=1) 
    
    #TODO: update to use the `routes_from_to` function.

    if place < length(t.node2router_map) # at a compute node 
        return t.node2router_map[place] # only path is into network 
    else # currently in the routing network
        rs = t.routes[(place, dst)]
        nroutes = length(rs) # count the number of routes
        offset = (choice % nroutes) + 1 # choose base on the choise.
        return rs[offset] 
    end
end 
=#
function get_next_hop(rng::LehmerRNG, compute_nodes::Int32, t::RoutingTable, place::Int32, dst::Int32) 
    if place <= compute_nodes # at a compute node 
        return getindex(t.node2router_map,place)  # only path is into network 
    else # currently in the routing network
        rs = t.routes[(place, dst)]
        nroutes = length(rs)
        offset = rand(rng,1:nroutes) # choose randomly.
        return getindex(rs[offset],2) 
                         # first elemen should be place 
    end
end 

function get_next_hop_options(t::RoutingTable, place::Int32, dst::Int32) 
    if place <= length(t.node2router_map) # at a compute node 
        return t.node2router_map[place]  # only path is into network 
    else # currently in the routing network
        return t.routes[(place,dst)]
        #next_paths = t.routes[(place, dst)]
        #return map(r->r[2],next_paths)
                       # first elemen should be place,
                       # so we take the second element.
    end
end 