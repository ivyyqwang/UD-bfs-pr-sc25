from EFA_v2 import *
from Macro import *
from KVMSRMachineConfig import *

class ScratchpadCache:
    
    def __init__(self, state: State, cache_base_offset: int, cache_size: int, entry_size: int, cache_ival: int, policy: str, debug_flag = False, print_level = 0):
        # self.kvmsr = kvmsr
        self.state = state
        self.cache_base_offset = cache_base_offset
        self.cache_size = cache_size
        self.cache_entry_bsize = entry_size << LOG2_WORD_SIZE
        self.cache_entry_size = entry_size
        self.INACTIVE_MASK_SHIFT = 63
        self.INACTIVE_MASK = (1 << self.INACTIVE_MASK_SHIFT)
        self.cache_ival = cache_ival | self.INACTIVE_MASK
        self.cache_policy = policy
        self.debug_flag = debug_flag
        self.print_level = print_level
        
    def get_event_mapping(self, event_name: str):
        # return self.kvmsr.get_event_mapping(event_name)
        pass
    
    def gen_write_back_cache(self, tran: Transition, key: str, values: list, reduce_ret_ev_label: str, regs: list = [f'UDPR_{i}' for i in range(16)]):
        
        pass
    
    def gen_cache_flush(self, tran: Transition, regs: list = [f'UDPR_{i}' for i in range(16)]):
        
        pass
        
    def gen_write_through_cache(self, merge_tran: Transition, key: str, values: list, reduce_ret_ev_label: str, regs: list = [f'UDPR_{i}' for i in range(16)]):

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
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Merge incoming key = %d values = %d' {'X0'} {key} {values[0]}")
        merge_tran.writeAction(f"addi {'X7'} {lm_base_reg} 0")
        merge_tran.writeAction(f"lshift_and_imm {key} {key_lm_offset} {int(log2(self.cache_entry_bsize))} \
            {(self.cache_size << int(log2(self.cache_entry_bsize)))-1}")
        merge_tran.writeAction(f"add {lm_base_reg} {key_lm_offset} {key_lm_offset}")
        merge_tran.writeAction(f"move {self.cache_base_offset}({key_lm_offset}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cached key = %d at offset %d' {'X0'} {cached_key} {key_lm_offset}")
        merge_tran.writeAction(f"beq {cached_key} {key} {tlb_active_hit_label}")
        merge_tran.writeAction(f"mov_imm2reg {masked_key} {1}")
        merge_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        merge_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Masked key = %d' {'X0'} {masked_key}")
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
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache entry occupied, push back to queue key = %d values = {' '.join(['%d' for _ in range(self.inter_kvpair_size - 1)])}' \
                {'X0'} {key} {' '.join(values)}")
        merge_tran.writeAction(f"ev_update_2 {self.ev_word} {self.kv_reduce_ev_label} 255 5")
        merge_tran.writeAction(f"sendops_wcont {self.ev_word} X1 {key} {self.inter_kvpair_size}")
        merge_tran.writeAction(f"move {self.num_reduce_th_offset}({lm_base_reg}) {temp_val} 0 8")
        merge_tran.writeAction(f"subi {temp_val} {temp_val} 1")
        merge_tran.writeAction(f"move {temp_val}  {self.num_reduce_th_offset}({lm_base_reg}) 0 8")
        merge_tran.writeAction("yield_terminate")

        # Still waiting for the read to the output kv pair on DRAM coming back, merge locally
        merge_tran.writeAction(f"{tlb_active_hit_label}: move {WORD_SIZE + self.cache_base_offset}({key_lm_offset}) {cached_values[0]} 1 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache active hit, cached value[0] = %d' {'X0'} {cached_values[0]}")
        for i in range(len(cached_values) - 1):
            merge_tran.writeAction(f"move {WORD_SIZE * (i+1) + self.cache_base_offset}({key_lm_offset}) {cached_values[i+1]} 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cached value[{i+1}] = %d' {'X0'} {cached_values[i+1]}")
        self.kv_merge_op(merge_tran, key, values, cached_values, result_regs)
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + self.cache_base_offset}({key_lm_offset}) 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[{i}] = %d' {'X0'} {result_regs[i]}")
        merge_tran = self.msr_return(merge_tran, reduce_ret_ev_label, temp_val, operands=f"EQT {cached_key}")
        merge_tran.writeAction(f"yield")

        # The output kv pair is cached in the scratchpad, merge and immediate write back the newest value (write through policy)
        merge_tran.writeAction(f"{tlb_hit_label}: move {WORD_SIZE + self.cache_base_offset}({key_lm_offset}) {cached_values[0]} 1 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache hit, cached value[0] = %d' {'X0'} {cached_values[0]}")
        for i in range(len(cached_values) - 1):
            merge_tran.writeAction(f"move {WORD_SIZE * (i+1) + self.cache_base_offset}({key_lm_offset}) {cached_values[i+1]} 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cached value[{i+1}] = %d' {'X0'} {cached_values[i+1]}")
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
            merge_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + self.cache_base_offset}({key_lm_offset}) 0 8")
            if self.debug_flag and self.print_level > 2:
                merge_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[{i}] = %d' {'X0'} {result_regs[i]}")
        merge_tran.writeAction("yield")

        # Current entry has been written back to DRAM, (i.e., can be evicted). Insert the new entry.
        merge_tran.writeAction(f"{tlb_evict_label}: move {key} {self.cache_base_offset}({key_lm_offset}) 1 8")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Cache miss evict old entry %d' {'X0'} {cached_key}")
        # Retrieve the DRAM address of the output kvpair corresponding to {key} based on the user-defined access function
        merge_tran = self.out_kvset.get_pair(merge_tran, key, pair_addr, result_regs)
        merge_tran = set_ev_label(merge_tran, self.ev_word, self.ld_merge_ev_label)
        merge_tran.writeAction(f"send_dmlm_ld {pair_addr} {self.ev_word} {self.out_kvpair_size}")
        if self.debug_flag and self.print_level > 2:
            merge_tran.writeAction(f"print '[DEBUG][NWID %d] Load pair key = %d from DRAM' {'X0'} {key}")
        # Store the new entry to the cache
        for i in range(self.cache_entry_size - 1):
            merge_tran.writeAction(f"move {values[i]} {WORD_SIZE * i + self.cache_base_offset}({key_lm_offset}) 0 8")
        merge_tran.writeAction(f"addi {key} {cached_key} 0")
        merge_tran.writeAction(f"yield")

        # Triggered when the old output kvpair is read from DRAM ready for merging with the (accumulated) updates
        load_tran = self.kvmsr.state.writeTransition("eventCarry", self.kvmsr.state, self.kvmsr.state, self.ld_merge_ev_label)
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print ' '")
            load_tran.writeAction(f"print '[DEBUG][NWID %d] Event <kvmsr_load_merge> ev_word = %d:' {'X0'} {'EQT'}")

        ld_key = "OB_0"
        ld_values = [f"OB_{1+i}" for i in range(self.cache_entry_size - 1)]

        # Check if the key loaded is the same as cached
        # load_tran.writeAction(f"bne {ld_key} {cached_key} {error_label}")

        # lm_base_reg = self.__get_lm_base(load_tran, lm_base_reg)
        # load_tran.writeAction(f"lshift_and_imm {ld_key} {key_lm_offset} {int(log2(self.cache_entry_bsize))} \
        #     {(self.cache_size << int(log2(self.cache_entry_bsize)))-1}")
        # load_tran.writeAction(f"add {lm_base_reg} {key_lm_offset} {key_lm_offset}")

        # Read the accumulated value and update the cache accordingly
        # load_tran.writeAction(f"move {self.cache_base_offset - WORD_SIZE}({key_lm_offset}) {cached_key} 0 8")
        for i in range(len(cached_values)):
            load_tran.writeAction(f"move {WORD_SIZE * i + self.cache_base_offset}({key_lm_offset}) {cached_values[i]} 0 8")
            if self.debug_flag and self.print_level > 2:
                load_tran.writeAction(f"print '[DEBUG][NWID %d] Cached value[{i}] = %d' {'X0'} {cached_values[i]}")

        # Apply the accumulated updates based on user-defined reduce funtion
        result_regs = self.kv_merge_op(load_tran, cached_key, cached_values, ld_values, result_regs)
        # Store back the updated values to DRAM
        load_tran = self.out_kvset.get_pair(load_tran, cached_key, pair_addr, cached_values)
        load_tran = set_ev_label(load_tran, self.ev_word, self.store_ack_ev_label)
        load_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {cached_key} {result_regs[0]}")
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[0] = %d to addr = 0x%x' {'X0'} {result_regs[0]} {pair_addr}")
        if self.cache_entry_size > 2:
            load_tran = set_ev_label(load_tran, self.ev_word, self.store_ack_more_ev_label, src_ev=self.ev_word)
            for i in range(1, len(result_regs), 2):
                load_tran.writeAction(f"addi {pair_addr} {pair_addr} {WORD_SIZE * 2}")
                load_tran.writeAction(f"sendr2_dmlm {pair_addr} {self.ev_word} {result_regs[i]} {result_regs[i+1]}")
                if self.debug_flag and self.print_level > 2:
                    load_tran.writeAction(f"print '[DEBUG][NWID %d] Store result value[{i}] = %d result value[{i+1}] = %d to addr = 0x%x' \
                        {'X0'} {result_regs[i]} {result_regs[i+1]} {pair_addr}")
        # Store the updated value back to the cache
        for i in range(self.cache_entry_size - 1):
            load_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + self.cache_base_offset}({key_lm_offset}) 0 8")
        # load_tran.writeAction(f"or {cached_key} {cache_key_mask} {cached_key}")
        if self.debug_flag and self.print_level > 2:
            load_tran.writeAction(f"print '[DEBUG][NWID %d] Store masked key = %d to addr = 0x%x' {'X0'} {masked_key} {key_lm_offset}")
        load_tran.writeAction(f"move {masked_key} {self.cache_base_offset - WORD_SIZE}({key_lm_offset}) 0 8")    # flip the highest bit indicating the value is written back
        load_tran.writeAction(f"yield")

        # load_tran.writeAction(f"{error_label}: print '[DEBUG][NWID %d] ERROR! loaded key=%d is not equal to the cached key=%d' {'X0'} {ld_key} {cached_key}")
        # load_tran.writeAction(f"yield")

        # Triggered when the write comes back from DRAM, finish the merge and store back the updated value
        store_ack_tran = self.kvmsr.state.writeTransition("eventCarry", self.kvmsr.state, self.kvmsr.state, self.store_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            store_ack_tran.writeAction(f"print ' '")
            store_ack_tran.writeAction(f"print '[DEBUG][NWID %d] Event <store_ack> ev_word = %d addr = 0x%x' {'X0'} {'EQT'} {'OB_0'}")
        store_ack_tran = self.msr_return(store_ack_tran, reduce_ret_ev_label, temp_val, operands=f"EQT {cached_key}")
        store_ack_tran.writeAction("yield")

        store_ack_more_tran = self.kvmsr.state.writeTransition("eventCarry", self.kvmsr.state, self.kvmsr.state, self.store_ack_more_ev_label)
        if self.debug_flag and self.print_level > 3:
            store_ack_more_tran.writeAction(f"print ' '")
            store_ack_more_tran.writeAction(f"print '[DEBUG][NWID %d] Event <store_ack_more> ev_word = %d addr = 0x%x' {'X0'} {'EQT'} {'OB_0'}")
        store_ack_more_tran.writeAction(f"yield")

        return
