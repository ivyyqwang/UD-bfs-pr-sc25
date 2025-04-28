

struct Buffers
    node2router_map::Vector{Int32} # this maps a node id to the corresponding router
    node_inflows::Vector{CircularQueue{Message}} # this node->router buffers (indexed by node)
    node_outflows::Vector{CircularQueue{Message}} # this router->node buffers (indexed by node)
    r2r::OffsetMatrix{CircularQueue{Message}, Matrix{CircularQueue{Message}}} # this is the router to router array of buffers
end 

function Buffers(router_network::SparseMatrixCSC)
    return Buffers(router_network,create_nodemap_from_num_routers(size(router_network)))
end 

function Buffers(router_network::SparseMatrixCSC,node_to_router_map::Vector{Int32})
    
    number_of_routers = size(router_network,1)
    numnodes = length(node_to_router_map)
    atleast = maximum(node_to_router_map) - numnodes 
    @assert(number_of_routers >= atleast)
    #println(node_to_router_map)
    @assert(minimum(node_to_router_map) > numnodes) 

    node_inflow_buffers = Vector{CircularQueue{Message}}(undef,numnodes)
    node_outflow_buffers = Vector{CircularQueue{Message}}(undef,numnodes)

    for idx = 1:numnodes
        node_inflow_buffers[idx] = CircularQueue{Message}(QUEUE_CAPACITY)
        node_outflow_buffers[idx] = CircularQueue{Message}(QUEUE_CAPACITY)
    end 

    R = Matrix{CircularQueue{Message}}(undef, number_of_routers, number_of_routers) # assume a dense route map
    empty_queue = CircularQueue{Message}(0) 
    map(idx->R[idx] = empty_queue, 1:size(R,1)*size(R,2))# initialize every entry to be the same empty queue, 
                                                # and overwrite with non-empty queues where there are
                                                # edges in the routing network.
    init_r2r_buffers!(R,router_network)
    OA = OffsetArray(R, numnodes+1:numnodes+number_of_routers, numnodes+1:numnodes+number_of_routers)
   
    return Buffers(node_to_router_map,node_inflow_buffers,node_outflow_buffers, OA)
end

function init_r2r_buffers!(R::Matrix{CircularQueue{Message}},A::SparseMatrixCSC)
    # only initialize where the non-zeros of the buffers are 
    for j = 1:size(A,2)
        for offset in nzrange(A,j)
            R[A.rowvals[offset],j] = CircularQueue{Message}(QUEUE_CAPACITY)
        end 
    end 
end 

function init_r2r_buffers!(R::Matrix{CircularQueue{Message}},A::Matrix)
    for j = 1:size(A,2)
        for i = 1:size(A,1)
            R[A.rowvals[offset],j] = CircularQueue{Message}(QUEUE_CAPACITY)
        end 
    end 
end 



function push!(B::Buffers, msg::Message, src::Int32, dst::Int32)
    nnodes = length(B.node_inflows)
    if src <= nnodes # then we have a message from a node -> network 
        # dst should be a router
        @assert(dst == B.node2router_map[src])
        push!(B.node_inflows[src],msg)
    elseif dst <= length(L.node_inflows) 
        # src should be a router
        @assert(src ==  B.node2router_map[dst])
        push!(B.node_outflows[dst],msg)
    else
        push!(r2r[src,dst],msg)
    end
end 

function popfirst!(B::Buffers, src::Int32, dst::Int32)
    nnodes = length(L.node_inflows)
    if src <= nnodes # then we have a message from a node -> network 
        # dst should be a router
        @assert(dst == B.node2router_map[src])
        return popfirst!(B.node_inflows[src])
    elseif dst <= length(L.node_inflows) 
        # src should be a router
        @assert(src == B.node2router_map[dst])
        return popfirst!(B.node_outflows[src])
    else
        return popfirst!(B.B.r2r[src,dst])
    end
end 

function length(B::Buffers)
    #=
    buffered_elements = 0
    compute_nodes = length(B.node_inflows)
    for i = 1:length(B.node_inflows)
        buffered_elements += length(B.node_inflows[i])
        buffered_elements += length(B.node_outflows[i])
    end 

    for j = 1:size(B.r2r,2)
        j_idx += compute_nodes
        for i = 1:size(B.r2r,1)
            i_idx += compute_nodes
            buffered_elements += B.r2r[i_idx,j_idx]
        end 
    end 

    return buffered_elements
    =#
    buffered_elements = 0
    buffered_elements += sum(length(buf) for buf in B.node_inflows)
    buffered_elements += sum(length(buf) for buf in B.node_outflows)
    println(buffered_elements)
    buffered_elements += sum(length(buf) for buf in B.r2r)
    println(buffered_elements)
    println()
    return buffered_elements
end