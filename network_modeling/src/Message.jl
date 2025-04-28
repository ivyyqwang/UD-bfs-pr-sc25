
abstract type Message end 


struct Message_v1 <: Message
    src::Int32
    dst::Int32
    start_time::Int32
    place::Int32 
end

where_is(m::Message) = m.place
get_source(m::Message) = m.src
get_destination(m::Message) = m.dst
get_send_time(m::Message) = m.start_time

update_place(m::Message_v1, p::Int32) = Message_v1(m.src, m.dst, m.start_time, p)
                                       # not sure if there's a way to do this based on the constructor of the subtype. 

struct Message_v2 <: Message
    src::Int32
    dst::Int32
    start_time::Int32
    place::Int32 
    reroute_dst::Int32
end # has an extra reroute dst for 
update_place(m::Message_v2, p::Int32) = Message_v2(m.src, m.dst, m.start_time, p, m.reroute_dst)
update_reroute_destination_to_visited(m::Message_v2) = Message_v2(m.src, m.dst, m.start_time, m.reroute_dst, Int32(-1))
                                                                                            # only calling this if we've made it. 
get_reroute_destination(m::Message_v2) = m.reroute_dst
