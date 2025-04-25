from linker.EFAProgram import efaProgram, EFAProgram

from libraries.UDMapShuffleReduce.linkable.LinkableKVMapShuffleCombineTPL import UDKeyValueMapShuffleReduceTemplate
from libraries.UDMapShuffleReduce.utils.OneDimArrayKeyValueSet import OneDimKeyValueSet
from libraries.UDMapShuffleReduce.utils.IntermediateKeyValueSet import IntermediateKeyValueSet

from Macro import *

WORD_SIZE = 8
LOG2_WORD_SIZE = 3
TOP_FLAG_OFFSET = 0

'''
Below is an naive map reduce example. The map function masks the input key by the number of workerand send it with input value to the reducer.
The reducer takes the intermediate key-value pairs and sums up all the values correspond to the same key.
To write a map reduce program using the template, one needs to implement the two abstract method, namely kv_map() and kv_reduce(),
instantiate the map reduce task, and set up the metadata required by the template using the provided helper functions.
'''
class PagerankMapShuffleReduce(UDKeyValueMapShuffleReduceTemplate):
    BATCH_SIZE = 8
    MAX_LOAD_REQUESTS = 8
    
    def kv_emit(self, tran: EFAProgram.Transition, key: str, values: list, reg1: str):
        
        tran.writeAction(f"evii {reg1} {self.kv_map_emit_ev_label} 255 5")
        tran.writeAction(f"sendr_wcont {reg1} {'X2'} {key} {' '.join(values)}")
    
    def msr_return(self, tran: EFAProgram.Transition, ret_label: str, temp_reg:str, operands: str = 'EQT EQT', cont_label: str = '', branch_label = '') -> EFAProgram.Transition:
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

    def kv_combine_op(self, tran: EFAProgram.Transition, key: str, in_values: list, old_values: list, results: list) -> EFAProgram.Transition:
        for in_val, old_val, result in zip(in_values, old_values, results):
            tran.writeAction(f"fadd.64 {in_val} {old_val} {result}")
            if self.debug_flag:
                tran.writeAction(f"print '[DEBUG][NWID %d] Merge values for key = %d incoming value = %g old value = %g result = %g' {'X0'} {key} {in_val} {old_val} {result}")
        return tran

@efaProgram
def GenMSRPagerankEFA(efa: EFAProgram):

    '''
    Initialize the map reduce task. The following parameters are required:
        task_name:      name of the task, unique for each task
        num_workers:    number of updown lanes used in this task
        partition_parm: parameter controlling the number of partitions each level of hierarchy has (optional), default is 1
        enable_cache:   enable cache for the kv_merge() function (optional), default is False
        lm_mode:        scratchpad addressing mode, determines the value in X7 (optional), default is 1
        debug_flag:     enable debug print (optional), default is False
    '''
    pagerankMSR = PagerankMapShuffleReduce(efa=efa, task_name="pr", meta_data_offset=64, debug_flag=False)
    # Setup the input and output key value set. 
    pagerankMSR.set_input_kvset(OneDimKeyValueSet("Input", element_size=4, bypass_gen_partition=True))
    pagerankMSR.set_intermediate_kvset(IntermediateKeyValueSet("Intermediate", key_size=1, value_size=1))
    pagerankMSR.set_output_kvset(OneDimKeyValueSet("Output", element_size=1))
    # If kv_merge() is used, the cache must be enabled and the cache size must be set.
    pagerankMSR.setup_cache(cache_offset=72+32*8, num_entries=4030, entry_size=2)
    # Set the maximum number of map and reduce threads concurrently running on each lane. Should be less than the max hardware threads supported.
    pagerankMSR.set_max_thread_per_lane(max_map_th_per_lane=30, max_reduce_th_per_lane=210)
    
    pagerankMSR.generate_udkvmsr_task()
    
    DEBUG_FLAG = pagerankMSR.debug_flag

    temp_reg    = "UDPR_0"
    lm_base_reg = "UDPR_1"
    send_buffer = "UDPR_2"
    ev_word_reg = "UDPR_9"
    
    '''
    Entry event transition to be triggered by the top program. Updown program starts from here.
      operands
      X8:   Pointer to the partition array (64-bit DRAM address)
      X9:   Number of partitions per lane
      X10:  Number of lanes
      X11:  Pointer to input kvset (64-bit DRAM address)
      X12:  Number of elements in the input kvset (1D array)
      X13:  Pointer to outKVMap (64-bit DRAM address)
      X14:  Number of elements in the output kvset (1D array)
    '''
    init_tran = pagerankMSR.state.writeTransition("eventCarry", pagerankMSR.state, pagerankMSR.state, 'updown_init')
    init_tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_init> ' {'X0'} ")
    # Move the UDKVMSR call parameters to scratchpad.
    init_tran.writeAction(f"movir {send_buffer} {pagerankMSR.send_buffer_offset}")
    init_tran.writeAction(f"add {'X7'} {send_buffer} {send_buffer}")
    init_tran.writeAction(f"movrl {'X8'} 0({send_buffer}) 0 8")
    if DEBUG_FLAG:
        init_tran.writeAction(f"print '[DEBUG][NWID %d] Partition array %lu(0x%lx) and number of partition per lane = %ld' {'X0'} {'X8'} {'X8'} {'X9'}")
    init_tran.writeAction(f"movrl {'X9'} 8({send_buffer}) 0 8")
    init_tran.writeAction(f"movrl {'X10'} 16({send_buffer}) 0 8")
    init_tran.writeAction(f"addi {'X7'} {lm_base_reg} {pagerankMSR.in_kvset_offset}")
    init_tran.writeAction(f"movrl {lm_base_reg} 24({send_buffer}) 0 8")
    if DEBUG_FLAG:
        init_tran.writeAction(f"print '[DEBUG][NWID %d] Save input key value set base pointer %lu(0x%lx) and size %ld to scratchpad addr %ld(0x%lx)' {'X0'} {'X11'} {'X11'} {'X12'} {lm_base_reg} {lm_base_reg}")
    init_tran.writeAction(f"movrl {'X11'} 0({lm_base_reg}) 1 8")
    init_tran.writeAction(f"movrl {'X12'} 0({lm_base_reg}) 1 8")
    init_tran.writeAction(f"movrl {lm_base_reg} 32({send_buffer}) 0 8")
    if DEBUG_FLAG:
        init_tran.writeAction(f"print '[DEBUG][NWID %d] Save output key value set base pointer %lu(0x%lx) to scratchpad addr %ld(0x%lx)' {'X0'} {'X13'} {'X13'} {'X14'} {lm_base_reg} {lm_base_reg}")
    init_tran.writeAction(f"movrl {'X13'} 0({lm_base_reg}) 1 8")
    init_tran.writeAction(f"movrl {'X14'} 0({lm_base_reg}) 1 8")
    '''
    Send the parameter to UDKVMSR library to start the UDKVMSR program. 
        Operands:
        OB_0: Pointer to the partition array (64-bit DRAM address)
        OB_1: Number of partitions per lane
        OB_2: Number of lanes
        OB_3: Scratchapd addr storing the input kvset metadata (base address and size)
        OB_4: Scratchapd addr storing the output kvset metadata (base address and size)
    '''
    init_tran.writeAction(f"evii {ev_word_reg} {pagerankMSR.init_kvmsr_ev_label} 255 5")
    init_tran.writeAction(f"send_wret {ev_word_reg} {'updown_terminate'} {send_buffer} 5 {temp_reg}")
    init_tran.writeAction(f"movir {temp_reg} 0")
    init_tran.writeAction(f"addi {'X7'} {lm_base_reg} {TOP_FLAG_OFFSET}")
    init_tran.writeAction(f"move {temp_reg} {0}({lm_base_reg}) 0 8")
    init_tran.writeAction("yield")
    
    '''
    User defined continuation event transition to be triggered when the UDKVMSR task finishes.
    '''
    term_tran = pagerankMSR.state.writeTransition("eventCarry", pagerankMSR.state, pagerankMSR.state, 'updown_terminate')
    if DEBUG_FLAG:
        term_tran.writeAction(f"print '[DEBUG][NWID %d] Event <updown_terminate> Finish PageRank' {'X0'}")
    term_tran.writeAction(f"print '[DEBUG][NWID %d] Finish PageRank, number of edge updates = %ld' {'X0'} {'X8'}")
    # UpDown program finishes, Signal the top 
    term_tran.writeAction(f"movir {temp_reg} 1")
    term_tran.writeAction(f"move {temp_reg} {0}({lm_base_reg}) 0 8")
    term_tran.writeAction("yield_terminate")
    
    
    kv_map(pagerankMSR)

    pagerankMSR.generate_udkvmsr_task()

    return pagerankMSR.efa

def kv_map(pagerankMSR: PagerankMapShuffleReduce) -> int:
    '''
    values[0]: degree
    values[1]: neighbor list pointer
    values[2]: PageRank value
    '''
    tran = pagerankMSR.state.writeTransition("eventCarry", pagerankMSR.state, pagerankMSR.state, pagerankMSR.kv_map_ev_label)
    ld_ret_ev_label = pagerankMSR.get_event_mapping("map_load_return")
    map_ret_ev_label = pagerankMSR.kv_map_ret_ev_label
    map_emit_ev_label = pagerankMSR.kv_map_emit_ev_label
    
    key     = f"X{1+OB_REG_BASE}"       # Register X1 stores the vertex id
    values  = [f"X{i+OB_REG_BASE+1}" for i in range(3)]
    degree_op = values[0]   # value[0] stores the degree of the node
    pr_value  = values[2]   # value[2] stores the PageRank value of the node
    nbor_list = "UDPR_0"    # Register UDPR_0 stores the pointer to the neighbor list 
    nbor_bnd  = "UDPR_1"    # Register UDPR_1 stores the bound of the neighbor list
    vid       = "UDPR_2"    # Register UDPR_2 stores the vertex id
    new_pr_value = "UDPR_3" # Register UDPR_3 stores the new PageRank value
    degree    = "UDPR_4" # Register UDPR_4 stores the vertex degree
    dest_nwid = "UDPR_5"    # Register UDPR_5 stores the lane id where the intermediate kvmap will be sent to
    nbor_reg  = "UDPR_6"    # Register UDPR_6 stores the neighbors[0] pointer
    ctr       = "UDPR_7"    # Register UDPR_7 stores the temporary counter
    nwid_mask = "UDPR_8"    # Register UDPR_10 stores the number of lanes mask
    max_req   = "UDPR_9"    # Register UDPR_9 stores the maximum number of ongoing load requests 
    lm_base   = "UDPR_10"   # Register UDPR_10 stores the base address of the metadata
    reduce_evw = "UDPR_11"  # Register UDPR_11 stores the event word for reduce event
    cont_evw  = "UDPR_12"  # Register UDPR_12 stores the event word for continue event
    scratch   = ["UDPR_14", "UDPR_15"]  # Scratch registers
    ld_loop_label = "array_load"        # Label for the load loop
    ld_fin_label  = "array_load_fin"    # Label for finishing load
    empty_label   = "empty"             # Label for empty neighbor list
    bcst_cont_label = "broadcast_continue" # Label for broadcast continue

    if pagerankMSR.debug_flag:
        tran.writeAction(f"addi {key} {vid} 0")
        tran.writeAction(f"addi {values[1]} {nbor_reg} 0")
        tran.writeAction(f"print '[DEBUG][NWID %d] Start map task for vertex %d degree %d neighbor list 0x%x' {'X0'} {key} {degree_op} {nbor_reg}")
    tran.writeAction(f"beqi {degree_op} 0 {empty_label}")
    tran.writeAction(f"addi {values[1]} {nbor_list} 0")
    tran.writeAction(f"lshift {degree_op} {nbor_bnd} {LOG2_WORD_SIZE}")
    tran.writeAction(f"add {nbor_list} {nbor_bnd} {nbor_bnd}")
    tran.writeAction(f"movir {ctr} 0")
    tran.writeAction(f"movir {max_req} {pagerankMSR.MAX_LOAD_REQUESTS * pagerankMSR.BATCH_SIZE}")
    tran.writeAction(f"{ld_loop_label}: bge {nbor_list} {nbor_bnd} {ld_fin_label}")
    tran.writeAction(f"send_dmlm_ld_wret {nbor_list} {ld_ret_ev_label} {pagerankMSR.BATCH_SIZE} {scratch[0]}")
    tran.writeAction(f"addi {nbor_list} {nbor_list} {pagerankMSR.BATCH_SIZE << LOG2_WORD_SIZE}")
    tran.writeAction(f"addi {ctr} {ctr} {pagerankMSR.BATCH_SIZE}")
    tran.writeAction(f"bge {ctr} {max_req} {ld_fin_label}") # break if the number of fetch requests reaches the maximum
    tran.writeAction(f"jmp {ld_loop_label}")
    tran.writeAction(f"{ld_fin_label}: fcnvt.i64.64 {degree_op} {degree}")
    tran.writeAction(f"fdiv.64 {pr_value} {degree} {new_pr_value}")
    tran.writeAction(f"addi {degree_op} {degree} 0")
    tran.writeAction(f"addi {'X7'} {lm_base} {0}")
    tran.writeAction(f"movlr {pagerankMSR.nwid_mask_offset}({lm_base}) {nwid_mask} 0 8")
    set_ev_label(tran, reduce_evw, pagerankMSR.kv_reduce_init_ev_label, new_thread = True)
    set_ev_label(tran, cont_evw, pagerankMSR.kv_reduce_ret_ev_label, new_thread = True)
    tran.writeAction(f"move {pagerankMSR.map_ctr_offset}({lm_base}) {scratch[0]}  0 8")
    tran.writeAction(f"add {degree_op} {scratch[0]} {scratch[0]}")
    tran.writeAction(f"move {scratch[0]} {pagerankMSR.map_ctr_offset}({lm_base}) 0 8")
    tran.writeAction(f"movir {ctr} 0")
    if pagerankMSR.debug_flag:
        tran.writeAction(f"print '[DEBUG][NWID %d] Vertex %d outgoing PageRank value = %g' {'X0'} {key} {new_pr_value}")
    tran.writeAction(f"yield")
    if pagerankMSR.debug_flag:
        tran.writeAction(f"{empty_label}: print '[DEBUG][NWID %d] Vertex %d empty neighbor list return to lane master ' {'X0'} {key}")
        pagerankMSR.msr_return(tran, ret_label=map_ret_ev_label, temp_reg=scratch[0])
    else:
        pagerankMSR.msr_return(tran, ret_label=map_ret_ev_label, branch_label=empty_label, temp_reg=scratch[0])
    tran.writeAction(f"yield")
    
    ld_address = 'UDPR_9'
    
    bcst_fin_label  = "finish_broadcast"    # Label for finishing broadcast to all neighbors
    fetch_fin_label = "finish_fetch"        # Label for finishing fetching all neighbors
    ld_tran = pagerankMSR.state.writeTransition("eventCarry", pagerankMSR.state, pagerankMSR.state, ld_ret_ev_label)
    if pagerankMSR.debug_flag:
        ld_tran.writeAction(f"print ' '")
        # ld_tran.writeAction(f"print '[DEBUG][NWID %d] Event <map_load_return> ev_word = %d' \
        #     {'X0'} {'X1'}")
        ld_tran.writeAction(f"print '[DEBUG][NWID %d] Event <map_load_return> ev_word = %d vertex %d degree = %d nlist_addr = 0x%x nlist_bound = 0x%x' \
            {'X0'} {'X1'} {vid} {degree} {'X3'} {nbor_bnd}")
    ld_tran.writeAction(f"bge {nbor_list} {nbor_bnd} {fetch_fin_label}") # Continue if all the neighbors have been fetched
    ld_tran.writeAction(f"send_dmlm_ld_wret {nbor_list} {ld_ret_ev_label} {pagerankMSR.BATCH_SIZE} {scratch[0]}")
    ld_tran.writeAction(f"addi {nbor_list} {nbor_list} {pagerankMSR.BATCH_SIZE << LOG2_WORD_SIZE}")
    ld_tran.writeAction(f"{fetch_fin_label}: addi {'X3'} {ld_address} 0")
    for k in range(pagerankMSR.BATCH_SIZE):
        ld_tran.writeAction(f"bge {ld_address} {nbor_bnd} {bcst_cont_label}")
        ld_tran.writeAction(f"movir {dest_nwid} {8}")
        ld_tran.writeAction(f"hash {f'X{k+OB_REG_BASE}'} {dest_nwid}")
        ld_tran.writeAction(f"and {dest_nwid} {nwid_mask} {dest_nwid}")
        ld_tran.writeAction(f"ev {reduce_evw}  {reduce_evw}  {dest_nwid} {dest_nwid} 8")
        ld_tran.writeAction(f"sendr_wcont {reduce_evw} {cont_evw} {f'X{k+OB_REG_BASE}'} {new_pr_value}")
        if pagerankMSR.debug_flag:
            ld_tran.writeAction(f"print '[DEBUG][NWID %d] Map generates intermediate key = %d, send to lane %d' {'X0'} {f'X{k+OB_REG_BASE}'} {dest_nwid}")
        ld_tran.writeAction(f"addi {ld_address} {ld_address} {WORD_SIZE}")
        ld_tran.writeAction(f"addi {ctr} {ctr} 1")
        ld_tran.writeAction(f"bge {ctr} {degree} {bcst_fin_label}")
    ld_tran.writeAction(f"{bcst_cont_label}: yield")
    if pagerankMSR.debug_flag:
        ld_tran.writeAction(f"{bcst_fin_label}: print '[DEBUG][NWID %d] Finish broadcasting to %d neighbors' {'X0'} {degree}")
        pagerankMSR.msr_return(ld_tran, ret_label=map_ret_ev_label, operands=f'{vid} {nbor_reg}', temp_reg=scratch[0]) 
    else:
        pagerankMSR.msr_return(ld_tran, ret_label=map_ret_ev_label, operands=f'{vid} {nbor_reg}', branch_label=bcst_fin_label, temp_reg=scratch[0]) 
    ld_tran.writeAction("yield")
    
    return 
