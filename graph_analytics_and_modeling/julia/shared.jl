# ] add JSON, MAT, MatrixNetworks, SparseArrays, Conda, PyCall, GenericArpack, LinearAlgebra, StatsBase, SNAPDatasets
using MAT 
using MatrixNetworks
using SparseArrays
using JSON

using NearestNeighbors: BallTree, knn
using Random: seed!

PROJECT_LOC = "../"
if PROJECT_LOC == "../"
   println("  WARNING: `PROJECT_LOC` is uninitialized and currently using parent directory of `julia` folder.\n  Please set to absolute path of where project location is installed.")
end 
    

PYTHON_LOC = PROJECT_LOC*"python/"

DATA_LOC = PROJECT_LOC*"data/"
RANDOM_GRAPHS = DATA_LOC*"randomGraphs/"
SNAP_GRAPHS = DATA_LOC*"SNAP/"
const RESULTS_LOC = DATA_LOC*"julia_output/"


function get_undirected_neighbors(A::MatrixNetwork,i::Int)
	return @view A.ci[A.rp[i]:A.rp[i+1]-1]
end 

function get_undirected_degree(A::MatrixNetwork,i::Int)
	return A.rp[i+1]-A.rp[i]
end 
function get_undirected_degree(A::SparseMatrixCSC{T,Int},i::Int) where T
	return length(nzrange(A,i))#(length(nzrange(A,i)) for i = 1:size(A,1))
end 

function get_undirected_neighbors(A::SparseMatrixCSC{T,Int}, i::Int) where T
	rowval = rowvals(A)
	return (rowval[j] for j in nzrange(A,i))
end 

function SparseArrays.nnz(A::MatrixNetwork)
    return length(A.vals)
end 

#
#  -- FileIO
#

#  -- Experiment Results FileIO 

function save_output_to_json(testing::Bool, filename, result_dict)
    folder = RESULTS_LOC
    if testing
        folder *= "test/"
    end 
    if !ispath(folder)
        mkpath(folder)
    end 
    t = @timed begin
        open(folder*filename,"w") do f
            JSON.print(f,result_dict)
        end 
        # saving in JSON is less memory efficient, but more robust to reopen. 
    end
    println("saved: $(filename)\n in $(t) seconds.\n")
end


function load_output_from_json(filename::String)
    output = JSON.parsefile(filename)
    return load_output_from_json(output)
end

function load_output_from_json(output::Dict)

    # json saves ND-Arrays as recursive list of lists. 
    # Reshape them back into their original shape. 
    for (key,val) in output 
        if typeof(first(val)) <: Vector 
            output[key] = vector_of_vectors_to_array(val)
        else 
            if typeof(val) <: Vector 
                output[key] = Vector{typeof(first(val))}(val)
            end # need to tell julia what the type of the vectors loaded are. 
        end
    end
    return output
end 

#  -- Graph FileIO 




function load_graph(file, delimiter = " ")

    if endswith(file,".mat")
        matfile = matread(file)
        A = matfile["A"] # NOTE: this may fail depending on how it was saved
    elseif endswith(file,".smat")
        #A = MatrixNetworks.readSMAT(DATA_LOC*file)
        println("loading smat file:$(file)")
        A = load_edge_file(file,delimiter)
    elseif endswith(file,".txt")
        println("loading txt file:$(file)")
        A,_ = load_txt_edge_file(file)
    else
        throw(error("file:$(file)\n has is an unsupported file format.\n Expecting '.smat' or '.mat'")) 
    end 

    #symmetrize the networks and reduce to largest component
    A = max.(A,A')
    A,_ = largest_component(A)
    return A 

end 


#TODO: make file list version with pmap too? 
function load_edge_file(filename, delimiter=" ")
    n, nnzs = -1, -1
    Is, Js = Int[], Int[]
    
    open(filename,"r") do file
        header = readline(file)
        n, _, nnzs = parse.(Int,split(rstrip(header), delimiter))
        #n = parse(Int, n)
        #nnzs = parse(Int, nnzs)
        Is = Vector{Int}(undef, nnzs)
        Js = Vector{Int}(undef, nnzs)

        for idx in 1:nnzs
            line = readline(file)
            i, j = parse.(Int,split(line, delimiter))
            Is[idx] = i + 1
            Js[idx] = j + 1
                     # files generated with python
                     # convert 0 indexing to 1.  
        end
    end

    # Create a sparse matrix from I, J, and a vector of ones for the data
    sparse_matrix = sparse(Is, Js, 1, n, n)
    return sparse_matrix
end

function load_txt_edge_file(filename)
    Is, Js = Int[], Int[]

    id_to_idx = Dict{Int,Int}()
    next_id = 1
    open(filename,"r") do file
        for line in eachline(file)
            if startswith(line,"#")
                continue 
            end 

            i_id,j_id = parse.(Int,split(rstrip(line)))

            if !haskey(id_to_idx,i_id)
                id_to_idx[i_id] = next_id
                next_id +=1 
            end 

            if !haskey(id_to_idx,j_id)
                id_to_idx[j_id] = next_id
                next_id +=1 
            end 

            push!(Is,id_to_idx[i_id]); push!(Js,id_to_idx[j_id])
        end
    end

    n = maximum(Is)
    m = maximum(Js)
    # Create a sparse matrix from I, J, and a vector of ones for the data
    return sparse(Is, Js, 1, max(n,m), max(n,m)), id_to_idx
end


function save_edge_list(A, output_file, delimiter = " ")
    """-------------------------------------------------------------------------
        Note that this file will save the graphs as 0 indexed files because we 
      plan to use Python with them.
    -------------------------------------------------------------------------"""
    open(output_file,"w") do file 
        write(file,"$(size(A,1))$(delimiter)$(size(A,2))$(delimiter)$(nnz(A))\n")
        for (i,j,_) in zip(findnz(A)...)
            write(file,"$(i-1)$(delimiter)$(j-1)\n")
        end 
    end 
end 



function vector_of_vectors_to_array(vector_of_vectors::V) where {V <: AbstractVector}

    components = vector_of_vectors
    sizes = Int[length(components)]
    while typeof(first(components)) <: Vector 
        
        dim_size = isnothing(first(components)) ? 1 : length(first(components))
        components = vcat(components...)
    
        if all(isnothing.(components))
            push!(sizes,dim_size)
            break
        end 

        if all(length.(components) .== (isnothing(first(components)) ? 1 : length(first(components))))
            push!(sizes,dim_size)
        else
            push!(sizes,dim_size)
            break
        end    # may have irregular nested arrays 
    end 

    X::Array{typeof(first(components)),length(sizes)} = reshape(components,reverse(sizes)...)
    return X # Compiler won't be able to infer what the type of 
             # the array is so we need to explicitly tell it. 
end 

function vector_of_vectors_to_array_v2(vector_of_vectors::V) where {V <: AbstractVector}

    components = vector_of_vectors
    sizes = Int[length(components)]
    while typeof(first(components)) <: Vector 
        dim_size = length(first(components))
        components = vcat(components...)
        if all(length.(components) .== length(first(components)))
            push!(sizes,dim_size)
        end    # may have irregular nested arrays 
        println(sizes)
    end 

    X::Array{typeof(first(components)),length(sizes)} = reshape(components,reverse(sizes)...)
    return X # Compiler won't be able to infer what the type of 
             # the array is so we need to explicitly tell it. 
end 

function log_iter_bins(max_val)

    max_10_pow = nextpow(10,max_val)
    phases = Int(log10(max_10_pow))

    bins = Int[1]
    for i = 1:phases 
        append!(bins,2*10^(i-1):10^(i-1):10^i)
    end 
    
    return bins
end 
