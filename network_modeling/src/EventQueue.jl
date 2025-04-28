"""
    EventQueue

Create a calendar queue for a discrete event simulator with a 
circular backing array. This assumes a discrete integer time model.
And puts a finite limit on the max time that can be scheduled into
the future. 
"""
mutable struct EventQueue{T}
    events::Vector{Vector{T}}
    headposition::Int
    headtime::Int
    enqued_events::Int
end 

EventQueue(T::Type, maxtime::Int) = init!(EventQueue{T}(Vector{Vector{T}}(undef,maxtime), 1, 0, 0))

function init!(Q::EventQueue{T}) where T
    for i = 1:length(Q.events)
        Q.events[i] = Vector{T}(undef,0)
        sizehint!(Q.events[i],1000000) # expecting at least 100 messages
    end 
    return Q
end 

"""
    clear_head_and_step(q::EventQueue)

Clear the entries at the head of the queue
and move the head position and time forward by one.
"""
function clear_head_and_step(q::EventQueue)
    q.enqued_events -= length(q.events[q.headposition])
    empty!(q.events[q.headposition]) # empty the head position
    q.headposition = (q.headposition % length(q.events)) + 1 # move the head position
    q.headtime += 1 # move the head time
end 

"""
    schedule!(q::EventQueue, m::Message, t::Int)

Schedule a message for the event queue at a future time. 
"""
function schedule!(q::EventQueue{T}, m::T, t::Integer) where T
    # find the time offset from the head time
    offset = t - q.headtime
    @assert offset > 0 "Cannot schedule a message in the past"
    # make sure we aren't scheduling too far into the future...
    @assert offset < length(q.events) "Cannot schedule a message too far into the future"
    # schedule the message in light of the circular queue structure
    idx = (q.headposition + offset - 1) % length(q.events) + 1

    push!(q.events[idx], m)
    q.enqued_events += 1
end

"""
    head(q::EventQueue)
Return the list of events at the head of the queue
"""
function head(q::EventQueue)
    return q.events[q.headposition]
end

function clear!(q::EventQueue)
    empty!.(q.events)
    q.headposition = 1
    q.headtime = 0
    q.enqued_events = 0
end 
