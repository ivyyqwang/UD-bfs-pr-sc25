using Test
using DiscreteEventNetworkSim
const DENS = DiscreteEventNetworkSim
using MatrixNetworks: floydwarshall

#TODO: add in seeding here. 

n = 10
A = DiscreteEventNetworkSim.SparseArrays.sprand(10,10,.4);
A.nzval .= 1.0
A = max.(A,A');
routes = all_simple_paths_up_to_p(A,3)
avg_msg_size = 48

# -- test_noerror solution -- #
# src: https://github.com/JuliaLang/julia/issues/18780#issuecomment-863505347
struct NoException <: Exception end
macro test_nothrow(ex)
    esc(:(@test_throws NoException ($(ex); throw(NoException()))))
end

include("helpers.jl")
include("drivers_tests.jl")
include("LinkLoads_tests.jl")
include("enumerate_fixed_length_paths_tests.jl")


