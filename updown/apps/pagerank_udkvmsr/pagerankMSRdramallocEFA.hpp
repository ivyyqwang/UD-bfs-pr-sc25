#ifndef __pagerankMSRdramallocEFA_H__
#define __pagerankMSRdramallocEFA_H__

namespace pagerankMSRdramallocEFA {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol Broadcast__broadcast_global = 0;
    constexpr EventSymbol Broadcast__broadcast_node = 1;
    constexpr EventSymbol Broadcast__broadcast_ud = 2;
    constexpr EventSymbol Broadcast__broadcast_ud_fin = 3;
    constexpr EventSymbol Broadcast__broadcast_node_fin = 4;
    constexpr EventSymbol Broadcast__broadcast_global_fin = 5;
    constexpr EventSymbol Broadcast__broadcast_value_to_scratchpad = 6;
    constexpr EventSymbol pr__map_shuffle_reduce = 7;
    constexpr EventSymbol pr__finish_init_udkvmsr = 8;
    constexpr EventSymbol pr__broadcast_global = 9;
    constexpr EventSymbol pr__broadcast_node = 10;
    constexpr EventSymbol pr__broadcast_ud = 11;
    constexpr EventSymbol pr__broadcast_ud_fin = 12;
    constexpr EventSymbol pr__broadcast_node_fin = 13;
    constexpr EventSymbol pr__broadcast_global_fin = 14;
    constexpr EventSymbol pr__broadcast_value_to_scratchpad = 15;
    constexpr EventSymbol pr__init_input_kvset_on_lane = 16;
    constexpr EventSymbol pr__init_output_kvset_on_lane = 17;
    constexpr EventSymbol pr__init_sp_lane = 18;
    constexpr EventSymbol pr__init_global_master = 19;
    constexpr EventSymbol pr__global_master = 20;
    constexpr EventSymbol pr__cache_flush = 21;
    constexpr EventSymbol pr__cache_flush_return = 22;
    constexpr EventSymbol pr__init_node_master = 23;
    constexpr EventSymbol pr__node_master = 24;
    constexpr EventSymbol pr__termiante_node_master = 25;
    constexpr EventSymbol pr__init_updown_master = 26;
    constexpr EventSymbol pr__updown_master = 27;
    constexpr EventSymbol pr__terminate_updown_master = 28;
    constexpr EventSymbol pr__lane_master_init = 29;
    constexpr EventSymbol pr__lane_master_loop = 30;
    constexpr EventSymbol pr__lane_master_read_partition = 31;
    constexpr EventSymbol pr__lane_master_get_next_return = 32;
    constexpr EventSymbol pr__lane_master_terminate = 33;
    constexpr EventSymbol pr__init_global_snyc = 34;
    constexpr EventSymbol pr__init_node_sync = 35;
    constexpr EventSymbol pr__ud_accumulate = 36;
    constexpr EventSymbol pr__global_sync_return = 37;
    constexpr EventSymbol pr__node_sync_return = 38;
    constexpr EventSymbol pr__ud_entry = 39;
    constexpr EventSymbol pr__ud_delay = 40;
    constexpr EventSymbol pr__kv_map_emit = 41;
    constexpr EventSymbol pr__kv_reduce_emit = 42;
    constexpr EventSymbol pr__kv_map_return = 43;
    constexpr EventSymbol pr__init_reduce_thread = 44;
    constexpr EventSymbol pr__combine_get_pair = 45;
    constexpr EventSymbol pr__combine_put_pair_ack = 46;
    constexpr EventSymbol pr__kv_reduce_return = 47;
    constexpr EventSymbol pr__combine_flush_lane = 48;
    constexpr EventSymbol pr__combine_flush_ack = 49;
    constexpr EventSymbol updown_init = 50;
    constexpr EventSymbol updown_terminate = 51;
    constexpr EventSymbol pr__kv_map = 52;
    constexpr EventSymbol pr__map_load_return = 53;
    constexpr EventSymbol DRAMalloc__dramalloc = 54;
    constexpr EventSymbol DRAMalloc__dramalloc_write_param_return = 55;
    constexpr EventSymbol DRAMalloc__global_broadcast = 56;
    constexpr EventSymbol DRAMalloc__node_broadcast = 57;
    constexpr EventSymbol DRAMalloc__updown_translation_install = 58;
    constexpr EventSymbol DRAMalloc__node_broadcast_return = 59;
    constexpr EventSymbol DRAMalloc__global_broadcast_return = 60;

} // namespace

#endif