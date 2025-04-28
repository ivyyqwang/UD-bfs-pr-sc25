using Graphs, GraphPlayground


function visualize_load(sim, time_stamp)

    link_idx = Dict(Edge(e[1],e[2])=>idx for (idx,e) in enumerate(sim.links.links))
    g = Graph([Edge(e[1],e[2]) for e in sim.links.links])
    edge_color = [sim.network_stats.r2rqueue_lengths[time_stamp][link_idx[e]] for e in Graphs.edges(g)]
    log_edge_color = log10.(edge_color .+ 1.0)

    maximum(edge_color)

    p = playground(g;
        graphplot_options=(; edge_color=log_edge_color, 
        edge_attr = (colorrange=(0.0,maximum(log_edge_color)),
                    colormap="viridis"), 
        )
    )    
end 


function visualize_load(A::SparseMatrixCSC)

    g = Graph([Edge(i,j) for (i,j,_) in findnz(A)])
    edge_color = [10.0 for e in Graphs.edges(g)]
    log_edge_color = log10.(edge_color .+ 1.0)

    maximum(edge_color)

    p = playground(g;
        graphplot_options=(; edge_color=log_edge_color, 
        edge_attr = (colorrange=(0.0,maximum(log_edge_color)),
                    colormap="viridis"), 
        )
    )    
end 