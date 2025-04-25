#pragma once

#include <cstdint>
#include <unordered_map>
#include "lanetypes.hh"

namespace basim {

/* Lane-level stats*/
struct LaneStats {
    Cycles cycle_count = Cycles(0);
    Cycles cur_activation_cycle_count = Cycles(0);

    uint64_t inst_count = 0;  // NOTE: inst_count does not include tran_count
    uint64_t tran_count = 0;
    uint64_t thread_count = 0;
    uint64_t max_thread_count = 0;
    uint64_t cycles_gt128th = 0;
    int64_t start_gt128th = -1;

    uint64_t inst_count_atomic = 0;
    uint64_t inst_count_bitwise = 0;
    uint64_t inst_count_ctrlflow = 0;
    uint64_t inst_count_datmov = 0;
    uint64_t inst_count_ev = 0;
    uint64_t inst_count_fparith = 0;
    uint64_t inst_count_hash = 0;
    uint64_t inst_count_intarith = 0;
    uint64_t inst_count_intcmp = 0;
    uint64_t inst_count_msg = 0;
    uint64_t inst_count_msg_mem = 0;
    uint64_t inst_count_msg_lane = 0;
    uint64_t inst_count_threadctrl = 0;
    uint64_t inst_count_tranctrl = 0;
    uint64_t inst_count_vec = 0;

    uint64_t tran_count_basic = 0;
    uint64_t tran_count_majority = 0;
    uint64_t tran_count_default = 0;
    uint64_t tran_count_epsilon = 0;
    uint64_t tran_count_common = 0;
    uint64_t tran_count_flagged = 0;
    uint64_t tran_count_refill = 0;
    uint64_t tran_count_event = 0;

    uint64_t lm_load_bytes = 0;
    uint64_t lm_store_bytes = 0;
    uint64_t lm_load_count = 0;
    uint64_t lm_store_count = 0;

    uint64_t dram_load_bytes = 0;
    uint64_t dram_store_bytes = 0;
    uint64_t dram_load_count = 0;
    uint64_t dram_store_count = 0;

    uint64_t message_bytes = 0;
    uint64_t eventq_len_max = 0;
    uint64_t opbuff_len_max = 0;
    uint64_t tran_count_other_node = 0;
    uint64_t tran_bytes_other_node = 0;
    uint64_t dram_store_count_other_node = 0;
    uint64_t dram_load_count_other_node = 0;
    uint64_t dram_store_ack_count_other_node = 0;
    uint64_t dram_load_ack_count_other_node = 0;
    uint64_t dram_store_bytes_other_node = 0;
    uint64_t dram_load_bytes_other_node = 0;
    uint64_t dram_store_ack_bytes_other_node = 0;
    uint64_t dram_load_ack_bytes_other_node = 0;
#ifdef DETAIL_STATS
    uint64_t inst_per_event[MAX_BINS] = {0};
    uint64_t inst_per_tx[MAX_BINS] = {0};
    uint64_t lm_load_count_per_event[MAX_COUNT_BINS] = {0};
    uint64_t lm_store_count_per_event[MAX_COUNT_BINS] = {0};
    uint64_t dram_load_count_per_event[MAX_COUNT_BINS] = {0};
    uint64_t dram_store_count_per_event[MAX_COUNT_BINS] = {0};
    uint64_t lm_load_bytes_per_event[MAX_BYTES_BINS] = {0};
    uint64_t lm_store_bytes_per_event[MAX_BYTES_BINS] = {0};
    uint64_t dram_load_bytes_per_event[MAX_BYTES_BINS] = {0};
    uint64_t dram_store_bytes_per_event[MAX_BYTES_BINS] = {0};
    uint64_t max_inst_per_event = 0;
    uint64_t max_inst_per_tx = 0;
    uint64_t max_cycles_per_event = 0;
    uint64_t max_cycles_per_tx = 0;
    uint64_t max_lm_load_count_per_event = 0;
    uint64_t max_lm_store_count_per_event = 0;
    uint64_t max_dram_load_count_per_event = 0;
    uint64_t max_dram_store_count_per_event = 0;
    uint64_t max_lm_load_bytes_per_event = 0;
    uint64_t max_lm_store_bytes_per_event = 0;
    uint64_t max_dram_load_bytes_per_event = 0;
    uint64_t max_dram_store_bytes_per_event = 0;

    std::unordered_map<uint32_t, uint64_t> event_activation_count;
    std::unordered_map<uint32_t, uint64_t> event_cycle_count;
#endif
    // double eventq_len_mean;
    // double opbuff_len_mean;

    // user counters? - yes?
    void reset(){
        cycle_count = Cycles(0);
        cur_activation_cycle_count = Cycles(0);
        inst_count = 0;
        tran_count = 0;
        thread_count = 0;
        max_thread_count = 0;
        cycles_gt128th = 0;
        start_gt128th = -1;
        inst_count_atomic = 0;
        inst_count_bitwise = 0;
        inst_count_ctrlflow = 0;
        inst_count_datmov = 0;
        inst_count_ev = 0;
        inst_count_fparith = 0;
        inst_count_hash = 0;
        inst_count_intarith = 0;
        inst_count_intcmp = 0;
        inst_count_msg = 0;
        inst_count_msg_mem = 0;
        inst_count_msg_lane = 0;
        inst_count_threadctrl = 0;
        inst_count_tranctrl = 0;
        inst_count_vec = 0;
        tran_count_basic = 0;
        tran_count_majority = 0;
        tran_count_default = 0;
        tran_count_epsilon = 0;
        tran_count_common = 0;
        tran_count_flagged = 0;
        tran_count_refill = 0;
        tran_count_event = 0;
        lm_load_bytes = 0;
        lm_store_bytes = 0;
        lm_load_count = 0;
        lm_store_count = 0;
        dram_load_bytes = 0;
        dram_store_bytes = 0;
        dram_load_count = 0;
        dram_store_count = 0;
        message_bytes = 0;
        eventq_len_max = 0;
        opbuff_len_max = 0;
        tran_count_other_node = 0;
        tran_bytes_other_node = 0;
        dram_store_count_other_node = 0;
        dram_load_count_other_node = 0;
        dram_store_ack_count_other_node = 0;
        dram_load_ack_count_other_node = 0;
        dram_store_bytes_other_node = 0;
        dram_load_bytes_other_node = 0;
        dram_store_ack_bytes_other_node = 0;
        dram_load_ack_bytes_other_node = 0;
#ifdef DETAIL_STATS
        for(int i = 0; i < MAX_BINS; i++){
            inst_per_event[i] = 0;
            inst_per_tx[i] = 0;
        }
        for(int i = 0; i < MAX_COUNT_BINS; i++){
            lm_load_count_per_event[i] = 0;
            lm_store_count_per_event[i] = 0;
            dram_load_count_per_event[i] = 0;
            dram_store_count_per_event[i] = 0;
        }
        for(int i = 0; i < MAX_BYTES_BINS; i++){
            lm_load_bytes_per_event[i] = 0;
            lm_store_bytes_per_event[i] = 0;
            dram_load_bytes_per_event[i] = 0;
            dram_store_bytes_per_event[i] = 0;
        }
        max_inst_per_event = 0;
        max_inst_per_tx = 0;
        max_cycles_per_event = 0;
        max_cycles_per_tx = 0;
        max_lm_load_count_per_event = 0;
        max_lm_store_count_per_event = 0;
        max_dram_load_count_per_event = 0;
        max_dram_store_count_per_event = 0;
        max_lm_load_bytes_per_event = 0;
        max_lm_store_bytes_per_event = 0;
        max_dram_load_bytes_per_event = 0;
        max_dram_store_bytes_per_event = 0;

        event_activation_count.clear();
        event_cycle_count.clear();
#endif
    }
};

/* UpDown-level stats*/
struct UDStats {

};

/* Stack level Stats*/
struct StackStats{
    uint64_t dram_load_bytes = 0;
    uint64_t dram_store_bytes = 0;
    uint64_t dram_load_count = 0;
    uint64_t dram_store_count = 0;
    
    uint64_t dram_load_bytes_prev = 0;
    uint64_t dram_store_bytes_prev = 0;
    uint64_t dram_load_count_prev = 0;
    uint64_t dram_store_count_prev = 0;

    uint64_t peak_dram_load_bytes = 0;
    uint64_t peak_dram_store_bytes = 0;
    uint64_t peak_dram_load_count = 0;
    uint64_t peak_dram_store_count = 0;
    uint64_t peak_dram_load_store_count = 0;
    void reset(){
        dram_load_bytes = 0;
        dram_store_bytes = 0;
        dram_load_count = 0;
        dram_store_count = 0;

        dram_load_bytes_prev = 0;
        dram_store_bytes_prev = 0;
        dram_load_count_prev = 0;
        dram_store_count_prev = 0;

        peak_dram_load_bytes = 0;
        peak_dram_store_bytes = 0;
        peak_dram_load_count = 0;
        peak_dram_store_count = 0;
        peak_dram_load_store_count = 0;
    }
};



}; // namespace basim