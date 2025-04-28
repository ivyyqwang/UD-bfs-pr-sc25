module DiscreteEventNetworkSim

# run this in the repl to install the needed dependencies
# ] add OffsetArrays, SparseArrays,MatrixNetworks,StableRNGs,StatsBase, Random

using OffsetArrays
using SparseArrays
using MatrixNetworks: floydwarshall
#using Metis
using IterTools: chain
using StatsBase: percentile
using StableRNGs: StableRNG, LehmerRNG, seed!
using Random: shuffle!
#using DataStructures: CircularDeque, Queue, enqueue!, dequeue!


const LINK_TRANSMISSION_RATE = 2.2e12 # TB/s
const QUEUE_CAPACITY = 100
const SAVE_FREQUENCY = 100

const PROJ_LOC = first(split(pathof(DiscreteEventNetworkSim),"src/DiscreteEventNetworkSim.jl"))
const DATA_LOC = PROJ_LOC*"data/"
const RESULTS_LOC = DATA_LOC*"results/"

include("helpers.jl")
export create_subgraph_for_compute_nodes, test_matrix

include("enumerate_fixed_length_paths.jl")
export all_simple_paths_up_to_p, enumerate_all_simple_paths

include("Message.jl")
export Message, where_is, get_source, get_destination, update_place

import Base.push!
import Base.popfirst!
import Base.length
import Base.isempty 
include("CircularQueues.jl")
export CircularQueue

include("Links.jl")
export LinkLoads
export add_messages, remove_messages, get_load, clear!

include("RoutingTable.jl")
export RoutingTable
export routes_from_to, get_next_hop

include("EventQueue.jl")
export CircularQueue
export EventQueue, clear_head_and_step, schedule!, head

include("Buffers.jl")
export Buffers

include("NetworkSim.jl")
export NetworkSim, Clock 
export route_message!, get_delay, can_route, step!, reset!
export schedule_AlltoAll_messages_to_neighbors!
export MsgInjection, Linear, AllSendToAll, EachRandomNeighbor


include("fileio.jl")
export load_polarstar_network, load_paths_between_polarstar

include("drivers.jl")
export run_network_simulation
export simulate, simulate! 
export CommunicationPattern, AllToAll, SingleMessage 


end # module DiscreteEventNetworkSim
