#ifndef __bfs_udweave_exe_H__
#define __bfs_udweave_exe_H__

namespace bfs_udweave_exe {

    typedef unsigned int EventSymbol;

    constexpr EventSymbol DRAMalloc__dramalloc = 0;
    constexpr EventSymbol DRAMalloc__dramalloc_write_param_return = 1;
    constexpr EventSymbol DRAMalloc__global_broadcast = 2;
    constexpr EventSymbol DRAMalloc__node_broadcast = 3;
    constexpr EventSymbol DRAMalloc__updown_translation_install = 4;
    constexpr EventSymbol DRAMalloc__node_broadcast_return = 5;
    constexpr EventSymbol DRAMalloc__global_broadcast_return = 6;
    constexpr EventSymbol vertex_master__launch = 7;
    constexpr EventSymbol vertex_master__v_return = 8;
    constexpr EventSymbol vertex_master__v_orig_return = 9;
    constexpr EventSymbol vertex_master__v_neighs = 10;
    constexpr EventSymbol vertex_master__v_neighs_return = 11;
    constexpr EventSymbol map_master__init = 12;
    constexpr EventSymbol map_master__read_length_from_dram = 13;
    constexpr EventSymbol map_master__send_to_map_master_thread = 14;
    constexpr EventSymbol map_master__start = 15;
    constexpr EventSymbol map_master__start_split_v = 16;
    constexpr EventSymbol map_master__receive_dram = 17;
    constexpr EventSymbol map_master__receive_dram_split_v = 18;
    constexpr EventSymbol map_master__vertex_term = 19;
    constexpr EventSymbol map_master__vertex_term_split_v = 20;
    constexpr EventSymbol map_master__map_all_launched = 21;
    constexpr EventSymbol map_master__map_split_all_launched = 22;
    constexpr EventSymbol map_master__wrtie_reduce_length = 23;
    constexpr EventSymbol map_master__add_v = 24;
    constexpr EventSymbol map_master__add_vertex = 25;
    constexpr EventSymbol map_master__add_split_vertex = 26;
    constexpr EventSymbol map_master__add_split_v = 27;
    constexpr EventSymbol map_master__write_map_queue_return = 28;
    constexpr EventSymbol map_master__wrtie_reduce_queue_return = 29;
    constexpr EventSymbol main_master__init = 30;
    constexpr EventSymbol main_master__init_done = 31;
    constexpr EventSymbol main_master__send_to_global_master_thread = 32;
    constexpr EventSymbol main_master__start = 33;
    constexpr EventSymbol main_master__map_launcher_done = 34;
    constexpr EventSymbol main_master__map_all_launched = 35;
    constexpr EventSymbol main_master__map_split_launcher_done = 36;
    constexpr EventSymbol main_master__map_split_all_launched = 37;
    constexpr EventSymbol main_master__reduce_launcher_done = 38;
    constexpr EventSymbol dram_copy__send_reads = 39;
    constexpr EventSymbol dram_copy__read_returns = 40;
    constexpr EventSymbol dram_copy__write_returns = 41;

} // namespace

#endif