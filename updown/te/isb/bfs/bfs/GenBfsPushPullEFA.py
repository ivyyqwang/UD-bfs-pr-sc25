from linker.EFAProgram import EFAProgram, efaProgram
from math import log2
from GenGlobalSyncEFA import *
from Macro import *
from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet

WORD_SIZE           = 8
LOG2_WORD_SIZE      = int(log2(WORD_SIZE))
LANE_PER_UD         = 64
UD_PER_NODE         = 32
LOG2_LANE_PER_UD    = int(log2(LANE_PER_UD))
LOG2_UD_PER_NODE    = int(log2(UD_PER_NODE))
VERTEX_STRUCT_SIZE  = 8
VERTEX_STRUCT_BSIZE = 8 * WORD_SIZE

ITERATION_INFO_FLAG = True

NUM_UPDATE_THREAD_PER_LANE  = 28
LOCAL_FETCH_MAX_REQUESTS = 32
VERTEX_ID_HASH_SEED      = 5
NWID_HASH_SEED           = 7
PULL_SWITCH_AT_ITERATION = 2
PUSH_SWITCH_AT_ITERATION = 5

class BFS:

    FLAG            = 1
    INACTIVE_MASK   = 1 << 63
    INVALID_VAL     = 0xffffffffffffffff

    def __init__(self, efa: EFAProgram, vertex_struct_size, ctr_base_offset, max_thread_per_lane = 250, debug_flag = False):

        self.task   = 'build_neighbor_list'
        self.efa    = efa
        self.efa.code_level = 'machine'
        self.state  = efa.State()
        efa.add_initId(self.state.state_id)

        self.task = "BFS"

        '''
        | vertex_array_ptr  | ud_mask       | log2_num_uds  | num_updates   |
        | num_consume       | flag          | num_threads   |               |
        '''
        self.vertices_ptr_offset= ctr_base_offset                       # 0
        self.nwid_mask_offset   = self.vertices_ptr_offset + WORD_SIZE  # 8
        self.ln_mstr_evw_offset = self.nwid_mask_offset + WORD_SIZE     # 16
        self.num_updates_offset = self.ln_mstr_evw_offset + WORD_SIZE   # 24
        self.num_consume_offset = self.num_updates_offset + WORD_SIZE   # 32
        self.top_flag_offset    = self.num_consume_offset + WORD_SIZE   # 40
        self.num_threads_offset = self.top_flag_offset + WORD_SIZE      # 48
        self.ofront_base_offset = self.num_threads_offset + WORD_SIZE   # 56
        self.ofront_ptr_offset  = self.ofront_base_offset + WORD_SIZE   # 64
        self.nfront_base_offset = self.ofront_ptr_offset + WORD_SIZE    # 72
        self.nfront_ptr_offset  = self.nfront_base_offset + WORD_SIZE   # 80
        self.orig_graph_offset  = self.nfront_ptr_offset + WORD_SIZE    # 88
        self.max_thread_offset  = self.orig_graph_offset + WORD_SIZE    # 96
        self.front_evw_offset   = self.max_thread_offset + WORD_SIZE    # 104
        
        self.kvmsr_offset       = self.front_evw_offset + WORD_SIZE     # 112
        self.send_buffer_offset = self.kvmsr_offset + 8 * WORD_SIZE     # 176
        self.iteration_offset   = self.kvmsr_offset + 18 * WORD_SIZE    # 256
        self.kvmsr_ops_offset   = self.kvmsr_offset + 24 * WORD_SIZE    # 304

        self.SIZEOF_VERTEX      = vertex_struct_size
        self.LOG2_SIZEOF_VERTEX = int(log2(vertex_struct_size))

        self.event_map  = {}
        self.num_events = 0
        self.max_thread_per_lane = max_thread_per_lane

        self.scratch    = [f"UDPR_{n}" for n in range(12, 16)]
        self.debug_flag = debug_flag
        self.debug_flag_term = debug_flag
        self.debug_thread_count_flag = debug_flag and False
        
        self.graph_ptr      = "UDPR_0"

    def __get_event_mapping(self, label):

        return get_event_label(self.task, label)

    def setup_cache(self, cache_base_offset, num_entries, entry_size):

        self.cache_base_offset  = self.kvmsr_offset + 32 * WORD_SIZE
        self.cache_size         = ((1 << 16) - self.cache_base_offset - 32) // entry_size
        self.cache_mask         = (1 << int(log2(num_entries))) - 1
        self.cache_entry_size   = entry_size
        self.INACTIVE_MASK_SHIFT= 63
        self.INACTIVE_MASK      = (1 << self.INACTIVE_MASK_SHIFT)
        self.cache_ival         = -1

        self.val_1_offset       = self.cache_base_offset + WORD_SIZE
        self.val_2_offset       = self.cache_base_offset + (2 * WORD_SIZE)
        
    def gen_pull_kvmsr(self):
        
        
        self.udkvmsr = UDKeyValueMapShuffleReduceTemplate(efa=self.efa, task_name=f"{self.task}_pull", meta_data_offset=self.kvmsr_offset, debug_flag=False)
        
        self.udkvmsr.set_input_kvset(OneDimKeyValueSet(f"{self.task}_input_kvset", element_size=VERTEX_STRUCT_SIZE, argument_size=1, bypass_gen_partition=True), map_lane_range = (1, 64))

        self.udkvmsr.set_max_thread_per_lane(max_map_th_per_lane=200)
        
        self.udkvmsr.generate_udkvmsr_task()
    

    def gen_lm_init(self):
        ud_ctr          = "UDPR_3"
        total_num_uds   = "UDPR_4"
        total_num_lns   = "UDPR_4"
        fin_init_evw    = "UDPR_5"
        nwid            = "UDPR_6"
        ofront_arr_ptr  = "UDPR_7"
        fron_init_ev    = "UDPR_8"
        front_stride    = "UDPR_9"
        lm_base         = "UDPR_10"
        init_ud_evw     = "UDPR_11"
        init_ln_evw     = "UDPR_11"

        init_ud_ev_label    = self.__get_event_mapping("init_updown")
        init_ud_ret_ev_label = self.__get_event_mapping("init_updown_return")
        init_ln_ev_label    = self.__get_event_mapping("init_lane")
        fin_init_ev_label   = self.__get_event_mapping('fin_init_node')
        init_front_sp_ev_label = self.__get_event_mapping("init_frontier_scratchpad")

        init_node_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_event_mapping("init_node"))
        '''
        Operands:
            OB_0:   Node 0's vertex array pointer.
            OB_1:   Number of vertices.
            OB_2:   Number of UpDowns.
            OB_3:   Pointer to the partition array (64-bit DRAM address)
            OB_4:   Number of lanes - 1
            OB_5:   Froniter base pointer
            OB_6:   Froniter stride
            OB_7:   Number of partitions per lane
        '''
        if self.debug_flag:
            init_node_tran.writeAction(f"print ' '")
            init_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_node> ev_word=%lu' {'X0'} {'EQT'}")
            init_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: graph_ptr=0x%lx, num_vertices=%ld, num_uds=%ld, partition_array=0x%lx (PART_PARAM=%ld), orig_graph_ptr=0x%lx, front=0x%lx, front_stride=0x%lx' \
                {'X0'} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+1}'} {f'X{OB_REG_BASE+2}'} {f'X{OB_REG_BASE+3}'} {f'X{OB_REG_BASE+7}'} {f'X{OB_REG_BASE+4}'} {f'X{OB_REG_BASE+5}'} {f'X{OB_REG_BASE+6}'}")
        # init_node_tran.writeAction(f"addi {f'X{OB_REG_BASE+0}'} {vertex_arr_ptr} 0")     # {vertex_arr_ptr} <- vertex array base pointer
        init_node_tran.writeAction(f"addi {f'X{OB_REG_BASE+2}'} {total_num_uds} 0")
        init_node_tran.writeAction(f"addi {f'X{OB_REG_BASE+5}'} {ofront_arr_ptr} 0")
        init_node_tran.writeAction(f"lshift {f'X{OB_REG_BASE+6}'} {front_stride} {1}")
        init_node_tran = set_ev_label(init_node_tran, init_ud_evw, init_ud_ev_label, new_thread=True)
        init_node_tran = set_ev_label(init_node_tran, fron_init_ev, init_front_sp_ev_label, new_thread=True)
        init_node_tran = set_ev_label(init_node_tran, fin_init_evw, fin_init_ev_label)
        init_node_tran
        init_node_tran.writeAction(f"mov_imm2reg {ud_ctr} 0")
        if self.debug_flag:
            init_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Initialize %ld UpDowns' {'X0'} {total_num_uds}")
        init_node_tran.writeAction(f"ud_init_loop: lshift {ud_ctr} {nwid} {LOG2_LANE_PER_UD}")
        init_node_tran = set_nwid(init_node_tran, init_ud_evw, nwid, init_ud_evw)
        init_node_tran = set_nwid(init_node_tran, fron_init_ev, nwid, fron_init_ev)
        init_node_tran.writeAction(f"sendr3_wcont {init_ud_evw} {fin_init_evw} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+4}'} {f'X{OB_REG_BASE+2}'}")
        init_node_tran.writeAction(f"sendr_wcont {fron_init_ev} {fin_init_evw} {ofront_arr_ptr} {f'X{OB_REG_BASE+6}'}")
        init_node_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        init_node_tran.writeAction(f"add {ofront_arr_ptr} {front_stride} {ofront_arr_ptr}")
        init_node_tran.writeAction(f"blt {ud_ctr} {total_num_uds} ud_init_loop")
        init_node_tran.writeAction(f"lshift {total_num_uds} {total_num_uds} {1}")
        # Move the UDKVMSR call parameters to scratchpad.
        init_node_tran.writeAction(f"movir {lm_base} {self.kvmsr_ops_offset}")
        init_node_tran.writeAction(f"add {'X7'} {lm_base} {lm_base}")
        init_node_tran.writeAction(f"movrl {f'X{OB_REG_BASE+3}'} 0({lm_base}) 0 8")
        if self.debug_flag:
            init_node_tran.writeAction(f"print '[DEBUG][NWID %d] Partition array %lu(0x%lx) and number of partition per lane = %ld' {'X0'} {f'X{OB_REG_BASE+3}'} {f'X{OB_REG_BASE+3}'} {f'X{OB_REG_BASE+7}'}")
        init_node_tran.writeAction(f"movrl {f'X{OB_REG_BASE+7}'} 8({lm_base}) 0 8")
        init_node_tran.writeAction(f"muli {f'X{OB_REG_BASE+2}'} {nwid} {LANE_PER_UD}")
        init_node_tran.writeAction(f"movrl {nwid} 16({lm_base}) 0 8")
        init_node_tran.writeAction(f"addi {'X7'} {self.scratch[0]} {self.udkvmsr.in_kvset_offset}")
        init_node_tran.writeAction(f"movrl {self.scratch[0]} 24({lm_base}) 0 8")
        if self.debug_flag:
            init_node_tran.writeAction(f"print '[DEBUG][NWID %d] Save input key value set base pointer %lu(0x%lx) and size %ld to scratchpad addr %ld(0x%lx)' " + 
                                       f"{'X0'} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+1}'} {self.scratch[0]} {self.scratch[0]}")
        init_node_tran.writeAction(f"movrl {f'X{OB_REG_BASE+0}'} 0({self.scratch[0]}) 1 8")
        init_node_tran.writeAction(f"movrl {f'X{OB_REG_BASE+1}'} 0({self.scratch[0]}) 1 8")
        init_node_tran.writeAction("yield")

        init_ud_tran = self.state.writeTransition("eventCarry", self.state, self.state, init_ud_ev_label)
        if self.debug_flag and False:
            init_ud_tran.writeAction(f"print ' '")
            init_ud_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_updown> ev_word=%lu' {'X0'} {'EQT'}")
            init_ud_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: ud_bin_ptr=0x%lx, udid=%ld, log2_num_uds=%ld' {'X0'} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+1}'} {f'X{OB_REG_BASE+2}'}")
        init_ud_tran.writeAction(f"movir {total_num_lns} {LANE_PER_UD}")
        set_ev_label(init_ud_tran, init_ln_evw, init_ln_ev_label, new_thread=True)
        set_ev_label(init_ud_tran, fin_init_evw, init_ud_ret_ev_label)
        broadcast(init_ud_tran, init_ln_evw, total_num_lns, fin_init_evw, 0, data="X8 X9 X10", scratch=self.scratch, mode="r3")
        init_ud_tran.writeAction(f"yield")
        
        
        init_front_tran = self.state.writeTransition("eventCarry", self.state, self.state, init_front_sp_ev_label)
        val         = self.scratch[0]
        lm_addr     = "UDPR_0"
        ofront_base  = "UDPR_1"
        nfront_base  = "UDPR_2"
        init_front_tran.writeAction(f"addi {f'X{OB_REG_BASE+0}'} {ofront_base} 0")
        init_front_tran.writeAction(f"add {ofront_base} {f'X{OB_REG_BASE+1}'} {nfront_base}")
        if self.debug_flag and False:
            init_front_tran.writeAction(f"print ' '")
            init_front_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_updown_frontier_scratchpad> ev_word=%lu' {'X0'} {'EQT'}")
            init_front_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: ofront_ptr=%u(0x%lx), nfront_ptr=%lu(0x%lx), front_stride=0x%lx' \
                {'X0'} {ofront_base} {ofront_base} {nfront_base} {nfront_base} {f'X{OB_REG_BASE+1}'}")
        init_front_tran.writeAction(f"addi X7 {lm_addr} 0")
        init_front_tran.writeAction(f"movir {val} {0}")
        init_front_tran.writeAction(f"movrl {val} {self.front_evw_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"move {ofront_base} {self.ofront_base_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"move {nfront_base} {self.nfront_base_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"move {ofront_base} {self.ofront_ptr_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"move {nfront_base} {self.nfront_ptr_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"sendr_reply EQT EQT {self.scratch[2]}")
        init_front_tran.writeAction("yield_terminate")
        
        init_ln_tran = self.state.writeTransition("eventCarry", self.state, self.state, init_ln_ev_label)
        if self.debug_flag and False:
            init_ln_tran.writeAction(f"print ' '")
            init_ln_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_lane> ev_word=%lu' {'X0'} {'EQT'}")
        self.__init_lane(init_ln_tran)
        init_ln_tran.writeAction(f"sendr_reply {'X0'} {'X0'} {self.scratch[2]}")
        init_ln_tran.writeAction("yield_terminate")
        
        init_ud_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, init_ud_ret_ev_label)
        init_ud_ret_tran.writeAction(f"subi {total_num_lns} {total_num_lns} 1")
        if self.debug_flag and False:
            init_ud_ret_tran.writeAction(f"print ' '")
            init_ud_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_updown_return> from lane %ld ev_word=%lu pending returns=%ld' {'X0'} {'X8'} {'EQT'} {total_num_lns}")
        init_ud_ret_tran.writeAction(f"beqi {total_num_lns} {0} break")
        init_ud_ret_tran.writeAction(f"yield")
        init_ud_ret_tran.writeAction(f"break: sendr_reply EQT EQT {self.scratch[2]}")
        init_ud_ret_tran.writeAction("yield_terminate")

        fin_init_node_tran = self.state.writeTransition("eventCarry", self.state, self.state, fin_init_ev_label)
        fin_init_node_tran.writeAction(f"subi {total_num_uds} {total_num_uds} 1")
        if self.debug_flag and False:
            fin_init_node_tran.writeAction(f"print ' '")
            fin_init_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <fin_init_ud> ev_word=%lu' {'X0'} {'EQT'}")
            fin_init_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: source_ud=%ld, pending returns=%ld' {'X0'} {f'X{OB_REG_BASE+0}'} {total_num_uds}")
        fin_init_node_tran.writeAction(f"beqi {total_num_uds} {0} fin_init_node")
        fin_init_node_tran.writeAction("yield")
        fin_init_node_tran.writeAction(f"fin_init_node: mov_imm2reg {self.scratch[0]} {self.FLAG}")
        fin_init_node_tran.writeAction(f"addi {'X7'} {lm_base} 0")
        fin_init_node_tran.writeAction(f"move {self.scratch[0]} {self.top_flag_offset}({lm_base}) 0 8")  # Set the flag
        fin_init_node_tran.writeAction("yield_terminate")

        return
    
    def __init_lane(self, tran: EFAProgram.Transition):
        
        val                 = "UDPR_0"
        lane_bank_base      = "UDPR_1"
        cache_end_offset    = "UDPR_2"
        total_cache_size    = "UDPR_3"
        cache_base_offset   = "UDPR_4"
        max_thread_per_lane = "UDPR_5"
        nwid_mask           = "UDPR_6"
        
        tran.writeAction(f"movir {val} 0")
        tran.writeAction(f"addi X7 {lane_bank_base} 0")
        tran.writeAction(f"move {f'X{OB_REG_BASE+0}'} {self.vertices_ptr_offset}({lane_bank_base}) 0 8")
        tran.writeAction(f"move {f'X{OB_REG_BASE+1}'} {self.orig_graph_offset}({lane_bank_base}) 0 8")
        tran.writeAction(f"muli {f'X{OB_REG_BASE+2}'} {nwid_mask} {LANE_PER_UD}")
        tran.writeAction(f"subi {nwid_mask} {nwid_mask} 1")
        tran.writeAction(f"move {nwid_mask} {self.nwid_mask_offset}({lane_bank_base}) 0 8")
        tran.writeAction(f"move {val} {self.num_updates_offset}({lane_bank_base}) 0 8")
        tran.writeAction(f"move {val} {self.num_consume_offset}({lane_bank_base}) 0 8")
        tran.writeAction(f"move {val} {self.num_threads_offset}({lane_bank_base}) 0 8")
        tran.writeAction(f"movir {max_thread_per_lane} {self.max_thread_per_lane}")
        tran.writeAction(f"move {max_thread_per_lane} {self.max_thread_offset}({lane_bank_base}) 0 8")

        #Initialize the sw cache in scratchpad to merge Read-Modify-Write updates and ensure TSO
        tran.writeAction(f"movir {val} {self.cache_ival}")
        tran.writeAction(f"addi X7 {cache_base_offset} {self.cache_base_offset}")
        tran.writeAction(f"movir {total_cache_size} {self.cache_size}")
        tran.writeAction(f"muli {total_cache_size} {total_cache_size} {self.cache_entry_size}")
        # print(f"Initialize lane {n}'s cache in scratchpad memory")
        tran.writeAction(f"add {cache_base_offset} {total_cache_size} {cache_end_offset}")
        tran.writeAction(f"init_cache_loop: movrl {val} {0}({cache_base_offset}) 0 8")
        tran.writeAction(f"addi {cache_base_offset} {cache_base_offset} {self.cache_entry_size}")
        tran.writeAction(f"blt {cache_base_offset} {cache_end_offset} init_cache_loop")
        
        return tran

    def gen_global_broadcast(self):
        
        self.init_iter_ev_label     = self.__get_event_mapping("initialize_iteration")
        self.bcst_fetch_ev_label    = self.__get_event_mapping("broadcast_frontier_fetch")
        self.bcst_ret_ev_label      = self.__get_event_mapping("finish_fetch_return")
        self.term_sync_ev_label     = self.__get_event_mapping("terminate_sync")
        self.term_frontier_ev_label = self.__get_event_mapping("terminate_frontier")
        self.term_front_node_ev_label   = self.__get_event_mapping("terminate_frontier_node")
        self.term_sync_node_ev_label    = self.__get_event_mapping("terminate_sync_node")
        self.udkvmsr_return_ev_label    = self.__get_event_mapping("udkvmsr_return")
        self.fetch_node_ev_label        = self.__get_event_mapping("broadcast_fetch_node")
        self.fetch_node_ret_ev_label    = self.__get_event_mapping("finish_broadcast_fetch_return")
        
        '''
        Broadcast to all the updown to fetch its local frontier and sent out the update.
        '''
        
        num_uds     = "UDPR_0"
        ud_ctr      = "UDPR_1"
        nd_ctr      = "UDPR_1"
        nwid        = "UDPR_2"
        num_updates = "UDPR_3"
        lm_base     = "UDPR_4"
        num_iter    = "UDPR_5"
        num_nodes   = "UDPR_6"
        num_ud_per_node = "UDPR_7"
        sync_evw    = "UDPR_8"
        nfront_size = "UDPR_9"

        '''
        Broadcast to all the updown lane 0 to initialize its local frontiers.
        Operands:
            OB_0:   number of nodes
            OB_1:   number of updowns per node
            OB_2:   iteration number
        '''
        bcst_loop_label = "broadcast_loop"
        continue_label  = "continue"
        init_frontier_label = "init_frontier"
        pull_phase_label = "pull_phase"
        push_phase_label = "push_phase"
        init_iter_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.init_iter_ev_label)
        if self.debug_flag:
            init_iter_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <initialize_iteration> Start %ld iteration BFS. ' {'X0'} {'X10'} ")
        init_iter_tran.writeAction(f"addi {'X0'} {nwid} 0")
        init_iter_tran.writeAction(f"addi {f'X{OB_REG_BASE+0}'} {num_nodes} 0")
        init_iter_tran.writeAction(f"addi {f'X{OB_REG_BASE+1}'} {num_ud_per_node} 0")
        init_iter_tran.writeAction(f"addi {f'X{OB_REG_BASE+2}'} {num_iter} 1")
        init_iter_tran.writeAction(f"perflog 1 {0} 'Start %ld iteration BFS. ' {num_iter} ")
        init_iter_tran.writeAction(f"mul {num_nodes} {num_ud_per_node} {num_uds}")
        set_ev_label(init_iter_tran, sync_evw, self.bcst_fetch_ev_label)
        init_iter_tran.writeAction(f"beqi {num_iter} {1} {init_frontier_label}")
        init_iter_tran.writeAction(f"movir {self.scratch[0]} {PULL_SWITCH_AT_ITERATION}")
        init_iter_tran.writeAction(f"bge {num_iter} {self.scratch[0]} {pull_phase_label}")
        init_iter_tran.writeAction(f"{push_phase_label}: movir {ud_ctr} 1")
        init_iter_tran.writeAction(f"sendr_wcont {sync_evw} {sync_evw} {num_iter} {ud_ctr}")
        if ITERATION_INFO_FLAG:
            init_iter_tran.writeAction(f"print ' '")
            init_iter_tran.writeAction(f"print '[DEBUG][NWID %ld] Start push phase at iteration %ld (PUSH_SWITCH_AT_ITERATION={PUSH_SWITCH_AT_ITERATION})' {'X0'} {num_iter}")
        init_iter_tran.writeAction(f"yield")
        
        # Switch to pull phase
        if PUSH_SWITCH_AT_ITERATION > 0b11111:
            init_iter_tran.writeAction(f"{pull_phase_label}: movir {self.scratch[0]} {PUSH_SWITCH_AT_ITERATION}")
            init_iter_tran.writeAction(f"bgt {num_iter} {self.scratch[0]} {push_phase_label}")
        else:
            init_iter_tran.writeAction(f"{pull_phase_label}: bgtiu {num_iter} {PUSH_SWITCH_AT_ITERATION} {push_phase_label}")
        if ITERATION_INFO_FLAG:
            init_iter_tran.writeAction(f"print ' '")
            init_iter_tran.writeAction(f"print '[DEBUG][NWID %ld] Start pull phase at iteration %ld (PULL_SWITCH_AT_ITERATION={PULL_SWITCH_AT_ITERATION})' {'X0'} {num_iter}")
            init_iter_tran.writeAction(f"perflog 1 {1} 'Start pull phase at iteration %ld' {num_iter}")
            init_iter_tran.writeAction(f"addi {'X7'} {lm_base} {self.iteration_offset}")
        else:
            init_iter_tran.writeAction(f"addi {'X7'} {lm_base} {self.iteration_offset}")
        init_iter_tran.writeAction(f"move {num_iter} {0}({lm_base}) 0 8")
        init_iter_tran.writeAction(f"addi {'X7'} {lm_base} {self.kvmsr_ops_offset}")
        init_iter_tran.writeAction(f"evii {self.ev_word} {self.udkvmsr.init_kvmsr_ev_label} 255 5")
        init_iter_tran.writeAction(f"send_wret {self.ev_word} {self.udkvmsr_return_ev_label} {lm_base} 5 {self.scratch[0]}")
        init_iter_tran.writeAction(f"mov_imm2reg {nfront_size} {0}")
        init_iter_tran.writeAction(f"movir {ud_ctr} 1")
        init_iter_tran.writeAction(f"yield")
        
        # Initialize the frontier
        init_iter_tran.writeAction(f"{init_frontier_label}: movir {ud_ctr} 0")
        set_ev_label(init_iter_tran, self.ev_word, self.init_front_ev_label, new_thread=True)
        set_nwid(init_iter_tran, self.ev_word, nwid, src_ev=self.ev_word, label=bcst_loop_label)
        init_iter_tran.writeAction(f"sendr_wcont {self.ev_word} {sync_evw} {num_iter} {ud_ctr} ")
        init_iter_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        init_iter_tran.writeAction(f"addi {nwid} {nwid} {LANE_PER_UD}")
        init_iter_tran.writeAction(f"blt {ud_ctr} {num_uds} {bcst_loop_label}")
        init_iter_tran.writeAction(f"mov_imm2reg {num_updates} {0}")
        init_iter_tran.writeAction(f"mov_imm2reg {nfront_size} {0}")
        init_iter_tran.writeAction(f"yield")
        
        '''
        Finish the initialization of the frontier and start the BFS iteration
        '''
        bcst_fetch_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.bcst_fetch_ev_label)
        if self.debug_flag:
            bcst_fetch_tran.writeAction(f"print ' '")
            bcst_fetch_tran.writeAction(f"sri {'X0'} {nwid} {LOG2_LANE_PER_UD}")
            bcst_fetch_tran.writeAction(f"andi {nwid} {nwid} {LANE_PER_UD - 1}")
            bcst_fetch_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <broadcast_fetch_frontier> iteration=%ld init frontier return from udid %ld pending_ack = %ld' {'X0'} {num_iter} {nwid} {ud_ctr}")
        bcst_fetch_tran.writeAction(f"subi {ud_ctr} {ud_ctr} 1")
        bcst_fetch_tran.writeAction(f"bnei {ud_ctr} {0} {continue_label}")
        bcst_fetch_tran.writeAction(f"addi {'X0'} {nwid} 0")
        bcst_fetch_tran.writeAction(f"movir {nd_ctr} 0")
        set_ev_label(bcst_fetch_tran, self.ev_word, self.fetch_node_ev_label, new_thread=True)
        set_ev_label(bcst_fetch_tran, sync_evw, self.bcst_ret_ev_label)
        set_nwid(bcst_fetch_tran, self.ev_word, nwid, src_ev=self.ev_word, label=bcst_loop_label)
        bcst_fetch_tran.writeAction(f"sendr3_wcont {self.ev_word} {sync_evw} {num_iter} {num_ud_per_node} {nd_ctr} ")
        bcst_fetch_tran.writeAction(f"addi {nd_ctr} {nd_ctr} 1")
        bcst_fetch_tran.writeAction(f"addi {nwid} {nwid} {LANE_PER_UD * UD_PER_NODE}")
        bcst_fetch_tran.writeAction(f"blt {nd_ctr} {num_nodes} {bcst_loop_label}")
        bcst_fetch_tran.writeAction(f"movir {num_updates} {0}")
        bcst_fetch_tran.writeAction(f"{continue_label}: yield")

        '''
        Fetch frontier node 
        X8:     iteration number
        X9:     number of updown per node
        X10:    current node id
        '''
        num_iter_op     = "X8"
        ud_per_node_op  = "X9"
        curr_ndid_op    = "X10"
        fetch_node_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.fetch_node_ev_label)
        if self.debug_flag:
            fetch_node_tran.writeAction(f"print ' '")
            fetch_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_node_ev_label}> iteration=%ld fetch node frontiers' {'X0'} {num_iter} {nwid} {ud_ctr}")
        set_ev_label(fetch_node_tran, self.ev_word, self.init_ud_mstr_ev_label, new_thread=True)
        set_ev_label(fetch_node_tran, sync_evw, self.fetch_node_ret_ev_label)
        fetch_node_tran.writeAction(f"addi {'X0'} {nwid} 0")
        fetch_node_tran.writeAction(f"movir {ud_ctr} 0")
        set_nwid(fetch_node_tran, self.ev_word, nwid, src_ev=self.ev_word, label=bcst_loop_label)
        fetch_node_tran.writeAction(f"sendr3_wcont {self.ev_word} {sync_evw} {num_iter} {ud_ctr} {'X10'}")
        fetch_node_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        fetch_node_tran.writeAction(f"addi {nwid} {nwid} {LANE_PER_UD}")
        if self.debug_flag:
            fetch_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_node_ev_label}> Start fetch frontiers init the frontier master on node %ld udid %ld' {'X0'} {curr_ndid_op} {ud_ctr}")
        fetch_node_tran.writeAction(f"blt {ud_ctr} {ud_per_node_op} {bcst_loop_label}")
        fetch_node_tran.writeAction(f"movir {num_updates} {0}")
        fetch_node_tran.writeAction(f"addi {'X1'} {self.ev_word} 0")
        fetch_node_tran.writeAction(f"addi {num_iter_op} {num_iter} 0")
        fetch_node_tran.writeAction(f"addi {curr_ndid_op} {nwid} 0")
        fetch_node_tran.writeAction(f"yield")

        '''
        Fetch frontier node return 
            OB_0:   number of updates sent out
            OB_1:   updown nwid
        '''
        fetch_node_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.fetch_node_ret_ev_label)
        if self.debug_flag:
            fetch_node_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_node_ret_ev_label}> Updown %ld sends out num_updates= = %lu Node %ld pending ack = %ld' {'X0'} {'X9'} {'X8'} {nwid} {ud_ctr}")
        fetch_node_ret_tran.writeAction(f"subi {ud_ctr} {ud_ctr} 1")
        fetch_node_ret_tran.writeAction(f"add {num_updates} {'X8'} {num_updates}")
        fetch_node_ret_tran.writeAction(f"bnei {ud_ctr} {0} {continue_label}")
        fetch_node_ret_tran.writeAction(f"sendr_wcont {self.ev_word} {'EQT'} {num_updates} {'X0'}")
        if self.debug_flag:
            fetch_node_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_node_ret_ev_label}> Node %ld sends out the frontiers, num_updates=%lu' {'X0'} {nwid} {num_updates}")
        fetch_node_ret_tran.writeAction(f"yieldt")
        fetch_node_ret_tran.writeAction(f"{continue_label}: yield")
        
        '''
        Return event when updown finish fetch its frontier and send out the update.
        Operands:
            OB_0:   number of updates sent out
            OB_1:   updown nwid
        '''
        fin_fetch_label = "finish_fetch_all_updown"
        zero_front_label = "zero_frontier"

        bcst_r_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.bcst_ret_ev_label)
        if self.debug_flag:
            bcst_r_tran.writeAction(f"print ' '")
            bcst_r_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <updown_finish_fetch_return> ev_word=%lu' {'X0'} {'EQT'}")
            bcst_r_tran.writeAction(f"print '[DEBUG][NWID %ld] Node %ld sends out num_updates=%ld pending_ack=%ld' {'X0'} {f'X{OB_REG_BASE+1}'} {f'X{OB_REG_BASE+0}'} {ud_ctr}")
        bcst_r_tran.writeAction(f"add {f'X{OB_REG_BASE+0}'} {num_updates} {num_updates}")
        bcst_r_tran.writeAction(f"subi {nd_ctr} {nd_ctr} 1")
        bcst_r_tran.writeAction(f"beqi {nd_ctr} {0} {fin_fetch_label}")
        bcst_r_tran.writeAction(f"yield")
        # Finish sending out update requests in all updown's frontier, start global synchronization
        bcst_r_tran.writeAction(f"{fin_fetch_label}: beqi {num_updates} {0} {zero_front_label}")
        if ITERATION_INFO_FLAG:
            bcst_r_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish fetching all the frontiers (= %ld) on iteration %ld. Frontier size = %ld. Start synchronization.' \
                                 {'X0'} {num_uds} {num_iter} {num_updates}")
            bcst_r_tran.writeAction(f"perflog 1 {2} 'Finish fetching all the frontiers on iteration %ld. Frontier size = %ld. Start synchronization.' {num_iter} {num_updates}")
        # set_ev_label(bcst_r_tran, self.ev_word, self.global_init_ev_label, new_thread=True)
        set_ev_label(bcst_r_tran, self.ev_word, self.term_frontier_ev_label)
        set_ev_label(bcst_r_tran, self.scratch[0], self.global_init_ev_label, new_thread=True)
        bcst_r_tran.writeAction(f"sendr3_wcont {self.scratch[0]} {self.ev_word} {num_nodes} {num_ud_per_node} {num_iter}")
        bcst_r_tran.writeAction(f"yield")
        # All frontiers are empty, return to top program.
        bcst_r_tran.writeAction(f"{zero_front_label}: movir {self.scratch[0]} {1}")
        bcst_r_tran.writeAction(f"addi {'X7'} {lm_base} 0")
        bcst_r_tran.writeAction(f"move {self.scratch[0]} {self.top_flag_offset}({lm_base}) 0 8")
        # bcst_r_tran.writeAction(f"move {num_iter} {self.top_val_offset}({lm_base}) 0 8")
        if ITERATION_INFO_FLAG:
            bcst_r_tran.writeAction(f"print '[DEBUG][NWID %ld] BFS converges at iteration = %ld. Return to top.' {'X0'} {num_iter}")
        bcst_r_tran.writeAction(f"yieldt")

        '''
        UDKVMSR pull bfs returns
        X8:     number of map threads executed
        X9:     number of updates
        '''
        pull_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.udkvmsr_return_ev_label)
        if self.debug_flag:
            pull_ret_tran.writeAction(f"print ' '")
            pull_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <udkvmsr_return> ev_word=%lu' {'X0'} {'EQT'}")
            pull_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: num_map_th=%ld, num_updates=%ld' {'X0'} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+1}'}")
        pull_ret_tran.writeAction(f"addi {f'X{OB_REG_BASE+1}'} {num_updates} {0}")
        pull_ret_tran.writeAction(f"beqiu {num_updates} {0} {zero_front_label}")
        set_ev_label(pull_ret_tran, self.ev_word, self.term_frontier_ev_label)
        pull_ret_tran.writeAction(f"sendr3_wcont {self.ev_word} {'EQT'} {num_iter} {num_ud_per_node} {nd_ctr}")
        pull_ret_tran.writeAction(f"yield")
        # All frontiers are empty, return to top program.
        pull_ret_tran.writeAction(f"{zero_front_label}: mov_imm2reg {self.scratch[0]} {1}")
        pull_ret_tran.writeAction(f"addi {'X7'} {lm_base} 0")
        pull_ret_tran.writeAction(f"move {self.scratch[0]} {self.top_flag_offset}({lm_base}) 0 8")
        # term_sync_tran.writeAction(f"move {num_iter} {self.top_val_offset}({lm_base}) 0 8")
        if ITERATION_INFO_FLAG:
            pull_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] BFS converges at iteration = %ld. Return to top.' {'X0'} {num_iter}")
        pull_ret_tran.writeAction(f"yieldt")

        
        '''
        Frontier master return, finish iteration
        X8:     iteration number
        '''
        term_frontier_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.term_frontier_ev_label)
        if self.debug_flag:
            term_frontier_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish global sync on iter %ld, terminating all frontiers' {'X0'} {num_iter}")
        set_ev_label(term_frontier_tran, self.ev_word, self.term_front_node_ev_label, new_thread=True)
        set_ev_label(term_frontier_tran, sync_evw, self.term_sync_ev_label)
        term_frontier_tran.writeAction(f"addi {'X0'} {nwid} 0")
        term_frontier_tran.writeAction(f"movir {nd_ctr} 0")
        # set_ev_label(term_sync_tran, sync_evw, self.term_sync_ev_label)
        set_nwid(term_frontier_tran, self.ev_word, nwid, src_ev=self.ev_word, label=bcst_loop_label)
        term_frontier_tran.writeAction(f"sendr3_wcont {self.ev_word} {sync_evw} {num_iter} {num_ud_per_node} {nd_ctr}")
        term_frontier_tran.writeAction(f"addi {nd_ctr} {nd_ctr} 1")
        term_frontier_tran.writeAction(f"addi {nwid} {nwid} {LANE_PER_UD * UD_PER_NODE}")
        if self.debug_flag:
            term_frontier_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish fetching all frontiers on iter %ld terminate the frontier master on node %ld' {'X0'} {num_iter} {nd_ctr}")
        term_frontier_tran.writeAction(f"blt {nd_ctr} {num_nodes} {bcst_loop_label}")
        term_frontier_tran.writeAction(f"yield")

        '''
        Terminate frontier node 
        X8:     iteration number
        X9:     number of updown per node
        X10:    current node id
        '''
        num_iter_op     = "X8"
        ud_per_node_op  = "X9"
        curr_ndid_op    = "X10"
        term_front_node_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.term_front_node_ev_label)
        if self.debug_flag:
            term_front_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Terminate frontiers on node %ld at iter %ld' {'X0'} {curr_ndid_op} {num_iter_op}")
        set_ev_label(term_front_node_tran, self.ev_word, self.term_ud_mstr_ev_label, new_thread=True)
        set_ev_label(term_front_node_tran, sync_evw, self.term_sync_node_ev_label)
        term_front_node_tran.writeAction(f"addi {'X0'} {nwid} 0")
        term_front_node_tran.writeAction(f"movir {ud_ctr} 0")
        set_nwid(term_front_node_tran, self.ev_word, nwid, src_ev=self.ev_word, label=bcst_loop_label)
        term_front_node_tran.writeAction(f"sendr3_wcont {self.ev_word} {sync_evw} {num_iter} {ud_ctr} {'X10'}")
        term_front_node_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        term_front_node_tran.writeAction(f"addi {nwid} {nwid} {LANE_PER_UD}")
        if self.debug_flag:
            term_front_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish fetching all frontiers terminate the frontier master on node %ld udid %ld' {'X0'} {curr_ndid_op} {ud_ctr}")
        term_front_node_tran.writeAction(f"blt {ud_ctr} {ud_per_node_op} {bcst_loop_label}")
        term_front_node_tran.writeAction(f"movir {nfront_size} 0")
        term_front_node_tran.writeAction(f"addi {'X1'} {self.ev_word} 0")
        term_front_node_tran.writeAction(f"addi {num_iter_op} {num_iter} 0")
        term_front_node_tran.writeAction(f"yield")

        '''
        Terminate frontier node return 
        X8:     iteration number
        X9:     new frontier size
        '''
        term_sync_node_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.term_sync_node_ev_label)
        if self.debug_flag:
            term_sync_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.term_sync_node_ev_label}> ev_word=%lu receive frontier size = %lu pending ack = %ld' {'X0'} {'EQT'} {'X9'} {ud_ctr}")
        term_sync_node_tran.writeAction(f"subi {ud_ctr} {ud_ctr} 1")
        term_sync_node_tran.writeAction(f"add {nfront_size} {'X9'} {nfront_size}")
        term_sync_node_tran.writeAction(f"bnei {ud_ctr} {0} {continue_label}")
        term_sync_node_tran.writeAction(f"sendr_wcont {self.ev_word} {'EQT'} {num_iter} {nfront_size}")
        if self.debug_flag:
            term_sync_node_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.term_sync_node_ev_label}> Finish terminate all the frontiers, local new frontier size = %lu' {'X0'} {nfront_size}")
        term_sync_node_tran.writeAction(f"yieldt")
        term_sync_node_tran.writeAction(f"{continue_label}: yield")
        
        '''
        Syncing all the frontier master
        X8:     iteration number
        X9:     new frontier size
        '''
        continue_bfs_label = "continue_bfs"
        term_sync_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.term_sync_ev_label)
        if self.debug_flag:
            term_sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <terminate_sync> ev_word=%lu pending ack = %ld' {'X0'} {'EQT'} {nd_ctr}")
        term_sync_tran.writeAction(f"subi {nd_ctr} {nd_ctr} 1")
        term_sync_tran.writeAction(f"add {nfront_size} {'X9'} {nfront_size}")
        term_sync_tran.writeAction(f"bnei {nd_ctr} {0} {continue_label}")
        term_sync_tran.writeAction(f"movir {self.scratch[0]} {PULL_SWITCH_AT_ITERATION}")
        term_sync_tran.writeAction(f"bge {num_iter} {self.scratch[0]} {pull_phase_label}")
        term_sync_tran.writeAction(f"{push_phase_label}: beqi {nfront_size} {0} {zero_front_label}")
        if ITERATION_INFO_FLAG:
            term_sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <terminate_sync> Finish iteration %ld, global new frontier size = %lu' {'X0'} {num_iter} {nfront_size}")
            term_sync_tran.writeAction(f"perflog 1 {2} 'Finish terminate all the frontiers at iteration %ld, global new frontier size = %lu' {num_iter} {nfront_size}")
        term_sync_tran.writeAction(f"jmp {continue_bfs_label}")
        if PUSH_SWITCH_AT_ITERATION > 0b11111:
            term_sync_tran.writeAction(f"{pull_phase_label}: movir {self.scratch[0]} {PUSH_SWITCH_AT_ITERATION}")
            term_sync_tran.writeAction(f"bgt {num_iter} {self.scratch[0]} {push_phase_label}")
        else:
            term_sync_tran.writeAction(f"{pull_phase_label}: bgtiu {num_iter} {PUSH_SWITCH_AT_ITERATION} {push_phase_label}")
        # term_sync_tran.writeAction(f"{pull_phase_label}: bgtiu {num_iter} {PUSH_SWITCH_AT_ITERATION} {push_phase_label}")
        if ITERATION_INFO_FLAG:
            term_sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <terminate_sync> Finish iteration %ld, global new frontier size = %lu' {'X0'} {num_iter} {num_updates}")
            term_sync_tran.writeAction(f"perflog 1 {2} 'Finish terminate all the frontiers at iteration %ld, global new frontier size = %lu' {num_iter} {num_updates}")
        set_ev_label(term_sync_tran, self.scratch[0], self.init_iter_ev_label, label=continue_bfs_label)
        term_sync_tran.writeAction(f"sendr3_wcont {self.scratch[0]} {'X1'}  {num_nodes} {num_ud_per_node} {num_iter}")
        term_sync_tran.writeAction(f"movir {nfront_size} 0")
        term_sync_tran.writeAction(f"{continue_label}: yield")
        # All frontiers are empty, return to top program.
        term_sync_tran.writeAction(f"{zero_front_label}: mov_imm2reg {self.scratch[0]} {1}")
        term_sync_tran.writeAction(f"addi {'X7'} {lm_base} 0")
        term_sync_tran.writeAction(f"move {self.scratch[0]} {self.top_flag_offset}({lm_base}) 0 8")
        # term_sync_tran.writeAction(f"move {num_iter} {self.top_val_offset}({lm_base}) 0 8")
        if ITERATION_INFO_FLAG:
            term_sync_tran.writeAction(f"print '[DEBUG][NWID %ld] BFS converges at iteration = %ld. Return to top.' {'X0'} {num_iter}")
        term_sync_tran.writeAction(f"yieldt")
        
        return 

    def gen_frontier_master(self):
        
        self.init_front_ev_label   = self.__get_event_mapping("init_frontier")
        self.insert_front_ev_label = self.__get_event_mapping("insert_to_frontier")
        self.insert_ack_ev_label   = self.__get_event_mapping("insert_ack")
        self.alloc_front_ev_label   = self.__get_event_mapping("allocate_frontier")
        self.fin_fetch_front_ev_label = self.__get_event_mapping("finish_read_frontier")
        self.front_term_ev_label   = self.__get_event_mapping("frontier_terminate")
        
        val         = self.scratch[0]
        lm_addr     = "UDPR_0"
        ofront_base = "UDPR_1"
        nfront_base = "UDPR_2"
        pending_ack = "UDPR_3"
        nfront_ptr  = "UDPR_4"
        front_ins_evw   = "UDPR_5"
        fin_fetch_flag  = "UDPR_6"
        ins_ack_evw = "UDPR_7"
        bcst_mstr_evw = "UDPR_8"
        num_upd     = "UDPR_9"
        ofront_ptr  = "UDPR_10"
        num_element = self.scratch[1]
        
        '''
        Operands:
            OB_0:   iteration number
            OB_1:   new frontier size
        '''

        init_front_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.init_front_ev_label)
        
        bcst_frontier_label = "broadcast_frontier_evw"
        init_front_tran.writeAction(f"addi {'X7'} {lm_addr} 0")
        # switch the frontier 
        init_front_tran.writeAction(f"move {self.ofront_base_offset}({'X7'}) {nfront_base} 0 8")
        init_front_tran.writeAction(f"move {self.nfront_base_offset}({'X7'}) {ofront_base} 0 8")
        init_front_tran.writeAction(f"move {self.nfront_ptr_offset}({'X7'}) {ofront_ptr} 0 8")
        if self.debug_flag:
            init_front_tran.writeAction(f"print ' '")
            init_front_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_updown_frontier_master> iteration = %ld " + 
                                        f"Read in ofront_base=%lu(0x%lx), nfront_base=%lu(0x%lx), ofront_ptr=%lu(0x%lx)' {'X0'} {'X8'} {nfront_base} {nfront_base} {ofront_base} {ofront_base} {ofront_ptr} {ofront_ptr}")
        init_front_tran.writeAction(f"move {ofront_base} {self.ofront_base_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"move {ofront_ptr} {self.ofront_ptr_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"move {nfront_base} {self.nfront_base_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"move {nfront_base} {self.nfront_ptr_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"addi {nfront_base} {nfront_ptr} {0}")
        if self.debug_flag:
            init_front_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_updown_frontier_master> iteration = %ld " + 
                                        f"ofront_base=%lu(0x%lx), nfront_base=%lu(0x%lx)' {'X0'} {'X8'} {ofront_base} {ofront_base} {nfront_base} {nfront_base}")
        init_front_tran.writeAction(f"movir {pending_ack} 0")
        set_ev_label(init_front_tran, front_ins_evw, self.insert_front_ev_label)
        init_front_tran.writeAction(f"movir {val} {LANE_PER_UD}")
        init_front_tran.writeAction(f"{bcst_frontier_label}: sli {pending_ack} {lm_addr} {16}")
        init_front_tran.writeAction(f"add {'X7'} {lm_addr} {lm_addr}")
        init_front_tran.writeAction(f"movrl {front_ins_evw} {self.front_evw_offset}({lm_addr}) 0 8")
        init_front_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        # if self.debug_flag:
        #     init_front_tran.writeAction(f"print '[DEBUG][NWID %ld] Broadcast frontier insert evw %lu to lane %ld base=%lu(%lx) on ud %ld' {'X0'} {front_ins_evw} {pending_ack} {lm_addr} {lm_addr} {'X0'}")
        init_front_tran.writeAction(f"blt {pending_ack} {val} {bcst_frontier_label}")
        init_front_tran.writeAction(f"sendr_reply {'X0'} EQT {self.scratch[2]}")
        init_front_tran.writeAction(f"movir {pending_ack} 0")
        init_front_tran.writeAction(f"movir {fin_fetch_flag} 0")
        set_ev_label(init_front_tran, ins_ack_evw, self.insert_ack_ev_label)
        init_front_tran.writeAction("yield")
        
        '''
        Insert vertex into frontier.
        OB_0:   vertex id
        '''
        insert_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.insert_front_ev_label)
        if self.debug_flag:
            insert_tran.writeAction(f"print ''")
            insert_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <insert_to_frontier> ev_word=%lu insack_evw = %lu Operands: vid=%ld' {'X0'} {'EQT'} {ins_ack_evw} {f'X{OB_REG_BASE+0}'}")
        insert_tran.writeAction(f"sendr_dmlm {nfront_ptr} {ins_ack_evw} {f'X{OB_REG_BASE+0}'}")
        insert_tran.writeAction(f"addi {nfront_ptr} {nfront_ptr} {WORD_SIZE}")
        insert_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        if self.debug_flag:
            insert_tran.writeAction(f"sub {nfront_ptr} {nfront_base} {val}")
            insert_tran.writeAction(f"sri {val} {val} {LOG2_WORD_SIZE}")
            insert_tran.writeAction(f"print '[DEBUG][NWID %ld] Insert vertex %ld to frontier at addr %lu(0x%lx), frontier_base_addr = %lu(0x%lx) " + 
                                    f"frontier_size = %ld pending_ack = %ld' {'X0'} {f'X{OB_REG_BASE+0}'} {nfront_ptr} {nfront_ptr} {nfront_base} {nfront_base} {val} {pending_ack}")
        insert_tran.writeAction(f"yield")
        
        '''
        Insert vertex into frontier.
        OB_0:   number of elements to insert
        '''
        alloc_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.alloc_front_ev_label)
        if self.debug_flag:
            alloc_tran.writeAction(f"addi {'X7'} {lm_addr} 0")
            alloc_tran.writeAction(f"move {self.iteration_offset}({lm_addr}) {self.scratch[0]}  0 8")
            alloc_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <allocate_frontier> ev_word=%lu iteration %ld continuation = %lu Operands: num_elements=%ld request_vid=%ld' {'X0'} {'EQT'} {self.scratch[0]}  {'X1'} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+1}'} ")
        alloc_tran.writeAction(f"sli {f'X{OB_REG_BASE+0}'} {val} {LOG2_WORD_SIZE}")
        # alloc_tran.writeAction(f"addi {'X7'} {lm_addr} 0")
        # alloc_tran.writeAction(f"move {self.nfront_ptr_offset}({lm_addr}) {nfront_ptr}  0 8")
        alloc_tran.writeAction(f"sendr_wcont {'X1'} {front_ins_evw} {nfront_ptr} {val} EQT")
        if self.debug_flag:
            alloc_tran.writeAction(f"move {self.nfront_base_offset}({lm_addr}) {nfront_base} 0 8")
            alloc_tran.writeAction(f"sub {nfront_ptr} {nfront_base} {num_element}")
            alloc_tran.writeAction(f"sri {num_element} {num_element} {LOG2_WORD_SIZE}")
            alloc_tran.writeAction(f"print '[DEBUG][NWID %ld] Allocate %ld elements in frontier starting at at addr %lu(0x%lx), frontier_base_addr = %lu(0x%lx) " + 
                                    f"frontier_size = %ld'  {'X0'} {f'X{OB_REG_BASE+0}'} {nfront_ptr} {nfront_ptr} {nfront_base} {nfront_base} {val}")
        alloc_tran.writeAction(f"add {nfront_ptr} {val} {nfront_ptr}")
        # alloc_tran.writeAction(f"move {nfront_ptr} {self.nfront_ptr_offset}({lm_addr}) 0 8")
        if self.debug_flag:
            alloc_tran.writeAction(f"print '[DEBUG][NWID %ld] New frontier address %lu(0x%lx)' {'X0'} {nfront_ptr} {nfront_ptr}")
        alloc_tran.writeAction(f"yield")
        
        
        '''`
        BFS master finish reading the frontier, notify the frontier master.
        X8:     iteration number
        X9:     udid
        X10:    ndid
        '''
        finish_iteration_label = "finish_iteration"
        continue_label = "continue"
        fin_rd_front_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.fin_fetch_front_ev_label)
        
        if self.debug_flag:
            fin_rd_front_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.fin_fetch_front_ev_label}] Event <finish_read_frontier> ev_word=%lu " + 
                                          f"node %ld updown %ld (nwid=%ld) master finish reading frontier at iteration %ld' {'X0'} {'EQT'} {'X9'} {'X10'} {'X0'} {'X8'}")
        # Return immediately if all the entries have been inserted into the frontier.
        fin_rd_front_tran.writeAction(f"beqi {pending_ack} {0} {finish_iteration_label}")
        # Otherwise wait for the pending insertions to finish.
        fin_rd_front_tran.writeAction(f"movir {fin_fetch_flag} {FLAG}")
        fin_rd_front_tran.writeAction(f"addi {'X1'} {bcst_mstr_evw} 0")
        fin_rd_front_tran.writeAction(f"addi {'X8'} {num_upd} 0")
        fin_rd_front_tran.writeAction(f"yield")
        # Finish insert all the entries into the frontier, given master the frontier for next iteration.
        fin_rd_front_tran.writeAction(f"{finish_iteration_label}: addi {'X7'} {lm_addr} 0")
        # fin_rd_front_tran.writeAction(f"move {nfront_ptr} {self.nfront_ptr_offset}({lm_addr}) 0 8")
        fin_rd_front_tran.writeAction(f"sub {nfront_ptr} {nfront_base} {val}")
        fin_rd_front_tran.writeAction(f"sri {val} {val} {LOG2_WORD_SIZE}")
        if self.debug_flag:
            fin_rd_front_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.fin_fetch_front_ev_label}] Event <finish_insertion> ev_word=%lu finish reading frontier at " + 
                                          f"iteration %ld store new frontier pointer %lu(0x%lx) base %lu(0x%lx) size=%ld' {'X0'} {'EQT'} {'X8'} {nfront_ptr} {nfront_ptr} {nfront_base} {nfront_base} {val}")
        fin_rd_front_tran.writeAction(f"sendr3_wcont {'X1'} {front_ins_evw} {'X8'} {val} {nfront_base}")
        # Exchange the frontier and clear the new frontier to be inserted.
        # fin_rd_front_tran.writeAction(f"movir {fin_fetch_flag} {0}")
        # fin_rd_front_tran.writeAction(f"addi {old_front_base_ptr} {scratch[0]} 0")
        # fin_rd_front_tran.writeAction(f"addi {new_front_base_ptr} {old_front_base_ptr} 0")
        # fin_rd_front_tran.writeAction(f"addi {scratch[0]} {new_front_base_ptr} 0")
        # fin_rd_front_tran.writeAction(f"addi {new_front_size} {old_front_size} 0")
        # fin_rd_front_tran.writeAction(f"movir {new_front_size} {0}")
        fin_rd_front_tran.writeAction(f"addi {ofront_base} {val} 0")
        fin_rd_front_tran.writeAction(f"addi {nfront_base} {ofront_base} 0")
        fin_rd_front_tran.writeAction(f"addi {val} {nfront_base} 0")
        fin_rd_front_tran.writeAction(f"addi {nfront_ptr} {ofront_ptr} 0")
        fin_rd_front_tran.writeAction(f"addi {nfront_base} {nfront_ptr} 0")
        fin_rd_front_tran.writeAction(f"move {ofront_base} {self.ofront_base_offset}({lm_addr}) 0 8")
        fin_rd_front_tran.writeAction(f"move {ofront_ptr} {self.ofront_ptr_offset}({lm_addr}) 0 8")
        fin_rd_front_tran.writeAction(f"move {nfront_base} {self.nfront_base_offset}({lm_addr}) 0 8")
        fin_rd_front_tran.writeAction(f"move {nfront_base} {self.nfront_ptr_offset}({lm_addr}) 0 8")
        if self.debug_flag:
            fin_rd_front_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.fin_fetch_front_ev_label}] After switch frontier, ofront_base=%lu(0x%lx), ofront_ptr=%lu(0x%lx), nfront_base=%lu(0x%lx), " + 
                                          f"nfront_ptr=%lu(0x%lx)' {'X0'} {ofront_base} {ofront_base} {ofront_ptr} {ofront_ptr} {nfront_base} {nfront_base} {nfront_ptr} {nfront_ptr}")
        fin_rd_front_tran.writeAction(f"movir {pending_ack} {0}")
        fin_rd_front_tran.writeAction(f"yield")
        

        '''
        Acknowledge the insertion.
        X8:   DRAM address of the insertion
        '''
        empty_front_label = "empty_frontier"
        insert_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.insert_ack_ev_label)
        if self.debug_flag:
            insert_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex inserted into frontier at addr %lu(0x%lx)' {'X0'} {'X8'} {'X8'}")
        insert_ack_tran.writeAction(f"subi {pending_ack} {pending_ack} {1}")
        insert_ack_tran.writeAction(f"beqi {fin_fetch_flag} {FLAG} {finish_iteration_label}")
        insert_ack_tran.writeAction(f"{continue_label}: yield")
        # Finish insert all the entries into the frontier, given master the frontier for next iteration.
        insert_ack_tran.writeAction(f"{finish_iteration_label}: bnei {pending_ack} {0} {continue_label}")
        insert_ack_tran.writeAction(f"addi {'X7'} {lm_addr} 0")
        # insert_ack_tran.writeAction(f"move {nfront_ptr} {self.nfront_ptr_offset}({lm_addr}) 0 8")
        insert_ack_tran.writeAction(f"sub {nfront_ptr} {nfront_base} {val}")
        insert_ack_tran.writeAction(f"sri {val} {val} {LOG2_WORD_SIZE}")
        if self.debug_flag:
            insert_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.insert_ack_ev_label}] Event <finish_insertion> ev_word=%lu finish reading frontier at " + 
                                          f"iteration %ld store new frontier pointer %lu(0x%lx) base %lu(0x%lx) frontier_size=%ld' {'X0'} {'EQT'} {'X8'} {nfront_ptr} {nfront_ptr} {nfront_base} {nfront_base} {val}")
        insert_ack_tran.writeAction(f"sendr3_wcont {bcst_mstr_evw} {front_ins_evw} {num_upd} {val} {nfront_base}")
        # Exchange the frontier and clear the new frontier to be inserted.
        insert_ack_tran.writeAction(f"addi {ofront_base} {val} 0")
        insert_ack_tran.writeAction(f"addi {nfront_base} {ofront_base} 0")
        insert_ack_tran.writeAction(f"addi {val} {nfront_base} 0")
        insert_ack_tran.writeAction(f"addi {nfront_ptr} {ofront_ptr} 0")
        insert_ack_tran.writeAction(f"addi {nfront_base} {nfront_ptr} 0")
        insert_ack_tran.writeAction(f"move {ofront_base} {self.ofront_base_offset}({lm_addr}) 0 8")
        insert_ack_tran.writeAction(f"move {ofront_ptr} {self.ofront_ptr_offset}({lm_addr}) 0 8")
        insert_ack_tran.writeAction(f"move {nfront_base} {self.nfront_base_offset}({lm_addr}) 0 8")
        insert_ack_tran.writeAction(f"move {nfront_base} {self.nfront_ptr_offset}({lm_addr}) 0 8")
        if self.debug_flag:
            insert_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.insert_ack_ev_label}] After switch frontier, ofront_base=%lu(0x%lx), ofront_ptr=%lu(0x%lx), nfront_base=%lu(0x%lx), " + 
                                          f"nfront_ptr=%lu(0x%lx)' {'X0'} {ofront_base} {ofront_base} {ofront_ptr} {ofront_ptr} {nfront_base} {nfront_base} {nfront_ptr} {nfront_ptr}")
        
        # insert_ack_tran.writeAction(f"addi {old_front_base_ptr} {scratch[0]} 0")
        # insert_ack_tran.writeAction(f"addi {new_front_base_ptr} {old_front_base_ptr} 0")
        # insert_ack_tran.writeAction(f"addi {scratch[0]} {new_front_base_ptr} 0")
        # insert_ack_tran.writeAction(f"addi {new_front_size} {old_front_size} 0")
        # insert_ack_tran.writeAction(f"movir {new_front_size} {0}")
        # insert_ack_tran.writeAction(f"movir {fin_fetch_flag} {0}")
        insert_ack_tran.writeAction(f"movir {pending_ack} {0}")
        insert_ack_tran.writeAction(f"yield")
        
        
        return 
    
    def gen_ud_frontier(self):

        self.init_ud_mstr_ev_label = self.__get_event_mapping("init_updown_master")
        self.ud_sync_ev_label   = self.__get_event_mapping("updown_master_sync")
        
        self.term_ud_mstr_ev_label = self.__get_event_mapping("terminate_updown_master")
        
        self.init_lane_mstr_ev_label = self.__get_event_mapping("init_lane_master")
        self.rcv_update_ev_label   = self.__get_event_mapping("receive_update")

        front_ptr   = "UDPR_0"
        front_bsize = "UDPR_1"
        front_bound = "UDPR_2"
        iter_idx    = "UDPR_3"
        nwid        = "UDPR_4"
        num_init_ln = "UDPR_5"
        front_stride= "UDPR_6"
        front_size  = "UDPR_7"
        sync_evw    = "UDPR_8"
        saved_cont  = "UDPR_9"
        init_ln_evw = "UDPR_10"
        num_update  = "UDPR_11"
        
        empty_frontier_label = "empty_frontier"

        '''
        Start fetching the frontier.
        '''
        lane_fin_init_label = "finish_init_lane"
        lane_init_loop = "lane_init_loop"
        break_label = "break"

        init_ud_mstr_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.init_ud_mstr_ev_label)
        init_ud_mstr_tran.writeAction(f"addi {'X8'} {iter_idx} 0")
        init_ud_mstr_tran.writeAction(f"move {self.ofront_base_offset}({'X7'}) {front_ptr} 0 8")
        init_ud_mstr_tran.writeAction(f"move {self.ofront_ptr_offset}({'X7'}) {front_bound} 0 8")
        if self.debug_flag:
            init_ud_mstr_tran.writeAction(f"print ' '")
        init_ud_mstr_tran.writeAction(f"beq {front_ptr} {front_bound} {empty_frontier_label}")
        init_ud_mstr_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        init_ud_mstr_tran.writeAction(f"sub {front_bound} {front_ptr} {front_bsize}")
        init_ud_mstr_tran.writeAction(f"sri {front_bsize} {front_size} {LOG2_WORD_SIZE}")
        if self.debug_flag:
            init_ud_mstr_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown %ld fetch frontier_ptr=%lu(0x%lx), frontier_boundary=%lu(0x%lx), " + 
                                   f"size=%ld bsize=%ld' {'X0'} {self.scratch[1]} {front_ptr} {front_ptr} {front_bound} {front_bound} {front_size} {front_bsize}")
        init_ud_mstr_tran.writeAction(f"divi {front_size} {front_stride} {LANE_PER_UD - 1}")
        init_ud_mstr_tran.writeAction(f"addi {front_stride} {front_stride} {1}")
        init_ud_mstr_tran.writeAction(f"sli {front_stride} {front_stride} {LOG2_WORD_SIZE}")
        if self.debug_flag:
            init_ud_mstr_tran.writeAction(f"rshift {'X0'} {self.scratch[1]} {LOG2_LANE_PER_UD}")
            init_ud_mstr_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown %ld fetch frontier_ptr=%lu(0x%lx), frontier_boundary=%lu(0x%lx), " + 
                                   f"size=%ld bsize=%ld stride=%ld' {'X0'} {self.scratch[1]} {front_ptr} {front_ptr} {front_bound} {front_bound} {front_size} {front_bsize} {front_stride}")
        init_ud_mstr_tran.writeAction(f"addi {'X0'} {nwid} 1")
        init_ud_mstr_tran.writeAction(f"addi {'X0'} {num_init_ln} {LANE_PER_UD}")
        set_ev_label(init_ud_mstr_tran, init_ln_evw, self.init_lane_mstr_ev_label, new_thread=True)
        set_ev_label(init_ud_mstr_tran, sync_evw, self.ud_sync_ev_label)
        init_ud_mstr_tran.writeAction(f"{lane_init_loop}: ev {init_ln_evw} {init_ln_evw} {nwid} {nwid} {0b1000} ")
        init_ud_mstr_tran.writeAction(f"sendr3_wcont {init_ln_evw} {sync_evw} {front_ptr} {front_stride} {iter_idx}")
        if self.debug_flag:
            init_ud_mstr_tran.writeAction(f"print '[DEBUG][NWID %ld] Send fetch frontier_ptr=%lu(0x%lx), fetch_size=%lu(0x%lx) " +
                                          f"to lane %ld sync_cont=%lu' {'X0'} {front_ptr} {front_ptr} {front_stride} {front_stride} {nwid} {sync_evw}")
        init_ud_mstr_tran.writeAction(f"add {front_ptr} {front_stride} {front_ptr} ")
        init_ud_mstr_tran.writeAction(f"addi {nwid} {nwid} 1")
        init_ud_mstr_tran.writeAction(f"bge {front_ptr} {front_bound} {lane_fin_init_label}")
        init_ud_mstr_tran.writeAction(f"blt {nwid} {num_init_ln} {lane_init_loop}")
        # Finish sending the frontier to all the lanes in this updown except the current one.
        init_ud_mstr_tran.writeAction(f"sub {front_bound} {front_ptr} {front_stride}")
        init_ud_mstr_tran.writeAction(f"ev {init_ln_evw} {init_ln_evw} {'X0'} {'X0'} {0b1000} ")
        init_ud_mstr_tran.writeAction(f"sendr3_wcont {init_ln_evw} {sync_evw} {front_ptr} {front_stride} {iter_idx}")
        if self.debug_flag:
            init_ud_mstr_tran.writeAction(f"print '[DEBUG][NWID %ld] Send fetch frontier_ptr=%lu(0x%lx), fetch_size=%lu(0x%lx)" + 
                                          f"to lane %ld sync_cont=%lu' {'X0'} {'X0'} {front_ptr} {front_ptr} {front_stride} {front_stride} {'X0'} {sync_evw}")
        init_ud_mstr_tran.writeAction(f"movir {num_init_ln} {LANE_PER_UD}")
        init_ud_mstr_tran.writeAction(f"yield")
        init_ud_mstr_tran.writeAction(f"{lane_fin_init_label}: sub {nwid} {'X0'} {num_init_ln}")
        init_ud_mstr_tran.writeAction(f"subi {num_init_ln} {num_init_ln} 1")
        init_ud_mstr_tran.writeAction(f"yield")
        init_ud_mstr_tran.writeAction(f"{empty_frontier_label}: movir {num_update} {0}")
        init_ud_mstr_tran.writeAction(f"sendr_reply {num_update} {'X0'} {self.scratch[2]}")
        if self.debug_flag:
            init_ud_mstr_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown %ld frontier is empty, return to global master.' {'X0'} {'X0'}")
        init_ud_mstr_tran.writeAction(f"yield_terminate")
        
        '''
        Lane finish its assigned frontier segment.
        X8:     Frontier size
        X9:     Return lane nwid
        '''
        ud_sync_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_sync_ev_label)
        ud_sync_tran.writeAction(f"subi {num_init_ln} {num_init_ln} 1")
        if self.debug_flag:
            ud_sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld finish its assigned frontier segment size=%ld, wait for the remaining %ld lanes.' {'X0'} {'X8'} {'X9'} {num_init_ln}")
        ud_sync_tran.writeAction(f"beqi {num_init_ln} {0} {break_label}")
        ud_sync_tran.writeAction(f"yield")
        ud_sync_tran.writeAction(f"{break_label}: sendr_wcont {saved_cont} {'X2'} {front_size} {'X0'} {self.scratch[2]}")
        if self.debug_flag:
            ud_sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown %ld finish its assigned frontier segment, return to global master.' {'X0'} {'X0'}")
        ud_sync_tran.writeAction(f"yield_terminate")
        
        '''
        Finish fetching the frontier, termiante the frontier master.
        X8:     iteration number
        X9:     udid
        X10:    ndid
        '''
        term_ud_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.term_ud_mstr_ev_label)
        term_ud_tran.writeAction(f"movlr {self.front_evw_offset}(X7) {self.ev_word} 0 8")
        set_ev_label(term_ud_tran, self.ev_word, self.fin_fetch_front_ev_label, src_ev=self.ev_word)
        term_ud_tran.writeAction(f"sendr3_wcont {self.ev_word} {'X1'} {'X8'} {'X9'} {'X10'}")
        term_ud_tran.writeAction("yield_terminate")

    def gen_lane_master(self):

        self.fetch_front_ev_label  = self.__get_event_mapping("frontier_fetch_init")
        self.front_rd_ret_ev_label = self.__get_event_mapping("frontier_fetch_return")
        self.front_loop_ev_label   = self.__get_event_mapping("frontier_fetch_loop")
        
        self.rcv_update_ev_label   = self.__get_event_mapping("receive_update")

        fetch_ptr   = "UDPR_0"
        fetch_size  = "UDPR_1"
        fetch_bound = "UDPR_2"
        iter_idx    = "UDPR_3"
        max_thread  = "UDPR_4"
        num_thread  = "UDPR_7"
        lm_base     = "UDPR_8"
        saved_cont  = "UDPR_9"
        upd_evw     = "UDPR_10"
        loop_evw    = "UDPR_11"
        
        finish_frontier_label   = "finish_frontier"
        empty_frontier_label    = "empty_frontier"
        front_fetch_loop_label  = "frontier_fetch_loop"
        finish_fetch_label      = "finish_fetch"

        '''
        Start fetching the frontier.
        X8:    Frontier base address
        X9:    Frontier size
        X10:   Iteration number
        '''
        fetch_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.init_lane_mstr_ev_label)
        fetch_tran.writeAction(f"addi {'X8'} {fetch_ptr} 0")
        fetch_tran.writeAction(f"sri {'X9'} {fetch_size} {LOG2_WORD_SIZE}")
        fetch_tran.writeAction(f"add {fetch_ptr} {'X9'} {fetch_bound}")
        fetch_tran.writeAction(f"addi {'X10'} {iter_idx} 0")
        if self.debug_flag:
            fetch_tran.writeAction(f"print '[DEBUG][NWID %ld] Iteration %ld lane %ld fetch frontier_ptr=%lu(0x%lx), frontier_boundary=%lu(0x%lx), " + 
                                   f"size=%ld' {'X0'} {iter_idx} {'X0'} {fetch_ptr} {fetch_ptr} {fetch_bound} {fetch_bound} {fetch_size}")
        fetch_tran.writeAction(f"beq {fetch_ptr} {fetch_bound} {empty_frontier_label}")
        fetch_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        fetch_tran.writeAction(f"movir {num_thread} {0}")
        fetch_tran.writeAction(f"movir {max_thread} {NUM_UPDATE_THREAD_PER_LANE}")
        set_ev_label(fetch_tran, upd_evw, self.rcv_update_ev_label, new_thread=True)
        fetch_tran.writeAction(f"{front_fetch_loop_label}: send_dmlm_ld {fetch_ptr} {upd_evw} {1}")
        fetch_tran.writeAction(f"addi {fetch_ptr} {fetch_ptr} {WORD_SIZE}")
        fetch_tran.writeAction(f"addi {num_thread} {num_thread} {1}")
        fetch_tran.writeAction(f"bge {fetch_ptr} {fetch_bound} {finish_fetch_label}")
        fetch_tran.writeAction(f"blt {num_thread} {max_thread} {front_fetch_loop_label}")
        fetch_tran.writeAction(f"{finish_fetch_label}: addi {'X7'} {lm_base} 0")
        set_ev_label(fetch_tran, loop_evw, self.front_loop_ev_label)
        fetch_tran.writeAction(f"movrl {loop_evw} {self.ln_mstr_evw_offset}({lm_base}) 0 8")
        fetch_tran.writeAction(f"yield")
        
        fetch_tran.writeAction(f"{empty_frontier_label}: sendr_reply {fetch_size} {'X0'} {self.scratch[2]}")
        if self.debug_flag:
            fetch_tran.writeAction(f"print '[DEBUG][NWID %ld] lane %ld assigned frontier is empty, return to the updown master.' {'X0'} {'X0'}")
        fetch_tran.writeAction(f"yield_terminate")

        '''
        Update finished and returned.
        X1:     update thread event word
        X8:     update vid
        '''
        fetch_loop_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.front_loop_ev_label)
        if self.debug_flag:
            fetch_loop_tran.writeAction(f"print ' '")
            fetch_loop_tran.writeAction(f"sub {fetch_bound} {fetch_ptr} {self.scratch[1]}")
            fetch_loop_tran.writeAction(f"sri {self.scratch[1]} {self.scratch[1]} {LOG2_WORD_SIZE}")
            fetch_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <frontier_fetch_loop> ev_word=%lu return from " + 
                f"update vid=%ld num_active_thread=%ld remaining_frontier_entries=%ld' {'X0'} {'EQT'} {f'X{OB_REG_BASE+0}'} {num_thread} {self.scratch[1]}")
        fetch_loop_tran.writeAction(f"bge {fetch_ptr} {fetch_bound} {finish_fetch_label}")
        if self.debug_flag:
            fetch_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Read next update from frontier at addr 0x%lx' {'X0'} {fetch_ptr}")
        fetch_loop_tran.writeAction(f"send_dmlm_ld {fetch_ptr} {'X1'} {1}")
        fetch_loop_tran.writeAction(f"addi {fetch_ptr} {fetch_ptr} {WORD_SIZE}")
        fetch_loop_tran.writeAction(f"yield")
        # Finish fetching all the updates in the assigned frontier, termiante the update thread
        fetch_loop_tran.writeAction(f"{finish_fetch_label}: subi {num_thread} {num_thread} 1")
        fetch_loop_tran.writeAction(f"beqi {num_thread} {0} {finish_frontier_label}")
        fetch_loop_tran.writeAction(f"yield")
        # Finish sending all the updates, return to updown master
        fetch_loop_tran.writeAction(f"{finish_frontier_label}: sendr_wcont {saved_cont} {'X2'} {fetch_size} {'X0'}")
        if self.debug_flag:
            fetch_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld finish all the assigned updates. " + 
                                        f"Return to ud master cont=%lu' {'X0'} {'X0'} {saved_cont}")
        fetch_loop_tran.writeAction(f"yield_terminate")

        return

    def gen_update_neighbor(self):

        self.fetch_vertex_ev_label  = self.__get_event_mapping("fetch_vertex")
        self.fetch_nbors_local_ev_label     = self.__get_event_mapping("fetch_neighbors_local")

        nlist_bound = "UDPR_0"
        fetch_evw   = "UDPR_1"
        vertex_addr = "UDPR_3"
        max_fetch   = "UDPR_3"
        pending_ack = "UDPR_3"
        saved_cont  = "UDPR_4"
        degree      = "UDPR_5"
        nlist_ptr   = "UDPR_6"
        hash_seed   = "UDPR_7"
        nwid_mask   = "UDPR_8"
        nbor_dist   = "UDPR_9"
        evw_mask    = "UDPR_10"
        nwid        = "UDPR_10"
        orig_vid    = "UDPR_15"
        
        '''
        Receive update from the updown frontier fetch.
        Operands:
            OB_0:   vertex id
        '''
        rcv_upd_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.rcv_update_ev_label)
        if self.debug_flag:
            rcv_upd_tran.writeAction(f"print ' '")
            rcv_upd_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <receive_update> ev_word=%lu vid=%ld dram_addr=%lu(0x%lx)' {'X0'} {'EQT'} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+1}'} {f'X{OB_REG_BASE+1}'}")
        # Read the vertex struct from DRAM
        rcv_upd_tran.writeAction(f"addi {f'X{OB_REG_BASE+0}'} {self.vid} 0")
        rcv_upd_tran = self.__read_vertex(rcv_upd_tran, self.fetch_vertex_ev_label, vertex_addr)
        rcv_upd_tran.writeAction(f"yield")

        '''
        Vertex structure return from DRAM
        Operands:
            OB_0 degree;
            OB_1 orig_vid;
            OB_2 vid;
            OB_3 *neighbors;
            OB_4 distance;
            OB_5 parent;
            OB_6 split_range;
            OB_7 padding;
        '''
        deg_op      = f"X{OB_REG_BASE+0}"
        orig_vid_op = f"X{OB_REG_BASE+1}"
        vid_op      = f"X{OB_REG_BASE+2}"
        nlist_op    = f"X{OB_REG_BASE+3}"
        dist_op     = f"X{OB_REG_BASE+4}"
        
        zero_deg_label          = "zero_degree"
        root_v_label            = "root_vertex"
        continue_label          = "continue"
        send_remote_loop_label  = "send_remote_loop"
        fetch_loop_label        = "fetch_loop"
        skip_remote_label       = "skip_remote"

        fetch_vert_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.fetch_vertex_ev_label)
        if self.debug_flag:
            fetch_vert_tran.writeAction(f"print ' '")
            fetch_vert_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <fetch_vertex> ev_word=%lu vid=%ld ori_vid=%ld " + 
                                        f"distance=%ld degree=%ld' {'X0'} {'EQT'} {vid_op} {orig_vid_op} {dist_op} {deg_op}")
        fetch_vert_tran.writeAction(f"addi {'X7'} {self.scratch[0]} 0")
        fetch_vert_tran.writeAction(f"move {self.nwid_mask_offset}({self.scratch[0]}) {nwid_mask} 0 8")
        
        fetch_vert_tran.writeAction(f"blei {deg_op} 1 {zero_deg_label}")
        fetch_vert_tran.writeAction(f"{continue_label}: addi {deg_op} {degree} 0")
        fetch_vert_tran.writeAction(f"addi {dist_op} {nbor_dist} 1")
        fetch_vert_tran.writeAction(f"addi {orig_vid_op} {orig_vid} 0")
        set_ev_label(fetch_vert_tran, fetch_evw, self.fetch_nbors_remote_ev_label, new_thread=True)
        self.send_to_shortest_flag = True
        if self.send_to_shortest_flag:
            # Create send policy (shortest within 64 lanes)
            fetch_vert_tran.writeAction(f"movir {evw_mask} {1}")
            fetch_vert_tran.writeAction(f"sli {evw_mask} {evw_mask} {27}")
            fetch_vert_tran.writeAction(f"or {'X0'} {evw_mask} {evw_mask}")
            set_nwid(fetch_vert_tran, fetch_evw, evw_mask, src_ev=fetch_evw)
        else:
            fetch_vert_tran.writeAction(f"mul {'X0'} {self.vid} {nwid}")
            fetch_vert_tran.writeAction(f"movir {hash_seed} {NWID_HASH_SEED}")
        fetch_vert_tran.writeAction(f"addi {nlist_op} {nlist_ptr} 0")
        fetch_vert_tran.writeAction(f"lshift {degree} {nlist_bound} {LOG2_WORD_SIZE}")
        fetch_vert_tran.writeAction(f"add {nlist_op} {nlist_bound} {nlist_bound}")
        fetch_vert_tran.writeAction(f"movir {max_fetch} {LOCAL_FETCH_MAX_REQUESTS * DRAM_MSG_SIZE}")
        fetch_vert_tran.writeAction(f"ble {deg_op} {max_fetch} {skip_remote_label}")
        fetch_vert_tran.writeAction(f"muli {max_fetch} {max_fetch} {WORD_SIZE}")
        fetch_vert_tran.writeAction(f"sub {nlist_bound} {max_fetch} {nlist_bound}")
        if self.send_to_shortest_flag:
            fetch_vert_tran.writeAction(f"{send_remote_loop_label}: sendr3_wcont {fetch_evw} {'EQT'} {nlist_ptr} {orig_vid} {nbor_dist}")
        else:
            # Send updates to other lanes for load balance
            fetch_vert_tran.writeAction(f"{send_remote_loop_label}: hash {hash_seed} {nwid}")
            fetch_vert_tran.writeAction(f"and {nwid} {nwid_mask} {nwid}")
            set_nwid(fetch_vert_tran, fetch_evw, nwid, src_ev=fetch_evw)
            fetch_vert_tran.writeAction(f"sendr3_wcont {fetch_evw} {'EQT'} {nlist_ptr} {orig_vid} {nbor_dist}")
        if self.debug_flag:
            fetch_vert_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld sends fetch update orig_vid=%ld new_dist=%ld nlist_ptr=%lu(0x%lx) to nwid=%lu' \
                {'X0'} {self.vid} {orig_vid_op} {nbor_dist} {nlist_ptr} {nlist_ptr} {nwid}")
        fetch_vert_tran.writeAction(f"add {nlist_ptr} {max_fetch} {nlist_ptr}")
        fetch_vert_tran.writeAction(f"blt {nlist_ptr} {nlist_bound} {send_remote_loop_label}")
        fetch_vert_tran.writeAction(f"add {nlist_bound} {max_fetch} {nlist_bound}")
        # Fetch the last few neighbors locally in the same lane
        if self.debug_flag:
            remote_print_label = "remote_print"
            fetch_vert_tran.writeAction(f"jmp {remote_print_label}")
            fetch_vert_tran.writeAction(f"{skip_remote_label}: print '[DEBUG][NWID %ld] Vertex %ld (deg=%ld) skip send to remote' {'X0'} {self.vid} {deg_op}")
            set_ev_label(fetch_vert_tran, fetch_evw, self.fetch_nbors_local_ev_label, label=remote_print_label)
        else:
            set_ev_label(fetch_vert_tran, fetch_evw, self.fetch_nbors_local_ev_label, label=skip_remote_label)
        fetch_vert_tran.writeAction(f"movir {pending_ack} {0}")
        fetch_vert_tran.writeAction(f"{fetch_loop_label}: send_dmlm_ld {nlist_ptr} {fetch_evw} {DRAM_MSG_SIZE}")
        fetch_vert_tran.writeAction(f"addi {nlist_ptr} {nlist_ptr} {DRAM_MSG_SIZE * WORD_SIZE}")
        fetch_vert_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        fetch_vert_tran.writeAction(f"blt {nlist_ptr} {nlist_bound} {fetch_loop_label}")
        set_ev_label(fetch_vert_tran, self.ev_word, self.update_dist_ev_label, new_thread=True)
        if self.debug_flag:
            fetch_vert_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld (deg=%ld) send %ld fetch neighbor from memory' {'X0'} {self.vid} {deg_op} {pending_ack}")
        fetch_vert_tran.writeAction(f"addi {'X7'} {self.scratch[0]} 0")
        fetch_vert_tran = self.__incre_counter(fetch_vert_tran, self.num_updates_offset, deg_op, self.scratch[2], self.scratch[0])
        fetch_vert_tran.writeAction(f"yield")

        fetch_vert_tran.writeAction(f"{zero_deg_label}: beqi {dist_op} {0} {root_v_label}")
        fetch_vert_tran.writeAction(f"movlr {self.ln_mstr_evw_offset}({'X7'}) {saved_cont} 0 8")
        set_ev_label(fetch_vert_tran, self.ev_word, self.rcv_update_ev_label, new_thread=True)
        fetch_vert_tran.writeAction(f"sendr_wcont {saved_cont} {self.ev_word} {vid_op} {orig_vid_op}")
        if self.debug_flag:
            fetch_vert_tran.writeAction(f"print '[DEBUG][NWID %ld] vid=%ld, ori_vid=%ld degree=%ld no update sent' {'X0'} {self.vid} {orig_vid_op} {deg_op}")
        fetch_vert_tran.writeAction(f"yield_terminate")
        
        fetch_vert_tran.writeAction(f"{root_v_label}: beqi {dist_op} {0} {continue_label}")
        fetch_vert_tran.writeAction(f"movlr {self.ln_mstr_evw_offset}({'X7'}) {saved_cont} 0 8")
        set_ev_label(fetch_vert_tran, self.ev_word, self.rcv_update_ev_label, new_thread=True)
        fetch_vert_tran.writeAction(f"sendr_wcont {saved_cont} {self.ev_word} {vid_op} {orig_vid_op}")
        if self.debug_flag:
            fetch_vert_tran.writeAction(f"print '[DEBUG][NWID %ld] vid=%ld, ori_vid=%ld degree=%ld no update sent' {'X0'} {self.vid} {orig_vid_op} {deg_op}")
        fetch_vert_tran.writeAction(f"yield_terminate")

        '''
        Neighbor list return from DRAM
        Operands:
            OB_[0-7]:   neighbor vertex ids
            OB_8:       load address
        '''
        # send updates to neighbors
        temp_ptr    = self.scratch[0]
        nwid        = self.scratch[1]

        nlist_end_label     = "reach_nlist_end"
        fin_update_label    = "finish_update"
        fetch_nbor_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.fetch_nbors_local_ev_label)
        if self.debug_flag:
            fetch_nbor_tran.writeAction(f"print ' '")
            fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_nbors_local_ev_label}> Vertex %ld's neighbors return from DRAM: addr=%ld (0x%lx). " + 
                                        f"Neighbor list ends at addr=%ld (0x%lx) degree=%ld' {'X0'} {self.vid} {'X3'} {'X3'} {nlist_bound} {nlist_bound} {degree}")
        fetch_nbor_tran.writeAction(f"addi {'X3'} {temp_ptr} 0")
        for k in range(DRAM_MSG_SIZE):
            fetch_nbor_tran.writeAction(f"movir {hash_seed} {VERTEX_ID_HASH_SEED}")
            fetch_nbor_tran.writeAction(f"hash X{OB_REG_BASE+k} {hash_seed}")
            fetch_nbor_tran.writeAction(f"sri {hash_seed} {hash_seed} {1}")
            fetch_nbor_tran.writeAction(f"and {hash_seed} {nwid_mask} {nwid}")
            fetch_nbor_tran = set_nwid(fetch_nbor_tran, self.ev_word, nwid, src_ev=self.ev_word)
            fetch_nbor_tran.writeAction(f"sendr3_wcont {self.ev_word} {self.ev_word} X{OB_REG_BASE+k} {nbor_dist} {orig_vid}")
            if self.debug_flag:
                fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld sends update vid=%ld new_dist=%ld parent=%ld to network_id=%ld' \
                    {'X0'} {self.vid} X{OB_REG_BASE+k} {nbor_dist} {orig_vid} {nwid}")
            fetch_nbor_tran.writeAction(f"addi {temp_ptr} {temp_ptr} {WORD_SIZE}")
            fetch_nbor_tran.writeAction(f"bge {temp_ptr} {nlist_bound} {nlist_end_label}")
        fetch_nbor_tran.writeAction(f"{nlist_end_label}: subi {pending_ack} {pending_ack} 1")
        fetch_nbor_tran.writeAction(f"beqi {pending_ack} {0} {fin_update_label}")
        if self.debug_flag:
            fetch_nbor_tran.writeAction(f"sub {nlist_bound} {'X3'} {self.scratch[2]}")
            fetch_nbor_tran.writeAction(f"divi {self.scratch[2]} {self.scratch[2]} {WORD_SIZE}")
            fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld send %ld updates to neighbors, pending_ack = %ld.' {'X0'} {self.scratch[2]} {pending_ack}")
        fetch_nbor_tran.writeAction("yield")
        fetch_nbor_tran.writeAction(f"{fin_update_label}: movlr {self.ln_mstr_evw_offset}({'X7'}) {saved_cont} 0 8")
        set_ev_label(fetch_nbor_tran, self.ev_word, self.rcv_update_ev_label, new_thread=True)
        fetch_nbor_tran.writeAction(f"sendr_wcont {saved_cont} {self.ev_word} {self.vid} {nbor_dist}")
        if self.debug_flag:
            fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld finish sending updates to neighbors. Return to updown master evw=%lu.' {'X0'} {self.vid} {saved_cont}")
        fetch_nbor_tran.writeAction("yield_terminate")

    def gen_fetch_neighbor_remote(self):

        self.fetch_nbors_remote_ev_label    = self.__get_event_mapping("fetch_neighbors_remote")
        self.nbors_ret_ev_label             = self.__get_event_mapping("fetch_neighbors_return")

        nlist_bound = "UDPR_0"
        fetch_evw   = "UDPR_1"
        pending_ack = "UDPR_3"
        max_fetch   = "UDPR_4"
        nlist_ptr   = "UDPR_6"
        hash_seed   = "UDPR_7"
        nwid_mask   = "UDPR_8"
        neighbor_dist   = "UDPR_9"
        orig_vid    = "UDPR_15"

        '''
        Receive fetch request from remote
        Operands:
            OB_0:   neighbor list pointer to be fetched
            0B_1:   original vertex id
            OB_2:   new distance to be sent to neighbor
        '''
        nlist_ptr_op    = f"X{OB_REG_BASE+0}"
        orig_vid_op = f"X{OB_REG_BASE+1}"
        distance_op = f"X{OB_REG_BASE+2}"
        no_tid_label = "no_available_tid"
        fetch_loop_label = "fetch_loop"
        fetch_remote_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.fetch_nbors_remote_ev_label)
        if self.debug_flag:
            # fetch_remote_tran.writeAction(f"print ' '")
            fetch_remote_tran.writeAction(f"movir {max_fetch} {LOCAL_FETCH_MAX_REQUESTS * DRAM_MSG_SIZE}")
            fetch_remote_tran.writeAction(f"muli {max_fetch} {max_fetch} {WORD_SIZE}")
            fetch_remote_tran.writeAction(f"add {nlist_ptr_op} {max_fetch} {nlist_bound}")
            fetch_remote_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_nbors_remote_ev_label}> Vertex %ld sends fetch neighbor request to lane %ld. Neighbor list start at addr=%ld (0x%lx) " + 
                                          f"to addr=%ld (0x%lx) new_distance=%ld' {'X0'} {orig_vid_op} {'X0'} {nlist_ptr_op} {nlist_ptr_op} {nlist_bound} {nlist_bound} {distance_op}")
        fetch_remote_tran.writeAction(f"move {self.num_threads_offset}(X7) {self.scratch[3]} 0 8")
        if self.debug_thread_count_flag:
            fetch_remote_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_nbors_remote_ev_label}> Current number of thread count = %ld' {'X0'} {self.scratch[3]}")
        fetch_remote_tran.writeAction(f"move {self.max_thread_offset}(X7) {self.scratch[1]} 0 8")
        fetch_remote_tran.writeAction(f"bge {self.scratch[3]} {self.scratch[1]} {no_tid_label}")
        fetch_remote_tran.writeAction(f"addi {self.scratch[3]} {self.scratch[3]} 1")
        if self.debug_thread_count_flag:
            fetch_remote_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_nbors_remote_ev_label}> Has available thread id, new number of thread count = %ld' {'X0'} {self.scratch[3]}")
        fetch_remote_tran.writeAction(f"addi {'X7'} {self.scratch[0]} 0")
        fetch_remote_tran.writeAction(f"move {self.scratch[3]} {self.num_threads_offset}({self.scratch[0]}) 0 8")
        fetch_remote_tran.writeAction(f"move {self.nwid_mask_offset}({self.scratch[0]}) {nwid_mask} 0 8")
        fetch_remote_tran.writeAction(f"movir {pending_ack} {0}")
        fetch_remote_tran.writeAction(f"movir {max_fetch} {LOCAL_FETCH_MAX_REQUESTS * DRAM_MSG_SIZE}")
        fetch_remote_tran.writeAction(f"muli {max_fetch} {max_fetch} {WORD_SIZE}")
        fetch_remote_tran.writeAction(f"add {nlist_ptr_op} {max_fetch} {nlist_bound}")
        fetch_remote_tran.writeAction(f"addi {nlist_ptr_op} {nlist_ptr} {0}")
        set_ev_label(fetch_remote_tran, fetch_evw, self.nbors_ret_ev_label)
        fetch_remote_tran.writeAction(f"{fetch_loop_label}: send_dmlm_ld {nlist_ptr} {fetch_evw} {DRAM_MSG_SIZE}")
        fetch_remote_tran.writeAction(f"addi {nlist_ptr} {nlist_ptr} {DRAM_MSG_SIZE * WORD_SIZE}")
        fetch_remote_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        fetch_remote_tran.writeAction(f"blt {nlist_ptr} {nlist_bound} {fetch_loop_label}")
        fetch_remote_tran.writeAction(f"addi {orig_vid_op} {orig_vid} 0")
        fetch_remote_tran.writeAction(f"addi {distance_op} {neighbor_dist} 0")
        set_ev_label(fetch_remote_tran, self.ev_word, self.update_dist_ev_label, new_thread=True)
        if self.debug_thread_count_flag:
            fetch_remote_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.fetch_nbors_remote_ev_label}> Read {LOCAL_FETCH_MAX_REQUESTS * WORD_SIZE} words from vertex %ld neighbor list start " +
                                          f"at addr=%ld (0x%lx) to addr=%ld (0x%lx) pending_ack=%ld' {'X0'} {orig_vid_op} {nlist_ptr_op} {nlist_ptr_op} {nlist_bound} {nlist_bound} {pending_ack}")
        fetch_remote_tran.writeAction(f"yield")
        fetch_remote_tran.writeAction(f"{no_tid_label}: evi EQT {self.ev_word} {255} {0b0100}")
        fetch_remote_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {nlist_ptr_op} 3")
        if self.debug_flag or self.debug_thread_count_flag:
            fetch_remote_tran.writeAction(f"print '[DEBUG][NWID %ld] Push back to queue num_threads=%ld EQT=%ld ev_word=%lu - fetch neighbors vid=%ld dist=%ld nlist_ptr=%ld' \
                {'X0'} {self.scratch[3]} {'EQT'} {self.ev_word} {orig_vid_op} {distance_op} {nlist_ptr_op}")
        fetch_remote_tran.writeAction(f"yield_terminate")

        '''
        Neighbor list return from DRAM
        Operands:
            OB_[0-7]:   neighbor vertex ids
            OB_8:       load address
        '''
        # send updates to neighbors
        temp_ptr    = self.scratch[0]
        nwid        = self.scratch[1]
        nlist_ptr_op = 'X3'
        finish_fetch_label = "finish_fetch"
        fetch_nbor_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.nbors_ret_ev_label)
        if self.debug_flag:
            fetch_nbor_tran.writeAction(f"print ' '")
            fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.nbors_ret_ev_label}> Vertex %ld's neighbors return from DRAM: addr=%ld (0x%lx).' {'X0'} {orig_vid} {'X3'} {'X3'}")
        fetch_nbor_tran.writeAction(f"addi {'X3'} {temp_ptr} 0")
        for k in range(DRAM_MSG_SIZE):
            fetch_nbor_tran.writeAction(f"movir {hash_seed} {VERTEX_ID_HASH_SEED}")
            fetch_nbor_tran.writeAction(f"hash X{OB_REG_BASE+k} {hash_seed}")
            fetch_nbor_tran.writeAction(f"sri {hash_seed} {hash_seed} {1}")
            fetch_nbor_tran.writeAction(f"and {hash_seed} {nwid_mask} {nwid}")
            fetch_nbor_tran = set_nwid(fetch_nbor_tran, self.ev_word, nwid, src_ev=self.ev_word)
            fetch_nbor_tran.writeAction(f"sendr3_wcont {self.ev_word} {self.ev_word} X{OB_REG_BASE+k} {neighbor_dist} {orig_vid}")
            if self.debug_flag:
                fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld sends update to vid=%ld new_dist=%ld parent=%ld to network_id=%ld' \
                    {'X0'} {orig_vid} X{OB_REG_BASE+k} {neighbor_dist} {orig_vid} {nwid}")
            fetch_nbor_tran.writeAction(f"addi {temp_ptr} {temp_ptr} {WORD_SIZE}")
        fetch_nbor_tran.writeAction(f"subi {pending_ack} {pending_ack} 1")
        fetch_nbor_tran.writeAction(f"beqi {pending_ack} {0} {finish_fetch_label}")
        if self.debug_flag:
            fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld send {DRAM_MSG_SIZE} updates to neighbors, pending_ack = %ld.' {'X0'} {orig_vid} {pending_ack}")
        fetch_nbor_tran.writeAction("yield")
        fetch_nbor_tran.writeAction(f"{finish_fetch_label}: move {self.num_threads_offset}(X7) {self.scratch[3]} 0 8")
        fetch_nbor_tran.writeAction(f"subi {self.scratch[3]} {self.scratch[3]} 1")
        fetch_nbor_tran.writeAction(f"addi {'X7'} {self.scratch[0]} 0")
        fetch_nbor_tran.writeAction(f"move {self.scratch[3]} {self.num_threads_offset}({self.scratch[0]}) 0 8")
        if self.debug_thread_count_flag:
            fetch_nbor_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.nbors_ret_ev_label}> Finish send out updates, new number of thread count = %ld' {'X0'} {self.scratch[3]}")
        fetch_nbor_tran.writeAction("yield_terminate")

    def gen_update_dist(self):

        self.update_dist_ev_label   = self.__get_event_mapping("update_distance")
        self.read_v_ev_label        = self.__get_event_mapping("read_vertex")
        self.store_ack_ev_label     = self.__get_event_mapping("store_ack")
        self.update_sib_ev_label   = self.__get_event_mapping("update_sibling")

        '''
        Update the distance of the vertex.
        OB_0:   incoming vid
        OB_1:   incoming dist
        OB_2:   incoming parent
        '''
        income_vid  = f"X{OB_REG_BASE+0}"
        new_dist    = f"X{OB_REG_BASE+1}"
        new_parent  = f"X{OB_REG_BASE+2}"
        no_tid_label = "no_available_tid"
        udp_dist_tran       = self.state.writeTransition("eventCarry", self.state, self.state, self.update_dist_ev_label)
        if self.debug_flag:
            udp_dist_tran.writeAction(f"print ' '")
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <update_distance> Receive update to vid=%ld, new_dist=%ld, new_parent=%ld' {'X0'} {income_vid} {new_dist} {new_parent}")


        self.graph_ptr      = "UDPR_0"
        self.entry_offset   = "UDPR_1"
        self.vid        = "UDPR_2"
        self.parent     = "UDPR_3"
        self.dist       = "UDPR_4"
        store_ack_evw   = "UDPR_5"
        pending_ack     = "UDPR_6"
        cached_key      = "UDPR_6"
        vertex_addr     = "UDPR_7"
        nwid_mask       = "UDPR_8"
        from_sibling    = "UDPR_15"
        self.ev_word    = "UDPR_11"

        skip_update_label = "skip_update"
        cache_evict_label = "cache_evict"
        udp_dist_tran.writeAction(f"addi {'X7'} {self.scratch[2]} 0")
        udp_dist_tran.writeAction(f"move {self.nwid_mask_offset}({self.scratch[2]}) {nwid_mask} 0 8")
        udp_dist_tran = self.__look_up_cache(udp_dist_tran, income_vid, cached_key)
        udp_dist_tran.writeAction(f"beq {cached_key} {income_vid} {skip_update_label}")
        udp_dist_tran.writeAction(f"mov_imm2reg {self.scratch[0]} {1}")
        udp_dist_tran.writeAction(f"sli {self.scratch[0]} {self.scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        udp_dist_tran.writeAction(f"add {self.scratch[0]} {income_vid} {self.scratch[0]}")
        udp_dist_tran.writeAction(f"beq {self.scratch[0]} {cached_key} {skip_update_label}")
        udp_dist_tran.writeAction(f"sri {cached_key} {self.scratch[1]} {self.INACTIVE_MASK_SHIFT}")
        udp_dist_tran.writeAction(f"beqi {self.scratch[1]} 1 {cache_evict_label}")  # miss yet value can be evicted
        if self.debug_flag:
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Cache miss vid=%ld, cached_key=%ld' {'X0'} {income_vid} {cached_key}")
        udp_dist_tran.writeAction(f"evi EQT {self.ev_word} {255} {0b0100}")
        udp_dist_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {income_vid} 3")
        if self.debug_flag:
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Push back to queue due to cache conflict - update vid=%ld dist=%ld parent=%ld' \
                {'X0'} {income_vid} {f'X{OB_REG_BASE+1}'} {f'X{OB_REG_BASE+2}'}")
        udp_dist_tran.writeAction(f"yield_terminate")

        udp_dist_tran.writeAction(f"{no_tid_label}: evi EQT {self.ev_word} {255} {0b0100}")
        udp_dist_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {income_vid} 3")
        if self.debug_flag:
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Push back to queue due to tid limit: num_threads=%ld - update vid=%ld dist=%ld parent=%ld' \
                {'X0'} {self.scratch[3]} {income_vid} {f'X{OB_REG_BASE+1}'} {f'X{OB_REG_BASE+2}'}")
        udp_dist_tran.writeAction(f"yield_terminate")

        # Check the thread name space usage before evicting the cached value
        udp_dist_tran.writeAction(f"{cache_evict_label}: move {self.num_threads_offset}(X7) {self.scratch[3]} 0 8")
        if self.debug_thread_count_flag:
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.update_dist_ev_label}> Current number of thread count = %ld' {'X0'} {self.scratch[3]}")
        udp_dist_tran.writeAction(f"move {self.max_thread_offset}(X7) {self.scratch[1]} 0 8")
        udp_dist_tran.writeAction(f"bge {self.scratch[3]} {self.scratch[1]} {no_tid_label}")
        udp_dist_tran.writeAction(f"addi {income_vid} {self.vid} 0")
        if self.debug_flag:
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Cache miss vid=%ld, evicts cached_key=%ld' {'X0'} {income_vid} {cached_key}")
        udp_dist_tran.writeAction(f"addi {self.scratch[0]} {cached_key} 0")
        udp_dist_tran.writeAction(f"move {self.vid} {self.cache_base_offset}({self.entry_offset}) 0 8")
        udp_dist_tran = self.__read_vertex(udp_dist_tran, self.read_v_ev_label, vertex_addr)
        udp_dist_tran.writeAction(f"move {new_dist} {self.val_1_offset}({self.entry_offset}) 0 8")
        udp_dist_tran.writeAction(f"move {new_parent} {self.val_2_offset}({self.entry_offset}) 0 8")
        udp_dist_tran = self.__incre_counter(udp_dist_tran, self.num_threads_offset, '1', self.scratch[3], self.scratch[2])
        if self.debug_thread_count_flag:
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.update_dist_ev_label}> Has available thread id, new number of thread count = %ld' {'X0'} {self.scratch[3]}")
        udp_dist_tran.writeAction(f"movir {from_sibling} 0")
        udp_dist_tran.writeAction("yield")

        # Vertex is cached, incoming distance must be no less than the cached distance.
        udp_dist_tran = self.__incre_counter(udp_dist_tran, self.num_consume_offset, '1', self.scratch[3], self.scratch[2], skip_update_label)
        if self.debug_flag:
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Skip update. Comsume vid=%ld.' {'X0'} {income_vid}")
            udp_dist_tran.writeAction(f"move {self.val_1_offset}({self.entry_offset}) {self.dist} 0 8")
            udp_dist_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish update vid=%ld, cached dist=%ld skip update' {'X0'} {income_vid} {self.dist}")
        udp_dist_tran.writeAction("yield_terminate")

        '''
        Read the vertex from DRAM.
            OB_0 degree;
            OB_1 orig_vid;
            OB_2 vid;
            OB_3 *neighbors;
            OB_4 distance;
            OB_5 parent;
            OB_6 split_range;
            OB_7 padding;
        '''
        skip_sibling_label  = "skip_insert_sibling"
        ins_sibling_label   = "insert_sibling"
        skip_update_label   = "skip_update"
        finish_update_label = "finish_update"
        skip_current_label  = "skip_current"
        skip_orig_label     = "skip_original_vertex"
        read_v_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.read_v_ev_label)
        if self.debug_flag:
            read_v_tran.writeAction(f"print ' '")
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <read_vertex> ev_word=%lu' {'X0'} {'EQT'}")
        read_v_tran.writeAction(f"move {self.val_1_offset}({self.entry_offset}) {self.dist} 0 8")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Read return vid=%ld, Cached distance=%ld, distance_from_dram=%ld' {'X0'} {self.vid} {self.dist} {f'X{OB_REG_BASE+4}'}")
        read_v_tran.writeAction(f"bleu {f'X{OB_REG_BASE+4}'} {self.dist} {skip_update_label}")
        read_v_tran.writeAction(f"move {cached_key} {self.cache_base_offset}({self.entry_offset}) 0 8")
        read_v_tran.writeAction(f"move {self.val_2_offset}({self.entry_offset}) {self.parent} 0 8")
        set_ev_label(read_v_tran, store_ack_evw, self.store_ack_ev_label)
        read_v_tran.writeAction(f"movir {pending_ack} {1}")
        
        sibling_vid     = "UDPR_1"
        sibling_max_vid = "UDPR_9"
        num_siblings    = "UDPR_10"
        nwid    = self.scratch[2]
        # Send updates to siblings of the same original vertex
        # read_v_tran.writeAction(f"ble {f'X{OB_REG_BASE+2}'} {f'X{OB_REG_BASE+1}'} {skip_sibling_label}")
        read_v_tran.writeAction(f"beqiu {from_sibling} {1} {skip_sibling_label}")
        read_v_tran.writeAction(f"sri {f'X{OB_REG_BASE+6}'} {sibling_vid} {32}")
        read_v_tran.writeAction(f"sli {f'X{OB_REG_BASE+6}'} {sibling_max_vid} {32}")
        read_v_tran.writeAction(f"sri {sibling_max_vid} {sibling_max_vid} {32}")
        read_v_tran.writeAction(f"sub {sibling_max_vid} {sibling_vid} {num_siblings}")
        read_v_tran.writeAction(f"beqi {num_siblings} {1} {skip_sibling_label}")
        # read_v_tran.writeAction(f"add {pending_ack} {num_siblings} {pending_ack}")
        # read_v_tran.writeAction(f"add {pending_ack} {num_siblings} {pending_ack}")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Update siblings of vid=%ld, sibling_vid_range=[%ld, %ld], " + 
                                    f"num_siblings=%d' {'X0'} {f'X{OB_REG_BASE+2}'} {sibling_vid} {sibling_max_vid} {num_siblings}")
        set_ev_label(read_v_tran, self.ev_word, self.update_sib_ev_label, new_thread=True)
        read_v_tran.writeAction(f"movlr {self.nwid_mask_offset}({'X7'}) {nwid_mask} 0 8")
        read_v_tran.writeAction(f"{ins_sibling_label}: beq {sibling_vid} {self.vid} {skip_current_label}")
        read_v_tran.writeAction(f"movir {self.scratch[0]} {VERTEX_ID_HASH_SEED}")
        read_v_tran.writeAction(f"hash {sibling_vid} {self.scratch[0]}")
        read_v_tran.writeAction(f"and {self.scratch[0]} {nwid_mask} {nwid}")
        read_v_tran = set_nwid(read_v_tran, self.ev_word, nwid, src_ev=self.ev_word)
        read_v_tran.writeAction(f"sendr3_wcont {self.ev_word} {store_ack_evw} {sibling_vid} {self.dist} {self.parent}")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Vertex %ld sends update to sibling vid=%ld new_dist=%ld to network_id=%ld' \
                {'X0'} {self.vid} {sibling_vid} {self.dist} {nwid}")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.read_v_ev_label}] Send update sibling request for vid = %ld to lane %ld' {'X0'} {sibling_vid} {nwid} ")
        read_v_tran.writeAction(f"{skip_current_label}: addi {sibling_vid} {sibling_vid} {1}")
        read_v_tran.writeAction(f"blt {sibling_vid} {sibling_max_vid} {ins_sibling_label}")
        # Increment the number of updates by the number of siblings - 1 (the current vertex)
        read_v_tran.writeAction(f"subi {num_siblings} {self.scratch[0]} 1")
        read_v_tran.writeAction(f"addi {'X7'} {self.scratch[1]} 0")
        read_v_tran = self.__incre_counter(read_v_tran, self.num_updates_offset, self.scratch[0], self.scratch[2], self.scratch[1])
        
        # Insert the current vertex to the frontier
        read_v_tran.writeAction(f"movlr {self.front_evw_offset}({'X7'}) {self.ev_word} 0 8")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Send update request for vid = %ld to frontier insert evw %lu' {'X0'} {self.vid} {self.ev_word} ")
        read_v_tran.writeAction(f"sendr3_wcont {self.ev_word} {store_ack_evw} {self.vid} {self.vid} {self.parent} ")
        self.__get_v_dist_addr(read_v_tran, self.vid, vertex_addr)
        read_v_tran.writeAction(f"sendr2_dmlm {vertex_addr} {store_ack_evw} {self.dist} {self.parent}")
        read_v_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        
        # Store the newest distance and parent id to the orignal vertex to DRAM
        self.__get_orig_v_dist_addr(read_v_tran, f'X{OB_REG_BASE+1}', vertex_addr)
        read_v_tran.writeAction(f"sendr2_dmlm {vertex_addr} {store_ack_evw} {self.dist} {self.parent}")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Write back original vertex %ld's distance %ld parent %ld at addr=%lu(0x%lx), return ev_word=%lu' " + 
                                    f"{'X0'} {f'X{OB_REG_BASE+1}'} {self.dist} {self.parent} {vertex_addr} {vertex_addr} {store_ack_evw}")
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] update vid=%ld pending ack = %ld' {'X0'} {self.vid} {pending_ack}")
        read_v_tran.writeAction(f"yield")
        
        # Insert the vertex to frontier
        read_v_tran.writeAction(f"{skip_sibling_label}: movlr {self.front_evw_offset}({'X7'}) {self.ev_word} 0 8")
        read_v_tran.writeAction(f"sendr_wcont {self.ev_word} {store_ack_evw} {self.vid} {self.vid}")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Insert vid=%ld to frontier.' {'X0'} {self.vid}")# Store the newest distance and parent id to DRAM
        read_v_tran.writeAction(f"addi {'X3'} {self.scratch[1]} {WORD_SIZE * 4}")
        read_v_tran.writeAction(f"sendr2_dmlm {self.scratch[1]} {store_ack_evw} {self.dist} {self.parent}")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Write back vertex %ld's distance %ld parent %ld, addr=%lu(0x%lx)' " + 
                                    f"{'X0'} {self.vid} {self.dist} {self.parent} {self.scratch[1]}")
        read_v_tran.writeAction(f"beqiu {from_sibling} {1} {skip_orig_label}")
        self.__get_orig_v_dist_addr(read_v_tran, f'X{OB_REG_BASE+1}', vertex_addr)
        read_v_tran.writeAction(f"sendr2_dmlm {vertex_addr} {store_ack_evw} {self.dist} {self.parent}")
        read_v_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Write back orig vertex %ld's distance %ld parent %ld, addr=%lu(0x%lx)' " + 
                                    f"{'X0'} {f'X{OB_REG_BASE+1}'} {self.dist} {self.parent} {vertex_addr}")
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] update vid=%ld pending ack = %ld' {'X0'} {self.vid} {pending_ack}")
        
        read_v_tran.writeAction(f"{skip_orig_label}: yield")
        
        # Income distance is larger than the current distance, no need to update.
        read_v_tran.writeAction(f"{skip_update_label}: move {cached_key} {self.cache_base_offset}({self.entry_offset}) 0 8")
        read_v_tran.writeAction(f"move {f'X{OB_REG_BASE+4}'} {self.val_1_offset}({self.entry_offset}) 0 8")
        read_v_tran.writeAction(f"move {f'X{OB_REG_BASE+5}'} {self.val_2_offset}({self.entry_offset}) 0 8")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Skip update for vid=%ld, dist_from_dram=%ld, incoming_dist=%ld' {'X0'} {self.vid} {f'X{OB_REG_BASE+4}'} {self.dist}")
        read_v_tran.writeAction(f"addi {'X7'} {self.scratch[1]} 0")
        read_v_tran = self.__incre_counter(read_v_tran, self.num_consume_offset, '1', self.scratch[2], self.scratch[1])
        read_v_tran = self.__incre_counter(read_v_tran, self.num_threads_offset, '-1', self.scratch[2], self.scratch[1])
        if self.debug_thread_count_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.read_v_ev_label}> Skip update and terminate thread, new number of thread count = %ld' {'X0'} {self.scratch[3]}")
        if self.debug_flag:
            read_v_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish update vid=%ld, new_dist=%ld skip update' {'X0'} {self.vid} {f'X{OB_REG_BASE+5}'}")
        read_v_tran.writeAction(f"yield_terminate")


        store_ack_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.store_ack_ev_label)
        store_ack_tran.writeAction(f"subi {pending_ack} {pending_ack} 1")
        if self.debug_flag:
            store_ack_tran.writeAction(f"print ' '")
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <store_ack> vid = %ld OB_0=%lu(0x%lx) pending_ack = %ld.' {'X0'} {self.vid} {f'X{OB_REG_BASE+0}'} {f'X{OB_REG_BASE+0}'} {pending_ack}")
        store_ack_tran.writeAction(f"beqi {pending_ack} 0 {finish_update_label}")
        store_ack_tran.writeAction(f"yield")
        store_ack_tran.writeAction(f"{finish_update_label}: addi {'X7'} {self.scratch[1]} 0")
        self.__incre_counter(store_ack_tran, self.num_consume_offset, '1', self.scratch[2], self.scratch[1])
        self.__incre_counter(store_ack_tran, self.num_threads_offset, '-1', self.scratch[2], self.scratch[1])
        if self.debug_thread_count_flag:
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.store_ack_ev_label}> Finish writing back the updated distance and parent, new number of thread count = %ld' {'X0'} {self.scratch[3]}")
        if self.debug_flag:
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish update vid=%ld local_num_consumes=%lu' {'X0'} {self.vid} {self.dist} {self.scratch[2]}")
        store_ack_tran.writeAction("yield_terminate")

        '''
        Update the distance of the vertex.
        OB_0:   incoming vid
        OB_1:   incoming dist
        OB_2:   incoming parent
        '''
        income_vid  = f"X{OB_REG_BASE+0}"
        new_dist    = f"X{OB_REG_BASE+1}"
        new_parent  = f"X{OB_REG_BASE+2}"
        no_tid_label = "no_available_tid"
        upd_sib_tran       = self.state.writeTransition("eventCarry", self.state, self.state, self.update_sib_ev_label)
        if self.debug_flag:
            upd_sib_tran.writeAction(f"print ' '")
            upd_sib_tran.writeAction(f"print '[DEBUG][NWID %ld][update_sibling] Event <update_sibling> Receive update to vid=%ld, new_dist=%ld, new_parent=%ld' {'X0'} {income_vid} {new_dist} {new_parent}")

        skip_update_label = "skip_update"
        cache_evict_label = "cache_evict"
        upd_sib_tran.writeAction(f"addi {'X7'} {self.scratch[2]} 0")
        upd_sib_tran.writeAction(f"move {self.nwid_mask_offset}({self.scratch[2]}) {nwid_mask} 0 8")
        upd_sib_tran = self.__look_up_cache(upd_sib_tran, income_vid, cached_key)
        upd_sib_tran.writeAction(f"beq {cached_key} {income_vid} {skip_update_label}")
        upd_sib_tran.writeAction(f"mov_imm2reg {self.scratch[0]} {1}")
        upd_sib_tran.writeAction(f"sli {self.scratch[0]} {self.scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        upd_sib_tran.writeAction(f"add {self.scratch[0]} {income_vid} {self.scratch[0]}")
        upd_sib_tran.writeAction(f"beq {self.scratch[0]} {cached_key} {skip_update_label}")
        upd_sib_tran.writeAction(f"sri {cached_key} {self.scratch[1]} {self.INACTIVE_MASK_SHIFT}")
        upd_sib_tran.writeAction(f"beqi {self.scratch[1]} 1 {cache_evict_label}")  # miss yet value can be evicted
        if self.debug_flag:
            upd_sib_tran.writeAction(f"print '[DEBUG][NWID %ld][update_sibling] Cache miss vid=%ld, cached_key=%ld' {'X0'} {income_vid} {cached_key}")
        upd_sib_tran.writeAction(f"{no_tid_label}: evi EQT {self.ev_word} {255} {0b0100}")
        upd_sib_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {income_vid} 3")
        if self.debug_flag:
            upd_sib_tran.writeAction(f"print '[DEBUG][NWID %ld][update_sibling] Push back to queue num_threads=%ld EQT=%ld ev_word=%lu - update vid=%ld dist=%ld parent=%ld' \
                {'X0'} {self.scratch[3]} {'EQT'} {self.ev_word} {income_vid} {f'X{OB_REG_BASE+1}'} {f'X{OB_REG_BASE+2}'}")
        upd_sib_tran.writeAction(f"yield_terminate")

        # Check the thread name space usage before evicting the cached value
        upd_sib_tran.writeAction(f"{cache_evict_label}: move {self.num_threads_offset}(X7) {self.scratch[3]} 0 8")
        if self.debug_thread_count_flag:
            upd_sib_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.update_sib_ev_label}> Current number of thread count = %ld' {'X0'} {self.scratch[3]}")
        upd_sib_tran.writeAction(f"move {self.max_thread_offset}(X7) {self.scratch[1]} 0 8")
        upd_sib_tran.writeAction(f"bge {self.scratch[3]} {self.scratch[1]} {no_tid_label}")
        upd_sib_tran.writeAction(f"addi {income_vid} {self.vid} 0")
        if self.debug_flag:
            upd_sib_tran.writeAction(f"print '[DEBUG][NWID %ld][update_sibling] Cache miss vid=%ld, evicts cached_key=%ld' {'X0'} {income_vid} {cached_key}")
        upd_sib_tran.writeAction(f"addi {self.scratch[0]} {cached_key} 0")
        upd_sib_tran.writeAction(f"move {self.vid} {self.cache_base_offset}({self.entry_offset}) 0 8")
        upd_sib_tran = self.__read_vertex(upd_sib_tran, self.read_v_ev_label, vertex_addr)
        upd_sib_tran.writeAction(f"move {new_dist} {self.val_1_offset}({self.entry_offset}) 0 8")
        upd_sib_tran.writeAction(f"move {new_parent} {self.val_2_offset}({self.entry_offset}) 0 8")
        upd_sib_tran = self.__incre_counter(upd_sib_tran, self.num_threads_offset, '1', self.scratch[3], self.scratch[2])
        if self.debug_thread_count_flag:
            upd_sib_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <{self.update_sib_ev_label}> Has available thread id, new number of thread count = %ld' {'X0'} {self.scratch[3]}")
        upd_sib_tran.writeAction(f"movir {from_sibling} 1")
        upd_sib_tran.writeAction("yield")

        # Vertex is cached, incoming distance must be no less than the cached distance.
        upd_sib_tran.writeAction(f"{skip_update_label}: addi {'X7'} {self.scratch[1]} 0")
        if self.debug_flag:
            upd_sib_tran.writeAction(f"print '[DEBUG][NWID %ld] Skip update sibling. Comsume vid=%ld.' {'X0'} {income_vid}")
        self.__incre_counter(upd_sib_tran, self.num_consume_offset, '1', self.scratch[2], self.scratch[1])
        upd_sib_tran.writeAction(f"yield_terminate")


        return

    def __incre_counter(self, tran: EFAProgram.Transition, offset, val, reg1, lm_base, label = "") -> EFAProgram.Transition:

        if label:
            tran.writeAction(f"{label}: move {offset}({lm_base}) {reg1} 0 8")
        else:
            tran.writeAction(f"move {offset}({lm_base}) {reg1} 0 8")
        if isinstance(val, int) or val.isdigit():
            if int(val) >= 0:
                tran.writeAction(f"addi {reg1} {reg1} {val}")
            else:
                tran.writeAction(f"subi {reg1} {reg1} {abs(val)}")
        elif val[0] == '-' and val[1:].isdigit():
            tran.writeAction(f"subi {reg1} {reg1} {val[1:]}")
        else:
            tran.writeAction(f"add {reg1} {val} {reg1}")
        tran.writeAction(f"move {reg1} {offset}({lm_base}) 0 8")
        return tran

    def __look_up_cache(self, tran: EFAProgram.Transition, key, cached_key) -> EFAProgram.Transition:

        HASH_SEED = 11
        tran.writeAction(f"movir {self.entry_offset} {self.cache_size}")
        tran.writeAction(f"movir {cached_key} {HASH_SEED}")
        tran.writeAction(f"hash {key} {cached_key}")
        tran.writeAction(f"sri {cached_key} {cached_key} {1}")
        tran.writeAction(f"mod {cached_key} {self.entry_offset} {self.entry_offset}")
        tran.writeAction(f"sli {self.entry_offset} {self.entry_offset} {int(log2(self.cache_entry_size))} ")
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] Look up vertex %ld in the cache offset = %ld' {'X0'} {key} {self.entry_offset}")
        tran.writeAction(f"add X7 {self.entry_offset} {self.entry_offset}")                         # get entry offset
        tran.writeAction(f"move {self.cache_base_offset}({self.entry_offset}) {cached_key} 0 8")    # get cached key
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] key = %ld, cached_key = %ld' {'X0'} {key} {cached_key}")
        return tran

    def __read_vertex(self, tran: EFAProgram.Transition, ret_ev_label: str, vertex_addr: str) -> EFAProgram.Transition:

        tran.writeAction(f"move {self.vertices_ptr_offset}(X7) {self.graph_ptr} 0 8")
        tran.writeAction(f"sli {self.vid} {vertex_addr} {self.LOG2_SIZEOF_VERTEX}")
        tran.writeAction(f"add {vertex_addr} {self.graph_ptr} {vertex_addr}")
        tran.writeAction(f"send_dmlm_ld_wret {vertex_addr} {ret_ev_label} {self.SIZEOF_VERTEX // WORD_SIZE} {self.scratch[1]}")
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] Read vertex %ld addr 0x%lx' {'X0'} {self.vid} {vertex_addr}")
        return tran
    
    def __get_v_dist_addr(self, tran: EFAProgram.Transition, vid: str, addr: str, label: str = '') -> EFAProgram.Transition:
        
        label = f'{label}: ' if label else ''
        tran.writeAction(f"{label}move {self.vertices_ptr_offset}(X7) {self.graph_ptr} 0 8")
        tran.writeAction(f"lshift {vid} {addr} {self.LOG2_SIZEOF_VERTEX}")
        tran.writeAction(f"add {addr} {self.graph_ptr} {addr}")
        tran.writeAction(f"addi {addr} {addr} {WORD_SIZE * 4}")

    def __get_orig_v_dist_addr(self, tran: EFAProgram.Transition, vid: str, addr: str, label: str = '') -> EFAProgram.Transition:
        
        label = f'{label}: ' if label else ''
        tran.writeAction(f"{label}move {self.orig_graph_offset}(X7) {self.graph_ptr} 0 8")
        tran.writeAction(f"lshift {vid} {addr} {self.LOG2_SIZEOF_VERTEX}")
        tran.writeAction(f"add {addr} {self.graph_ptr} {addr}")
        tran.writeAction(f"addi {addr} {addr} {WORD_SIZE * 4}")

    def gen_global_sync(self):

        self.global_init_ev_label   = self.__get_event_mapping("init_global_sync")
        self.node_init_ev_label     = self.__get_event_mapping("init_node_sync")
        self.ud_accum_ev_label      = self.__get_event_mapping("ud_accumulate")
        self.global_sync_ev_label   = self.__get_event_mapping("global_sync")
        self.node_sync_ev_label     = self.__get_event_mapping("node_sync")
        
        self.ev_word    = "UDPR_11"

        global_sync_offsets = [self.num_updates_offset, self.num_consume_offset, self.top_flag_offset]
        global_sync = GlobalSync("sync_bfs", self.state, self.ev_word, global_sync_offsets, self.scratch, self.debug_flag_term)

        global_sync.set_labels(self.global_init_ev_label, self.global_sync_ev_label, self.node_init_ev_label,
                               self.node_sync_ev_label, self.ud_accum_ev_label)

        global_sync.global_sync()

        global_sync.node_sync()

        global_sync.updown_accumulate()


@efaProgram
def GenerateSyncBfsEFA(efa: EFAProgram):
    

    bfs_generator = BFS(efa, vertex_struct_size = 64, ctr_base_offset = 0, max_thread_per_lane=220, debug_flag=False)

    bfs_generator.setup_cache(cache_base_offset=384, num_entries=2035, entry_size=32)

    bfs_generator.gen_pull_kvmsr()
    bfs_generator.gen_lm_init()
    bfs_generator.gen_global_sync()
    bfs_generator.gen_frontier_master()
    bfs_generator.gen_ud_frontier()
    bfs_generator.gen_lane_master()
    bfs_generator.gen_global_broadcast()
    bfs_generator.gen_update_dist()
    bfs_generator.gen_fetch_neighbor_remote()
    bfs_generator.gen_update_neighbor()

    return efa