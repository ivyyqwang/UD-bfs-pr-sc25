#=
    Methods included here for generating random graph routines, not contained in
    MatrixNetworks.

    includes RMAT and Forest Fire graphs. 
=#
using Random
using SparseArrays
using MatrixNetworks

#
#  -- RMAT 
#

function rmat(scale) # must be lower-case to avoid clash with RMAT() type
    L = RMAT_lower_tri(scale)
    return max.(L,L')
end
function RMAT_lower_tri(scale)

    L = rmatedges_A(scale)

    L.nzval .= 1
    for i = 1:size(L,1)
        L[i,i] = 0
    end 
    dropzeros!(L)
    return L 
end 

function rmatedges_explicit_edges!(
	rng::AbstractRNG, 
	Is::Vector{TI},
	Js::Vector{TI},
	scale::Integer,ngenedges::Integer;
	a::Real = 0.57, b::Real=0.19, c::Real=0.19, 
	sym::Bool = true) where TI <: Integer 
	#ngenedges = avgdeg*2^scale 
	for ei in 1:ngenedges
		src::TI,dst::TI = 0,0 
		for i in 1:scale
			rval = rand(rng)
			if rval <= a
				src = (src << 1) + 0
				dst = (dst << 1) + 0
			elseif rval <= a+b
				src = (src << 1) + 0
				dst = (dst << 1) + 1			
			elseif rval <= a+b+c
				src = (src << 1) + 1
				dst = (dst << 1) + 0
			else
				src = (src << 1) + 1
				dst = (dst << 1) + 1
			end 
		end 
		if src != dst
			if sym && src > dst
				src,dst = dst,src
			end
		end
		push!(Is,src+1)
		push!(Js,dst+1)
	end  
	
	return Is,Js
end

rmatedges_explicit_edges!(Is,Js,scale::Integer,edge_count::Integer; kwargs...) = rmatedges_explicit_edges!(Random.GLOBAL_RNG, Is, Js, scale, edge_count; kwargs...)
rmatedges_explicit_edges(rng::AbstractRNG, scale::Integer,edge_count::Integer; kwargs...) = rmatedges_explicit_edges!(rng, Vector{Int}(undef,0),Vector{Int}(undef,0), scale, edge_count; kwargs...)
rmatedges_explicit_edges(scale::Integer,edge_count; kwargs...) = rmatedges_explicit_edges(Random.GLOBAL_RNG, scale, edge_count; kwargs...)
rmatedges_explicit_edges(scale::Integer; kwargs...) = rmatedges_explicit_edges(Random.GLOBAL_RNG, scale, 16*2^scale; kwargs...)

function rmatedges_A(scale::Integer, args...; kwargs...)
	Is,Js = rmatedges_explicit_edges(scale, args...;kwargs...)
	n = max(maximum(Is),maximum(Js))
	return sparse(Js,Is,1,n,n)
			# returns a lower triangular matrix 
end 


#
#  -- ForestFire 
#

"""
`forest fire graph`
===================

Generate a forest fire network with burn probability `burn_p` of `target_size`
from a given undirected `seed_network`. The final network is built one vertex at
a time which gain neighbors by "burning" the edges along a random walk starting
from a random pre-existing node. 

Input
-----
- 'A::Union{MatrixNetwork,SparseMatrixCSC}': An undirected seed Network. 
- 'target_sizes::Int': The final number of vertices of the target graph.
- 'burn_p::Float64': The probability of success when drawing the number of 
   neighbors to burn from a geometric distribution. 
- 'seed::Union{Nothing,UInt}' - An optional seed for the network.
- 'random_node::Int -> Int'  - The function to randomly select parents. 
Reference: 

    (section 4.2.1) Graph Evolution: Densification and Shrinking Diameters
    Jure Leskovec, Jon Kleinberg, Christos Faloutsos
    https://arxiv.org/pdf/physics/0603229.pdf

Functions
---------
* 'forest\\_fire\\_graph(n)' Generate an n node graph from a 10 node clique with a .4 
   burn probability. 
* 'forest\\_fire\\_graph(G,n,p)' Generate an n node graph from the seed graph G, with a 
   burn probability of p. 
* 'forest\\_fire\\_graph(::Type{S},G,n,p)' Generate an n node graph from the seed 
   graph G, with a probability of p for vertex labels of type S. 

Output
------
- 'G' - the newly generated network of the same type as `seed_network`.
- 'parents::Vector{Int}': The list of vertices selected to start the random
   walks from. Vertices who are their own parents are from the seed_network.
""" 
function forest_fire_graph(target_size::Int,m::Int=10, 
    burn_p::Float64=.4; kwargs...)
    clique = sprand(m,m,1.0)
    clique[1:(m+1):m^2] .= 0
    dropzeros!(clique)
    return forest_fire_graph(eltype(clique.rowval),clique,target_size,burn_p;kwargs...)
end 

forest_fire_graph(seed_network::SparseMatrixCSC,target_size::Int, burn_p::Float64;kwargs...) = 
                forest_fire_graph(eltype(seed_network.rowval),seed_network,target_size, burn_p; kwargs...)

forest_fire_graph(seed_network::MatrixNetwork,target_size::Int, burn_p::Float64;kwargs...) = 
                forest_fire_graph(eltype(seed_network.ci),seed_network,target_size, burn_p; kwargs...)

function forest_fire_graph(::Type{S},seed_network::Union{MatrixNetwork,SparseMatrixCSC}, 
                           target_size::Int, burn_p::Float64;
                           rng::AbstractRNG=Random.GLOBAL_RNG,
                           random_node=x->rand(rng,1:x)) where S

    graph_size = size(seed_network,1)
    steps = target_size - graph_size
    parents = Vector{S}(undef,target_size)
    parents[1:graph_size] .= 1:graph_size

    toburn = Set{S}()
    burnt = Set{S}()
    burning = Set{S}()

    alive = Vector{S}(undef,0)


    #  -- convert seed_graph to List of Lists format -- #
    neighbors = matrix_to_list_of_list(S,seed_network) # assuming symmetric network
    for _ = 1:steps
        push!(neighbors,Vector{S}(undef,0))
    end

    for v_i = (graph_size+1):target_size
        parent = random_node(graph_size)
        
        new_v = graph_size+1
        burn!(neighbors,neighbors[new_v],parent,burn_p,
              toburn,burnt,burning,alive;rng)

        parents[v_i] = parent
        graph_size += 1

        #symmetrize the neighbor list with the new neighbors of new_v
        for v_j in neighbors[new_v]
            push!(neighbors[v_j],new_v)
        end 

    end 
    
    return list_of_list_to_matrix(typeof(seed_network),neighbors), parents
end 

"""
`burn`
======

Produce a list of vertices randomly traversed (a.k.a "burned"), starting from
`v0` in a MatrixNetwork `A`. The number of edges selected at each step is 
determined by a geometric distribution with success rate `p`.

Input
-----
- `A::Union{MatrixNetwork,SparseMatrixCSC}`: An undirected seed Network. 
- `v0 <:Integer`: The starting node of the random walk. 
- `p::Float64`: The geometric distribution's success probability for selecting
  the edges in the random walk. 

Output
------
- `walked_edges::Vector{S}`: The final produced neighbor list from the burn 
  process. 

See also [`forest_fire_graph`](@ref), [`burn!`](@ref)
""" 
function burn(A::MatrixNetwork,v0::S,p;kwargs...) where S

    walked_edges = Vector{S}(undef,0)
    burn!(A,walked_edges,v0,p;kwargs...)
    return walked_edges
end 

function burn(A::SparseMatrixCSC{S,T},args...;kwargs...) where {S,T}
    burn(MatrixNetwork(copy(A')),args...;kwargs...)
end

"""
`burn!`
=======

Update the array `walked_edges` with vertices traversed in a random walk (a.k.a
"burning") starting from `v0` in `A`. `A` is either a MatrixNetwork or a edge 
list representation. The number of edges selected at each step of the walk is
determined by a geometric distribution with success rate `p`.

Input
-----
- `neighbor::Union{Vector{Vector{S}},MatrixNetwork{T}}`: The graph being walked.
- `walked_edges::Vector{S}`: Array to store the vertices visited on the walk. 
- `v0 <: Integer`: The starting vertex of the random walk. 
- `p::Float64`: The geometric distribution's success probability for selecting
  the edges in the random walk. 

Functions
---------
* `burn!(A,walked_edges,v0,p)` Same as below, but returns initialized variables
  for reuse (fewer allocations). 
* burn!(A,walked_edges,v0,p,toburn,burnt,burning,alive) Updates the Array 
  `walked_edges` with vertices visted from a random walk starting at `v0`, which
  keeps edges proportional to geomdist(`p`). `toburn`, `burnt`, `burning`,and 
  `alive` are variables used for running the walk, and are returned for reuse if
  the routine is going to be run multiple times. These variables have no 
  assumption of their contents and have `empty!` called on them at the beginning
  of the routine. 

See also [`forest_fire_graph`](@ref), [`burn`](@ref)
""" 
function burn!(A::Union{Vector{Vector{S}},MatrixNetwork{T}},
               walked_edges::Vector{S},v0::S,p::Float64;kwargs...) where {S,T}

    toburn = Set{S}()
    burnt = Set{S}()
    burning = Set{S}()
    alive = Vector{S}(undef,0)
    burn!(A,walked_edges,v0,p,toburn,burnt,burning,alive;kwargs...)
    
    return toburn,burnt,burning,alive
        # returned for optional reuse
end

function burn!(A::Union{Vector{Vector{S}},MatrixNetwork{T}},
               walked_edges::Vector{S},v0::Int,p::Float64,
               toburn::Set{S},burnt::Set{S},burning::Set{S},alive::Vector{S};
               rng::AbstractRNG=Random.GLOBAL_RNG) where {T,S} 

    empty!(toburn)
    empty!(burnt)
    empty!(burning)
    empty!(alive)

    push!(walked_edges,v0)
    push!(toburn,v0)
    push!(burnt,v0)

    while (length(toburn) > 0)
        # -- burning = toburn -- # 
        empty!(burning)
        for v in toburn
            push!(burning,v)
        end 
        empty!(toburn)

        # -- randomly walk v's edges, visited nodes become v_new's neighbors -- # 
        for v in burning
            
            empty!(alive)

            for j in _get_neighbors_to_burn(A,v)
                if !(j in burnt)
                    push!(alive,j)
                end
            end

            if length(alive) > 0 #add `#' of survivors to v_new's neighbor list
                
                shuffle!(alive)

                y = Int(floor(log(rand(rng))/log(p))) 
                             # geometric_dist(1-p)
                new_edges = min(y, length(alive))

                for i=1:new_edges
                    push!(toburn,alive[i])
                    push!(burnt,alive[i])
                    push!(walked_edges,alive[i])
                end
            end 
        end 
    end
end 

function _get_neighbors_to_burn(A::MatrixNetwork,v::Int)
    edges,_ =  _get_outedges(A,v)
    return edges
end 

function _get_neighbors_to_burn(A::Vector{Vector{S}},v::Int) where S
    return A[v]
end 

matrix_to_list_of_list(A::MatrixNetwork) = matrix_to_list_of_list(eltype(A.ci),A)
matrix_to_list_of_list(A::SparseMatrixCSC) = matrix_to_list_of_list(eltype(A.rowval),A)


function matrix_to_list_of_list(::Type{S}, A::MatrixNetwork) where S 
    
    neighbors = Vector{Vector{S}}(undef,A.n)

    for i = 1:A.n
        @inbounds edges,_ = _get_outedges(A,i)
        neighbors[i] = collect(edges)
    end 
    return neighbors

end 

function matrix_to_list_of_list(::Type{S}, A::SparseMatrixCSC) where S 
    
    At = copy(A')

    neighbors = Vector{Vector{S}}(undef,At.n)

    for i = 1:At.n
        @inbounds edges,_ = _get_inedges(At,i)
        neighbors[i] = collect(edges)
    end 
    return neighbors

end 


function list_of_list_to_matrix(::Type{MatrixNetwork{T}}, neighbors::Vector{Vector{S}}) where {S,T}
    return MatrixNetwork(list_of_list_to_matrix(SparseMatrixCSC{T,S},neighbors))
end 

function list_of_list_to_matrix(::Type{SparseMatrixCSC{T1,T2}}, neighbors::Vector{Vector{S}}) where {S,T1,T2} 

    Is = S[]
    Js = S[] 
    n = length(neighbors)

    for (v_i,v_i_neighbors) in enumerate(neighbors)
        for v_j in v_i_neighbors
            push!(Is,v_i)
            push!(Js,v_j)
        end 
    end 

    return sparse(Is,Js,1,n,n)
end 


"""
'_get_inedges'
==========
Helper function to extract out a column of a SparseMatrixCSC.

Output
------
- 'nz_indices'::Array{Int,1}: non-zero column indices.
- 'nz_weights'::Array{T,1}: non-zero weights.

"""
function _get_inedges(A::SparseMatrixCSC{S,T},i::Int) where {S,T}

    @boundscheck (i >= 1 && i <= size(A,1)) || throw(ArgumentError("i must be in {1,...,$(size(A,1))}"))
    return (A.rowval[offset] for offset in A.colptr[i]:A.colptr[i+1]-1), (A.nzval[offset] for offset in A.colptr[i]:A.colptr[i+1]-1)
 
 end
