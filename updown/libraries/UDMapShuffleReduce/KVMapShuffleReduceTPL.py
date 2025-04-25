from EFA_v2 import *
from math import log2, ceil
from Macro import *
from abc import abstractmethod, ABCMeta
from GlobalSync import *
from KeyValueSetTPL import *
from KVMSRMachineConfig import *
from ScratchpadCache import ScratchpadCache

class UDKeyValueMapShuffleReduceTemplate(metaclass=ABCMeta):
    """
    UpDown KeyValue MapShuffleReduce Library

    Usage:
    1. Import the module into UpDown source code file.
        import os, sys
        sys.path.append("<UPDOWN_INSTALL_DIR>/updown/libraries")
        from KVMapShuffleReduceTPL import UDKeyValueMapShuffleReduceTemplate
    2. Extend the UDKeyValueMapShuffleReduceTemplate class and implement kv_map() and kv_reduce().
       (Optionally, overwrite key mapping functions for e.g. customized work distribution.)
    3. Instantiate the child UDMapShuffleReduce class and wrap in customized GenerateEFA() function to generate UpDown assembly code.

    Example:

    class ExampleUDKeyValueMapShuffleReduce(UDMapShuffleReduceTemplate):

        def kv_map(self, tran, key, values, ret_ev_label):
            # user defined map code
            return ...

        def kv_reduce(self, tran, key, values, ret_ev_label):
            # user defined reduce code
            return ...

    Example UpDown KVMSR programs can be find in updown/apps/msr_examples.
    """
    FLAG    = 1

    def __init__(self, task_name: str, meta_data_offset:int, partition_parm: int = 1, lm_mode: int = 1, debug_flag: bool = False):
        '''
        Parameters
            task_name:      String identifier, unique for each UDKVMSR program.
            metadata_offset:  Offset of the metadata in the scratchpad memory. Starting from the offset, reserve 6 words for metadata.
            partition_parm: Parameter controlling the number of partitions assgined to each level of master.
                            (= paramter x the number of partitions in next level, base level = number of lane per updown), default is 1.
                            Should be the same as the parameter used to initialize the input key-value map.
                            Total number of partitions = num_workers * (partition_parm ** 3)
            lm_mode:        Local memory access mode, 0: X7 uses updown base, 1: X7 uses lane bank base, default is 1. (Deprecated, always use lane base address.)
                            Please use the same mode as the updown machine configuration.
            debug_flag:     Flag to enable debug print, default is False.
        '''

        self.task = task_name
        self.efa = EFA([])
        self.efa.code_level = 'machine'

        self.state = State()
        self.efa.add_initId(self.state.state_id)
        self.efa.add_state(self.state)

        self.part_pram = partition_parm
        
        self.map_ctr_offset         = meta_data_offset
        self.reduce_ctr_offset      = self.map_ctr_offset + WORD_SIZE
        self.ln_mstr_evw_offset     = self.reduce_ctr_offset + WORD_SIZE
        self.num_reduce_th_offset   = self.ln_mstr_evw_offset + WORD_SIZE
        self.max_red_th_offset      = self.num_reduce_th_offset + WORD_SIZE
        self.nwid_mask_offset       = self.max_red_th_offset + WORD_SIZE
        self.user_cont_offset       = self.nwid_mask_offset + WORD_SIZE

        self.lm_mode        = lm_mode
        self.enable_cache   = False
        self.enable_cleanup = False
        self.debug_flag     = debug_flag
        self.print_level    = 1 if self.debug_flag else 0
        self.send_temp_reg_flag = True
        
        self.max_map_th_per_lane    = 10
        self.max_reduce_th_per_lane = 10
        
        self.event_map = {}
        self.num_events = 0
        
        self.num_init_ops = 1
        
        print(f"Initialize MapShuffleReduce task {self.task} - bookkeeping_data_offset: {meta_data_offset}, partition_parm: {partition_parm}, debug_flag: {debug_flag}")

    def set_max_thread_per_lane(self, max_map_th_per_lane, max_reduce_th_per_lane):
        self.max_map_th_per_lane = max_map_th_per_lane
        self.max_reduce_th_per_lane = max_reduce_th_per_lane

    def set_input_kvset(self, kvset: KeyValueSetTemplate):
        '''
        Set up the input key-value map's metadata, the kvmap is stored in DRAM.
        Parameters
            kvset:  Instance of key-value set. Input to UDKVMSR.
        '''

        self.in_kvset = kvset
        self.in_kvset_offset = kvset.meta_data_offset
        self.in_kvset_meta_size = kvset.meta_data_size
        self.in_kvpair_size = kvset.pair_size
        self.log2_in_kvpair_size = ceil(log2(self.in_kvpair_size))
        print(f"Set up {kvset.name} kvmap - meta_data_offset: {kvset.meta_data_offset},  meta_data_size: {kvset.meta_data_size}, pair_size: {kvset.pair_size}, log2 pair_size: {self.log2_in_kvpair_size}")

    def set_intermediate_kvset(self, kvset: KeyValueSetTemplate):
        '''
        Set up the output key-value map's metadata, the kvmap is stored in DRAM.
        Parameters
            kvset:  Instance of key-value set. Output of UDKVMSR.
        '''

        self.inter_kvset = kvset
        self.inter_kvpair_size = kvset.pair_size
        self.log2_inter_kvpair_size = ceil(log2(self.inter_kvpair_size))
        
    def set_output_kvset(self, kvset: KeyValueSetTemplate):
        '''
        Set up the output key-value map's metadata, the kvmap is stored in DRAM.
        Parameters
            kvset:  Instance of key-value set. Output of UDKVMSR.
        '''

        self.out_kvset = kvset
        self.out_kvset_offset = kvset.meta_data_offset
        self.out_kvset_meta_size = kvset.meta_data_size
        self.out_kvpair_size = kvset.pair_size
        self.log2_out_kvpair_size = ceil(log2(self.out_kvpair_size))
        if (2 ** self.log2_out_kvpair_size) == self.out_kvpair_size:
            self.out_kvpair_pow2 = True
        else:
            self.out_kvpair_pow2 = False
            print("Warning: Output key value pair size is not a power of 2. This would impede the performance of UDKVMSR.")
            print(f"       Suggest to increase it to the next power of two, i.e., {2 ** self.log2_out_kvpair_size}")
        print(f"Set up {kvset.name} kvmap - meta_data_offset: {kvset.meta_data_offset},  meta_data_size: {kvset.meta_data_size}, pair_size: {kvset.pair_size}, log2 pair_size: {self.log2_out_kvpair_size}")

    def setup_cache(self, cache_offset, num_entries, entry_size, ival=0xffffffffffffffff, policy="wt"):
        '''
        If the reduce function involves read-modify-write to a DRAM location, initiates a per-lane-private software write through
        cache to merge updates to the same location (i.e. intermediate kvpair with the same key)
        Parameters
            cache_offset:   per lane local cache base (Bytes offset relative to the local bank, limited to the 64KB bank size)
            num_entries:    number of entries for each of lane-private cache segment
            entry_size:     the size of a cache entry in bytes
            ival:           default value for invalid cache entry
        '''

        self.cache = ScratchpadCache(self, cache_offset, num_entries, entry_size, ival, policy, self.debug_flag)
        self.enable_cache = True
        self.cache_offset = cache_offset
        self.cache_size = num_entries
        self.cache_entry_bsize = entry_size << LOG2_WORD_SIZE
        self.cache_entry_size = entry_size
        self.INACTIVE_MASK_SHIFT = 63
        self.INACTIVE_MASK = (1 << self.INACTIVE_MASK_SHIFT)
        self.cache_ival = ival | self.INACTIVE_MASK
        self.cache_policy = policy
        
    def setup_cleanup(self, dram_addr_offset: int, num_element_offset: int, lm_offset: int, element_size: int = 1):
        '''
        Set up the cleanup parameters for UDKVMSR cleanup process.
        Parameters
            addr_offset:        the scratchpad offset storing the DRAM address where data needs to be stored
            num_element_offset: the scratchpad offset storing the number of words 
            lm_offset:          the scratchpad offset storing the elements to be stored to DRAM
            element_size:       the number of words for each element to be stored to DRAM, between 1 and 8
        '''
        self.enable_cleanup = True
        self.cleanup_parameters = [dram_addr_offset, num_element_offset, lm_offset, element_size]

    def get_event_mapping(self, label):
        '''
        Given a string label, retrieve the corresponding event id.
        If the event label does not exist in the mapping, add it to the mapping and return the event id.
        Parameter
            label:          string label
        Ouput
            the corresponding event id (integer) mapped to the input label
        '''

        ev_label = f"{self.task}_{label}"
        if ev_label not in self.event_map:
            self.event_map[ev_label] = self.num_events
            self.num_events += 1
        return self.event_map[ev_label]
        
    def __gen_event_labels(self):
        
        self.init_udkvmsr_ev_label  = self.get_event_mapping("map_shuffle_reduce")
        self.kv_map_ev_label        = self.get_event_mapping("kv_map")
        self.kv_map_emit_ev_label   = self.get_event_mapping("kv_map_emit")
        self.kv_map_ret_ev_label    = self.get_event_mapping("kv_map_return")
        self.kv_reduce_ev_label     = self.get_event_mapping("kv_reduce")
        self.kv_reduce_emit_ev_label    = self.get_event_mapping("kv_reduce_emit")
        self.kv_reduce_ret_ev_label     = self.get_event_mapping("kv_reduce_return")

        self.node_sp_init_ev_label  = self.get_event_mapping("init_sp_node")
        self.ud_sp_init_ev_label    = self.get_event_mapping("init_sp_ud")
        self.lane_sp_init_ev_label  = self.get_event_mapping("init_sp_lane")
        self.ud_sp_init_fin_ev_label    = self.get_event_mapping("init_sp_ud_fin")
        self.node_sp_init_fin_ev_label  = self.get_event_mapping("init_sp_node_fin")
        
        self.glb_mstr_init_ev_label = self.get_event_mapping("init_global_master")
        self.glb_mstr_loop_ev_label = self.get_event_mapping("global_master")

        self.nd_mstr_init_ev_label  = self.get_event_mapping("init_master_node")
        self.nd_mstr_loop_ev_label  = self.get_event_mapping("node_master")
        self.nd_mstr_term_ev_label  = self.get_event_mapping("termiante_node_master")

        self.ud_mstr_init_ev_label  = self.get_event_mapping("init_updown_master")
        self.ud_mstr_loop_ev_label  = self.get_event_mapping("updown_master")
        self.ud_mstr_term_ev_label  = self.get_event_mapping("terminate_updown_master")

        self.ln_mstr_init_ev_label  = self.get_event_mapping("init_lane_master")
        self.ln_mstr_loop_ev_label  = self.get_event_mapping("lane_master")
        self.ln_mstr_term_ev_label  = self.get_event_mapping("terminate_lane_master")

        self.ln_mstr_rd_part_ev_label   = self.get_event_mapping("lane_master_read_partition")
        self.ln_map_th_init_ev_label    = self.get_event_mapping("init_map_thread")
        self.ln_map_th_term_ev_label    = self.get_event_mapping("terminate_map_thread")
        
        self.kv_reduce_init_ev_label    = self.get_event_mapping("init_reduce_thread")

        self.glb_sync_init_ev_label = self.get_event_mapping("init_global_snyc")
        self.node_init_ev_label     = self.get_event_mapping("init_node_sync")
        self.ud_accum_ev_label      = self.get_event_mapping("ud_accumulate")
        self.global_sync_ev_label   = self.get_event_mapping("global_sync")
        self.node_sync_ev_label     = self.get_event_mapping("node_sync")
        
        self.glb_cleanup_ev_label       = self.get_event_mapping("cleanup_global")
        self.node_cleanup_ev_label      = self.get_event_mapping("cleanup_node")
        self.ud_cleanup_ev_label        = self.get_event_mapping("cleanup_ud")
        self.lane_cleanup_ev_label      = self.get_event_mapping("cleanup_lane")
        self.ud_cleanup_fin_ev_label    = self.get_event_mapping("cleanup_ud_fin")
        self.node_cleanup_fin_ev_label  = self.get_event_mapping("cleanup_node_fin")
        self.glb_cleanup_fin_ev_label   = self.get_event_mapping("cleanup_global_fin")
        self.cleanup_store_ack_ev_label = self.get_event_mapping("cleanup_store_ack")
        
        print(f"Event_mapping: {self.event_map}")

    def generate_udkvmsr_task(self):
        self.__gen_event_labels()
        self.__gen_init_scratchpad()
        self.__gen_masters()
        self.__gen_global_sync()
        self.__gen_map_thread()
        self.__gen_reduce_thread()
        if self.enable_cleanup: self.__gen_cleanup()

    def __gen_masters(self):
        self.__gen_global_master()
        self.__gen_node_master()
        self.__gen_updown_master()
        self.__gen_lane_master()

    def __init_lane_scratchpad(self, tran: Transition) -> Transition:

        lm_base     = "UDPR_4"
        tran.writeAction("mov_imm2reg UDPR_0 0")
        # Initialize termination counters (private per worker lane)
        tran.writeAction(f"addi X7 {lm_base} 0")
        tran.writeAction(f"movir {self.scratch[0]} {self.max_reduce_th_per_lane}")
        tran.writeAction(f"move UDPR_0 {self.map_ctr_offset}({lm_base}) 0 8")
        tran.writeAction(f"move UDPR_0 {self.reduce_ctr_offset}({lm_base}) 0 8")
        tran.writeAction(f"move {self.scratch[0]} {self.max_red_th_offset}({lm_base}) 0 8")
        tran.writeAction(f"subi X8 {self.scratch[0]} 1")
        tran.writeAction(f"move {self.scratch[0]} {self.nwid_mask_offset}({lm_base}) 0 8")
        for i in range(self.in_kvset_meta_size):
            tran.writeAction(f"move {f'OB_{i + self.num_init_ops}'} {self.in_kvset_offset + i * WORD_SIZE}({lm_base}) 0 8")
        for i in range(self.out_kvset_meta_size):
            tran.writeAction(f"move {f'OB_{self.in_kvset_meta_size + i + self.num_init_ops}'} \
                {self.out_kvset_offset + i * WORD_SIZE}({lm_base}) 0 8")

        # Initialize the per lane private cache in scratchpad to merge Read-Modify-Write updates and ensure TSO
        if self.enable_cache:
            cache_init_loop_label = "init_cache_loop"
            ival        = "UDPR_0"
            cache_base  = "UDPR_1"
            init_ctr    = "UDPR_2"
            num_entries = "UDPR_3"
            tran.writeAction(f"mov_imm2reg {ival} {(1<<21)-1}")
            tran.writeAction(f"sli {ival} {ival} {self.INACTIVE_MASK_SHIFT-20}")
            tran.writeAction(f"movir {num_entries} {self.cache_size}")
            # print(f"Initialize lane {n}'s cache in scratchpad memory")
            tran.writeAction(f"movir {cache_base} {self.cache_offset}")
            tran.writeAction(f"add {'X7'} {cache_base} {cache_base}")
            if self.debug_flag and self.print_level > 3:
                tran.writeAction(f"print '[DEBUG][NWID %ld] Initialize scratchpad cache base addr = %ld(0x%lx) initial value = %ld' {'X0'} {cache_base} {cache_base} {ival}")
            tran.writeAction(f"mov_imm2reg {init_ctr} 0")
            tran.writeAction(f"{cache_init_loop_label}: movwrl {ival} {cache_base}({init_ctr},1,{int(log2(self.cache_entry_size))})")
            tran.writeAction(f"blt {init_ctr} {num_entries} {cache_init_loop_label}")
        return tran

    def __gen_init_scratchpad(self):
        '''
        Generate the initialization code for the scratchpad memory.
        '''

        self.scratch = ["UDPR_12", "UDPR_13"]

        self.part_array_ptr = "UDPR_0"
        self.num_child  = "UDPR_9"
        num_finished    = "UDPR_10"
        self.num_lane_reg   = "UDPR_11"
        self.ev_word    = "UDPR_14"
        self.saved_cont = "UDPR_15"
        
        self.multiple_label = "modular_eq_zero"

        '''
        Event:      UDKVMSR entry point, start initializing scratchpad
        Operands:   X8: partitions array
                    X9: number of lanes
                    X10 ~ Xn: input and output key-value set metadata
        '''
        glb_sp_init_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.init_udkvmsr_ev_label)
        if self.debug_flag:
            glb_sp_init_tran.writeAction(f"print ' '")
            glb_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_global_sp_init> ev_word=%ld' {'X0'} {'EQT'}")
            glb_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: part_array = %ld(0x%lx)' {'X0'} {'X8'} {'X8'}")
            glb_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: num_lanes  = %ld(0x%lx)' {'X0'} {'X9'} {'X9'}")
            glb_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: in_kvset   = %ld(0x%lx)' {'X0'} {'X10'} {'X10'}")
            glb_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: out_kvset  = %ld(0x%lx)' {'X0'} {'X11'} {'X11'}")
        glb_sp_init_tran.writeAction(f"addi X8 {self.part_array_ptr} 0")    # save the base of global partition array
        glb_sp_init_tran.writeAction(f"addi X9 {self.num_lane_reg} 0")      # save the number of lanes
        glb_sp_init_tran.writeAction(f"addi X1 {self.saved_cont} 0")        # save the continuation event word
        glb_sp_init_tran.writeAction(f"addi {'X7'} {self.scratch[0]} 0")
        glb_sp_init_tran.writeAction(f"move {self.saved_cont} {self.user_cont_offset}({self.scratch[0]}) 0 8")
        get_num_node(glb_sp_init_tran, self.num_lane_reg, self.num_child, self.multiple_label, self.scratch[0])
        set_ev_label(glb_sp_init_tran, self.ev_word, self.node_sp_init_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag:
            glb_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Broadcast to %ld nodes' {'X0'} {self.num_child}")
        glb_sp_init_tran = broadcast(glb_sp_init_tran, self.ev_word, self.num_child, self.glb_mstr_init_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"X9 {self.in_kvset_meta_size + self.out_kvset_meta_size + self.num_init_ops}", self.scratch, 'ops', self.send_temp_reg_flag)
        glb_sp_init_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        glb_sp_init_tran.writeAction("yield")

        '''
        Event:      Initialize node scratchpad
        Operands:   X8: number of lanes
                    X9: input key-value set pointer
                    X10: output key-value set pointer
                    X11 ~ Xn: input and output key-value set metadata
        '''
        node_sp_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.node_sp_init_ev_label)
        if self.debug_flag and self.print_level > 3:
            node_sp_init_tran.writeAction(f"print ' '")
            node_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_node_sp_init> ev_word=%ld' {'X0'} {'EQT'}")
        node_sp_init_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        get_num_ud_per_node(node_sp_init_tran, 'X8', self.num_child, self.multiple_label, self.scratch[0])
        set_ev_label(node_sp_init_tran, self.ev_word, self.ud_sp_init_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag:
            node_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Broadcast to %ld updowns' {'X0'} {self.num_child}")
        node_sp_init_tran = broadcast(node_sp_init_tran, self.ev_word, self.num_child, self.node_sp_init_fin_ev_label, \
            (LOG2_LANE_PER_UD), f"X8 {self.in_kvset_meta_size + self.out_kvset_meta_size + self.num_init_ops}", self.scratch, 'ops', self.send_temp_reg_flag)
        node_sp_init_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        node_sp_init_tran.writeAction("yield")

        '''
        Event:      Initialize updown scratchpad
        Operands:   X8: number of lanes
                    X9: input key-value set pointer
                    X10: output key-value set pointer
                    X11 ~ Xn: input and output key-value set metadata
        '''
        ud_sp_init_tran     = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_sp_init_ev_label)
        if self.debug_flag and self.print_level > 3:
            ud_sp_init_tran.writeAction(f"print ' '")
            ud_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_updown_sp_init> ev_word=%ld' {'X0'} {'EQT'}")
        ud_sp_init_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        get_num_lane_per_ud(ud_sp_init_tran, 'X8', self.num_child, self.multiple_label)
        set_ev_label(ud_sp_init_tran, self.ev_word, self.lane_sp_init_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag:
            ud_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Broadcast to %ld lanes' {'X0'} {self.num_child}")
        ud_sp_init_tran = broadcast(ud_sp_init_tran, self.ev_word, self.num_child, self.ud_sp_init_fin_ev_label, 0, \
            f"X8 {self.in_kvset_meta_size + self.out_kvset_meta_size + self.num_init_ops}", self.scratch, 'ops', self.send_temp_reg_flag)
        ud_sp_init_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        ud_sp_init_tran.writeAction("yield")

        '''
        Event:      Initialize lane scratchpad
        Operands:   X8: number of workers
        Operands:   X8 ~ Xn: input and output key-value set metadata
        '''
        lane_sp_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_sp_init_ev_label)
        if self.debug_flag and self.print_level > 3:
            lane_sp_init_tran.writeAction(f"print ' '")
            lane_sp_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_lane_sp_init> ev_word=%ld' {'X0'} {'EQT'}")
        lane_sp_init_tran = self.__init_lane_scratchpad(lane_sp_init_tran)
        lane_sp_init_tran.writeAction(format_pseudo(f"sendr_reply X0 X16", self.scratch[0], self.send_temp_reg_flag))
        lane_sp_init_tran.writeAction("yield_terminate")

        continue_label = "continue"
        self.init_fin_label = "global_init_finish"
        '''
        Event:      Updown lane scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        ud_sp_init_fin_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_sp_init_fin_ev_label)
        if self.debug_flag and self.print_level > 3:
            ud_sp_init_fin_tran.writeAction(f"print ' '")
            ud_sp_init_fin_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_updown_sp_init_fin> ev_word=%ld num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        ud_sp_init_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        ud_sp_init_fin_tran.writeAction(f"blt {num_finished} {self.num_child} {continue_label}")
        ud_sp_init_fin_tran.writeAction(format_pseudo(f"sendr_reply X0 X16", self.scratch[0], self.send_temp_reg_flag))
        ud_sp_init_fin_tran.writeAction("yield_terminate")
        ud_sp_init_fin_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Node updown scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        node_sp_init_fin_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.node_sp_init_fin_ev_label)
        if self.debug_flag and self.print_level > 3:
            node_sp_init_fin_tran.writeAction(f"print ' '")
            node_sp_init_fin_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_node_sp_init_fin> ev_word=%ld num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        node_sp_init_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        node_sp_init_fin_tran.writeAction(f"blt {num_finished} {self.num_child} {continue_label}")
        node_sp_init_fin_tran.writeAction(format_pseudo("sendr_reply X0 X16", self.scratch[0], self.send_temp_reg_flag))
        node_sp_init_fin_tran.writeAction("yield_terminate")
        node_sp_init_fin_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Node scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        self.glb_mstr_init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_init_ev_label)
        if self.debug_flag and self.print_level > 3:
            self.glb_mstr_init_tran.writeAction(f"print ' '")
            self.glb_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_global_master_init> ev_word=%ld num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        self.glb_mstr_init_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        self.glb_mstr_init_tran.writeAction(f"blt {num_finished} {self.num_child} {continue_label}")
        self.glb_mstr_init_tran.writeAction(f"jmp {self.init_fin_label}")
        self.glb_mstr_init_tran.writeAction(f"{continue_label}: yield")

        return
        
    def __gen_cleanup(self):
        
        glb_cleanup_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_cleanup_ev_label)

        node_cleanup_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.node_cleanup_ev_label)

        ud_cleanup_tran     = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_cleanup_ev_label)

        lane_cleanup_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.lane_cleanup_ev_label)

        ud_cleanup_fin_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_cleanup_fin_ev_label)

        node_cleanup_fin_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.node_cleanup_fin_ev_label)

        glb_cleanup_fin_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_cleanup_fin_ev_label)
        
        all_reduce_val  = "UDPR_0"
        self.num_child  = "UDPR_9"
        num_finished    = "UDPR_10"
        self.num_lane_reg   = "UDPR_11"
        
        '''
        Event:      UDKVMSR exit point, clean up scratchpad
        Operands:   
        '''
        if self.debug_flag:
            glb_cleanup_tran.writeAction(f"print ' '")
            glb_cleanup_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_global_cleanup> ev_word=%ld' {'X0'} {'EQT'}")
        glb_cleanup_tran.writeAction(f"move {self.nwid_mask_offset}({'X7'}) {self.num_lane_reg} 0 8")
        glb_cleanup_tran.writeAction(f"addi {self.num_lane_reg} {self.num_lane_reg} 1")
        glb_cleanup_tran.writeAction(f"addi X8 {all_reduce_val} 0")
        get_num_node(glb_cleanup_tran, self.num_lane_reg, self.num_child, self.multiple_label, self.scratch[0])
        set_ev_label(glb_cleanup_tran, self.ev_word, self.node_cleanup_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag:
            glb_cleanup_tran.writeAction(f"print '[DEBUG][NWID %ld] Broadcast to %ld nodes' {'X0'} {self.num_child}")
        glb_cleanup_tran = broadcast(glb_cleanup_tran, self.ev_word, self.num_child, self.glb_cleanup_fin_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{self.num_lane_reg} {self.num_lane_reg}", self.scratch, 'r', self.send_temp_reg_flag)
        glb_cleanup_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        glb_cleanup_tran.writeAction("yield")

        '''
        Event:      clean up node
        Operands:   X8: number of lanes
                    X9: input key-value set pointer
                    X10: output key-value set pointer
                    X11 ~ Xn: input and output key-value set metadata
        '''
        if self.debug_flag:
            node_cleanup_tran.writeAction(f"print ' '")
            node_cleanup_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_node_cleanup> ev_word=%ld' {'X0'} {'EQT'}")
        node_cleanup_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        get_num_ud_per_node(node_cleanup_tran, 'X8', self.num_child, self.multiple_label, self.scratch[0])
        set_ev_label(node_cleanup_tran, self.ev_word, self.ud_cleanup_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag:
            node_cleanup_tran.writeAction(f"print '[DEBUG][NWID %ld] Broadcast to %ld updowns' {'X0'} {self.num_child}")
        node_cleanup_tran = broadcast(node_cleanup_tran, self.ev_word, self.num_child, self.node_cleanup_fin_ev_label, \
            (LOG2_LANE_PER_UD), f"X8 2", self.scratch, 'ops', self.send_temp_reg_flag)
        node_cleanup_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        node_cleanup_tran.writeAction("yield")

        '''
        Event:      Initialize updown scratchpad
        Operands:   X8: number of lanes
                    X9: input key-value set pointer
                    X10: output key-value set pointer
                    X11 ~ Xn: input and output key-value set metadata
        '''
        if self.debug_flag:
            ud_cleanup_tran.writeAction(f"print ' '")
            ud_cleanup_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_updown_cleanup> ev_word=%ld' {'X0'} {'EQT'}")
        ud_cleanup_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        get_num_lane_per_ud(ud_cleanup_tran, 'X8', self.num_child, self.multiple_label)
        ud_cleanup_tran = set_ev_label(ud_cleanup_tran, self.ev_word, self.lane_cleanup_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag:
            ud_cleanup_tran.writeAction(f"print '[DEBUG][NWID %ld] Broadcast to %ld lanes' {'X0'} {self.num_child}")
        ud_cleanup_tran = broadcast(ud_cleanup_tran, self.ev_word, self.num_child, self.ud_cleanup_fin_ev_label, 0, \
            f"X8 2", self.scratch, 'ops', self.send_temp_reg_flag)
        ud_cleanup_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        ud_cleanup_tran.writeAction("yield")

        '''
        Event:      Initialize lane scratchpad
        Operands:   X8: number of workers
        Operands:   X8 ~ Xn: input and output key-value set metadata
        '''
        if self.debug_flag:
            lane_cleanup_tran.writeAction(f"print ' '")
            lane_cleanup_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_lane_cleanup> ev_word=%ld' {'X0'} {'EQT'}")
        lane_cleanup_tran = self.msr_cleanup(lane_cleanup_tran)
        lane_cleanup_tran.writeAction(format_pseudo(f"sendr_reply X0 X16", self.scratch[0], self.send_temp_reg_flag))
        lane_cleanup_tran.writeAction("yield_terminate")

        continue_label  = "continue"
        cleanup_fin_label = "global_cleanup_finish"
        '''
        Event:      Updown lane scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        if self.debug_flag:
            ud_cleanup_fin_tran.writeAction(f"print ' '")
            ud_cleanup_fin_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_updown_cleanup_fin> ev_word=%ld num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        ud_cleanup_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        ud_cleanup_fin_tran.writeAction(f"blt {num_finished} {self.num_child} {continue_label}")
        ud_cleanup_fin_tran.writeAction(format_pseudo(f"sendr_reply X0 X16", self.scratch[0], self.send_temp_reg_flag))
        ud_cleanup_fin_tran.writeAction("yield_terminate")
        ud_cleanup_fin_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Node updown scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        if self.debug_flag:
            node_cleanup_fin_tran.writeAction(f"print ' '")
            node_cleanup_fin_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_node_cleanup_fin> ev_word=%ld num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        node_cleanup_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        node_cleanup_fin_tran.writeAction(f"blt {num_finished} {self.num_child} {continue_label}")
        node_cleanup_fin_tran.writeAction(format_pseudo("sendr_reply X0 X16", self.scratch[0], self.send_temp_reg_flag))
        node_cleanup_fin_tran.writeAction("yield_terminate")
        node_cleanup_fin_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Node scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        if self.debug_flag:
            glb_cleanup_fin_tran.writeAction(f"print ' '")
            glb_cleanup_fin_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_global_master_init> ev_word=%ld num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        glb_cleanup_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        glb_cleanup_fin_tran.writeAction(f"beq {num_finished} {self.num_child} {cleanup_fin_label}")
        glb_cleanup_fin_tran.writeAction(f"yield")
        glb_cleanup_fin_tran.writeAction(f"{cleanup_fin_label}: move {self.user_cont_offset}(X7) {self.saved_cont} 0 8")
        glb_cleanup_fin_tran.writeAction(f"sendr_wcont {self.saved_cont} EQT {all_reduce_val} {all_reduce_val}")
        if self.debug_flag:
            glb_cleanup_fin_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish cleanup, return to user continuation %ld. Number of reduce tasks = %ld' {'X0'} {self.saved_cont} {all_reduce_val}")
        glb_cleanup_fin_tran.writeAction(f"yieldt")
        
        return

    def __gen_global_master(self):

        self.num_part_issued    = "UDPR_1"
        self.part_array_stride  = "UDPR_2"
        self.num_map_gen    = "UDPR_3"
        self.part_stride    = "UDPR_4"
        num_node_active = "UDPR_5"
        ndid_stride     = "UDPR_6"
        nd_mstr_nwid    = "UDPR_7"
        num_part_reg    = "UDPR_8"

        glb_mstr_loop_label = "glb_master_loop"
        glb_mstr_fin_fetch_label = "global_master_fin_fetch"
        glb_mstr_init_sync_label = "global_master_init_sync"
        glb_mstr_full_label = "global_master_full_child"

        self.glb_mstr_init_tran.writeAction(f"{self.init_fin_label}: mov_imm2reg {num_node_active} 0")
        self.glb_mstr_init_tran.writeAction(f"muli {self.num_lane_reg} {num_part_reg} {self.part_pram ** 3}")
        if self.debug_flag or self.print_level >= 1:
            self.glb_mstr_init_tran.writeAction(f"print ' '")
            self.glb_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish initialize the scratchpad. Number of partitions = %ld' {'X0'} {num_part_reg}")
        self.glb_mstr_init_tran.writeAction(f"mov_imm2reg {ndid_stride} {UD_PER_NODE * LANE_PER_UD}")
        self.glb_mstr_init_tran.writeAction(f"bge {self.num_lane_reg} {ndid_stride} {glb_mstr_full_label}")
        self.glb_mstr_init_tran.writeAction(f"addi {self.num_lane_reg} {ndid_stride} 0")    # Adjust nwid stride if not all the lanes in a node is used.
        self.glb_mstr_init_tran.writeAction(f"{glb_mstr_full_label}: muli {ndid_stride} {self.part_stride} {self.part_pram ** 2}")
        self.glb_mstr_init_tran.writeAction(f"lshift {self.part_stride} {self.part_array_stride} {LOG2_WORD_SIZE}")
        self.glb_mstr_init_tran.writeAction(f"mov_reg2reg X0 {nd_mstr_nwid}")
        self.glb_mstr_init_tran = set_ev_label(self.glb_mstr_init_tran, self.ev_word,
            self.nd_mstr_init_ev_label, new_thread=True)
        # Create the node master on each node and send out a partition of input kv pairs
        self.glb_mstr_init_tran.writeAction(f"{glb_mstr_loop_label}: ev_update_reg_2 \
            {self.ev_word} {self.ev_word} {nd_mstr_nwid} {nd_mstr_nwid} 8")
        self.glb_mstr_init_tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {self.glb_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg}", self.scratch[0], self.send_temp_reg_flag))
        self.glb_mstr_init_tran.writeAction(f"add {ndid_stride} {nd_mstr_nwid} {nd_mstr_nwid}")
        self.glb_mstr_init_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        self.glb_mstr_init_tran.writeAction(f"addi {num_node_active} {num_node_active} 1")
        self.glb_mstr_init_tran.writeAction(f"blt {num_node_active} {self.num_child} {glb_mstr_loop_label}")
        self.glb_mstr_init_tran.writeAction(f"lshift {num_node_active} {self.num_part_issued} {LOG2_LANE_PER_UD + LOG2_UD_PER_NODE}")
        self.glb_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")    # total number of kv_pair generated by mapper
        if self.debug_flag:
            self.glb_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] num_partitions = %ld, num_part_issued = %ld' {'X0'} {num_part_reg} {self.num_part_issued}")
        self.glb_mstr_init_tran.writeAction("yield")

        '''
        Event:      Global master loop
        Operands:   X8: Number of map tasks generated
                    X9: Return node master thread loop event word
        '''
        glb_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_mstr_loop_ev_label)
        if self.debug_flag:
            glb_mstr_loop_tran.writeAction(f"print ' '")
            glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_global_master_loop> ev_word=%ld income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        glb_mstr_loop_tran.writeAction(f"add X8 {self.num_map_gen} {self.num_map_gen}")
        glb_mstr_loop_tran.writeAction(f"bge {self.num_part_issued} {num_part_reg} {glb_mstr_fin_fetch_label}")

        # Send next non-assigned partitions to the node
        glb_mstr_loop_tran.writeAction(format_pseudo(f"sendr3_wret X1 {self.glb_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg}", self.scratch[0], self.send_temp_reg_flag))
        glb_mstr_loop_tran.writeAction(f"add {self.part_stride} {self.num_part_issued} {self.num_part_issued}")
        glb_mstr_loop_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        if self.debug_flag:
            glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] num_partitions = %ld, num_part_issued = %ld' {'X0'} {num_part_reg} {self.num_part_issued}")
            glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] num_map_generated = %ld' {'X0'} {self.num_map_gen}")
        glb_mstr_loop_tran.writeAction(f"yield")

        # Finish issuing all the partitions of input kv set, terminate the node master thread
        glb_mstr_loop_tran.writeAction(f"{glb_mstr_fin_fetch_label}: subi {num_node_active} {num_node_active} 1")
        glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.ev_word, self.nd_mstr_term_ev_label, "X1")
        glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {ndid_stride}")
        if self.debug_flag:
            glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] num_map_generated = %ld' {'X0'} {self.num_map_gen}")
        glb_mstr_loop_tran.writeAction(f"beqi {num_node_active} 0 {glb_mstr_init_sync_label}")
        glb_mstr_loop_tran.writeAction(f"yield")

        # All the map master threads are termianted, call the global synchronization event
        glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.ev_word, self.glb_sync_init_ev_label, src_ev="X2", new_thread=True, label=glb_mstr_init_sync_label)
        if self.enable_cleanup:
            glb_mstr_loop_tran = set_ev_label(glb_mstr_loop_tran, self.scratch[0], self.glb_cleanup_ev_label, src_ev=self.ev_word)
            glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.scratch[0]} {self.num_lane_reg} {self.num_map_gen}")
        else:
            glb_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} {self.saved_cont} {self.num_lane_reg} {self.num_map_gen}")
        if self.debug_flag or self.print_level >= 1:
            glb_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Finish dispatch all the map tasks. Start the global synchronization, ev_word = %lu' {'X0'} {self.ev_word}")
        glb_mstr_loop_tran.writeAction(f"yield_terminate")

        return

    def __gen_node_master(self):

        num_ud_active   = "UDPR_5"
        udid_stride     = "UDPR_6"
        ud_mstr_nwid    = "UDPR_7"
        part_array_end  = "UDPR_8"

        nd_mstr_loop_label  = "node_master_loop"
        nd_mstr_fin_fetch_label = "node_master_fin_fetch"
        nd_mstr_fin_part_label  = "node_master_fin_partition"
        nd_mstr_full_label  = "node_master_full_child"

        '''
        Event:      Initialize node master
        Operands:   X8: Pointer to the base address of the initial partition
                    X9: Number of partitions assigned to this node x WORD_SIZE (partition stride)
                    X10: Number of lanes in total
        '''
        nd_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_mstr_init_ev_label)
        if self.debug_flag:
            nd_mstr_init_tran.writeAction(f"print ' '")
            nd_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <node_master_init> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")

            nd_mstr_init_tran.writeAction(f"rshift {'X9'} {self.scratch[0]} {LOG2_WORD_SIZE}")
            nd_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: partition_base = %ld(0x%lx) num_part_assigned = %ld num_lanes = %ld' \
                {'X0'} {'X8'} {'X8'} {self.scratch[0]} {'X10'}")
        nd_mstr_init_tran.writeAction(f"mov_reg2reg X1 {self.saved_cont}")
        nd_mstr_init_tran.writeAction(f"mov_reg2reg X8 {self.part_array_ptr}")
        nd_mstr_init_tran.writeAction(f"mov_reg2reg X10 {self.num_lane_reg}")
        get_num_ud_per_node(nd_mstr_init_tran, self.num_lane_reg, self.num_child, self.multiple_label, self.scratch[0])
        nd_mstr_init_tran.writeAction(f"{self.multiple_label}: add X9 {self.part_array_ptr} {part_array_end}")
        nd_mstr_init_tran.writeAction(f"mov_imm2reg {num_ud_active} 0")
        nd_mstr_init_tran.writeAction(f"mov_imm2reg {udid_stride} {LANE_PER_UD}")
        nd_mstr_init_tran.writeAction(f"bge {self.num_lane_reg} {udid_stride} {nd_mstr_full_label}")
        nd_mstr_init_tran.writeAction(f"addi {self.num_lane_reg} {udid_stride} 0")  # Adjust nwid stride if not all the lanes in a updown is used.
        nd_mstr_init_tran.writeAction(f"{nd_mstr_full_label}: muli {udid_stride} {self.part_stride} {self.part_pram}")
        nd_mstr_init_tran.writeAction(f"lshift {self.part_stride} {self.part_array_stride} {LOG2_WORD_SIZE}")
        if self.debug_flag:
            nd_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] udid_stride = %ld part_stride = %ld' {'X0'} {udid_stride} {self.part_stride}")
        nd_mstr_init_tran.writeAction(f"mov_reg2reg X0 {ud_mstr_nwid}")
        nd_mstr_init_tran = set_ev_label(nd_mstr_init_tran, self.ev_word, self.ud_mstr_init_ev_label, new_thread=True)

        # Create the node master on each node and send out a partition of input kv pairs
        nd_mstr_init_tran.writeAction(f"{nd_mstr_loop_label}: ev_update_reg_2 \
            {self.ev_word} {self.ev_word} {ud_mstr_nwid} {ud_mstr_nwid} 8")
        nd_mstr_init_tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {self.nd_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag or self.print_level >= 2:
            nd_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Node master sends part to ud %ld master part_array_ptr = %ld(0x%lx)' \
                {'X0'} {ud_mstr_nwid} {self.part_array_ptr} {self.part_array_ptr}")
        nd_mstr_init_tran.writeAction(f"add {udid_stride} {ud_mstr_nwid} {ud_mstr_nwid}")
        nd_mstr_init_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        nd_mstr_init_tran.writeAction(f"addi {num_ud_active} {num_ud_active} 1")
        nd_mstr_init_tran.writeAction(f"blt {num_ud_active} {self.num_child} {nd_mstr_loop_label}")
        nd_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        nd_mstr_init_tran.writeAction("yield")

        '''
        Event:      Node master loop
        Operands:   X8: Number of map tasks generated
                    X9: Return updown master thread loop event word
        '''

        nd_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_mstr_loop_ev_label)
        if self.debug_flag:
            nd_mstr_loop_tran.writeAction(f"print ' '")
            nd_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <node_master_loop> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        if self.debug_flag or self.print_level >= 1:
            nd_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32 + 6}")
            nd_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown %ld master returns. Number of map generated = %ld' {'X0'}  {self.scratch[0]} {'X8'}")
        nd_mstr_loop_tran.writeAction(f"add X8 {self.num_map_gen} {self.num_map_gen}")
        nd_mstr_loop_tran.writeAction(f"bge {self.part_array_ptr} {part_array_end} {nd_mstr_fin_fetch_label}")
        # Send next non-assigned partition to the updown
        nd_mstr_loop_tran.writeAction(format_pseudo(f"sendr3_wret X1 {self.nd_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {self.num_lane_reg}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            nd_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            nd_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            nd_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            nd_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Node master sends part to ud %ld master tid = %ld ev_word=%ld part_array_ptr = %ld(0x%lx) node_part_end = %ld(0x%lx)' \
                {'X0'} {self.scratch[0]} {self.scratch[1]} {'X1'} {self.part_array_ptr} {self.part_array_ptr} {part_array_end} {part_array_end}")
            nd_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Node master num_map_generated = %ld' {'X0'} {self.num_map_gen}")
        nd_mstr_loop_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        nd_mstr_loop_tran.writeAction(f"yield")
        # Finish issuing all the partitions of input kv set, terminate all the updown master threads
        nd_mstr_loop_tran.writeAction(f"{nd_mstr_fin_fetch_label}: subi {num_ud_active} {num_ud_active} 1")
        nd_mstr_loop_tran = set_ev_label(nd_mstr_loop_tran, self.ev_word, self.ud_mstr_term_ev_label, "X1")
        nd_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {udid_stride}")
        nd_mstr_loop_tran.writeAction(f"beqi {num_ud_active} 0 {nd_mstr_fin_part_label}")
        nd_mstr_loop_tran.writeAction(f"yield")
        nd_mstr_loop_tran.writeAction(format_pseudo(f"{nd_mstr_fin_part_label}: sendr_wret {self.saved_cont} {self.nd_mstr_init_ev_label} \
            {self.num_map_gen} {self.num_map_gen}", self.scratch[0], self.send_temp_reg_flag))
        nd_mstr_loop_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        nd_mstr_loop_tran.writeAction(f"yield")


        nd_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_mstr_term_ev_label)
        if self.debug_flag:
            nd_mstr_term_tran.writeAction(f"print ' '")
            nd_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <node_master_term> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        nd_mstr_term_tran.writeAction(f"yield_terminate")

        return


    def __gen_updown_master(self):


        num_ln_active       = "UDPR_5"
        num_part_assigned   = "UDPR_6"
        ln_mstr_nwid        = "UDPR_7"
        part_array_end      = "UDPR_8"

        ud_mstr_loop_label = "updown_master_loop"
        ud_mstr_fin_fetch_label = "updown_master_fin_fetch"
        ud_mstr_fin_part_label = "updown_master_fin_partition"

        '''
        Event:      Initialize updown master
        Operands:   X8: Pointer to the base address of the initial partition
                    X9: Number of partitions assigned to this updown x WORD_SIZE
                    X10: Number of lanes in total
        '''
        ud_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_mstr_init_ev_label)
        if self.debug_flag:
            ud_mstr_init_tran.writeAction("print ' '")
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <updown_master_init> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
            ud_mstr_init_tran.writeAction(f"rshift {'X9'} {self.scratch[0]} {LOG2_WORD_SIZE}")
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: partition_base = %ld(0x%lx) num_part = %ld part_stride = %ld num_lanes = %ld' \
                {'X0'} {'X8'} {'X8'} {self.scratch[0]} {'X9'} {'X10'}")
        ud_mstr_init_tran.writeAction(f"mov_reg2reg X1 {self.saved_cont}")
        ud_mstr_init_tran.writeAction(f"mov_reg2reg X8 {self.part_array_ptr}")
        ud_mstr_init_tran.writeAction(f"mov_reg2reg X10 {self.num_lane_reg}")
        get_num_lane_per_ud(ud_mstr_init_tran, self.num_lane_reg, self.num_child, self.multiple_label)
        ud_mstr_init_tran.writeAction(f"{self.multiple_label}: add X9 {self.part_array_ptr} {part_array_end}")
        ud_mstr_init_tran.writeAction(f"mov_imm2reg {num_ln_active} {0}")
        ud_mstr_init_tran.writeAction(f"mov_imm2reg {self.part_array_stride} {WORD_SIZE}")
        ud_mstr_init_tran.writeAction(f"mov_reg2reg X0 {ln_mstr_nwid}")
        ud_mstr_init_tran = set_ev_label(ud_mstr_init_tran, self.ev_word, self.ln_mstr_init_ev_label, new_thread=True)
        # Create the node master on each node and send out a partition of input kv pairs
        ud_mstr_init_tran.writeAction(f"{ud_mstr_loop_label}: ev_update_reg_2 \
            {self.ev_word} {self.ev_word} {ln_mstr_nwid} {ln_mstr_nwid} 8")
        ud_mstr_init_tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {self.ud_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {num_ln_active}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ud_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Send partition to lane %ld master part_array_ptr = %ld(0x%lx) num_part_assigned = %ld' \
                {'X0'} {ln_mstr_nwid} {self.part_array_ptr} {self.part_array_ptr} {num_ln_active}")
        ud_mstr_init_tran.writeAction(f"addi {ln_mstr_nwid} {ln_mstr_nwid} {1}")
        ud_mstr_init_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        ud_mstr_init_tran.writeAction(f"addi {num_ln_active} {num_ln_active} 1")
        ud_mstr_init_tran.writeAction(f"blt {num_ln_active} {self.num_child} {ud_mstr_loop_label}")
        ud_mstr_init_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        ud_mstr_init_tran.writeAction(f"addi {num_ln_active} {num_part_assigned} 0")
        ud_mstr_init_tran.writeAction("yield")

        '''
        Event:      Updown master loop
        Operands:   X8: Number of map tasks generated
                    X9: Return lane master thread loop event word
        '''

        ud_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_mstr_loop_ev_label)
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction("print ' '")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <updown_master_loop> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        if self.debug_flag or self.print_level >= 2:
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld master returns. Number of map generated = %ld' {'X0'}  {self.scratch[0]} {'X8'}")
        ud_mstr_loop_tran.writeAction(f"add X8 {self.num_map_gen} {self.num_map_gen}")
        ud_mstr_loop_tran.writeAction(f"bge {self.part_array_ptr} {part_array_end} {ud_mstr_fin_fetch_label}")
        # Send next non-assigned partition to the lane
        ud_mstr_loop_tran.writeAction(format_pseudo(f"sendr3_wret X1 {self.ud_mstr_loop_ev_label} \
            {self.part_array_ptr} {self.part_array_stride} {num_part_assigned}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Send partition to lane %ld master tid %ld part_array_ptr = %ld(0x%lx) num_part_assigned = %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]} {self.part_array_ptr} {self.part_array_ptr} {num_part_assigned}")
        if self.debug_flag or self.print_level >= 2:
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown master assignes %ld partition.' {'X0'} {num_part_assigned}")
        ud_mstr_loop_tran.writeAction(f"addi {num_part_assigned} {num_part_assigned} 1")
        ud_mstr_loop_tran.writeAction(f"add {self.part_array_stride} {self.part_array_ptr} {self.part_array_ptr} ")
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown master num_map_generated = %ld' {'X0'} {self.num_map_gen}")
        ud_mstr_loop_tran.writeAction(f"yield")
        # Finish issuing the assigned input kv set, terminate all the lane master threads
        ud_mstr_loop_tran.writeAction(f"{ud_mstr_fin_fetch_label}: subi {num_ln_active} {num_ln_active} 1")
        if self.debug_flag or self.print_level >= 2:
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown master assigned all partitions, number of lane master remains active = %ld' {'X0'} {num_ln_active}")
        ud_mstr_loop_tran = set_ev_label(ud_mstr_loop_tran, self.ev_word, self.ln_mstr_term_ev_label, "X1")
        ud_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {num_part_assigned}")
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown master %ld finishes assign all pairs. Terminates lane %ld master tid %ld, remain_active_lane = %ld' \
                {'X0'} {'X0'} {self.scratch[0]} {self.scratch[1]} {num_ln_active}")
        ud_mstr_loop_tran.writeAction(f"blei {num_ln_active} 0 {ud_mstr_fin_part_label}")
        ud_mstr_loop_tran.writeAction(f"yield")
        ud_mstr_loop_tran.writeAction(format_pseudo(f"{ud_mstr_fin_part_label}: sendr_wret {self.saved_cont} \
            {self.ud_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ud_mstr_loop_tran.writeAction(f"rshift {'X2'} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Updown master %ld tid %ld finishes issue num_map_generated = %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]} {self.num_map_gen}")
            ud_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ud_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[1]} {24}")
            ud_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ud_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Return to node master %ld tid %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]}")
        ud_mstr_loop_tran.writeAction(f"mov_imm2reg {self.num_map_gen} 0")
        ud_mstr_loop_tran.writeAction(f"yield")


        ud_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_mstr_term_ev_label)
        if self.debug_flag:
            ud_mstr_term_tran.writeAction(f"print ' '")
            ud_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <updown_master_term> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        ud_mstr_term_tran.writeAction(f"yield_terminate")

        return

    def __gen_lane_master(self):


        part_ptr    = "UDPR_1"
        part_end    = "UDPR_4"
        num_th_active   = "UDPR_5"
        lm_base_reg = "UDPR_6"
        max_map_th = "UDPR_7"

        empty_part_label = "lane_master_empty_partition"
        ln_mstr_loop_label = "lane_master_loop"
        ln_mstr_fin_fetch_label = "lane_master_fin_fetch"
        ln_mstr_cont_label = "lane_master_loop_cont"

        '''
        Event:      Initialize node master
        Operands:   X8: Pointer to the base address of the initial partition
                    X9: Number of partitions assigned to this lane x WORD_SIZE
                    X10: nth partition assigned to the lane
        '''
        ln_mstr_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_init_ev_label)
        if self.debug_flag:
            ln_mstr_init_tran.writeAction(f"print ' '")
            ln_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <lane_master_init> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
            ln_mstr_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: %ld partition assigned partition_base = %ld(0x%lx) partition_stride = %ld ' \
                {'X0'} {'X10'} {'X8'} {'X8'} {'X9'}")
        ln_mstr_init_tran.writeAction(f"mov_reg2reg X1 {self.saved_cont}")
        ln_mstr_init_tran.writeAction(format_pseudo(f"send_dmlm_ld_wret X8 {self.ln_mstr_rd_part_ev_label} {'2'}", self.scratch[0], self.send_temp_reg_flag))
        ln_mstr_init_tran.writeAction(f"yield")

        '''
        Event:      Read the start and end address of the assigned partition
        Operands:   X8: The base address of the first key-value pair in the partition
                    X9: The base address of the first key-value pair in the next partition / or the end address of the key-value set
        '''

        ln_mstr_rd_part_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_rd_part_ev_label)
        if self.debug_flag:
            ln_mstr_rd_part_tran.writeAction(f"print ' '")
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <lane_master_read_partition> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld] Operands: part[0] = %ld(0x%lx) next_part[0] = %ld(0x%lx)' {'X0'} {'X8'} {'X8'} {'X9'} {'X9'}")
        ln_mstr_rd_part_tran.writeAction(f"bge X8 X9 {empty_part_label}")
        ln_mstr_rd_part_tran.writeAction(f"mov_reg2reg X8 {part_ptr}")
        ln_mstr_rd_part_tran.writeAction(f"mov_reg2reg X9 {part_end}")
        ln_mstr_rd_part_tran.writeAction(f"mov_imm2reg {num_th_active} 0")
        ln_mstr_rd_part_tran.writeAction(f"movir {max_map_th} {self.max_map_th_per_lane}")
        ln_mstr_rd_part_tran = set_ev_label(ln_mstr_rd_part_tran, self.ev_word, self.ln_map_th_init_ev_label, new_thread=True)
        # Create the map worker threads on this lane and send out a key-value pair
        ln_mstr_rd_part_tran.writeAction(format_pseudo(f"{ln_mstr_loop_label}: sendr_wret {self.ev_word} {self.ln_mstr_loop_ev_label} \
            {part_ptr} {part_ptr}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld] Send kvpair to new map thread ev_word=%ld pair_ptr = %ld(0x%lx)' \
                {'X0'} {self.ev_word} {part_ptr} {part_ptr}")
        ln_mstr_rd_part_tran.writeAction(f"addi {num_th_active} {num_th_active} 1")
        ln_mstr_rd_part_tran, part_ptr = self.in_kvset.get_next_pair(ln_mstr_rd_part_tran, part_ptr, self.scratch)
        ln_mstr_rd_part_tran.writeAction(f"bge {part_ptr} {part_end} {ln_mstr_fin_fetch_label}")
        ln_mstr_rd_part_tran.writeAction(f"blt {num_th_active} {max_map_th} {ln_mstr_loop_label}")
        ln_mstr_rd_part_tran.writeAction(f"{ln_mstr_fin_fetch_label}: mov_imm2reg {self.num_map_gen} 0")
        # Initialize local counter and master thread event word.
        # lm_base_reg = self.__get_lm_base(ln_mstr_rd_part_tran, lm_base_reg)
        ln_mstr_rd_part_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
        ln_mstr_rd_part_tran.writeAction(f"move {self.num_map_gen} {self.map_ctr_offset}({lm_base_reg}) 0 8")
        ln_mstr_rd_part_tran = set_ev_label(ln_mstr_rd_part_tran, self.scratch[0], self.ln_mstr_loop_ev_label)
        if self.debug_flag:
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld] lane master event word = %ld' {'X0'} {self.scratch[0]}")
        ln_mstr_rd_part_tran.writeAction(f"move {self.scratch[0]} {self.ln_mstr_evw_offset}({lm_base_reg}) 0 8")
        ln_mstr_rd_part_tran.writeAction("yield")
        ln_mstr_rd_part_tran.writeAction(f"{empty_part_label}: mov_imm2reg {self.num_map_gen} 0")
        ln_mstr_rd_part_tran.writeAction(format_pseudo(f"sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen}", \
            self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld master receives empty partition, end_pair_addr = %ld(0x%lx)' \
                {'X0'} {'X0'} {part_end} {part_end}")
            ln_mstr_rd_part_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ln_mstr_rd_part_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_rd_part_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_mstr_rd_part_tran.writeAction(f"print '[DEBUG][NWID %ld] Return to updown master %ld tid %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]}")
        ln_mstr_rd_part_tran.writeAction(f"yield")

        '''
        Event:      Lane master loop
        Operands:   X8: Map thread event word
        '''

        ln_mstr_loop_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_loop_ev_label)
        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"print ' '")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <lane_master_loop> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
            ln_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[0]} {24}")
            ln_mstr_loop_tran.writeAction(f"andi {self.scratch[0]} {self.scratch[0]}  {0xFF}")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Source map thread tid = %ld return ops: X8 = %ld X9 = %ld' \
                {'X0'} {self.scratch[0]} {'X8'} {'X9'}")
        ln_mstr_loop_tran.writeAction(f"bge {part_ptr} {part_end} {ln_mstr_fin_fetch_label}")
        # Send next non-assigned partition to the lane
        ln_mstr_loop_tran.writeAction(f"send_dmlm_ld {part_ptr} {'X1'} {self.in_kvpair_size}")
        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Send kvpair to map thread %ld ev_word=%ld pair_ptr = %ld(0x%lx)' \
                {'X0'} {self.scratch[1]} {'X1'} {part_ptr} {part_ptr}")
        ln_mstr_loop_tran, part_ptr = self.in_kvset.get_next_pair(ln_mstr_loop_tran, part_ptr, self.scratch)
        ln_mstr_loop_tran.writeAction(f"yield")
        # Finish issuing the assigned input kv set, terminate the lane map thread
        ln_mstr_loop_tran.writeAction(f"{ln_mstr_fin_fetch_label}: subi {num_th_active} {num_th_active} 1")
        ln_mstr_loop_tran = set_ev_label(ln_mstr_loop_tran, self.ev_word, self.ln_map_th_term_ev_label, src_ev="X1")
        ln_mstr_loop_tran.writeAction(f"sendr_wcont {self.ev_word} X2 {self.part_array_ptr} {self.part_array_ptr}")
        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane master terminates map thread %ld ev_word=%ld remain_active_thread = %ld' \
                {'X0'} {self.scratch[1]} {self.ev_word} {num_th_active}")
        ln_mstr_loop_tran.writeAction(f"bnei {num_th_active} 0 {ln_mstr_cont_label}")
        # Finish issuing all the assigned input kv set, return to the updown master with the number of map tasks generated
        # lm_base_reg = self.__get_lm_base(ln_mstr_loop_tran, lm_base_reg)
        ln_mstr_loop_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
        ln_mstr_loop_tran.writeAction(f"move {self.map_ctr_offset}({lm_base_reg}) {self.num_map_gen} 0 8")
        ln_mstr_loop_tran.writeAction(format_pseudo(f"sendr_wret {self.saved_cont} {self.ln_mstr_init_ev_label} {self.num_map_gen} {self.num_map_gen}", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld master finishes all pairs assigned, num_map_generated = %ld, end_pair_addr = %ld(0x%lx)' \
                {'X0'} {'X0'} {self.num_map_gen} {part_end} {part_end}")
            ln_mstr_loop_tran.writeAction(f"rshift {self.saved_cont} {self.scratch[0]} {32}")
            ln_mstr_loop_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_mstr_loop_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_mstr_loop_tran.writeAction(f"print '[DEBUG][NWID %ld] Return to updown master %ld tid %ld' \
                {'X0'} {self.scratch[0]} {self.scratch[1]}")
        ln_mstr_loop_tran.writeAction(f"{ln_mstr_cont_label}: yield")


        ln_mstr_term_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_mstr_term_ev_label)
        if self.debug_flag:
            ln_mstr_term_tran.writeAction(f"print ' '")
            ln_mstr_term_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <lane_master_term> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        ln_mstr_term_tran.writeAction(f"yield_terminate")

        return

    def __gen_map_thread(self):


        '''
        Event:      Initialize map thread
        Operands:   OB_0: Pair address
        '''
        ln_map_init_th_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_map_th_init_ev_label)

        if self.debug_flag and self.print_level > 2:
            ln_map_init_th_tran.writeAction(f"print ' '")
            ln_map_init_th_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_map_thread> pair_addr = %ld(0x%lx)' \
                {'X0'} {f'OB_0'} {f'OB_0'}")
        ln_map_init_th_tran.writeAction(format_pseudo(f"send_dmlm_ld_wret {f'OB_0'} {self.kv_map_ev_label} {self.in_kvpair_size}", \
            self.scratch[0], self.send_temp_reg_flag))
        ln_map_init_th_tran.writeAction(f"yield")

        '''
        Event:      Map thread
        Operands:   Input key-value pair
        '''
        ln_map_th_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_map_ev_label)
        # Set up the map code
        if self.debug_flag:
            ln_map_th_tran.writeAction(f"print ' '")
            ln_map_th_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <map_thread> pair_addr = %ld(0x%lx)' \
                {'X0'} {f'OB_{self.in_kvpair_size}'} {f'OB_{self.in_kvpair_size}'}")
            ln_map_th_tran.writeAction(f"addi {f'OB_{self.in_kvpair_size}'} {self.saved_cont} 0")
        self.kv_map(ln_map_th_tran, "OB_0", [f"OB_{n+1}" for n in range((self.in_kvpair_size) - 1)], self.kv_map_ret_ev_label)

        '''
        Event:      Map thread return event
        Operands:
        '''
        lm_base_reg = 'UDPR_4'
        # Return to lane master

        ln_map_th_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_map_ret_ev_label)
        if self.debug_flag:
            ln_map_th_ret_tran.writeAction(f"print ' '")
            ln_map_th_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <map_thread_return> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
            ln_map_th_ret_tran.writeAction(f"rshift {'X2'} {self.scratch[1]} {24}")
            ln_map_th_ret_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_map_th_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Map thread %ld finishes pair %ld(0x%lx)' {'X0'} {self.scratch[1]} {self.saved_cont} {self.saved_cont}")
        # lm_base_reg = self.__get_lm_base(ln_map_th_ret_tran)
        ln_map_th_ret_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
        ln_map_th_ret_tran.writeAction(f"move {self.ln_mstr_evw_offset}({lm_base_reg}) {self.scratch[1]} 0 8")
        ln_map_th_ret_tran.writeAction(format_pseudo(f"sendops_wret {self.scratch[1]} {self.kv_map_ev_label} OB_0 2", self.scratch[0], self.send_temp_reg_flag))
        if self.debug_flag:
            ln_map_th_ret_tran.writeAction(f"rshift {'X1'} {self.scratch[1]} {24}")
            ln_map_th_ret_tran.writeAction(f"andi {self.scratch[1]} {self.scratch[1]}  {0xFF}")
            ln_map_th_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Map thread returns operands: OB_0 = %ld OB_1 = %ld to lane master tid %ld' \
                {'X0'} {'OB_0'} {'OB_1'} {self.scratch[0]}")
        ln_map_th_ret_tran.writeAction("yield")


        ln_map_th_term_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ln_map_th_term_ev_label)
        if self.debug_flag and self.print_level > 3:
            ln_map_th_term_tran.writeAction(f"print ' '")
            ln_map_th_term_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <map_thread_term> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        ln_map_th_term_tran.writeAction(f"yield_terminate")

        return

    def __gen_reduce_thread(self):

        inter_key       = "OB_0"
        inter_values    = [f"OB_{n+1}" for n in range((self.inter_kvpair_size) - 1)]
        lm_base_reg     = "UDPR_4"
        temp_value      = self.scratch[0]


        max_th_label = "push_back_to_queue"

        '''
        Event:      Reduce thread
        Operands:   Intermediate key-value pair
        '''
        # Check the thread name space usage
        ln_reduce_init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_reduce_ev_label)
        if self.debug_flag and self.print_level > 2:
            ln_reduce_init_tran.writeAction(f"print ' '")
            ln_reduce_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <lane_reduce_thread> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        # lm_base_reg = self.__get_lm_base(ln_reduce_init_tran)
        ln_reduce_init_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
        ln_reduce_init_tran.writeAction(f"move {self.num_reduce_th_offset}({lm_base_reg}) {temp_value} 0 8")
        ln_reduce_init_tran.writeAction(f"move {self.max_red_th_offset}({lm_base_reg}) {self.scratch[1]} 0 8")
        ln_reduce_init_tran.writeAction(f"bge {temp_value} {self.scratch[1]} {max_th_label}")
        ln_reduce_init_tran.writeAction(f"addi {temp_value} {temp_value} 1")
        ln_reduce_init_tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset}({lm_base_reg}) 0 8")

        self.kv_reduce(ln_reduce_init_tran, inter_key, inter_values, self.kv_reduce_ret_ev_label)

        ln_reduce_init_tran.writeAction(f"{max_th_label}: ev_update_1 EQT {self.ev_word} {255} {0b0100}")
        if self.debug_flag and self.print_level > 2:
            ln_reduce_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld has %ld reduce thread active, reaches max reduce threads, pushed back to queue.' {'X0'} {'X0'} {temp_value}")
        ln_reduce_init_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {'OB_0'} {self.inter_kvpair_size}")
        ln_reduce_init_tran.writeAction(f"yield_terminate")


        ln_reduce_ret_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.kv_reduce_ret_ev_label)
        if self.debug_flag and self.print_level > 2:
            ln_reduce_ret_tran.writeAction(f"print ' '")
            ln_reduce_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <lane_reduce_thread_return> ev_word = %lu income_cont = %ld' {'X0'} {'EQT'} {'X1'}")
        # lm_base_reg = self.__get_lm_base(ln_reduce_ret_tran)
        ln_reduce_ret_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
        # Increment the number of reduce tasks processed
        ln_reduce_ret_tran.writeAction(f"move {self.reduce_ctr_offset}({lm_base_reg}) {temp_value} 0 8")
        ln_reduce_ret_tran.writeAction(f"addi {temp_value} {temp_value} 1")
        ln_reduce_ret_tran.writeAction(f"move {temp_value} {self.reduce_ctr_offset}({lm_base_reg}) 0 8")
        if self.debug_flag and self.print_level > 2:
            ln_reduce_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld processed %ld reduce tasks' {'X0'} {'X0'} {temp_value}")

        # Decrement the number of active reduce threads
        ln_reduce_ret_tran.writeAction(f"move {self.num_reduce_th_offset}({lm_base_reg}) {temp_value} 0 8")
        ln_reduce_ret_tran.writeAction(f"subi {temp_value} {temp_value} 1")
        ln_reduce_ret_tran.writeAction(f"move {temp_value}  {self.num_reduce_th_offset}({lm_base_reg}) 0 8")
        if self.debug_flag and self.print_level > 2:
            ln_reduce_ret_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld has %ld reduce thread remain active' {'X0'} {'X0'} {temp_value}")

        ln_reduce_ret_tran.writeAction("yield_terminate")

        return

    def __gen_global_sync(self):

        self.ev_word        = "UDPR_14"
        global_sync_offsets = [self.reduce_ctr_offset]
        
        global_sync = GlobalSync(self.task, self.state, self.ev_word, global_sync_offsets, self.scratch, self.debug_flag, self.print_level, self.send_temp_reg_flag)
        global_sync.set_labels(self.glb_sync_init_ev_label, self.global_sync_ev_label, self.node_init_ev_label,
                               self.node_sync_ev_label, self.ud_accum_ev_label)

        '''
        Event:      Initialize global synchronization
        Operands:   X8:   Saved continuation
                    X9:   Number of map tasks generated
        '''
        global_sync.global_sync(continuation='X1', sync_value='X9', num_lanes='X8')

        return
    
    def __kv_merge(self):
        '''
        Helper function for atomic operation using scratchpad. First check if the newest value is cached or is being read (not coming back yet).
        If either, the update will be merged locally based on the user-defined merge function. When the data is ready, it will apply the accumulated 
        update(s), stores the data back to DRAM, and frees the hash table entry. If there's a hash conflict, the update will be postponed
        (i.e. append to the end of the event queue) until the event is popped up and the entry is freed.
        Parameter:
            key:        name of the operand buffer entries/registers containing the key to the cache entry
            values:     name of the operand buffer entries/registers containing the value to be merged
            reduce_ret_ev_label:    return event label to the udkvmsr library
            regs:       scratch registers, by default is all the 16 general purposed registers
        '''
        
        if self.cache_policy == 'wt':
            pass
        elif self.cache_policy == 'wb':
            pass

    @abstractmethod
    def kv_map(self, tran: Transition, key: str, values: list, map_ret_ev_label: str) -> int:
        '''
        User defined map function. It takes an key-value pair and produce one (or more) key-value pair(s).
        Parameters
            tran:       transition triggered by the map event
            key:        the name of the register/operand buffer entry which contains the input key
            value:      the name of the register/operand buffer entry which contains the input value
        Output
            tran(transition):
                        the last transtion in which the map thread termiantes
            size(int):       the size of the intermediate key-value pair (in words) generated by the mapper
        '''

        pass

    @abstractmethod
    def kv_reduce(self, tran: Transition, key: str, values: list, reduce_ret_ev_label: str) -> Transition:
        '''
        User defined reduce function. It takes an key-value pair generated by the mapper and updates the output value mapped to the given key accordingly.
        Parameters
            tran:       transition triggered by the reduce event
            key:        the name of the register/operand buffer entry which contains the intermediate key generated by the mapper
            value:      the name of the register/operand buffer entry which contains the intermediate value generated by the mapper (i.e. the incoming value)
        Output
            result_reg: the name of the register containing the reduced value to be stored back
        '''

        pass

    @abstractmethod
    def kv_merge_op(self, tran: Transition, in_key: str, in_values: list, old_values: list, regs: list) -> Transition:
        '''
        User defined merge operation used by the kv_merge() helper function.
        It takes an key-value pair generated by the mapper and updates the output value mapped to the given key accordingly.
        Parameters
            tran:       transition (codelet) triggered by the reduce event
            in_key:     the name of the register/operand buffer entry which contains the intermediate key generated by the mapper
            in_values:  the name of the register/operand buffer entry which contains the intermediate value generated by the mapper (i.e. the incoming value)
            old_values: the name of the register storing the current output kvpair's value corresponding with the incoming intermediate key
        Output
            result_reg: a list of register names containing the merged values to be stored back
        '''

        # user defined merge
        return tran
    
    def msr_cleanup(self, tran: Transition) -> Transition:
        '''
        User defined cleanup operations. This function is called by the cleanup toutine on each lane.
        The example implementation stores an array of elements to the DRAM. 
        '''
        
        # Array metadata is stored in the scratchpad memory
        dram_base_offset, num_element_offset, lm_offset, element_size = self.cleanup_parameters
        
        dram_base   = "UDPR_0"
        num_element = "UDPR_1"
        lm_addr     = "UDPR_2"
        lm_end_addr = "UDPR_3"
        array_size  = "UDPR_4"
        dram_offset = "UDPR_5"
        dram_addr   = "UDPR_6"
        counter     = "UDPR_7"
        
        dram_store_loop_label = "dram_store_loop"
        finish_label = "finish"
        
        tran.writeAction(f"movlr {dram_base_offset}({'X7'}) {dram_base} 0 8")
        tran.writeAction(f"movlr {num_element_offset}({'X7'}) {num_element} 0 8")
        tran.writeAction(f"addi {'X7'} {lm_addr} {lm_offset}")
        tran.writeAction(f"muli {num_element} {array_size} {element_size}")
        tran.writeAction(f"sli {array_size} {array_size} {LOG2_WORD_SIZE}")
        tran.writeAction(f"add {lm_addr} {array_size} {lm_end_addr}")
        tran.writeAction(f"mul {'X0'} {array_size} {dram_offset}")
        tran.writeAction(f"add {dram_offset} {dram_base} {dram_addr}")
        tran = set_ev_label(tran, self.ev_word, self.cleanup_store_ack_ev_label)
        tran.writeAction(f"{dram_store_loop_label}: bge {lm_addr} {lm_end_addr} {finish_label}")
        tran.writeAction(f"send_dmlm {dram_addr} {self.ev_word} {lm_addr} {element_size}")
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] Store {element_size} words from scratchpad addr = %ld(0x%lx) to DRAM addr = %ld(0x%lx)' \
                {'X0'} {lm_addr} {lm_addr} {dram_addr} {dram_addr}")
        tran.writeAction(f"addi {lm_addr} {lm_addr} {element_size * WORD_SIZE}")
        tran.writeAction(f"addi {dram_addr} {dram_addr} {element_size * WORD_SIZE}")
        tran.writeAction(f"jmp {dram_store_loop_label}")
        tran.writeAction(f"{finish_label}: movir {counter} 0")
        tran.writeAction(f"yield")
        
        store_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.cleanup_store_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            store_ack_tran.writeAction(f"print ' '")
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_cleanup_store_ack> ev_word=%ld' {'X0'} {'EQT'}")
        store_ack_tran.writeAction(f"addi {counter} {counter} 1")
        store_ack_tran.writeAction(f"beq {counter} {num_element} {finish_label}")
        if self.debug_flag:
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld stores %ld elements to DRAM' {'X0'} {'X0'} {counter}")
        store_ack_tran.writeAction(f"yield")
        store_ack_tran.writeAction(f"{finish_label}: movir {counter} 0")
        if self.debug_flag:
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Lane %ld finishes storing %ld elements to DRAM' {'X0'} {'X0'} {num_element}")
        
        return store_ack_tran

    def kv_reduce_loc(self, tran: Transition, key: str, nwid_mask:str, dest_id: str):
        '''
        User-defined mapping from a key to a reducer lane (id). Default implementation is a hash.
        Can be overwritten by the user and changed to customized mapping.
        Parameter
            tran:       transition (codelet) triggered by the map event
            key:        name of the register/operand buffer entry containing the key
            result:     name of the register reserved for storing the destination lane id
        '''

        tran.writeAction(f"and {key} {nwid_mask} {dest_id}")


    def kv_emit(self, tran: Transition, key: str, values: list, dest: str, reg1: str, reg2: str):
        '''
        Helper function which sends the intermediate key-value pair generated by the mapper to a reducer lane
        based on the key-lane mapping defined in self.kv_reduce_loc().
        Parameters:
            tran:       transition (codelet) triggered by the map event
            key:        name of the register/operand buffer entry containing the intermediate key to be sent to the reducer
            values:     name of the registers/operand buffer entry containing the intermediate value to be sent to the reducer
            dest:       name of the register reserved for the destination reducer id
            reg1&reg2:  name of scratch registers
        '''

        # lm_base_reg = self.__get_lm_base(tran, reg2)
        tran.writeAction(f"addi {'X7'} {reg2} 0")
        tran.writeAction(f"move {self.nwid_mask_offset}({reg2}) {reg1} 0 8")
        self.kv_reduce_loc(tran, key, reg1, dest)
        tran.writeAction(f"ev_update_2 {reg1} {self.kv_reduce_ev_label} 255 5")
        tran.writeAction(f"ev_update_reg_2 {reg1}  {reg1}  {dest} {dest} 8")
        tran.writeAction(f"sendr_wcont {reg1} EQT {key} {' '.join(values)}")
        tran.writeAction(f"move {self.map_ctr_offset}({reg2}) {reg1}  0 8")
        tran.writeAction(f"addi {reg1} {reg1} 1")
        tran.writeAction(f"move {reg1} {self.map_ctr_offset}({reg2}) 0 8")
    
    def msr_return(self, tran: Transition, ret_label: str, temp_reg:str, operands: str = 'EQT EQT', cont_label: str = '', branch_label = '') -> Transition:
        '''
        Helper function for returning to the UDKVMSR library from the user defined map/reduce function.
        Parameter:
            tran:       current transition
            ret_label:  return event label
            operands:   operands to be sent back to the UDKVMSR library (optional)
            cont_label: continuation event label for UDKVMSR (optional)
        '''
        
        tran = set_ev_label(tran, self.ev_word, ret_label, src_ev='X2', label=branch_label)
        if cont_label:
            if len(operands.split()) == 2:
                tran.writeAction(format_pseudo(f"sendr_wret {self.ev_word} {cont_label} {operands}", temp_reg, self.send_temp_reg_flag))
            elif len(operands.split()) == 3:
                tran.writeAction(format_pseudo(f"sendr3_wret {self.ev_word} {cont_label} {operands}", temp_reg, self.send_temp_reg_flag))
            else:
                exit("Error: invalid number of operands for msr_return")
        else:
            tran.writeAction(f"sendr_wcont {self.ev_word} {'X2'} {operands}")
        return tran

    def kv_merge(self, merge_tran: Transition, key: str, values: list, reduce_ret_ev_label: str, regs: list = [f'UDPR_{i}' for i in range(16)]):
        '''
        Helper function for atomic operation using scratchpad. First check if the newest value is cached or is being read (not coming back yet).
        If either, the update will be merged locally based on the user-defined merge function. When the data is ready, it will apply the accumulated 
        update(s), stores the data back to DRAM, and frees the hash table entry. If there's a hash conflict, the update will be postponed
        (i.e. append to the end of the event queue) until the event is popped up and the entry is freed.
        Parameter:
            key:        name of the operand buffer entries/registers containing the key to the cache entry
            values:     name of the operand buffer entries/registers containing the value to be merged
            reduce_ret_ev_label:    return event label to the udkvmsr library
            regs:       scratch registers, by default is all the 16 general purposed registers
        '''

        self.ld_merge_ev_label  = self.get_event_mapping("load_merge")
        self.store_ack_ev_label = self.get_event_mapping("store_ack")
        self.store_ack_more_ev_label = self.get_event_mapping("store_ack_more")

        lm_base_reg = regs[0]
        key_lm_offset   = regs[1]
        cached_key  = regs[2]
        pair_addr   = regs[3]
        temp_val    = regs[4]
        masked_key  = regs[5]
        cached_values   = [regs[6+i] for i in range(self.cache_entry_size - 1)]
        result_regs     = [regs[6+i+self.cache_entry_size] for i in range(self.cache_entry_size - 1)]

        tlb_active_hit_label = "tlb_active_hit"
        tlb_hit_label = "tlb_hit"
        tlb_evict_label = "tlb_evict"
        error_label = "error"

        '''
        check if the local scratchpad stores a pending update to the same key or a copy of the newest output kvpair with that key.
        '''
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Merge incoming key = %ld values = %ld' {'X0'} {key} {values[0]}")
        # lm_base_reg = self.__get_lm_base(merge_tran, lm_base_reg)
        merge_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
        merge_tran.writeAction(f"andi {key} {key_lm_offset} {self.cache_size - 1}")
        merge_tran.writeAction(f"sli {key_lm_offset} {key_lm_offset} {int(log2(self.cache_entry_bsize))}")
        merge_tran.writeAction(f"add {lm_base_reg} {key_lm_offset} {key_lm_offset}")
        merge_tran.writeAction(f"move {self.cache_offset}({key_lm_offset}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Cached key = %ld at offset %ld' {'X0'} {cached_key} {key_lm_offset}")
        merge_tran.writeAction(f"beq {cached_key} {key} {tlb_active_hit_label}")
        merge_tran.writeAction(f"mov_imm2reg {masked_key} {1}")
        merge_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        merge_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Masked key = %ld' {'X0'} {masked_key}")
        merge_tran.writeAction(f"beq {masked_key} {cached_key} {tlb_hit_label}")
        '''
        If not, check if the data cached has been written back to DRAM.
        If so, evict the current entry.
        '''
        merge_tran.writeAction(f"rshift {cached_key} {temp_val} {self.INACTIVE_MASK_SHIFT}")
        merge_tran.writeAction(f"beqi {temp_val} 1 {tlb_evict_label}")

        '''
        If all conditions failed, the entry is occupied and cannot be evicted for now, push the event back to the queue.
        '''
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Cache entry occupied, push back to queue key = %ld values = {' '.join(['%ld' for _ in range(self.inter_kvpair_size - 1)])}' \
                {'X0'} {key} {' '.join(values)}")
        merge_tran.writeAction(f"ev_update_2 {self.ev_word} {self.kv_reduce_ev_label} 255 5")
        merge_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {key} {self.inter_kvpair_size}")
        merge_tran.writeAction(f"move {self.num_reduce_th_offset}({lm_base_reg}) {temp_val} 0 8")
        merge_tran.writeAction(f"subi {temp_val} {temp_val} 1")
        merge_tran.writeAction(f"move {temp_val}  {self.num_reduce_th_offset}({lm_base_reg}) 0 8")
        merge_tran.writeAction("yield_terminate")

        # Still waiting for the read to the output kv pair on DRAM coming back, merge locally
        merge_tran.writeAction(f"{tlb_active_hit_label}: move {WORD_SIZE + self.cache_offset}({key_lm_offset}) {cached_values[0]} 1 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Cache active hit, cached value[0] = %ld' {'X0'} {cached_values[0]}")
        for i in range(len(cached_values) - 1):
            merge_tran.writeAction(f"move {WORD_SIZE * (i+1) + self.cache_offset}({key_lm_offset}) {cached_values[i+1]} 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Cached value[{i+1}] = %ld' {'X0'} {cached_values[i+1]}")
        self.kv_merge_op(merge_tran, key, values, cached_values, result_regs)
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + self.cache_offset}({key_lm_offset}) 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Store result value[{i}] = %ld' {'X0'} {result_regs[i]}")
        if self.send_temp_reg_flag:
            merge_tran = self.msr_return(merge_tran, reduce_ret_ev_label, temp_val, operands=f"EQT {cached_key}")
        else:
            merge_tran = self.msr_return_bkp(merge_tran, reduce_ret_ev_label)
        merge_tran.writeAction(f"yield")

        # The output kv pair is cached in the scratchpad, merge and immediate write back the newest value (write through policy)
        merge_tran.writeAction(f"{tlb_hit_label}: move {WORD_SIZE + self.cache_offset}({key_lm_offset}) {cached_values[0]} 1 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Cache hit, cached value[0] = %ld' {'X0'} {cached_values[0]}")
        for i in range(len(cached_values) - 1):
            merge_tran.writeAction(f"move {WORD_SIZE * (i+1) + self.cache_offset}({key_lm_offset}) {cached_values[i+1]} 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Cached value[{i+1}] = %ld' {'X0'} {cached_values[i+1]}")
        result_regs = self.kv_merge_op(merge_tran, key, values, cached_values, result_regs)
        # Store back the updated values to DRAM
        merge_tran = self.out_kvset.get_pair(merge_tran, key, pair_addr, cached_values)
        merge_tran = set_ev_label(merge_tran, self.ev_word, self.store_ack_ev_label)
        merge_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {key} {result_regs[0]}")
        if self.cache_entry_size > 2:
            merge_tran = set_ev_label(merge_tran, self.ev_word, self.store_ack_more_ev_label, src_ev=self.ev_word)
            for i in range(1, len(result_regs), 2):
                merge_tran.writeAction(f"addi {pair_addr} {pair_addr} {WORD_SIZE * 2}")
                merge_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {result_regs[i]} {result_regs[i+1]}")
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + self.cache_offset}({key_lm_offset}) 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Store result value[{i}] = %ld' {'X0'} {result_regs[i]}")
        merge_tran.writeAction("yield")

        # Current entry has been written back to DRAM, (i.e., can be evicted). Insert the new entry.
        merge_tran.writeAction(f"{tlb_evict_label}: move {key} {self.cache_offset}({key_lm_offset}) 1 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Cache miss evict old entry %ld' {'X0'} {cached_key}")
        # Retrieve the DRAM address of the output kvpair corresponding to {key} based on the user-defined access function
        merge_tran = self.out_kvset.get_pair(merge_tran, key, pair_addr, result_regs)
        merge_tran = set_ev_label(merge_tran, self.ev_word, self.ld_merge_ev_label)
        merge_tran.writeAction(f"send_dmlm_ld {pair_addr} {self.ev_word} {self.out_kvpair_size}")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %ld] Load pair key = %ld from DRAM' {'X0'} {key}")
        # Store the new entry to the cache
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {values[i]} {WORD_SIZE * i + self.cache_offset}({key_lm_offset}) 0 8")
        merge_tran.writeAction(f"addi {key} {cached_key} 0")
        merge_tran.writeAction(f"yield")

        # Triggered when the old output kvpair is read from DRAM ready for merging with the (accumulated) updates
        load_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ld_merge_ev_label)
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print ' '")
            load_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <kvmsr_load_merge> ev_word = %lu:' {'X0'} {'EQT'}")

        ld_key = "OB_0"
        ld_values = [f"OB_{1+i}" for i in range(self.cache_entry_size - 1)]

        # Check if the key loaded is the same as cached
        # load_tran.writeAction(f"bne {ld_key} {cached_key} {error_label}")

        # lm_base_reg = self.__get_lm_base(load_tran, lm_base_reg)
        # load_tran.writeAction(f"lshift_and_imm {ld_key} {key_lm_offset} {int(log2(self.cache_entry_bsize))} \
        #     {(self.cache_size << int(log2(self.cache_entry_bsize)))-1}")
        # load_tran.writeAction(f"add {lm_base_reg} {key_lm_offset} {key_lm_offset}")

        # Read the accumulated value and update the cache accordingly
        # load_tran.writeAction(f"move {self.cache_offset - WORD_SIZE}({key_lm_offset}) {cached_key} 0 8")
        for i in range(len(cached_values)):
            load_tran.writeAction(f"move {WORD_SIZE * i + self.cache_offset}({key_lm_offset}) {cached_values[i]} 0 8")
            if self.debug_flag and self.print_level > 2:
                load_tran.writeAction(f"print '[DEBUG][NWID %ld] Cached value[{i}] = %ld' {'X0'} {cached_values[i]}")

        # Apply the accumulated updates based on user-defined reduce funtion
        result_regs = self.kv_merge_op(load_tran, cached_key, cached_values, ld_values, result_regs)
        # Store back the updated values to DRAM
        load_tran = self.out_kvset.get_pair(load_tran, cached_key, pair_addr, cached_values)
        load_tran = set_ev_label(load_tran, self.ev_word, self.store_ack_ev_label)
        load_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {cached_key} {result_regs[0]}")
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print '[DEBUG][NWID %ld] Store result value[0] = %ld to addr = 0x%lx' {'X0'} {result_regs[0]} {pair_addr}")
        if self.cache_entry_size > 2:
            load_tran = set_ev_label(load_tran, self.ev_word, self.store_ack_more_ev_label, src_ev=self.ev_word)
            for i in range(1, len(result_regs), 2):
                load_tran.writeAction(f"addi {pair_addr} {pair_addr} {WORD_SIZE * 2}")
                load_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {result_regs[i]} {result_regs[i+1]}")
                if self.debug_flag and self.print_level > 2:
                    load_tran.writeAction(f"print '[DEBUG][NWID %ld] Store result value[{i}] = %ld result value[{i+1}] = %ld to addr = 0x%lx' \
                        {'X0'} {result_regs[i]} {result_regs[i+1]} {pair_addr}")
        # Store the updated value back to the cache
        for i in range(self.cache_entry_size - 1):
            load_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + self.cache_offset}({key_lm_offset}) 0 8")
        # load_tran.writeAction(f"or {cached_key} {cache_key_mask} {cached_key}")
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print '[DEBUG][NWID %ld] Store masked key = %ld to addr = 0x%lx' {'X0'} {masked_key} {key_lm_offset}")
        load_tran.writeAction(f"move {masked_key} {self.cache_offset - WORD_SIZE}({key_lm_offset}) 0 8")    # flip the highest bit indicating the value is written back
        load_tran.writeAction(f"yield")

        # load_tran.writeAction(f"{error_label}: print '[DEBUG][NWID %ld] ERROR! loaded key=%ld is not equal to the cached key=%ld' {'X0'} {ld_key} {cached_key}")
        # load_tran.writeAction(f"yield")

        # Triggered when the write comes back from DRAM, finish the merge and store back the updated value
        store_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.store_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            store_ack_tran.writeAction(f"print ' '")
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <store_ack> ev_word = %lu addr = 0x%lx' {'X0'} {'EQT'} {'OB_0'}")
        if self.send_temp_reg_flag:
            store_ack_tran = self.msr_return(store_ack_tran, reduce_ret_ev_label, temp_val, operands=f"EQT {cached_key}")
        else:
            store_ack_tran = self.msr_return_bkp(store_ack_tran, reduce_ret_ev_label)
        store_ack_tran.writeAction("yield")

        store_ack_more_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.store_ack_more_ev_label)
        if self.debug_flag and self.print_level > 3:
            store_ack_more_tran.writeAction(f"print ' '")
            store_ack_more_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <store_ack_more> ev_word = %lu addr = 0x%lx' {'X0'} {'EQT'} {'OB_0'}")
        store_ack_more_tran.writeAction(f"yield")

        return

'''
Template ends here
-----------------------------------------------------------------------
'''
