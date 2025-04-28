@testset "Drivers" begin

    @testset "simulate" begin

        for communication_pattern in [AllToAll(1000),SingleMessage()]
        
            @test_nothrow simulate(A,communication_pattern)
            @test_nothrow simulate(A, size(A,1)*DENS.NUM_NODES_PER_ROUTER ÷ 4, avg_msg_size, communication_pattern)
                                      # use fewer compute nodes than max 
            @test_nothrow simulate(A, routes, size(A,1)*DENS.NUM_NODES_PER_ROUTER ÷ 4, avg_msg_size, communication_pattern)                        
        end 
    end 
end 