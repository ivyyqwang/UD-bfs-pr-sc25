mutable struct Clock
    step::Int32
end

step!(c::Clock) = c.step += 1
get_tick(c::Clock) = c.step # convert nano-seconds to seconds
get_time(c::Clock) = get_tick(c) * 1e-9 # convert nano-seconds to seconds


struct MeasuredStatistics 
    #measured_latencies::Array{Int64,3}
    measured_latencies::Vector{Int64}
    latency_bins::Vector{Int64}

    outqueue_lengths::Vector{Vector{Float64}}
    r2rqueue_lengths::Vector{Vector{Float64}}
end 

function MeasuredStatistics(compute_nodes::Int32)

    latency_bins = collect(200:100:6000)
    #measured_latencies = zeros(Int64,length(latency_bins) + 1, compute_nodes, compute_nodes)
    measured_latencies = zeros(Int64,length(latency_bins) + 1)#, compute_nodes, compute_nodes)
    return MeasuredStatistics(measured_latencies, latency_bins, Vector{Vector{Int64}}(undef,0),Vector{Vector{Int64}}(undef,0))
end 

function clear!(stats::MeasuredStatistics)
    stats.measured_latencies .= 0
    empty!(stats.outqueue_lengths)
    empty!(stats.r2rqueue_lengths)
end

abstract type RoutingStrategy end 
struct queue_routing <: RoutingStrategy end
struct queue_profiled_routing <: RoutingStrategy end
struct queue_random_rerouting <: RoutingStrategy end
struct UGAL <: RoutingStrategy end
struct UGAL_v2 <: RoutingStrategy end



symbol_to_type(::Val{:queue}) = queue_routing
symbol_to_type(::Val{:queue_profiled}) = queue_profiled_routing
symbol_to_type(::Val{:queue_random_reroute}) = queue_random_rerouting
symbol_to_type(::Val{:UGAL}) = UGAL
symbol_to_type(::Val{:UGAL_v2}) = UGAL_v2

"""
    NetworkSim
"""
struct NetworkSim{M,R}
    n::Int32 # number of endpoint nodes
    N::Int32 # number of endpoints + routers
    Q::EventQueue{M}
    routes::RoutingTable
    links::Links{M}
    network_stats::MeasuredStatistics
    time::Clock
    routing_network::SparseMatrixCSC
    node_to_router_msg_capacity::Int32
    router_to_router_msg_capacity::Int32
    shuffle_events::Bool
    exp_file_tag::Union{Nothing,String}

    routing_rng::StableRNG
    traffic_rng::Union{Nothing,StableRNG}
    shuffle_rng::Union{Nothing,StableRNG}
    initial_seeds::Tuple{UInt, Union{Nothing,UInt},Union{Nothing,UInt}}
end
get_tick(sim::NetworkSim{M,R}) where {M,R} = get_tick(sim.time)
get_time(sim::NetworkSim{M,R}) where {M,R} = get_time(sim.time)
schedule!(sim::NetworkSim{M,R},msg::M) where {M,R} = schedule!(sim.Q, msg, sim.Q.headtime+1)
schedule!(sim::NetworkSim{M,R},msg::M,t::Int32) where {M,R} = schedule!(sim.Q, msg, t)


#      Adding in this constructor here bc having PolarStar find 
#      the routings every time we want to construct a sim is slow. 
function NetworkSim(A::SparseMatrixCSC,routing_paths::Dict{Tuple{Int64, Int64}, Vector{Vector{Int64}}},
                    compute_nodes::Int32, avg_msg_size::Int32,exp_file_tag::Union{Nothing,String};
                    nodes_per_router::Int=5, links_per_node::Int=2, links_per_router::Int=1,
                    assignment_strategy=:random,routing_strategy=:queue_random_reroute,shuffle_events=true,
                    routing_seed::Union{UInt,Nothing}=nothing,
                    node_assignment_seed::Union{UInt,Nothing}=nothing,
                    traffic_seed::Union{UInt,Nothing}=nothing,
                    shuffle_seed::Union{UInt,Nothing}=nothing)

    router_links = @time sparse_to_links(A) 
    # router links assume that the routers are numbered from compute_nodes onwards...
    

    if !isnothing(exp_file_tag)
        exp_file_tag *= "-rtng:$(routing_strategy)-npr:$(nodes_per_router)-lpn:$(links_per_node)-lpr:$(links_per_router)-ltr:$(LINK_TRANSMISSION_RATE)"
    end
    
    if assignment_strategy == :linear
        node2router_map = @time create_nodemap_from_num_compute_nodes(compute_nodes,size(A,1))
        if !isnothing(exp_file_tag)
            exp_file_tag *= "-linearRA"
        end
    else
        if isnothing(node_assignment_seed)
            node_assignment_seed = UInt(rand(1:100000))
        end     
        if !isnothing(exp_file_tag)
            exp_file_tag *= "-randRA:$(node_assignment_seed)"
        end
        node2router_map = @time create_nodemap_from_num_compute_nodes_randomly(StableRNG(node_assignment_seed), compute_nodes,nodes_per_router, Int32(size(A,1)))    
    end

    router_link_msg_capacity = Int32(floor(((LINK_TRANSMISSION_RATE*links_per_router)/avg_msg_size)*1e-9))
    compute_node_link_msg_capacity = Int32(floor(((LINK_TRANSMISSION_RATE*links_per_node)/avg_msg_size)*1e-9))

    if isnothing(routing_seed)
        routing_seed = UInt(rand(1:100000))
    end 
    if isnothing(traffic_seed)
        traffic_seed = UInt(rand(1:100000))
    end 

    if !isnothing(exp_file_tag)
        exp_file_tag *= "-rtngS:$(routing_seed)-trfcS:$(traffic_seed)"
    end

    if shuffle_events
        if isnothing(shuffle_seed)
            shuffle_seed = UInt(rand(1:100000))
        end 
        if !isnothing(exp_file_tag)
            exp_file_tag *= "-shflS:$(shuffle_seed)"
        end 
    end


    if routing_strategy == :UGAL || routing_strategy == :UGAL_v2
        msg_type = Message_v2
    else 
        msg_type = Message_v1
    end 

    LL = @time Links(node2router_map, router_links, msg_type)
    EQs = @time EventQueue(msg_type,10000)
    RT = @time RoutingTable(reindex(routing_paths,node2router_map,Int32(size(A,1)))...)
    
    routing_method_type = symbol_to_type(Val(routing_strategy))
    return NetworkSim{msg_type,routing_method_type}(compute_nodes, size(A,1), EQs, RT,
                                                 LL, MeasuredStatistics(compute_nodes), Clock(0), convert(SparseMatrixCSC{eltype(A.nzval), Int32}, A),
                                                 compute_node_link_msg_capacity, router_link_msg_capacity,
                                                 shuffle_events, exp_file_tag, StableRNG(routing_seed), StableRNG(traffic_seed), 
                                                 shuffle_events ? StableRNG(shuffle_seed) : nothing,
                                                 (routing_seed, traffic_seed, shuffle_seed)) 
end 


# NOTE:  defining this here because `Message.jl` is defined before NetworkSim
function create_message(sim::NetworkSim{M,R},src::Int32, dst::Int32, start_time::Int32,place::Int32 ) where {M <: Message, R <: Union{queue_routing, queue_profiled_routing, queue_random_rerouting}}
    return Message_v1(src, dst, start_time, place)
end 



function create_message(sim::Union{NetworkSim{Message_v2,UGAL},NetworkSim{Message_v2,UGAL_v2}}, src::Int32, dst::Int32, start_time::Int32,place::Int32)
    reroute_dst = Int32(rand(sim.routing_rng,Int(sim.n+Int32(1)):Int(sim.n+sim.N)))
                                        # pick a random router to reroute to. 
    return Message_v2(src, dst, start_time, place, reroute_dst)
end 



NetworkSim(A::SparseMatrixCSC, compute_nodes::Union{Real,Int32}, avg_msg_size::Union{Real,Int32}) = NetworkSim(A, Int32(compute_nodes), Int32(avg_msg_size), nothing)

function route_message!(sim::NetworkSim{M,queue_routing}, msg::Message) where M#;verbose) 
    rval = false 
    dst = get_destination(msg)
    place = where_is(msg)

    if where_is(msg) == dst
        latency = get_tick(sim) - get_send_time(msg)
        latency_bin = min((max((latency - 100),0) ÷ 100) + 1,60)
        sim.network_stats.measured_latencies[latency_bin,get_source(msg),dst] += 1
        return 
    else
        next_hop = get_next_hop(sim.routing_rng,sim.n, sim.routes, place, dst)
    end
    
    #verbose && println("can route $(place) -> $(next_hop):$(can_route(sim, place, next_hop))")
    if can_route(sim, place, next_hop)
        # do so... 
        d = get_delay()
        schedule!(sim.Q, update_place(msg,next_hop), sim.Q.headtime+d)
                        # if it's scheduled we assume that it's there. 
                        # (we wouldn't have scheduled if we couldn't route it.)
        add_messages(sim.links, msg.place, next_hop)
        rval = true 
    else
        # add it to the buffer... 
        add_to_queue(sim.links, place, next_hop, msg)
        rval = false 
    end 
    return rval 
end

function route_message!(sim::NetworkSim{M,queue_profiled_routing}, msg::Message) where M#;verbose) 
    arg_setup_t = @timed begin
        rval = false 
        dst = get_destination(msg)
        place = where_is(msg)
    end

    if where_is(msg) == dst
        arrived_t = @timed begin 
            latency = get_tick(sim) - get_send_time(msg)
            latency_bin = min((max((latency - 100),0) ÷ 100) + 1,60)
            #sim.network_stats.measured_latencies[latency_bin,get_source(msg),dst] += 1
            sim.network_stats.measured_latencies[latency_bin] += 1
        end
        println("arg_setup_t:$(arg_setup_t.time) | arrived_t:$(arrived_t.time)")
        return 
    else
        next_hop_t = @timed get_next_hop(sim.routing_rng,sim.n, sim.routes, place, dst)
        next_hop = next_hop_t.value
    end
    
    #verbose && println("can route $(place) -> $(next_hop):$(can_route(sim, place, next_hop))")
    if can_route(sim, place, next_hop)
        can_route_t = @timed begin 
            # do so... 
            d = get_delay()
            schedule!(sim.Q, update_place(msg,next_hop), sim.Q.headtime+d)
                            # if it's scheduled we assume that it's there. 
                            # (we wouldn't have scheduled if we couldn't route it.)
            add_messages(sim.links, msg.place, next_hop)
            rval = true 
        end
        println("arg_setup_t:$(arg_setup_t.time) | next_hop_t:$(next_hop_t.time) | can_route_t:$(can_route_t.time)")
    else
        add_to_buffer_t = @timed begin 
            # add it to the buffer... 
            add_to_queue(sim.links, place, next_hop, msg)
            rval = false 
        end
        println("arg_setup_t:$(arg_setup_t.time) | next_hop_t:$(next_hop_t.time) | add_to_buffer_t:$(add_to_buffer_t.time)")
    end 
    return rval 
end


function route_message!(sim::NetworkSim{M,queue_random_rerouting}, msg::Message) where M#;verbose) 
    rval = false 
    dst = get_destination(msg)
    place = where_is(msg)

    if where_is(msg) == dst
        latency = get_tick(sim) - get_send_time(msg)
        latency_bin = min((max((latency - 100),0) ÷ 100) + 1,60)
        sim.network_stats.measured_latencies[latency_bin] += 1
        
        #sim.network_stats.measured_latencies[latency_bin,get_source(msg),dst] += 1
        return true
    #else
   #     next_hop = get_next_hop(sim.routing_rng, sim.routes, place, dst)
    end

    if place <= sim.n # this is a compute node, and only one path to check 
        next_hop = get_next_hop(sim.routing_rng,sim.n, sim.routes, place, dst)
        
        if can_route(sim, place, next_hop)
            d = get_delay()
            schedule!(sim.Q, update_place(msg,next_hop), sim.Q.headtime+d)
                            # if it's scheduled we assume that it's there. 
                            # (we wouldn't have scheduled if we couldn't route it.)
            add_messages(sim.links, msg.place, next_hop)
            rval = true 
        else # queue up this message, nowhere else to go. 
            add_to_queue(sim.links, place, next_hop, msg)
            rval = false 
        end 

    else # this is a router link 
        next_hop = get_next_available_hop(sim, place, dst)
        can_route_message = (next_hop > 0)
                            # negative values mean all paths are full. 

        routing_attempts = Int32(0)
                                          # TODO: make | this a variable 
                                          #            v
        while !can_route_message && routing_attempts < Int32(5) 
            # direct path is saturated, choose a random neighbor
      
            routing_attempts += Int32(1) 
            start_idx = Int(sim.routing_network.colptr[place-sim.n])
            end_idx = Int(sim.routing_network.colptr[place-sim.n+Int32(1)]) - 1
            neighbor_offset = rand(sim.routing_rng, start_idx:end_idx)
            next_hop = sim.routing_network.rowval[neighbor_offset] + sim.n
         
            can_route_message = can_route(sim, place, next_hop)
        end 

        if can_route_message 
            d = get_delay()
            schedule!(sim.Q, update_place(msg,next_hop), sim.Q.headtime+d)
                            # if it's scheduled we assume that it's there. 
                            # (we wouldn't have scheduled if we couldn't route it.)

            add_messages(sim.links, msg.place, next_hop)
            rval = true 
        else 
            add_to_queue(sim.links, place, next_hop, msg)
            rval = false 
        end 
    end 

    return rval 
end

function route_message!(sim::NetworkSim{M,UGAL}, msg::Message_v2) where M#;verbose) 
    rval = false 
    dst = get_destination(msg)
    place = where_is(msg)

    if where_is(msg) == dst
        latency = get_tick(sim) - get_send_time(msg)
        latency_bin = min((max((latency - 100),0) ÷ 100) + 1,60)
        sim.network_stats.measured_latencies[latency_bin,get_source(msg),dst] += 1
        return true
    else
        reroute_dst = get_reroute_destination(msg)
        if reroute_dst == Int32(-1) # already been routed to random intermediate
            next_hop = get_next_hop(sim.routing_rng, sim.n, sim.routes, place, dst)
        else 
            if place == reroute_dst # arrived at rerouted intermediate.
                msg = update_reroute_destination_to_visited(msg) 
                next_hop = get_next_hop(sim.routing_rng, sim.n, sim.routes, place, dst)
            else 
                next_hop = get_next_hop(sim.routing_rng, sim.n, sim.routes, place, reroute_dst)
            end 
        end 
    end
    
    #verbose && println("can route $(place) -> $(next_hop):$(can_route(sim, place, next_hop))")
    if can_route(sim, place, next_hop)
        # do so... 
        d = get_delay()
        schedule!(sim.Q, update_place(msg,next_hop), sim.Q.headtime+d)
                        # if it's scheduled we assume that it's there. 
                        # (we wouldn't have scheduled if we couldn't route it.)
        add_messages(sim.links, msg.place, next_hop)
        rval = true 
    else
        # add it to the buffer... 
        add_to_queue(sim.links, place, next_hop, msg)
        rval = false 
    end 
    return rval 
end

function route_message!(sim::NetworkSim{M,UGAL_v2}, msg::Message_v2) where M#;verbose) 
    rval = false 
    dst = get_destination(msg)
    place = where_is(msg)

    if where_is(msg) == dst
        latency = get_tick(sim) - get_send_time(msg)
        latency_bin = min((max((latency - 100),0) ÷ 100) + 1,60)
        sim.network_stats.measured_latencies[latency_bin,get_source(msg),dst] += 1
        return true
    else
        reroute_dst = get_reroute_destination(msg)
        if reroute_dst == Int32(-1) # already been routed to random intermediate
            #next_hop = get_next_hop(sim.routing_rng, sim.n, sim.routes, place, dst)
            next_hop = get_next_available_hop(sim, place, dst)
        else 
            if place == reroute_dst # arrived at rerouted intermediate.
                msg = update_reroute_destination_to_visited(msg) 
                #next_hop = get_next_hop(sim.routing_rng, sim.n, sim.routes, place, dst)
                next_hop = get_next_available_hop(sim, place, dst)
            else 
                next_hop = get_next_available_hop(sim, place, reroute_dst)
                #next_hop = get_next_hop(sim.routing_rng, sim.n, sim.routes, place, reroute_dst)
            end 
        end 
    end
    
    #verbose && println("can route $(place) -> $(next_hop):$(can_route(sim, place, next_hop))")
    if next_hop > 0
            # `get_next_available_hop` returns negative value when no available routes.      
        # do so... 
        d = get_delay()
        schedule!(sim.Q, update_place(msg,next_hop), sim.Q.headtime+d)
                        # if it's scheduled we assume that it's there. 
                        # (we wouldn't have scheduled if we couldn't route it.)
        add_messages(sim.links, msg.place, next_hop)
        rval = true 
    else
        # add it to the buffer... 
        add_to_queue(sim.links, place, abs(next_hop), msg)
        rval = false 
    end 
    return rval 
end
"""-----------------------------------------------------------------------------
    get_next_available_hop(sim::NetworkSim{M,R}, place::Int32, dst::Int32)

    Find the next available hop by choosing a random routing path, and then 
  iterating through the returned paths. If none are available, then return the
  last option tested negated. 
-----------------------------------------------------------------------------"""
function get_next_available_hop(sim::NetworkSim{M,R}, place::Int32, dst::Int32) where {M,R}

    next_hops = get_next_hop_options(sim.routes, place, dst) 
    start_idx = rand(sim.routing_rng,1:length(next_hops))
    checks = 0 
    # check all available direct paths
    while true 
        if can_route(sim, place, next_hops[start_idx][2]) 
            return next_hops[start_idx][2]
        elseif checks > length(next_hops)
            return -next_hops[start_idx][2]
        end 
        start_idx = (start_idx % length(next_hops)) + 1
        checks += 1 
    end 
end 


function get_delay()
    return Int32(100) # 100ns from 500ns/5 links from CDR. 
end # TODO: need to make this more robust

function can_route(sim::NetworkSim{M,R}, src::Int32, dst::Int32) where {M,R}
    if src <= sim.n # this is a node-to-router link 
        return get_load(sim.links, src, dst) < sim.node_to_router_msg_capacity
    elseif  dst <= sim.n # this is a router-to-node link 
        return get_load(sim.links, src, dst) < sim.node_to_router_msg_capacity
    else # this is a router-to-router link 
        return get_load(sim.links, src, dst) < sim.router_to_router_msg_capacity
    end     
end

function _handle_buffer(sim::NetworkSim{M,R}, buffer) where {M,R}
    while !isempty(buffer)

        msg = head(buffer) 
        msg_routed = route_message!(sim, msg)
        if msg_routed
            # message was successfully routed, so remove from queue.
            popfirst!(buffer)
        else #no capacity for messages. try another one.
            return
        end 
    end
    return
end 

function step!(sim::NetworkSim{M,R}) where {M,R}#;kwargs...)

    # do a pass of the buffers 
    @allocated begin
        apply_to_waiting_queues(sim.links) do buf
            _handle_buffer(sim, buf)
        end
    end

    x = @allocated sim.shuffle_events && shuffle!(sim.shuffle_rng,head(sim.Q))
    @allocated begin 
        for msg in head(sim.Q)
            route_message!(sim,msg)#;kwargs...)
        end
    end

    if get_tick(sim) % 100 == 0 
        measure_queues!(sim)
    end 

    if !isnothing(sim.exp_file_tag)
        if get_tick(sim) % SAVE_FREQUENCY == 0 
            save_measured_stats(sim)
        end 
    end

    @allocated clear_head_and_step(sim.Q)
    @allocated step!(sim.time)
    @allocated clear_flow_counts!(sim.links) # empty the LinkLoads
end 

function step_profiled!(sim::NetworkSim{M,R}) where {M,R}#;kwargs...)

    # do a pass of the buffers 
    handle_buffer_t = @timed begin
        apply_to_waiting_queues(sim.links) do buf
            _handle_buffer(sim, buf)
        end
    end 
    
    msgs_in_head = length(head(sim.Q))
    route_message_t = @timed begin
        sim.shuffle_events && shuffle!(sim.shuffle_rng,head(sim.Q))
        for msg in head(sim.Q)
            route_message!(sim,msg)#;kwargs...)
        end
    end

    measure_queue_t = @timed begin 
        if get_tick(sim) % 1 == 0 
            measure_queues!(sim)
        end 
    end

    save_measured_queue_t = @timed begin 
        if !isnothing(sim.exp_file_tag)
            if get_tick(sim) % SAVE_FREQUENCY == 0 
                save_measured_stats(sim)
            end 
        end
    end 

    clear_and_step_t = @timed begin 
        clear_head_and_step(sim.Q)
        step!(sim.time)
        clear_flow_counts!(sim.links) # empty the LinkLoads
    end

    println("handle_buffer_t:$(handle_buffer_t.time) | route_message_t:$(route_message_t.time) -- msgs_in_head:$(msgs_in_head) | measure_queue_t:$(measure_queue_t.time) | save_measured_queue_t:$(save_measured_queue_t.time) | clear_and_step_t:$(clear_and_step_t.time)")
end 

function measure_queues!(sim::NetworkSim{M,R}) where {M,R}

    push!(sim.network_stats.outqueue_lengths, collect(length.(sim.links.node_outqueues)))
    push!(sim.network_stats.r2rqueue_lengths, collect(length(sim.links.r2r_queues[i+sim.n,j+sim.n]) for (i,j) in sim.links.links))

end 

function clear_previous_measured_stats(sim)
    open(RESULTS_LOC*sim.exp_file_tag*"_outqueues.bin","w") do io
    end
    open(RESULTS_LOC*sim.exp_file_tag*"_r2rqueues.bin","w") do io
    end # overwrites files from previous runs of the same experiment tag.
end 

function save_measured_stats(sim)
    open(RESULTS_LOC*sim.exp_file_tag*"_outqueues.bin","a") do io
        write(io,sim.network_stats.outqueue_lengths[end])
    end
    open(RESULTS_LOC*sim.exp_file_tag*"_r2rqueues.bin","a") do io
        write(io,sim.network_stats.r2rqueue_lengths[end])
    end
    #open(RESULTS_LOC*sim.exp_file_tag*"_latencies.bin","w") do io 
    #    write(io,sim.network_stats.measured_latencies)
    #end
    open(RESULTS_LOC*sim.exp_file_tag*"_msgsPerLatencyBin.bin","w") do io 
        write(io,sim.network_stats.measured_latencies)
        #write(io,sum.(eachslice(sim.network_stats.measured_latencies;dims=1)))
    end 
end 

abstract type MsgInjection end 
struct Linear <: MsgInjection end 
struct AllSendToAll <: MsgInjection end
struct EachRandomNeighbor <: MsgInjection end 

schedule_messages!(sim,num_msgs_to_neighbor,inj::MsgInjection) = schedule_messages!(sim, num_msgs_to_neighbor,Int32(0),inj)

function schedule_messages!(sim::NetworkSim{M,R}, num_msgs_to_neighbor,time::Int32,inj::Linear) where {M,R}
    for cn_i in 1:sim.n
        cn_j = (cn_i % NUM_NODES_PER_ROUTER) + 1 
        for _ = 1:num_msgs_to_neighbor
            msg = create_message(sim, Int32(cn_i),Int32(cn_j),time,Int32(cn_i))
            schedule!(sim,msg)
        end 
    end 
end 


function schedule_messages!(sim::NetworkSim{M,R},num_msgs_to_neighbor,time::Int32,inj::AllSendToAll) where {M,R}
    for cn_i in 1:sim.n
        for cn_j = 1:sim.n
            if cn_i != cn_j
                for _ = 1:num_msgs_to_neighbor
                    msg = create_message(sim,Int32(cn_i),Int32(cn_j),time,Int32(cn_i))
                    schedule!(sim,msg,time)
                end 
            end
        end
    end 
end 


#TODO: rename these functions to a common one so julia can dispatch on the final arg. 
function schedule_messages!(sim::NetworkSim{M,R},num_msgs_to_neighbor,time::Int32,inj::EachRandomNeighbor) where {M,R}
    for cn_i in 1:sim.n
        for _ = 1:num_msgs_to_neighbor
            cn_j = cn_i
            while cn_j == cn_i    
                cn_j = Int32(rand(sim.traffic_rng, 1:Int(sim.n)))
            end
            
            msg = create_message(sim,Int32(cn_i),Int32(cn_j),time,Int32(cn_i))
            schedule!(sim,msg,time)
        end
    end 
end 


function reset!(sim::NetworkSim{M,R}) where {M,R}

    clear!(sim.Q)
    clear!(sim.links)
    clear!(sim.network_stats)
    sim.time.step = 0

    seed!(sim.routing_rng,sim.initial_seeds[1])
    if !isnothing(sim.traffic_rng)
       seed!(sim.traffic_rng,sim.initial_seeds[2])
    end 
    if !isnothing(sim.shuffle_rng)
        seed!(sim.shuffle_rng,sim.initial_seeds[3])
    end 
end 