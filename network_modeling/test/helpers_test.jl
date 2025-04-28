@testset "Helper Functions" begin 


    
    @testset "node2router_map" begin 
        node2router_map = create_nodemap_from_num_routers(size(A,1))

        @test length(node2router_map) == size(A,1)*DENS.NUM_NODES_PER_ROUTER
        @test length(node2router_map) == size(A,1)*DENS.NUM_NODES_PER_ROUTER
        


    end

    @testset "router2node_map" begin 





    end 


end 