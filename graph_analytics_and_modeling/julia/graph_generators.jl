include("shared.jl")
include("randomGraphCode.jl")
# TODO: add in this functionality: 
using ImageFiltering: imfilter, Kernel
using StatsBase: median

abstract type Graph end
struct FileIOGraph <: Graph end #reads in a graph from file

abstract type RandomGraph <: Graph end
struct ForestFire <: RandomGraph end 
struct ErdosRenyi <: RandomGraph end 
struct RMAT <: RandomGraph end 
struct KNN <: RandomGraph end 
struct PreferentialAttachment <: RandomGraph end 



function estimate_graph_generation_time()

    graph_sizes = [2^scale for scale=8:18]
    trials = 3

    timings = Array{Float64}(undef,trials,length(graph_sizes))
    for (n_idx,n) in enumerate(graph_sizes)
        for t = 1:trials
            (A,_), timings[t,n_idx] = @timed _generate_random_graph(ErdosRenyi(),23223, n, 35)
            #(A,_), timings[t,n_idx] = @timed _generate_random_graph_julia(ForestFire(),23223, n, .5)
            #(A,_), timings[t,n_idx] = @timed _generate_random_graph_julia(RMAT(),23234334, n)
            #(A,_), timings[t,n_idx] = @timed _generate_random_graph_julia(KNN(),9923234,n,16, 35)
            #A, timings[t,n_idx] = @timed preferential_attachment_graph(n,20,10)
        end
    end 

    med_timings = median.(eachcol(timings))

    timing_scale_factors = []

    for i = 1:(length(graph_sizes)-1)
        push!(timing_scale_factors, med_timings[i+1]/med_timings[i])
    end

    println("time(scale) = med_timing[end]*(time_scaling_per_2x_graph_size)^(scale - log2(largest_graph_size))")
    println("time(scale) = $(med_timings[end])*($(median(timing_scale_factors)))^(scale - $(log2(graph_sizes[end])))")
    estimated_time = scale-> med_timings[end]*median(timing_scale_factors)^(scale -log2(graph_sizes[end]))
    return estimated_time, timing_scale_factors, med_timings
end 

# top level calls

function generate_random_graph(args...)

    file = RANDOM_GRAPHS*file_name(args...)
    if big_enough(args...)
        if isfile(file)
            println("loading $file\n")
            return MatrixNetwork(load_graph(file)), -1 
        else 
            A, seed = _generate_random_graph(args...)
            println("created $file\n")
            save_edge_list(sparse(A),file)
            println("saved $file\n")
            return A, seed
        end 
    else 
        return _generate_random_graph(args...)
    end
end


#  -- Graph Generators



function _generate_random_graph(::ForestFire, seed::Int, n::Int, p::Float64)
    Random.seed!(seed)
    MatrixNetwork(first(forest_fire_graph(n,10,p))),seed
                        # graphs start from a 10-clique 
end 
file_name(::ForestFire, seed::Int, n::Int, p::Float64) = "forestFire_burnP:$(p)_n:$(n)_seed:$(seed).smat"               
big_enough(::ForestFire, seed::Int, n::Int, p::Float64) = (p < .5 && n > 50000) || (p >= .5 && n > 10000)


function _generate_random_graph(::RMAT, seed::Int, n::Int)
    Random.seed!(seed)
    return MatrixNetwork(rmat(Int(log2(nextpow(2,n))))), seed
end 
file_name(::RMAT, seed::Int, n::Int) = "rmat_n:$(n)_seed:$(seed).smat"
big_enough(::RMAT, seed::Int, n::Int) = log2(n) > 16


function _generate_random_graph(::ErdosRenyi,seed::Int, n::Int, p::Float64)
    Random.seed!(seed)
    return MatrixNetworks.erdos_renyi_undirected(n,p), seed
end 
file_name(::ErdosRenyi,seed::Int, n::Int, p::Float64) = "er_n:$(n)_p:$(p)_seed:$(seed).smat"
big_enough(::ErdosRenyi,seed::Int, n::Int, p::Float64) = (n > 10000) || (p > 1000/n) # TODO: test this  


function _generate_random_graph(::ErdosRenyi,seed::Int, n::Int, d_avg::Int)
    Random.seed!(seed)
    return MatrixNetworks.erdos_renyi_undirected(n,d_avg), seed
end 
file_name(::ErdosRenyi,seed::Int, n::Int, d_avg::Int) = "er_dAvg:$(d_avg)_n:$(n)_seed:$(seed).smat"
big_enough(::ErdosRenyi,seed::Int, n::Int, d_avg::Int) = n > 10000 || d_avg > 100 # TODO: test this 


function _generate_random_graph(::ErdosRenyi,seed::Int, n::Int)
    Random.seed!(seed)                             #produce connected graph
    return MatrixNetworks.erdos_renyi_undirected(n,log(n)/n), seed
end 
file_name(::ErdosRenyi,seed::Int, n::Int) = "er_dAvg:ln(n)_n:$(n)_seed:$(seed).smat"
big_enough(::ErdosRenyi,seed::Int, n::Int) = n > 10000



function _generate_random_graph(::KNN,seed::Int, n::Int, d::Int, k::Int, blur::Bool=false)

    @assert n > d 
    Random.seed!(seed)
    #X = randn(d,n)
    #X = imfilter(X, Kernel.gaussian(rand(1:9)))

    tilesz = d
    X = zeros(tilesz^2,n)
    map(1:n) do i 
        rand_tile = (rand(tilesz, tilesz))
        blur_amount = rand(1:9)
        blur_tile = imfilter(rand_tile, Kernel.gaussian(blur_amount))
        X[:,i] = vec(blur_tile)
    end
    
    T_X = BallTree(X)
    A =embedding_to_graph(T_X,X,k)
    return MatrixNetwork(A), seed

end 
file_name(::KNN,seed::Int, n::Int, d::Int, k::Int) = "knn_k:$(k)_d:$(d)_n:$(n)_seed:$(seed).smat"
big_enough(::KNN,seed::Int, n::Int, d::Int, k::Int) = n > 10000

function embedding_to_graph(X::Matrix{T},k) where T
    d,n = size(X)
    @assert n > d
    T_X = BallTree(X)
    return T_X, embedding_to_graph(T_X,X,k)
end 

function embedding_to_graph(T_X,X::Matrix{T},k) where T 
    d,n = size(X)
    
    Is = Int[]
    Js = Int[]
    for (i, nearest_neigbors) in enumerate(first(knn(T_X, X,k)))
        for j in nearest_neigbors
            push!(Is,i)
            push!(Js,j)
        end 
    end 
    A = sparse(Is,Js,1,n,n)
    return max.(A,A')
end 

function _generate_random_graph(::PreferentialAttachment,seed::Int, n::Int,addedEdges::Int)
    Random.seed!(seed)
    return MatrixNetworks.preferential_attachment_graph(n,addedEdges,10), seed
end 
file_name(::PreferentialAttachment,seed::Int,n::Int, addedEdges::Int) = "pa_addedEdges:$(addedEdges)_n:$(n)_seed:$(seed).smat"
big_enough(::PreferentialAttachment,seed::Int, n::Int, addedEdges::Int) = n > 10000

