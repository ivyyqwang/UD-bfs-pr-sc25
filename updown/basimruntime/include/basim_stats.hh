#ifndef BASIM_STATS_HH
#define BASIM_STATS_HH
#include <updown_config.h>
#include <atomic>
struct BASimStats {
  uint64_t cycle_count;
  uint64_t inst_count; 
  uint64_t tran_count;
  uint64_t thread_count;
  uint64_t max_thread_count;
  uint64_t cycles_gt128th;
  uint64_t inst_count_atomic;
  uint64_t inst_count_bitwise;
  uint64_t inst_count_ctrlflow;
  uint64_t inst_count_datmov;
  uint64_t inst_count_ev;
  uint64_t inst_count_fparith;
  uint64_t inst_count_hash;
  uint64_t inst_count_intarith;
  uint64_t inst_count_intcmp;
  uint64_t inst_count_msg;
  uint64_t inst_count_msg_mem;
  uint64_t inst_count_msg_lane;
  uint64_t inst_count_threadctrl;
  uint64_t inst_count_tranctrl;
  uint64_t inst_count_vec;
  uint64_t tran_count_basic;
  uint64_t tran_count_majority;
  uint64_t tran_count_default;
  uint64_t tran_count_epsilon;
  uint64_t tran_count_common;
  uint64_t tran_count_flagged;
  uint64_t tran_count_refill;
  uint64_t tran_count_event;
  uint64_t max_inst_count_per_event;
  uint64_t max_inst_count_per_tx;
  uint64_t lm_load_bytes;
  uint64_t lm_store_bytes;
  uint64_t lm_load_count;
  uint64_t lm_store_count;
  uint64_t dram_load_bytes;
  uint64_t dram_store_bytes;
  uint64_t dram_load_count;
  uint64_t dram_store_count;
  uint64_t message_bytes;
  uint64_t eventq_len_max;
  uint64_t opbuff_len_max;
  double event_queue_mean;
  uint64_t operand_queue_max;
  double operand_queue_mean;
  uint64_t tran_count_other_node;
  uint64_t tran_bytes_other_node;
  uint64_t dram_store_count_other_node;
  uint64_t dram_load_count_other_node;
  uint64_t dram_store_ack_count_other_node;
  uint64_t dram_load_ack_count_other_node;
  uint64_t dram_store_bytes_other_node;
  uint64_t dram_load_bytes_other_node;
  uint64_t dram_store_ack_bytes_other_node;
  uint64_t dram_load_ack_bytes_other_node;
  uint64_t user_counter[16];
};

struct BASimNodeStats {
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> output_bytes;

  #if defined(NETWORK_STATS)
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> tran_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> tran_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_store_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_load_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_store_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_load_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_store_ack_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_load_ack_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_store_ack_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> dram_load_ack_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> total_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> total_bytes_other_node;

  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_bytes;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_counts;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_queue_size;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> total_queue_size;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_tran_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_tran_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_ack_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_ack_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_ack_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_ack_bytes_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_total_count_other_node;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_total_bytes_other_node;

  std::vector<std::shared_ptr<std::atomic<uint64_t>>> output_counts;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_queue_size_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_tran_count_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_tran_bytes_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_count_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_count_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_bytes_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_bytes_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_ack_count_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_ack_count_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_store_ack_bytes_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_dram_load_ack_bytes_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_total_count_other_node_tmp;
  std::vector<std::shared_ptr<std::atomic<uint64_t>>> max_total_bytes_other_node_tmp;

  std::vector<std::vector<std::shared_ptr<std::atomic<uint64_t>>>> tran_packet_size_other_node_histogram;
  std::vector<std::vector<std::shared_ptr<std::atomic<uint64_t>>>> dram_load_packet_size_other_node_histogram;
  std::vector<std::vector<std::shared_ptr<std::atomic<uint64_t>>>> dram_load_ack_packet_size_other_node_histogram;
  std::vector<std::vector<std::shared_ptr<std::atomic<uint64_t>>>> dram_store_packet_size_other_node_histogram;
  std::vector<std::vector<std::shared_ptr<std::atomic<uint64_t>>>> dram_store_ack_packet_size_other_node_histogram;
  std::vector<std::vector<std::shared_ptr<std::atomic<uint64_t>>>> total_packet_size_other_node_histogram;
  #endif

  void initialize_histogram(std::vector<std::vector<std::shared_ptr<std::atomic<uint64_t>>>>& vec, size_t rows, size_t cols) {
    vec.clear();   
    vec.resize(rows);

    for (auto& row : vec) {
        row.reserve(cols);  
        for (size_t i = 0; i < cols; ++i) {
            row.emplace_back(std::make_shared<std::atomic<uint64_t>>(0));  
        }
    }
  }

  void reset_tmp(int size){
    auto initialize_vector = [size](std::vector<std::shared_ptr<std::atomic<uint64_t>>>& vec) {
      vec.clear();
      vec.reserve(size);
      for (int i = 0; i < size; ++i) {
        vec.emplace_back(std::make_shared<std::atomic<uint64_t>>(0));
      }

    };

    initialize_vector(output_bytes);
    #if defined(NETWORK_STATS)
    initialize_vector(max_total_count_other_node_tmp);
    initialize_vector(max_total_bytes_other_node_tmp);
    initialize_vector(max_tran_count_other_node_tmp);
    initialize_vector(max_tran_bytes_other_node_tmp);
    initialize_vector(max_dram_store_count_other_node_tmp);
    initialize_vector(max_dram_load_count_other_node_tmp);
    initialize_vector(max_dram_store_bytes_other_node_tmp);
    initialize_vector(max_dram_load_bytes_other_node_tmp);
    initialize_vector(max_dram_store_ack_count_other_node_tmp);
    initialize_vector(max_dram_load_ack_count_other_node_tmp);
    initialize_vector(max_dram_store_ack_bytes_other_node_tmp);
    initialize_vector(max_dram_load_ack_bytes_other_node_tmp);
    initialize_vector(output_counts);
    initialize_vector(max_queue_size_tmp);
    #endif

  }

  // Initialize the vectors with the given size and set atomic values to 0
  void reset(int size) {
    auto initialize_vector = [size](std::vector<std::shared_ptr<std::atomic<uint64_t>>>& vec) {
      vec.clear();
      vec.reserve(size);
      for (int i = 0; i < size; ++i) {
        vec.emplace_back(std::make_shared<std::atomic<uint64_t>>(0));
      }
    };

    #if defined(NETWORK_STATS)
    initialize_vector(max_bytes);
    initialize_vector(max_counts);
    initialize_vector(max_queue_size);
    initialize_vector(total_queue_size);

    initialize_vector(total_count_other_node);
    initialize_vector(total_bytes_other_node);
    initialize_vector(tran_count_other_node);
    initialize_vector(tran_bytes_other_node);
    initialize_vector(dram_store_count_other_node);
    initialize_vector(dram_load_count_other_node);
    initialize_vector(dram_store_bytes_other_node);
    initialize_vector(dram_load_bytes_other_node);
    initialize_vector(dram_store_ack_count_other_node);
    initialize_vector(dram_load_ack_count_other_node);
    initialize_vector(dram_store_ack_bytes_other_node);
    initialize_vector(dram_load_ack_bytes_other_node);

    initialize_vector(max_total_count_other_node);
    initialize_vector(max_total_bytes_other_node);
    initialize_vector(max_tran_count_other_node);
    initialize_vector(max_tran_bytes_other_node);
    initialize_vector(max_dram_store_count_other_node);
    initialize_vector(max_dram_load_count_other_node);
    initialize_vector(max_dram_store_bytes_other_node);
    initialize_vector(max_dram_load_bytes_other_node);
    initialize_vector(max_dram_store_ack_count_other_node);
    initialize_vector(max_dram_load_ack_count_other_node);
    initialize_vector(max_dram_store_ack_bytes_other_node);
    initialize_vector(max_dram_load_ack_bytes_other_node);

    initialize_histogram(total_packet_size_other_node_histogram, size, 12);
    initialize_histogram(tran_packet_size_other_node_histogram, size, 12);
    initialize_histogram(dram_load_packet_size_other_node_histogram, size, 12);
    initialize_histogram(dram_load_ack_packet_size_other_node_histogram, size, 12);
    initialize_histogram(dram_store_packet_size_other_node_histogram, size, 12);
    initialize_histogram(dram_store_ack_packet_size_other_node_histogram, size, 12);
    #endif
  }
};

#ifdef INST_HIST
constexpr std::string_view InstNames[] =
{
  "ADDI",
  "SUBI",
  "MULI",
  "DIVI",
  "MODI",
  "CLTI",
  "CGTI",
  "CEQI",
  "ANDI",
  "ORI",
  "XORI",
  "MOVIL2",
  "MOVIL1",
  "YIELD",
  "YIELDT",
  "LASTACT",
  "SLI",
  "SRI",
  "SLORI",
  "SRORI",
  "SLANDI",
  "SRANDI",
  "SARI",
  "HASHSB32",
  "HASHSB64",
  "HASHL64",
  "HASH",
  "HASHL",
  "BCPYLLI",
  "MOVSBR",
  "MOVIPR",
  "MOVLSB",
  "SIW",
  "REFILL",
  "SSPROP",
  "EVLB",
  "MOVIR",
  "PRINT",
  "PERFLOG",
  "SLADDII",
  "SLSUBII",
  "SRADDII",
  "SRSUBII",
  "SLORII",
  "SRORII",
  "SLANDII",
  "SRANDII",
  "MOVBIL",
  "MOVBLR",
  "FSTATE",
  "CSWPI",
  "MOVLR",
  "MOVRL",
  "SWIZ",
  "BCPYOLI",
  "ADD",
  "SUB",
  "MUL",
  "DIV",
  "MOD",
  "AND",
  "OR",
  "XOR",
  "CLT",
  "CGT",
  "CEQ",
  "CSTR",
  "SR",
  "SL",
  "SAR",
  "BCPYLL",
  "MOVRR",
  "MOVWLR",
  "MOVWRL",
  "BCPYOL",
  "FMADD_64",
  "FADD_64",
  "FSUB_64",
  "FMUL_64",
  "FDIV_64",
  "FSQRT_64",
  "FEXP_64",
  "FMADD_32",
  "FADD_32",
  "FSUB_32",
  "FMUL_32",
  "FDIV_32",
  "FSQRT_32",
  "FEXP_32",
  "FMADD_B16",
  "FADD_B16",
  "FSUB_B16",
  "FMUL_B16",
  "FDIV_B16",
  "FSQRT_B16",
  "FEXP_B16",
  "FCNVT_64_I64",
  "FCNVT_32_I32",
  "FCNVT_I64_64",
  "FCNVT_I32_32",
  "FCNVT_64_32",
  "FCNVT_64_B16",
  "FCNVT_32_64",
  "FCNVT_32_B16",
  "FCNVT_B16_64",
  "FCNVT_B16_32",
  "VMADD_32",
  "VADD_32",
  "VSUB_32",
  "VMUL_32",
  "VDIV_32",
  "VSQRT_32",
  "VEXP_32",
  "VMADD_B16",
  "VADD_B16",
  "VSUB_B16",
  "VMUL_B16",
  "VDIV_B16",
  "VSQRT_B16",
  "VEXP_B16",
  "VMADD_I32",
  "VADD_I32",
  "VSUB_I32",
  "VMUL_I32",
  "VDIV_I32",
  "VSQRT_I32",
  "VEXP_I32",
  "VGT_32",
  "VGT_B16",
  "VGT_I32",
  "BNE",
  "BEQ",
  "BGT",
  "BLE",
  "BNEU",
  "BEQU",
  "BGTU",
  "BLEU",
  "BNEI",
  "BEQI",
  "BGTI",
  "BLEI",
  "BLTI",
  "BGEI",
  "BNEIU",
  "BEQIU",
  "BGTIU",
  "BLEIU",
  "BLTIU",
  "BGEIU",
  "JMP",
  "SEND",
  "SENDB",
  "SENDM",
  "SENDMB",
  "INSTRANS",
  "SENDR",
  "SENDR3",
  "SENDMR",
  "SENDMR2",
  "SENDOPS",
  "SENDMOPS",
  "EVI",
  "EVII",
  "EV",
  "CSWP",
  "VFILL_32",
  "VFILL_I32",
  "VFILL_B16",
  "BRANCH_TAKEN",
  "BRANCH_NOT_TAKEN",
  "COUNT",
};

#endif


#endif // SIM_STATS_HH
