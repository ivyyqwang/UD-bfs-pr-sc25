function make_node2router_map(n::Integer, r::Integer, nodes_per_router::Integer)
    node2router = zeros(Int32, n)
    for i in eachindex(node2router)
      node2router[i] = n + (i-1 % r) + 1
    end
    return node2router
  end 