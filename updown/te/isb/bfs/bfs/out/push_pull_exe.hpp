#ifndef __push_pull_exe_H__
#define __push_pull_exe_H__

namespace push_pull_exe {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol DRAMalloc__dramalloc = 0;
    constexpr EventSymbol DRAMalloc__dramalloc_write_param_return = 1;
    constexpr EventSymbol DRAMalloc__global_broadcast = 2;
    constexpr EventSymbol DRAMalloc__node_broadcast = 3;
    constexpr EventSymbol DRAMalloc__updown_translation_install = 4;
    constexpr EventSymbol DRAMalloc__node_broadcast_return = 5;
    constexpr EventSymbol DRAMalloc__global_broadcast_return = 6;
    constexpr EventSymbol Broadcast__broadcast_global = 7;
    constexpr EventSymbol Broadcast__broadcast_node = 8;
    constexpr EventSymbol Broadcast__broadcast_ud = 9;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 10;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 11;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 12;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 13;
    constexpr EventSymbol BFS_pull__map_shuffle_reduce = 14;
    constexpr EventSymbol BFS_pull__finish_init_udkvmsr = 15;
    constexpr EventSymbol BFS_pull__broadcast_global = 16;
    constexpr EventSymbol BFS_pull__broadcast_node = 17;
    constexpr EventSymbol BFS_pull__broadcast_ud = 18;
    constexpr EventSymbol BFS_pull__broadcast_ud_fin = 19;
    constexpr EventSymbol BFS_pull__broadcast_node_fin = 20;
    constexpr EventSymbol BFS_pull__broadcast_global_fin = 21;
    constexpr EventSymbol BFS_pull__broadcast_value_to_scratchpad = 22;
    constexpr EventSymbol BFS_pull__init_input_kvset_on_lane = 23;
    constexpr EventSymbol BFS_pull__init_sp_lane = 24;
    constexpr EventSymbol BFS_pull__init_global_master = 25;
    constexpr EventSymbol BFS_pull__global_master = 26;
    constexpr EventSymbol BFS_pull__init_master_node = 27;
    constexpr EventSymbol BFS_pull__node_master = 28;
    constexpr EventSymbol BFS_pull__termiante_node_master = 29;
    constexpr EventSymbol BFS_pull__init_updown_master = 30;
    constexpr EventSymbol BFS_pull__updown_master = 31;
    constexpr EventSymbol BFS_pull__terminate_updown_master = 32;
    constexpr EventSymbol BFS_pull__lane_master_init = 33;
    constexpr EventSymbol BFS_pull__lane_master_loop = 34;
    constexpr EventSymbol BFS_pull__lane_master_read_partition = 35;
    constexpr EventSymbol BFS_pull__lane_master_get_next_return = 36;
    constexpr EventSymbol BFS_pull__lane_master_terminate = 37;
    constexpr EventSymbol BFS_pull__init_global_snyc = 38;
    constexpr EventSymbol BFS_pull__init_node_sync = 39;
    constexpr EventSymbol BFS_pull__ud_accumulate = 40;
    constexpr EventSymbol BFS_pull__global_sync_return = 41;
    constexpr EventSymbol BFS_pull__node_sync_return = 42;
    constexpr EventSymbol BFS_pull__ud_entry = 43;
    constexpr EventSymbol BFS_pull__ud_delay = 44;
    constexpr EventSymbol BFS_pull__kv_map_return = 45;
    constexpr EventSymbol BFS__init_node = 46;
    constexpr EventSymbol BFS__init_updown = 47;
    constexpr EventSymbol BFS__init_frontier_scratchpad = 48;
    constexpr EventSymbol BFS__init_lane = 49;
    constexpr EventSymbol BFS__init_updown_return = 50;
    constexpr EventSymbol BFS__fin_init_node = 51;
    constexpr EventSymbol BFS__init_global_sync = 52;
    constexpr EventSymbol BFS__global_sync = 53;
    constexpr EventSymbol BFS__init_node_sync = 54;
    constexpr EventSymbol BFS__node_sync = 55;
    constexpr EventSymbol sync_bfs__ud_entry = 56;
    constexpr EventSymbol BFS__ud_accumulate = 57;
    constexpr EventSymbol sync_bfs__ud_delay = 58;
    constexpr EventSymbol BFS__init_frontier = 59;
    constexpr EventSymbol BFS__insert_to_frontier = 60;
    constexpr EventSymbol BFS__allocate_frontier = 61;
    constexpr EventSymbol BFS__finish_read_frontier = 62;
    constexpr EventSymbol BFS__insert_ack = 63;
    constexpr EventSymbol BFS__init_updown_master = 64;
    constexpr EventSymbol BFS__updown_master_sync = 65;
    constexpr EventSymbol BFS__terminate_updown_master = 66;
    constexpr EventSymbol BFS__init_lane_master = 67;
    constexpr EventSymbol BFS__frontier_fetch_loop = 68;
    constexpr EventSymbol BFS__initialize_iteration = 69;
    constexpr EventSymbol BFS__broadcast_frontier_fetch = 70;
    constexpr EventSymbol BFS__broadcast_fetch_node = 71;
    constexpr EventSymbol BFS__finish_broadcast_fetch_return = 72;
    constexpr EventSymbol BFS__finish_fetch_return = 73;
    constexpr EventSymbol BFS__udkvmsr_return = 74;
    constexpr EventSymbol BFS__terminate_frontier = 75;
    constexpr EventSymbol BFS__terminate_frontier_node = 76;
    constexpr EventSymbol BFS__terminate_sync_node = 77;
    constexpr EventSymbol BFS__terminate_sync = 78;
    constexpr EventSymbol BFS__update_distance = 79;
    constexpr EventSymbol BFS__read_vertex = 80;
    constexpr EventSymbol BFS__store_ack = 81;
    constexpr EventSymbol BFS__update_sibling = 82;
    constexpr EventSymbol BFS__fetch_neighbors_remote = 83;
    constexpr EventSymbol BFS__fetch_neighbors_return = 84;
    constexpr EventSymbol BFS__receive_update = 85;
    constexpr EventSymbol BFS__fetch_vertex = 86;
    constexpr EventSymbol BFS__fetch_neighbors_local = 87;
    constexpr EventSymbol BFS_pull__kv_map = 88;
    constexpr EventSymbol BFS_pull__rd_nlist_return = 89;
    constexpr EventSymbol BFS_pull__read_vertex = 90;
    constexpr EventSymbol BFS_pull__read_orig_vertex = 91;
    constexpr EventSymbol BFS_pull__update_siblings = 92;
    constexpr EventSymbol BFS_pull__alloc_frontier = 93;
    constexpr EventSymbol BFS_pull__update_siblings_frontier = 94;
    constexpr EventSymbol BFS_pull__write_dram_return = 95;

} // namespace

#endif