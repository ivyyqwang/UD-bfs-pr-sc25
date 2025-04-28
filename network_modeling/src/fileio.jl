#=
Needed plotting subroutines
_load_queue_length_data(
_plot_queue_lengths_v2(
_load_msgs_per_latency_bin

=#

#
#   Routing Path FileIO 
#

function save_all_paths(all_paths, file_path, delimeter = ",")

    if endswith(file_path,".txt")
        write_mode = "w"
    elseif endswith(file_path,".bin")
        write_mode = "wb"
    end 
    open(file_path,write_mode) do f 
        for ((router_i,router_j), paths) in all_paths
            # for each path store:
            #  router_i, router_j, num_paths, path_length
            write(f, "$(router_i)$delimeter$(router_j)$delimeter$(length(paths))$delimeter$(length(first(paths)))")
            if length(first(paths)) > 2
                write(f,delimeter)
            end 
            for (i,path) in enumerate(paths)
                # write out all the paths with a different delimiter, these will be parsed back with the number of paths and their path lengths
                if length(path) > 0 
                    @assert path[1] == router_i && path[end] == router_j
                    if length(path) > 2
                        write(f, join(path[2:end-1],delimeter))
                    end
                    if i != length(paths)
                        write(f,delimeter)
                    end
                end
            end
            write(f,"\n")
        end 
    end

end 

function save_all_paths_v2(all_paths,file_path, delimeter = ",")
    """
    Now there are paths of different lengths. Must account for those 
    """

    #=
    if endswith(file_path,".txt")
        write_mode = "w"
    elseif endswith(file_path,".bin")
        write_mode = "wb"
    end 
    =#
    open(file_path,"w") do f 
        for ((router_i,router_j), paths) in all_paths

            # find the counts of the 
            sorted_paths = sort(paths,by=l->length(l))
            path_length_counts = Dict{Int,Int}()
            #path_length_counts = zeros(Int64, length(unique(length.(sorted_paths))))
            for path_len in length.(sorted_paths)
                path_len -= 1 # path is list of vertices, not explicit edges.
                if haskey(path_length_counts,path_len)
                    path_length_counts[path_len] += 1 
                else 
                    path_length_counts[path_len] = 1 
                end 
            end 
        
            # for each path store:
            #  router_i, router_j, num_paths, unique_length_num_path,...
            write(f, "$(router_i)$delimeter$(router_j)$delimeter$(length(paths))$delimeter$(length(path_length_counts))")
            #path_length = length(first(paths))-1
            # write out how many paths of different lengths are present 
            # ... ,path_length, num_paths_with_that_length
            for (path_len,path_length_count) in sort(path_length_counts)
                write(f,"$delimeter$(path_len)$delimeter$(path_length_count)")
            end 
            if !(length(sorted_paths) == 1 && haskey(path_length_counts,1)) 
                write(f,"$delimeter")
            end # don't write out this delimiter if the there's only 1 path that's of length 2. 

            for (i,path) in enumerate(sorted_paths)

                if length(path) == 2 
                    continue # don't write out anything, the information is in the header for this entry. 
                else 
                    # write out all the paths with a different delimiter, these will be parsed back with the number of paths and their path lengths
                    if length(path) > 0 
                        @assert path[1] == router_i && path[end] == router_j
                        if length(path) > 2
                            write(f, join(path[2:end-1],delimeter))
                        end
                        if i != length(paths)
                            write(f,delimeter)
                        end
                    end
                end 
            end
            write(f,"\n")
        end 
    end

end 



function load_all_paths(file_path, 
                        element_delimeter = ",")

    all_paths = Dict{Tuple{Int,Int},Vector{Vector{Int}}}()

    open(file_path,"r") do f
        for line in eachline(f)
            if line[end] == element_delimeter
                line = chop(line) # remove the last delimeter 
            end
            parsed_line = parse.(Int,split(line,element_delimeter))
            router_i, router_j, num_paths, path_length = parsed_line[1:4]
            
            if path_length == 2
                all_paths[(router_i,router_j)] = Vector{Int}[Int[router_i,router_j]]
            else
                all_paths[(router_i,router_j)] = Vector{Int}[]
                remaining_paths = parsed_line[5:end]
                @assert length(remaining_paths) == num_paths * (path_length-2)
                                                                # Subtracting 2 bc we don't store 
                                                                # router_i, and router_j in paths 
                for p = 1:num_paths
                    # recreate the path
                    path = Int[router_i]
                    for idx = 1:(path_length-2)
                        push!(path,remaining_paths[(p-1)*(path_length-2) + idx])
                    end 
                    push!(path, router_j)
                    # add the path onto the ongoing list
                    push!(all_paths[(router_i,router_j)],path)
                end 
            end
        end 
    end     

    return all_paths
end 


function load_all_paths_v2(file_path, 
                        element_delimeter = ",")

    all_paths = Dict{Tuple{Int,Int},Vector{Vector{Int}}}()

    open(file_path,"r") do f
        for line in eachline(f)
            if line[end] == element_delimeter
                line = chop(line) # remove the last delimeter 
            end
            parsed_line = parse.(Int,split(line,element_delimeter))
            router_i, router_j, num_paths, num_path_lengths = parsed_line[1:4]

            path_lengths = Dict{Int,Int}()
            for idx = 5:2:4 + num_path_lengths*2 
                path_lengths[parsed_line[idx]] = parsed_line[idx+1]
            end 

            remaining_paths = parsed_line[5 + num_path_lengths*2:end]
            @assert sum(values(path_lengths)) == num_paths
            all_paths[(router_i,router_j)] = Vector{Int}[]
            start_offset = 0
            for (path_length,paths_with_this_length) in sort(path_lengths)
                if path_length == 1
                    @assert paths_with_this_length == 1
                    push!(all_paths[(router_i,router_j)],[router_i,router_j])
                    #don't update offset, nothing's stored. 
                else
                    for p = 1:paths_with_this_length
                        path = Int[router_i]
                        for idx = 1:(path_length-1)
                            push!(path,remaining_paths[start_offset + (p-1)*(path_length-1) + idx])
                        end                                                 # only storing the routers between router_i and router_j
                        push!(path, router_j)
                        push!(all_paths[(router_i,router_j)],path)
                    end 
                    start_offset += (path_length-1)*paths_with_this_length
                end
            end 
        end 
    end     

    return all_paths
end 


#
#   PolarStar FileIO 
#

function enumerate_paths_between_polarstar(radix::Int=22)

    A = load_polarstar_network(radix)
    all_paths = @time all_simple_paths_up_to_p(A,3)
    #@time verify_found_paths(A,all_paths)

    save_all_paths(all_paths,DATA_LOC*"Polarstar.$(radix).iq.paths.txt")
    return all_paths
end 

function load_paths_between_polarstar(radix::Int=22)
    filename = DATA_LOC*"Polarstar.$(radix).iq.paths.txt"
    if isfile(filename)
        return load_all_paths(filename)
    else
        return enumerate_paths_between_polarstar(radix)
    end 

end

function load_polarstar_network(radix::Int=22)
    
    open(DATA_LOC*"Polarstar.$(radix).iq.adj.txt","r") do f 
        n, edges = parse.(Int,split(readline(f)," "))
        Is = Int[]
        Js = Int[]
        for (i,line) in enumerate(eachline(f))
            for j in split(line," ")
                if length(j) > 0 
                    push!(Is,i)
                    push!(Js,parse(Int,j) + 1)
                end
            end
        end
    return sparse(Is,Js,1.0,n,n)
    end
end 



#
#  Load binary files
#

function load_outputqueue_file(file)

    @assert occursin("outqueues",file)
    nodes = parse(Int,first(split(last(split(file,"Nodes:")),"-")))
    entries = filesize(file) ÷ sizeof(Float64)
    time_stamps = entries ÷ nodes
    return open(file,"r") do io; 
        read!(io,Matrix{Float64}(undef,nodes,time_stamps))
    end #TODO: should make the output be a Float64

end 


function load_latency_file(file)

    @assert occursin("latencies",file)
    nodes = parse(Int,first(split(last(split(file,"Nodes:")),"-")))
    entries = filesize(file) ÷ sizeof(Int)
    bin_counts = entries ÷ (nodes * nodes)
    #@assert bin_counts == 20
    return open(file,"r") do io; 
        read!(io,Array{Int64,3}(undef,bin_counts,nodes,nodes))
    end
end 

function load_router_to_router_queue_file(file)
    @assert occursin("r2rqueues",file)
    nodes = parse(Int,first(split(last(split(file,"Nodes:")),"-")))
    entries = filesize(file) ÷ sizeof(Float64)
    time_stamps = entries ÷ 72468 # need to make this more robust. 
    #@assert bin_counts == 20
    return open(file,"r") do io; 
        read!(io,Array{Float64,2}(undef,72468,time_stamps))
    end
end 