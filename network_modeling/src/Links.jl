
struct Links{T}
    node2router_map::Vector{Int32} # this maps a node id to the corresponding router
    node_inflows::Vector{Int32} # this node->router flows (indexed by node)
    node_outflows::Vector{Int32} # this router->node flows (indexed by node)
    r2r::OffsetMatrix{Int32, Matrix{Int32}} # this is the router to router array 

    node_inqueues::Vector{CircularQueue{T}} # this is the node to router queues
    node_outqueues::Vector{CircularQueue{T}} # this is the router to node queues
    r2r_queues::OffsetMatrix{CircularQueue{T}, Matrix{CircularQueue{T}}} # this is the router to router queues

    links::Vector{Tuple{Int32,Int32}} # this is a list of links in the router network
end 


""" 
This assumes that all the router links are in the region between the last node and the last router. 
We should write a helper function to ensure this... 

This assumes that nodes are numbered 1->n
and routers are numbered n+1:n+r 
where there are r routers. 

Use sparse_to_links to convert a sparse matrix to a list of links. 
"""
function Links(node_to_router_map::Vector{Int32}, router_links::Vector{Tuple{Int32,Int32}},::Type{M}) where {M <: Message}
    numnodes = length(node_to_router_map)
    if length(router_links) > 0 
        number_of_routers = maximum(maximum(router_links))#  maximum(node_to_router_map) - numnodes
    else
        number_of_routers = 1 
    end
    
    @assert(minimum(node_to_router_map) > numnodes) 

    # The number of routers is the maximum of the router links and the number of routers in the map.
    if length(router_links) > 0
        number_of_routers = max(number_of_routers, maximum(e->maximum(e), router_links) - numnodes)
    end
    
    R = zeros(Int32, number_of_routers, number_of_routers) # assume a dense route map
    OA = OffsetMatrix(R, numnodes+1:numnodes+number_of_routers, numnodes+1:numnodes+number_of_routers)
   
    node_inqueues = [CircularQueue{M}(QUEUE_CAPACITY) for _ in 1:numnodes]
    node_outqueues = [CircularQueue{M}(QUEUE_CAPACITY) for _ in 1:numnodes]

    empty_q = CircularQueue{M}(0)
    RQ = Matrix{CircularQueue{M}}(undef, number_of_routers, number_of_routers)
    for i in eachindex(RQ)
      RQ[i] = empty_q
    end # copy an empty queue to all elements so we can still broadcast over RQ. 
    
    for (i,j) in router_links 
        RQ[i,j] = CircularQueue{M}(QUEUE_CAPACITY)
    end # replace the entries which correspond to edges in the graph with queues. 

    r2r_queues = OffsetMatrix(RQ, numnodes+1:numnodes+number_of_routers, numnodes+1:numnodes+number_of_routers)

    return Links{M}(node_to_router_map, 
                            zeros(Int32, numnodes), 
                            zeros(Int32, numnodes), 
                            OA, node_inqueues, node_outqueues, r2r_queues, 
                            router_links)
end

sparse_to_links(sparse::SparseMatrixCSC) = Tuple{Int32,Int32}.(collect(zip(findnz(sparse)[1:2]...)))

# """
# This assumes that nodes are numbered 1->n
# and routers are numbered n+1:n+r 
# where there are r routers. 
# """
# function LinkLoads(node_to_router_map::Vector{Int32}, number_of_routers::Int32)
#     numnodes = length(node_to_router_map)
#     atleast = maximum(node_to_router_map) - numnodes 
#     @assert(number_of_routers >= atleast)
#     #println(node_to_router_map)
#     @assert(minimum(node_to_router_map) > numnodes) 

#     R = zeros(Int32, number_of_routers, number_of_routers) # assume a dense route map
#     OA = OffsetArray(R, numnodes+1:numnodes+number_of_routers, numnodes+1:numnodes+number_of_routers)
   
#     return LinkLoads(node_to_router_map,zeros(Int32, numnodes), zeros(Int32, numnodes), OA)
# end     
# LinkLoads(node_to_router_map::Vector{Int32}, number_of_routers::Integer) = LinkLoads(node_to_router_map,Int32(number_of_routers))
# LinkLoads(number_of_routers::Int32) = LinkLoads(create_nodemap_from_num_routers(number_of_routers),number_of_routers)


function _lookup_and_adjust(src, dst, node_intype, node_outtype, routertype, router_map; adjust=nothing )
    nnodes = length(node_intype)
    if src <= nnodes # then we have node -> network 
        # dst should be a router
        @assert(dst == router_map[src])
        if adjust === nothing 
            return node_intype[src]
        else
            return (node_intype[src] += adjust)
        end
    elseif dst <= nnodes
        # src should be a router
        @assert(src == router_map[dst])
        if adjust === nothing 
            return node_outtype[dst]
        else
            return (node_outtype[dst] += adjust)
        end
    else
        if adjust === nothing 
            return routertype[src,dst]
        else
            return (routertype[src,dst] += adjust)
        end
    end
end 
_lookup(src, dst, node_intype, node_outtype, routertype, router_map) = _lookup_and_adjust(src, dst, node_intype, node_outtype, routertype, router_map; adjust=nothing)

function add_to_queue(L::Links{M}, src::Int32, dst::Int32, msg::Message) where M
  buffer = _lookup(src, dst, L.node_inqueues, L.node_outqueues, L.r2r_queues, L.node2router_map)
  push!(buffer, msg)
end 

function _waiting_queues(L::Links{M}) where M
    g1 = (q for q in L.node_inqueues if length(q) > 0)
    g2 = (q for q in L.node_outqueues if length(q) > 0)
    g3 = (q for q in L.r2r_queues if length(q) > 0)
    # for reasons that elude me, the above is much faster... 
    #g3 = (L.r2r_queues[src,dst] for (src,dst) in L.links if length(L.r2r_queues[src,dst]) > 0)
    return (g1, g2, g3)
end

function apply_to_waiting_queues(f, L::Links{M}) where M
    inqueues, outqueues, r2r_queues = _waiting_queues(L)
    for q in inqueues
        f(q)
    end
    for q in outqueues
        f(q)
    end
    for q in r2r_queues
        f(q)
    end
end 

function waiting_queues(L::Links{M}) where M
    # return a generator over all the queues that have messages in them... 
    gs = (_waiting_queues(L))
    return Iterators.flatten(gs)
end 

function messages_waiting(L::Links{M}) where M
    return mapreduce(q->length(q), +, waiting_queues(L); init=0)
end

function add_messages(L::Links{M}, src::Int32, dst::Int32) where M
    _lookup_and_adjust(src, dst, L.node_inflows, L.node_outflows, L.r2r, L.node2router_map; adjust=1)
end 

function remove_messages(L::Links{M}, src::Int32, dst::Int32) where M
    _lookup_and_adjust(src, dst, L.node_inflows, L.node_outflows, L.r2r, L.node2router_map; adjust=-1)
end 

function get_load(L::Links{M}, src::Int32, dst::Int32) where M
    return _lookup(src, dst, L.node_inflows, L.node_outflows, L.r2r, L.node2router_map)
end 

function clear_flow_counts!(L::Links{M}) where M
    fill!(L.node_inflows, Int32(0)); 
    fill!(L.node_outflows, Int32(0)); 
    fill!(L.r2r, Int32(0))
end 

function clear_buffers!(L::Links{M}) where M
    clear!.(L.node_inqueues)
    clear!.(L.node_inqueues)
    clear!.(L.r2r_queues)
end 

function clear!(L::Links{M}) where M
    clear_flow_counts!(L)
    clear_buffers!(L)
end 