#ifndef SIM_STATS_HH
#define SIM_STATS_HH

struct SimStats {
  uint64_t cur_num_sends;
  uint64_t num_sends;
  uint64_t exec_cycles;
  uint64_t idle_cycles;
  uint64_t lm_write_bytes;
  uint64_t lm_read_bytes;
  uint64_t transition_cnt;
  uint64_t total_inst_cnt;
  uint64_t send_inst_cnt;
  uint64_t move_inst_cnt;
  uint64_t branch_inst_cnt;
  uint64_t alu_inst_cnt;
  uint64_t yield_inst_cnt;
  uint64_t compare_inst_cnt;
  uint64_t cmp_swp_inst_cnt;
  uint64_t event_queue_max;
  double event_queue_mean;
  uint64_t operand_queue_max;
  double operand_queue_mean;
  uint64_t user_counter[16];
};

#endif // SIM_STATS_HH
