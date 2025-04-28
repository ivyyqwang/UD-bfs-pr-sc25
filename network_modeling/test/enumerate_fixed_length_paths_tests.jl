@testset "Enumerate Fixed Paths Tests" begin 


    D,_ = floydwarshall(A)
    max_dist = Int(maximum(D))

    (tmp_path, io) = mktemp()
    close(io)

    # all_simple_paths_up_to_p(A,max_dist),
    for (i,paths) in enumerate([ DENS.all_simple_paths_up_to_p_v2(A,max_dist)])

        all_paths_are_simple = true
        all_paths_include_true_distance = true
        for ((router_i,router_j),routing_paths) in paths 

            if router_i == router_j 
                continue 
            end 
            true_distance = D[router_i,router_j]
            true_distance_found = false
            for path in routing_paths

                # find the true distances between all 
                if length(path) -1 == true_distance 
                    true_distance_found = true 
                end 
                # check all the paths produced are simple 
                if length(path) != length(unique(path))
                    println("TEST FAIL: no-simple path found between $((router_i, router_j))")
                    all_paths_are_simple = false
                end 
            end 
            if !true_distance_found
                println("TEST FAIL: no path of the correct min-distance found between $((router_i, router_j))")
                all_paths_include_true_distance = false
            end 
        end 

        @test all_paths_are_simple
        @test all_paths_include_true_distance

        @testset "FileIO" begin 
            DENS.save_all_paths_v2(paths, tmp_path)
            loaded_paths = DENS.load_all_paths_v2(tmp_path)
            @test all(sort(paths[k],by=l->length(l)) == loaded_paths[k] for k in keys(paths))
        end 

    end 



end 