@testset "NetworkSim Tests" begin

    @testset "Constructor" begin

        @test_nothrow NetworkSim(A,compute_nodes,avg_msg_size,nothing;make_subgraph=false)
        @test_nothrow NetworkSim(A,compute_nodes,avg_msg_size,nothing;make_subgraph=true)
        @test_nothrow NetworkSim(A,routes,compute_nodes,avg_msg_size,nothing)

    end     

end 