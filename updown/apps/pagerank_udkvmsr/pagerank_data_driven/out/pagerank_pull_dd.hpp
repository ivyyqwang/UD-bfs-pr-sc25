#ifndef __pagerank_pull_dd_H__
#define __pagerank_pull_dd_H__

namespace pagerank_pull_dd {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol DRAMalloc__dramalloc = 0;
    constexpr EventSymbol DRAMalloc__dramalloc_write_param_return = 1;
    constexpr EventSymbol DRAMalloc__global_broadcast = 2;
    constexpr EventSymbol DRAMalloc__node_broadcast = 3;
    constexpr EventSymbol DRAMalloc__updown_translation_install = 4;
    constexpr EventSymbol DRAMalloc__node_broadcast_return = 5;
    constexpr EventSymbol DRAMalloc__global_broadcast_return = 6;
    constexpr EventSymbol PageRankPullDD__kv_map = 7;
    constexpr EventSymbol PageRankPullDD__rd_nlist_return = 8;
    constexpr EventSymbol PageRankPullDD__read_nbor_vertex = 9;
    constexpr EventSymbol PageRankPullDD__update_value = 10;
    constexpr EventSymbol PageRankPullDD__rd_nlist_return_update = 11;
    constexpr EventSymbol PageRankPullDD__write_value_ack = 12;
    constexpr EventSymbol InitUpDown__init = 13;
    constexpr EventSymbol InitUpDown__terminate = 14;
    constexpr EventSymbol Broadcast__broadcast_global = 15;
    constexpr EventSymbol Broadcast__broadcast_node = 16;
    constexpr EventSymbol Broadcast__broadcast_ud = 17;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 18;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 19;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 20;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 21;
    constexpr EventSymbol PageRankPullDD__map_shuffle_reduce = 22;
    constexpr EventSymbol PageRankPullDD__finish_init_udkvmsr = 23;
    constexpr EventSymbol PageRankPullDD__broadcast_global = 24;
    constexpr EventSymbol PageRankPullDD__broadcast_node = 25;
    constexpr EventSymbol PageRankPullDD__broadcast_ud = 26;
    constexpr EventSymbol PageRankPullDD__broadcast_ud_fin = 27;
    constexpr EventSymbol PageRankPullDD__broadcast_node_fin = 28;
    constexpr EventSymbol PageRankPullDD__broadcast_global_fin = 29;
    constexpr EventSymbol PageRankPullDD__broadcast_value_to_scratchpad = 30;
    constexpr EventSymbol PageRankPullDD__init_input_kvset_on_lane = 31;
    constexpr EventSymbol PageRankPullDD__init_sp_lane = 32;
    constexpr EventSymbol PageRankPullDD__init_global_master = 33;
    constexpr EventSymbol PageRankPullDD__global_master = 34;
    constexpr EventSymbol PageRankPullDD__init_master_node = 35;
    constexpr EventSymbol PageRankPullDD__node_master = 36;
    constexpr EventSymbol PageRankPullDD__termiante_node_master = 37;
    constexpr EventSymbol PageRankPullDD__init_updown_master = 38;
    constexpr EventSymbol PageRankPullDD__updown_master = 39;
    constexpr EventSymbol PageRankPullDD__terminate_updown_master = 40;
    constexpr EventSymbol PageRankPullDD__lane_master_init = 41;
    constexpr EventSymbol PageRankPullDD__lane_master_loop = 42;
    constexpr EventSymbol PageRankPullDD__lane_master_read_partition = 43;
    constexpr EventSymbol PageRankPullDD__lane_master_get_next_return = 44;
    constexpr EventSymbol PageRankPullDD__lane_master_terminate = 45;
    constexpr EventSymbol PageRankPullDD__init_global_snyc = 46;
    constexpr EventSymbol PageRankPullDD__init_node_sync = 47;
    constexpr EventSymbol PageRankPullDD__ud_accumulate = 48;
    constexpr EventSymbol PageRankPullDD__global_sync_return = 49;
    constexpr EventSymbol PageRankPullDD__node_sync_return = 50;
    constexpr EventSymbol PageRankPullDD__ud_entry = 51;
    constexpr EventSymbol PageRankPullDD__ud_delay = 52;
    constexpr EventSymbol PageRankPullDD__kv_map_return = 53;

} // namespace

#endif