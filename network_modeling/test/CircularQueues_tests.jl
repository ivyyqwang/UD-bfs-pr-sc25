@testset "CircularQueues" begin

    test_queue = CircularQueue{Int}(10)


    @testset "Single Access" begin
        element = 34
        push!(test_queue,element)
        @test length(test_queue) == 1
        @test test_queue.tail == 2

        @test popfirst!(test_queue) == element 
    end 

    @testset "Force resize" begin


    end

end