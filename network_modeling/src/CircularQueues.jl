#
#  Circular Queue Implementation 
#
mutable struct CircularQueue{T}
    data::Vector{T}
    head::Int
    tail::Int
    size::Int
end

function CircularQueue{T}(size::Int) where T
    return CircularQueue{T}(Vector{T}(undef,size), 1, 1, 0)
end
function push!(q::CircularQueue{T}, item::T) where T
    if q.size == length(q.data)
        original_length = length(q.data)
        @info "resizing queue to $(original_length)"
        resize!(q.data,original_length*10)
        if q.head > 1
            # if head is > 1, then the data has wrapped around 
            # and we need to move it toto the new space allocated.
            for idx = 1:q.tail
                q.data[original_length + idx] = q.data[idx]
            end # just need to move everything before the tail, head:original_length is fine. 
        end
        q.tail += original_length
    end
    q.data[q.tail] = item
    q.tail = (q.tail % length(q.data)) + 1
    q.size += 1
end
function head(q::CircularQueue{T}) where T 
    return q.data[q.head]
end 
function popfirst!(q::CircularQueue{T}) where T
    if q.size == 0
        error("Queue is empty")
    end
    item = q.data[q.head]
    q.head = (q.head % length(q.data)) + 1
    q.size -= 1
    return item
end
function length(q::CircularQueue{T}) where T
    return q.size
end

function isempty(q::CircularQueue{T}) where T
    return q.size == 0
end

function clear!(q::CircularQueue{T}) where T 
    q.head = 1 
    q.tail = 1 
    q.size = 0 
end 