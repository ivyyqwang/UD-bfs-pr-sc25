using MatrixNetworks 
using SparseArrays 
using Random: seed!


function test()

    seed!(4323443)
    n = 100
    A = sprand(n,n,.1); A = max.(A,A');
    A.nzval .= 1.0 

    v0 = 10 
    max_k = 3
    return A, test(A, v0, max_k)
end 


function test(A,v0, max_k)
    vertex_T = eltype(A.rowval)


    dist, dt, pred = bfs(A,v0)
    dist_perm = sortperm(dist)

    paths_by_length = Vector{Vector{Vector{vertex_T}}}(undef,max_k)

    for k in 1:max_k
        paths_by_length[k] = Vector{Vector{vertex_T}}(undef,0)
    end     

    for u_idx in dist_perm

        d,p = dist[u_idx], pred[u_idx];
        if d == 0
            continue 
        end 

        path = vertex_T[u_idx]
        while p != v0 
            push!(path,p)
            p = pred[p]
        end

        push!(paths_by_length[d],path)
    end 


    return paths_by_length
end


function paths_from_vertex_i_to_all(A,v,k) 
    v_type = eltype(A.rowval)
    piall = Vector{Vector{Vector{v_type}}}(undef,k)

    for idx = 1:k 
        piall[idx] = Vector{v_type}[]
    end 


    piall[k][v] # vector of vectors of paths of length k from i to v.
    
    #piall[0][i] = [[i]] # this is a list of lists. 
    #piall[0][!u] = nothing
    
    for k=1:maxk 
        # for each edge 
        for dst in 1:size(A,2)
            for offset in A.colptr[j]
                src = A.rowval[offset]
                # check if we can extend a path with this edge...
                if piall[k-1][src] != nothing 
                # then we can extend the edge, unless dst is already in the path.
                    for p in piall[k-1][src]
                        if !(dst in p)
                        # add a new path with dst
                        newp = [p...,dst]
                        push!(piall[k-1][src], append(p))
                        end
                    end 
                end
            end
        end 
    end	 
          
    return piall
end 


