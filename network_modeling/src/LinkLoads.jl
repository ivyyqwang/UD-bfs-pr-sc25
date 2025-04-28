
struct LinkLoads
    node2router_map::Vector{Int32} # this maps a node id to the corresponding router
    node_inflows::Vector{Int32} # this node->router flows (indexed by node)
    node_outflows::Vector{Int32} # this router->node flows (indexed by node)
    r2r::OffsetMatrix{Int32, Matrix{Int32}} # this is the router to router array 
end 


"""
This assumes that nodes are numbered 1->n
and routers are numbered n+1:n+r 
where there are r routers. 
"""
function LinkLoads(node_to_router_map::Vector{Int32}, number_of_routers::Int32)
    numnodes = length(node_to_router_map)
    atleast = maximum(node_to_router_map) - numnodes 
    @assert(number_of_routers >= atleast)
    @assert(minimum(node_to_router_map) > numnodes) 

    R = zeros(Int32, number_of_routers, number_of_routers) # assume a dense route map
    OA = OffsetArray(R, numnodes+1:numnodes+number_of_routers, numnodes+1:numnodes+number_of_routers)
   
    return LinkLoads(node_to_router_map,zeros(Int32, numnodes), zeros(Int32, numnodes), OA)
end     
#LinkLoads(node_to_router_map::Vector{Int32}, number_of_routers::Integer) = LinkLoads(node_to_router_map,Int32(number_of_routers))
LinkLoads(number_of_routers::Int32) = LinkLoads(create_nodemap_from_num_routers(number_of_routers),number_of_routers)


function add_messages(L::LinkLoads, src::Int32, dst::Int32)
    nnodes = length(L.node_inflows)
    if src <= nnodes # then we have a message from a node -> network 
        # dst should be a router
        @assert(dst == L.node2router_map[src])
        L.node_inflows[src] += 1
    elseif dst <= length(L.node_inflows) 
        # src should be a router
        @assert(src == L.node2router_map[dst])
        L.node_outflows[dst] += 1
    else
        L.r2r[src,dst] += 1
    end
end 

function remove_messages(L::LinkLoads, src::Int32, dst::Int32)
    nnodes = length(L.node_inflows)
    if src <= nnodes # then we have a message from a node -> network 
        # dst should be a router
        @assert(dst == L.node2router_map[src])
        L.node_inflows[src] -= 1
    elseif dst <= length(L.node_inflows) 
        # src should be a router
        @assert(src == L.node2router_map[dst])
        L.node_outflows[dst] -= 1
    else
        L.r2r[src,dst] -= 1
    end
end 

function get_load(L::LinkLoads, src::Int32, dst::Int32)
    nnodes = length(L.node_inflows)
    if src <= nnodes # then we have a message from a node -> network 
        # dst should be a router
        @assert(dst == L.node2router_map[src])
        return L.node_inflows[src]
    elseif dst <= length(L.node_inflows) 
        # src should be a router
        @assert(src == L.node2router_map[dst])
        return L.node_outflows[dst]
    else
        return L.r2r[src,dst]
    end
end 


function router_to_router_loads()

end 


function clear!(L::LinkLoads) 
    fill!(L.node_inflows, 0); 
    fill!(L.node_outflows, 0); 
    fill!(L.r2r, 0)
end 