
function all_simple_paths_up_to_p(A::SparseMatrixCSC, p::Int)
    all_paths = Dict{NTuple{2,Int},Vector{Vector{Int}}}()
    
    
    seen_distances = Matrix{Float64}(undef,size(A,1),size(A,2))
    seen_distances .= Inf
    for path_length = 2:p
        memo,_ = enumerate_all_simple_paths(A, path_length)
        for ((i,j,distance),paths) in filter((x)->length(x[2])>0,memo)
            if (seen_distances[i,j] > distance) && (length(paths) > 0 )
                all_paths[(i,j)] = paths 
                seen_distances[i,j] = distance
            end 
        end 
    end
    return all_paths
end 


function enumerate_all_simple_paths(A::SparseMatrixCSC, p::Int)
    memo = Dict{Tuple{Int, Int, Int}, Vector{Vector{Int}}}()  # Memoize all_paths
    return memo,  enumerate_all_simple_paths!(memo,A, p)
end


function enumerate_all_simple_paths!(memo::Dict{NTuple{3,T}, Vector{Vector{T}}},A::SparseMatrixCSC, p::Int) where T 
    N = size(A, 1)  # Number of nodes in the graph
    #memo = Dict{Tuple{Int, Int, Int}, Vector{Vector{Int}}}()  # Memoize paths

    function find_paths(start::Int, target::Int, length::Int)
        # Check memoization to avoid redundant computation
        if haskey(memo, (start, target, length))
            return memo[(start, target, length)]
        end
        
        # Base case: if length is 1, the only paths are direct edges
        if length == 1
            paths = Vector{Int}[]
            if A[target,start] > 0 
                push!(paths,[start, target])
            end 
            memo[(start, target, length)] = paths
            return paths
        end
        
        # General case: build paths of length `length` from paths of length `length-1`
        paths = []
        for neighbor in findnz(A[:, start])[1]  # Only consider non-zero entries in the column
            # Recursive call to find all paths of length `length-1` from `neighbor` to `target`
            subpaths = find_paths(neighbor, target, length - 1)
            
            # Concatenate start node with each subpath if it doesn't revisit a node
            for subpath in subpaths
                if start ∉ subpath  # Ensures simple paths (no repeated vertices)
                    push!(paths, [start; subpath])
                end
            end
        end
        
        # Memoize the result to avoid recomputing
        memo[(start, target, length)] = paths
        return paths
    end

    # Gather all paths of length `p` between all pairs of vertices
    all_paths = Dict{Tuple{Int, Int}, Vector{Vector{Int}}}()
    for start in 1:N
        for target in 1:N#findnz(A[:, start])[2] 
            all_paths[(start, target)] = find_paths(start, target, p)
        end
    end
    return all_paths
end
