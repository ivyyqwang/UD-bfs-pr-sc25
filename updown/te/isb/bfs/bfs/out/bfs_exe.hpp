#ifndef __bfs_exe_H__
#define __bfs_exe_H__

namespace bfs_exe {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol DRAMalloc__dramalloc = 0;
    constexpr EventSymbol DRAMalloc__dramalloc_write_param_return = 1;
    constexpr EventSymbol DRAMalloc__global_broadcast = 2;
    constexpr EventSymbol DRAMalloc__node_broadcast = 3;
    constexpr EventSymbol DRAMalloc__updown_translation_install = 4;
    constexpr EventSymbol DRAMalloc__node_broadcast_return = 5;
    constexpr EventSymbol DRAMalloc__global_broadcast_return = 6;
    constexpr EventSymbol BFS__init_node = 7;
    constexpr EventSymbol BFS__init_updown = 8;
    constexpr EventSymbol BFS__init_frontier_scratchpad = 9;
    constexpr EventSymbol BFS__init_lane = 10;
    constexpr EventSymbol BFS__init_updown_return = 11;
    constexpr EventSymbol BFS__fin_init_node = 12;
    constexpr EventSymbol BFS__init_global_sync = 13;
    constexpr EventSymbol BFS__global_sync = 14;
    constexpr EventSymbol BFS__init_node_sync = 15;
    constexpr EventSymbol BFS__node_sync = 16;
    constexpr EventSymbol sync_bfs__ud_entry = 17;
    constexpr EventSymbol BFS__ud_accumulate = 18;
    constexpr EventSymbol sync_bfs__ud_delay = 19;
    constexpr EventSymbol BFS__init_frontier = 20;
    constexpr EventSymbol BFS__insert_to_frontier = 21;
    constexpr EventSymbol BFS__finish_read_frontier = 22;
    constexpr EventSymbol BFS__insert_ack = 23;
    constexpr EventSymbol BFS__init_updown_master = 24;
    constexpr EventSymbol BFS__updown_master_sync = 25;
    constexpr EventSymbol BFS__terminate_updown_master = 26;
    constexpr EventSymbol BFS__init_lane_master = 27;
    constexpr EventSymbol BFS__frontier_fetch_loop = 28;
    constexpr EventSymbol BFS__broadcast_frontier = 29;
    constexpr EventSymbol BFS__broadcast_frontier_fetch = 30;
    constexpr EventSymbol BFS__finish_fetch_return = 31;
    constexpr EventSymbol BFS__terminate_frontier = 32;
    constexpr EventSymbol BFS__terminate_sync = 33;
    constexpr EventSymbol BFS__update_distance = 34;
    constexpr EventSymbol BFS__read_vertex = 35;
    constexpr EventSymbol BFS__store_ack = 36;
    constexpr EventSymbol BFS__update_sibling = 37;
    constexpr EventSymbol BFS__receive_update = 38;
    constexpr EventSymbol BFS__fetch_vertex = 39;
    constexpr EventSymbol BFS__fetch_neighbors = 40;

} // namespace

#endif