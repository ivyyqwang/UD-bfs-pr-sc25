#ifndef __pagerank_msr_H__
#define __pagerank_msr_H__

namespace pagerank_msr {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol PageRankMSR__kv_map = 0;
    constexpr EventSymbol PageRankMSR__rd_nlist_return = 1;
    constexpr EventSymbol InitUpDown__init = 2;
    constexpr EventSymbol InitUpDown__terminate = 3;
    constexpr EventSymbol Broadcast__broadcast_global = 4;
    constexpr EventSymbol Broadcast__broadcast_node = 5;
    constexpr EventSymbol Broadcast__broadcast_ud = 6;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 7;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 8;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 9;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 10;
    constexpr EventSymbol PageRankMSR__map_shuffle_reduce = 11;
    constexpr EventSymbol PageRankMSR__finish_init_udkvmsr = 12;
    constexpr EventSymbol PageRankMSR__broadcast_global = 13;
    constexpr EventSymbol PageRankMSR__broadcast_node = 14;
    constexpr EventSymbol PageRankMSR__broadcast_ud = 15;
    constexpr EventSymbol PageRankMSR__broadcast_ud_fin = 16;
    constexpr EventSymbol PageRankMSR__broadcast_node_fin = 17;
    constexpr EventSymbol PageRankMSR__broadcast_global_fin = 18;
    constexpr EventSymbol PageRankMSR__broadcast_value_to_scratchpad = 19;
    constexpr EventSymbol PageRankMSR__init_input_kvset_on_lane = 20;
    constexpr EventSymbol PageRankMSR__init_output_kvset_on_lane = 21;
    constexpr EventSymbol PageRankMSR__init_sp_lane = 22;
    constexpr EventSymbol PageRankMSR__init_global_master = 23;
    constexpr EventSymbol PageRankMSR__global_master = 24;
    constexpr EventSymbol PageRankMSR__cache_flush = 25;
    constexpr EventSymbol PageRankMSR__cache_flush_return = 26;
    constexpr EventSymbol PageRankMSR__init_node_master = 27;
    constexpr EventSymbol PageRankMSR__node_master = 28;
    constexpr EventSymbol PageRankMSR__termiante_node_master = 29;
    constexpr EventSymbol PageRankMSR__init_updown_master = 30;
    constexpr EventSymbol PageRankMSR__updown_master = 31;
    constexpr EventSymbol PageRankMSR__terminate_updown_master = 32;
    constexpr EventSymbol PageRankMSR__lane_master_init = 33;
    constexpr EventSymbol PageRankMSR__lane_master_loop = 34;
    constexpr EventSymbol PageRankMSR__lane_master_read_partition = 35;
    constexpr EventSymbol PageRankMSR__lane_master_get_next_return = 36;
    constexpr EventSymbol PageRankMSR__lane_master_terminate = 37;
    constexpr EventSymbol PageRankMSR__init_global_snyc = 38;
    constexpr EventSymbol PageRankMSR__init_node_sync = 39;
    constexpr EventSymbol PageRankMSR__ud_accumulate = 40;
    constexpr EventSymbol PageRankMSR__global_sync_return = 41;
    constexpr EventSymbol PageRankMSR__node_sync_return = 42;
    constexpr EventSymbol PageRankMSR__ud_entry = 43;
    constexpr EventSymbol PageRankMSR__ud_delay = 44;
    constexpr EventSymbol PageRankMSR__kv_map_emit = 45;
    constexpr EventSymbol PageRankMSR__kv_reduce_emit = 46;
    constexpr EventSymbol PageRankMSR__kv_map_return = 47;
    constexpr EventSymbol PageRankMSR__init_reduce_thread = 48;
    constexpr EventSymbol PageRankMSR__combine_get_pair = 49;
    constexpr EventSymbol PageRankMSR__combine_put_pair_ack = 50;
    constexpr EventSymbol PageRankMSR__kv_reduce_return = 51;
    constexpr EventSymbol PageRankMSR__combine_flush_lane = 52;
    constexpr EventSymbol PageRankMSR__combine_flush_ack = 53;

} // namespace

#endif