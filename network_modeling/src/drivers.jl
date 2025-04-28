
#   Top Level Driver
#
function run_network_simulation(compute_nodes::Int32, avg_msg_size::Int32, projected_communication::Int, projected_runtime::Float64,polarstar_radix=22;
                               nodes_per_router::Int=5, links_per_node::Int=2, links_per_router::Int=1,
                               test=true,routing_seed::Union{UInt,Nothing}=nothing,node_assignment_seed::Union{UInt,Nothing}=nothing,
                               traffic_seed::Union{UInt,Nothing}=nothing,shuffle_seed::Union{UInt,Nothing}=nothing,routing_strategy=:queue_random_reroute)

    if test
        A = test_matrix()
        paths = all_simple_paths_up_to_p(A,3)
    else 
        A = load_polarstar_network(polarstar_radix)
        paths = load_paths_between_polarstar(polarstar_radix)
    end

    msgs_per_ns = (projected_communication/(projected_runtime/1e-9))
    injection_method = EachRandomNeighbor()
    
    if typeof(injection_method) === EachRandomNeighbor
        msgs_per_node_per_ns = Int64(ceil(msgs_per_ns/compute_nodes))
    else # AllSendToAll
        msgs_per_node_per_ns = Int64(ceil(msgs_per_ns/(compute_nodes*compute_nodes - compute_nodes)))
    end 
    
    exp_file_tag = "simOutput-msgSize:$(avg_msg_size)-inj:$(typeof(injection_method))-RE:$(nnz(A))-V:$(compute_nodes)-msgVol:$(projected_communication)-rt:$(projected_runtime)-savefreq:$(SAVE_FREQUENCY)"
    if !test 
        exp_file_tag *= "-PSradix:$(polarstar_radix)"
    end

    sim = @time NetworkSim(A,paths,compute_nodes,avg_msg_size,exp_file_tag;
                           nodes_per_router=nodes_per_router, links_per_node=links_per_node, links_per_router=links_per_router,
                           routing_seed=routing_seed,routing_strategy=routing_strategy,shuffle_events = shuffle_seed === nothing,
                           node_assignment_seed=node_assignment_seed, 
                           traffic_seed=traffic_seed, shuffle_seed=shuffle_seed)
    println("starting trial:$(exp_file_tag)")

    if msgs_per_node_per_ns < 1
        simulate_with_new_messages_over_time!(sim,projected_runtime,msgs_per_node_per_ns,1,injection_method)#;kwargs...)
                                                                                                # when msgs_per_node_per_ns are less than 1, 
                                                                                                # use the rate as a coin flip to schedule all
                                                                                                # to all messages.
    else 
        simulate_with_new_messages_over_time!(sim,projected_runtime,1,msgs_per_node_per_ns,injection_method)
    end 

    return sim
end 



#
#   Shared Drivers
#

function simulate!(sim::NetworkSim{M,R}) where {M,R}#;kwargs...)
    
    if !isnothing(sim.exp_file_tag)
        clear_previous_measured_stats(sim)
    end
    while sim.Q.enqued_events > 0 || messages_waiting(sim.links) > 0
        step!(sim)#;kwargs...)
    end 
    if !isnothing(sim.exp_file_tag)
        save_measured_stats(sim) # write out all stats at the end.
    end
    return sim
end 

function simulate_with_new_messages_over_time!(sim::NetworkSim{M,R},min_runtime::Float64,msg_injection_frequency::Int,msgs_per_node::Int,msg_injection::MsgInjection) where {M,R}#;kwargs...)

    if !isnothing(sim.exp_file_tag)
        clear_previous_measured_stats(sim)
    end
    while sim.Q.enqued_events > 0 || get_time(sim) < min_runtime
        step!(sim)#;kwargs...)
        if get_time(sim) < min_runtime && (sim.time.step % msg_injection_frequency == 0)
            schedule_messages!(sim,msgs_per_node,get_tick(sim)+Int32(1),msg_injection)
        end 
    end 
    if !isnothing(sim.exp_file_tag)
        save_measured_stats(sim)
    end
    return sim
end 

function simulate_with_new_messages_over_time!(sim::NetworkSim{M,R},min_runtime::Float64,msg_injection_probability::Float64,msgs_per_node::Int,msg_injection::MsgInjection) where {M,R}#;kwargs...)

    if !isnothing(sim.exp_file_tag)
        clear_previous_measured_stats(sim)
    end
    while sim.Q.enqued_events > 0 || get_time(sim) < min_runtime
        @allocated step!(sim)#;kwargs...)
        if get_time(sim) < min_runtime && (rand(sim.traffic_rng) < msg_injection_probability)
            @allocated schedule_messages!(sim,msgs_per_node,get_tick(sim)+Int32(1),msg_injection)
        end 
    end 

    if !isnothing(sim.exp_file_tag)
       save_measured_stats(sim)
    end
    return sim
end 


