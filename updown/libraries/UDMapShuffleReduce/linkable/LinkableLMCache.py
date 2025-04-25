from linker.EFAProgram import efaProgram, EFAProgram
from KVMSRMachineConfig import *
from LinkableKeyValueSetTPL import KeyValueSetInterface
from LinkableGlobalSync import Broadcast
from Macro import *
from typing import Callable
from enum import Enum

# Replace with custom config file for your application
from DefaultLinkableConfig import *

class LMCache():
    
    class Policy(Enum):
        WRITE_BACK = 0
        WRITE_THROUGH = 1
        
    def __init__(self, state: EFAProgram.State, identifier: str, cache_offset: int, num_entries: int, entry_size: int, data_store: KeyValueSetInterface, 
                 metadata_offset: int, policy: Policy = Policy.WRITE_THROUGH, combine_func: Callable = None, ival:int = -1, key_size: int = 1,
                 max_active_threads: int = 0, debug_flag: bool = False,  wf4k4_patch_flag: bool = False, cache_stats_flag: bool = False):
        
        '''
        Cache in scratchpad for atomic combine operation. The cache is organized as a set of lane-private cache segments. Each segment is a hash table with
        the size of num_entries. Each entry is of size entry_size. The key is the first key_size words of the entry, and the value is the remaining words.
        Parameters
            state:          Linkable EFA state.
            identifier:     String identifier for generating event label.
            cache_offset:   Per lane local cache base offset (Bytes offset relative to the local bank, limited to the 64KB bank size).
            num_entries:    Number of entries for each of lane-private cache segment.
            entry_size:     The size of each cache entry in words.
            data_store:     The key value set used to store the data.
            metadata_offset: Offset of the metadata in the scratchpad (Bytes). Reserve 16 words. 
            policy:         Cache policy, WRITE_BACK or WRITE_THROUGH.
            combine_func:   User defined combine operation. If not specified, the default combine operation is used.
            ival:           invalid value for invalid cache entry, default is -1(0xffffffffffffffff).
            key_size:       Size of the key in words, default is 1.
            max_active_threads: Maximum number of threads for the cache, default equals to num_entries.
            debug_flag:     Enable debug print (optional), default is False.
            cache_stats_flag: Enable cache statistics (optional), default is False.
        '''
        
        self.id     = identifier
        self.state  = state
        
        self.data_store = data_store
        self.combine_func = self.__combine_func if combine_func is None else combine_func

        self.cache_offset   = cache_offset
        self.cache_size     = num_entries
        self.off_imm_flag   = (self.cache_offset > 0 and self.cache_offset < MAX_MOV_IMM)
        
        self.cache_entry_size   = entry_size
        self.cache_entry_bsize  = entry_size << LOG2_WORD_SIZE
        self.key_size       = key_size
        self.value_size     = entry_size - key_size
        self.power_of_two_cache_size = int(log2(self.cache_size)) != log2(self.cache_size)
        self.power_of_two_entry_size = int(log2(self.cache_entry_size)) != log2(self.cache_entry_size)

        self.max_active_threads = max_active_threads if max_active_threads > 0 else num_entries
        
        self.policy         = policy
        
        self.hash_seed      = 13
        self.INACTIVE_MASK_SHIFT = 63
        self.INACTIVE_MASK  = (1 << self.INACTIVE_MASK_SHIFT)
        self.cache_ival     = ival | self.INACTIVE_MASK
        
        self.send_buffer_offset = metadata_offset
        self.SEND_BUFFER_SIZE   = 8
        self.nwid_mask_offset   = metadata_offset + (self.SEND_BUFFER_SIZE * WORD_SIZE)
        self.nwid_base_offset   = self.nwid_mask_offset + WORD_SIZE
        self.num_threads_offset  = self.nwid_base_offset + WORD_SIZE
        self.max_threads_offset  = self.num_threads_offset + WORD_SIZE
        self.data_store.setup_kvset(state, lm_offset=self.max_threads_offset + WORD_SIZE, send_buffer_offset=self.send_buffer_offset, debug_flag=debug_flag)
        
        self.debug_flag         = debug_flag
        self.print_level        = 4
        self.wf4k4_patch_flag   = wf4k4_patch_flag
        
        self.cache_stats_flag   = cache_stats_flag
        
        self.cache_broadcast = Broadcast(self.state, self.id, self.debug_flag)
        self.cache_broadcast.gen_broadcast()
        
        self.__gen_ev_labels()
        self.__gen_cache()
    
    def __gen_cache(self):
        self.__init_cache()
        if self.policy == LMCache.Policy.WRITE_BACK:
            self.__gen_wb_get()
            self.__gen_wb_combine_value()
            self.__gen_flush_cache()
        elif self.policy == LMCache.Policy.WRITE_THROUGH:
            self.__gen_get()
            self.__gen_combine()
            self.__gen_combine_value()
        else:
            raise Exception("Invalid cache policy")
        
    def __gen_ev_labels(self):
        
        self.cache_init_ev_label    = get_event_label(self.id, "cache_init")
        self.cache_flush_ev_label   = get_event_label(self.id, "cache_flush")
        self.get_ev_label           = get_event_label(self.id, "cache_get")
        self.combine_ev_label       = get_event_label(self.id, "cache_combine")
        self.combine_val_ev_label   = get_event_label(self.id, "cache_combine_value")
        
        self.__init_fin_ev_label    = get_event_label(self.id, "__cache_init_finish")
        self.__init_lane_ev_label   = get_event_label(self.id, "__cache_init_lane")
        
        self.__flush_lane_ev_label  = get_event_label(self.id, "__cache_flush_lane")
        self.__flush_ack_ev_label   = get_event_label(self.id, "__cache_flush_lane_ack")
        self.__flush_fin_ev_label   = get_event_label(self.id, "__cache_flush_ack")
        
        self.__get_ev_label         = get_event_label(self.id, "__cache_get")
        self.__get_ret_ev_label     = get_event_label(self.id, "__cache_get_return")
        self.__get_put_ack_ev_label   = get_event_label(self.id, "__cache_get_flush_ack")
        
        self.__combine_ev_label     = get_event_label(self.id, "__cache_combine")
        self.__comb_get_ev_label    = get_event_label(self.id, "__combine_get_return")
        self.__comb_put_ack_ev_label= get_event_label(self.id, "__combine_put_pair_ack")
        
        self.__combine_val_ev_label     = get_event_label(self.id, "__cache_combine_value")
        self.__comb_val_get_ev_label    = get_event_label(self.id, "__combine_value_get_return")
        self.__comb_val_put_ack_ev_label= get_event_label(self.id, "__combine_value_put_pair_ack")
        
    def __init_cache(self):
        
        
        '''
        Event:      Initialize the lane scratchpad cache.
        Operands:   X8:     number of lanes
                    X9~Xn:  data store metadata 
        Return:     X1: return event
        '''
        cache_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.cache_init_ev_label)
        
        num_lanes       = f"X8"
        saved_cont      = f"X{GP_REG_BASE}"
        send_buffer_ptr = f"X{GP_REG_BASE + 1}"
        init_ev_word    = f"X{GP_REG_BASE + 2}"
        init_ret_ev_word= f"X{GP_REG_BASE + 3}"
        ev_word         = f"X{GP_REG_BASE + 4}"
        temp_lm_ptr     = f"X{GP_REG_BASE + 5}"
        
        if self.debug_flag:
            cache_init_tran.writeAction(f"print ' '")
            cache_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.cache_init_ev_label}> ev_word=%ld' {'X0'} {'EQT'}")
        cache_init_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        cache_init_tran.writeAction(f"addi {'X2'} {init_ret_ev_word} 0")
        cache_init_tran.writeAction(f"evlb {init_ret_ev_word} {self.__init_fin_ev_label}")
        set_ev_label(cache_init_tran, ev_word, self.cache_broadcast.get_broadcast_ev_label(), new_thread = True)
        cache_init_tran.writeAction(f"addi {'X7'} {send_buffer_ptr} {self.send_buffer_offset}")
        cache_init_tran.writeAction(f"movrl {num_lanes} 0({send_buffer_ptr}) 0 8")
        cache_init_tran.writeAction(f"addi {'X2'} {init_ev_word} 0")
        cache_init_tran.writeAction(f"evlb {init_ev_word} {self.__init_lane_ev_label}")
        cache_init_tran.writeAction(f"movrl {init_ev_word} {WORD_SIZE}({send_buffer_ptr}) 0 8")
        cache_init_tran.writeAction(f"movrl {num_lanes}  {WORD_SIZE * 2}({send_buffer_ptr}) 0 8")
        cache_init_tran.writeAction(f"movrl {'X0'}  {WORD_SIZE * 3}({send_buffer_ptr}) 0 8")
        cache_init_tran.writeAction(f"addi {send_buffer_ptr} {temp_lm_ptr} {WORD_SIZE * 4}")
        cache_init_tran.writeAction(f"bcpyoli {'X9'} {temp_lm_ptr} {self.data_store.meta_data_size}")
        cache_init_tran.writeAction(f"send_wcont {ev_word} {init_ret_ev_word} {send_buffer_ptr} {self.SEND_BUFFER_SIZE}")
        cache_init_tran.writeAction(f"yield")
        
        
        '''
        Event:      Initialize lane scratchpad
        Operands:   X8: number of lanes
                    X9: base nwid
                    X10-Xn: data store metadata
        '''
        ln_cache_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.__init_lane_ev_label)

        cache_init_loop_label = "init_cache_loop"
        ival        = "X16"
        cache_base  = "X17"
        init_ctr    = "X18"
        num_entries = "X19"
        lm_addr     = "X20"
        nwid_mask   = "X21"
        
        if self.debug_flag and self.print_level > 5:
            ln_cache_init_tran.writeAction(f"print ' '")
            ln_cache_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <kvmsr_lane_sp_init> ev_word=%ld' {'X0'} {'EQT'}")
        ln_cache_init_tran.writeAction(f"addi {'X7'} {lm_addr} {self.nwid_mask_offset}")
        ln_cache_init_tran.writeAction(f"subi {'X8'} {nwid_mask} 1")
        ln_cache_init_tran.writeAction(f"movrl {nwid_mask} 0({lm_addr}) 0 8")
        ln_cache_init_tran.writeAction(f"addi {'X7'} {lm_addr} {self.nwid_base_offset}")
        ln_cache_init_tran.writeAction(f"movrl {'X9'} {0}({lm_addr}) 0 8")
        ln_cache_init_tran.writeAction(f"addi {'X7'} {lm_addr} {self.num_threads_offset}")
        ln_cache_init_tran.writeAction(f"movir {ival} 0")
        ln_cache_init_tran.writeAction(f"movrl {ival} {0}({lm_addr}) 0 8")
        ln_cache_init_tran.writeAction(f"addi {'X7'} {lm_addr} {self.max_threads_offset}")
        ln_cache_init_tran.writeAction(f"movir {ival} {self.max_active_threads}")
        ln_cache_init_tran.writeAction(f"movrl {ival} {0}({lm_addr}) 0 8")
        ln_cache_init_tran.writeAction(f"addi {'X7'} {lm_addr} {self.data_store.meta_data_offset}")
        ln_cache_init_tran.writeAction(f"bcpyoli {'X10'} {lm_addr} {self.data_store.meta_data_size}")
        ln_cache_init_tran.writeAction(f"movir {ival} {self.cache_ival}")
        ln_cache_init_tran.writeAction(f"movir {num_entries} {self.cache_size}")
        ln_cache_init_tran.writeAction(f"addi {'X7'} {cache_base} {self.cache_offset}")
        if self.debug_flag and self.print_level > 5:
            ln_cache_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Initialize scratchpad cache base addr = %ld(0x%lx) " + 
                                           f"initial value = %ld' {'X0'} {cache_base} {cache_base} {ival}")
        ln_cache_init_tran.writeAction(f"mov_imm2reg {init_ctr} 0")
        ln_cache_init_tran.writeAction(f"{cache_init_loop_label}: movwrl {ival} {cache_base}({init_ctr},1,{int(log2(self.cache_entry_size))})")
        ln_cache_init_tran.writeAction(f"blt {init_ctr} {num_entries} {cache_init_loop_label}")
        ln_cache_init_tran.writeAction(f"sendr_reply X0 X16 X17")
        ln_cache_init_tran.writeAction("yield_terminate")
        
        '''
        Event:      Broadcast finish.
        '''
        cache_init_fin_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__init_fin_ev_label)
        cache_init_fin_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {num_lanes} {cache_base}")
        cache_init_fin_tran.writeAction(f"yieldt")

    def __gen_get(self):
        
        '''
        Atomic operation using scratchpad. First check if the newest value is cached or is being read (not coming back yet).
        If either, the update will be merged locally based on the user-defined merge function. When the data is ready, it will apply the accumulated 
        update(s), stores the data back to DRAM, and frees the hash table entry. If there's a hash conflict, the update will be postponed
        (i.e. append to the end of the event queue) until the event is popped up and the entry is freed.
        '''
        
        get_tran        = self.state.writeTransition("eventCarry", self.state, self.state, self.get_ev_label)
        
        __get_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_ev_label)
        
        __get_ret_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_ret_ev_label)
        
        key         = [f'X{OB_REG_BASE + i}' for i in range(self.key_size)]
        value_ops   = [f'X{OB_REG_BASE + self.key_size + n}' for n in range(self.value_size)]
        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        
        nwid_mask_addr = regs[0]
        num_lanes_mask = regs[1]
        dest_nwid   = regs[2]
        base_nwid   = regs[3]
        ev_word     = regs[-1]
        if self.debug_flag:
            get_tran.writeAction(f"print ' '")
            get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.get_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        get_tran.writeAction(f"addi {'X7'} {nwid_mask_addr} {self.nwid_mask_offset}")
        get_tran.writeAction(f"movlr {0}({nwid_mask_addr}) {num_lanes_mask} 0 8")
        get_tran.writeAction(f"movlr  {self.nwid_base_offset - self.nwid_mask_offset}({nwid_mask_addr}) {base_nwid} 0 8")
        self.__get_cache_loc(get_tran, key, num_lanes_mask, base_nwid, dest_nwid)
        if self.debug_flag:
            get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Send key = [{' '.join([ f'%ld' for _ in range(self.key_size)])}] to lane %ld' {'X0'} {' '.join(key)} {dest_nwid}")
        set_ev_label(get_tran, ev_word, self.__get_ev_label, new_thread = True)
        get_tran.writeAction(f"ev {ev_word}  {ev_word}  {dest_nwid} {dest_nwid} {8}")
        get_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key[0]} {2}")
        get_tran.writeAction(f"yieldt")

        key_lm_addr = regs[0]
        cached_key  = regs[1]
        buffer_addr = regs[2]
        masked_key  = regs[3]
        saved_cont  = regs[4]
        results = [regs[5+i] for i in range(self.value_size)]
        scratch = [regs[5+i+self.value_size] for i in range(3)]
        ev_word = regs[-1]

        wait_update_label   = "cache_active_miss"
        cache_hit_label     = "cache_get_hit"
        cache_miss_label    = "cache_get_miss"
        get_fail_label      = "error"

        key = key[0]
        '''
        Event:      Check if the scratchpad caches the value. If so, combine the incoming values with the cached values. If not, retrieve it from output key-value set.
        Operands:   X8: Key
        Return:     X1: return event
                    X8: Flag, -1 if get fails, otherwise equals to key
                    X9 ~ Xn: Values if get succeeds, otherwise returns key
        '''
        if self.debug_flag:
            __get_tran.writeAction(f"print ' '")
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Event <{self.__get_ev_label}> key = %ld cont = %lu' {'X0'} {key} {'X1'}")
        # check if the local scratchpad caches the value for the input key.
        # __get_tran.writeAction(f"movir {masked_key} {self.hash_seed}")
        # __get_tran.writeAction(f"hash {key} {masked_key}")
        if self.power_of_two_cache_size:
            __get_tran.writeAction(f"andi {key} {masked_key} {self.cache_size - 1}")
        else:
            __get_tran.writeAction(f"movir {scratch[0]} {self.cache_size}")
            __get_tran.writeAction(f"mod {key} {scratch[0]} {masked_key}")
        if self.power_of_two_entry_size:
            __get_tran.writeAction(f"sli {masked_key} {key_lm_addr} {int(log2(self.cache_entry_bsize))}")
        else:
            __get_tran.writeAction(f"muli {masked_key} {key_lm_addr} {self.cache_entry_bsize}")
        __get_tran.writeAction(f"add {'X7'} {key_lm_addr} {key_lm_addr}")
        if self.off_imm_flag:
            __get_tran.writeAction(f"move {self.cache_offset}({key_lm_addr}) {cached_key} 0 8")
        else:
            __get_tran.writeAction(f"addi {key_lm_addr} {key_lm_addr} {self.cache_offset}")
            __get_tran.writeAction(f"move {0}({key_lm_addr}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Get incoming key = %ld Cached key = %ld " + 
                                   f"at cache index %ld lm_addr = %lu(0x%lx)' {'X0'} {key} {cached_key} {masked_key} {key_lm_addr}")
        __get_tran.writeAction(f"beq {cached_key} {key} {wait_update_label}")
        __get_tran.writeAction(f"movir {masked_key} {1}")
        __get_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        __get_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 4:
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Masked key = %lu(0x%lx)' {'X0'} {masked_key} {masked_key}")
        __get_tran.writeAction(f"beq {masked_key} {cached_key} {cache_hit_label}")
        # If not, check if the data cached has been written back to DRAM. If so, evict the current entry.
        __get_tran.writeAction(f"rshift {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        __get_tran.writeAction(f"beqi {scratch[0]} 1 {cache_miss_label}")

        # Pending for an unmerged update to the values with the same key
        __get_tran.writeAction(f"{wait_update_label}: evi {'X2'} {ev_word} {NEW_THREAD_ID} {0b0100}")
        __get_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key} {self.key_size if self.key_size > 1 else 2}")
        if self.debug_flag and self.print_level > 2:
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Cache get miss key = %ld, " + 
                                   f"cache entry occupied/pending on an update.' {'X0'} {key}")
        __get_tran.writeAction(f"yieldt")

        # The value is cached in the scratchpad, return the newest value
        __get_tran.writeAction(f"{cache_hit_label}: move {key} {(self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            for i in range(self.value_size):
                __get_tran.writeAction(f"move {WORD_SIZE * (i+1) + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) {results[i]} 0 8")
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Cache hit key = %ld, cached values = " + 
                                   f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {key} {' '.join(results)}")
        # Return the cached value
        __get_tran.writeAction(f"addi {key_lm_addr} {key_lm_addr} {self.cache_offset if self.off_imm_flag else 0}")
        set_ignore_cont(__get_tran, ev_word)
        __get_tran.writeAction(f"send_wcont {'X1'} {ev_word} {key_lm_addr} {self.cache_entry_size}")
        __get_tran.writeAction(f"move {masked_key} {0}({key_lm_addr}) 0 8")
        __get_tran.writeAction("yieldt")

        # Cache miss, retrieve the current value.
        if self.debug_flag and self.print_level > 2:
            __get_tran.writeAction(f"{cache_miss_label}: print '[DEBUG][NWID %ld][{self.__get_ev_label}] Cache miss. Get values for key = %ld' {'X0'} {key}")
            set_ev_label(__get_tran, ev_word, self.__get_ret_ev_label)
        else:
            set_ev_label(__get_tran, ev_word, self.__get_ret_ev_label, label=cache_miss_label)
        __get_tran = self.data_store.get_pair(tran=__get_tran, cont_evw=ev_word, key=key, regs=scratch)
        __get_tran.writeAction(f"addi {key} {cached_key} 0")
        __get_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        __get_tran.writeAction(f"yield")

        '''
        Event:      Get pair returns.
        Operands:   X8 ~ Xn: Values retrieved.
        '''
        get_pair_ops = self.data_store.get_pair_ops()
        cache_occupied_label = "cache_occupied"
        
        __get_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_ret_ev_label)
        if self.debug_flag and self.print_level > 2:
            __get_ret_tran.writeAction(f"print ' '")
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Event word = %lu get key = %ld return ops = " + 
                                     f"[{' '.join(['%ld, ' for _ in range(len(get_pair_ops))])}]' {'X0'} {'EQT'} {cached_key} {' '.join(get_pair_ops)}")
        # Check if the get is successful (i.e., if the value corresponding to the key exists)
        self.data_store.check_get_pair(__get_ret_tran, cached_key, get_pair_ops, get_fail_label)
        
        # Store the returned values
        ld_values = self.data_store.get_pair_value_ops()
        if self.debug_flag and self.print_level > 2:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Get pair success, return values = [{''.join(['%ld, ' for _ in range(len(ld_values))])}]' \
                {'X0'} {' '.join(ld_values)}")
        __get_ret_tran.writeAction(f"movlr {(self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) {scratch[0]} 0 8")
        __get_ret_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        __get_ret_tran.writeAction(f"bnei {scratch[0]} 1 {cache_occupied_label}")
        # Store the value to the cache
        __get_ret_tran.writeAction(f"addi {key_lm_addr} {key_lm_addr} {self.cache_offset if self.off_imm_flag else 0}")
        for i in range(self.value_size):
            __get_ret_tran.writeAction(f"move {ld_values[i]} {WORD_SIZE * (i+1)}({key_lm_addr}) 0 8")
        __get_ret_tran.writeAction(f"movrl {cached_key} {0}({key_lm_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Store masked key = %lu(0x%lx) to addr = 0x%lx' {'X0'} {masked_key} {masked_key} {key_lm_addr}")
        set_ignore_cont(__get_ret_tran, ev_word)
        __get_ret_tran.writeAction(f"send_wcont {saved_cont} {ev_word} {key_lm_addr} {self.cache_entry_size}")
        __get_ret_tran.writeAction(f"move {masked_key} {0}({key_lm_addr}) 0 8")
        __get_ret_tran.writeAction(f"yieldt")
        
        __get_ret_tran.writeAction(f"{cache_occupied_label}: addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        __get_ret_tran.writeAction(f"movrl {cached_key} {0}({buffer_addr}) 0 8")
        for i in range(self.value_size):
            __get_ret_tran.writeAction(f"move {ld_values[i]} {WORD_SIZE * (i+1)}({buffer_addr}) 0 8")
        set_ignore_cont(__get_ret_tran, ev_word)
        __get_ret_tran.writeAction(f"send_wcont {saved_cont} {ev_word} {buffer_addr} {self.cache_entry_size}")
        __get_ret_tran.writeAction(f"yieldt")
            
        
        # Key not exist. Return failure.
        __get_ret_tran.writeAction(f"{get_fail_label}: movir {scratch[0]} {self.cache_ival}")
        set_ignore_cont(__get_ret_tran, ev_word)
        __get_ret_tran.writeAction(f"sendr_wcont {saved_cont} {ev_word} {scratch[0]} {cached_key}")
        if self.debug_flag:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Key = %ld not exist, return failure.' {'X0'} {cached_key}")
        __get_ret_tran.writeAction(f"yieldt")
        
        return
    
    
    def __gen_combine(self):
        
        '''
        Atomic operation using scratchpad. First check if the newest value is cached or is being read (not coming back yet).
        If either, the update will be merged locally based on the user-defined merge function. When the data is ready, it will apply the accumulated 
        update(s), stores the data back to DRAM, and frees the hash table entry. If there's a hash conflict, the update will be postponed
        (i.e. append to the end of the event queue) until the event is popped up and the entry is freed.
        '''
        
        combine_tran            = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_ev_label)
        
        __combine_tran          = self.state.writeTransition("eventCarry", self.state, self.state, self.__combine_ev_label)
        
        __combine_get_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_get_ev_label)
        
        __combine_put_ack_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_put_ack_ev_label)

        key     = [f'X{OB_REG_BASE + i}' for i in range(self.key_size)]
        values  = [f'X{OB_REG_BASE + self.key_size + n}' for n in range(self.value_size)]

        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        
        nwid_mask_addr = regs[0]
        num_lanes_mask = regs[1]
        dest_nwid   = regs[2]
        base_nwid   = regs[3]
        ev_word     = regs[-1]
        if self.debug_flag:
            combine_tran.writeAction(f"print ' '")
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_ev_label}] Event <{self.combine_ev_label}> ev_word = %lu key = " + 
                                   f"[{' '.join([ f'%ld' for _ in range(self.key_size)])}], cont = %lu' {'X0'} {'EQT'} {' '.join(key)} {'X1'}")
        combine_tran.writeAction(f"addi {'X7'} {nwid_mask_addr} {self.nwid_mask_offset}")
        combine_tran.writeAction(f"movlr {0}({nwid_mask_addr}) {num_lanes_mask} 0 8")
        combine_tran.writeAction(f"movlr {self.nwid_base_offset - self.nwid_mask_offset}({nwid_mask_addr}) {base_nwid} 0 8")
        self.__get_cache_loc(combine_tran, key, num_lanes_mask, base_nwid, dest_nwid)
        if self.debug_flag:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_ev_label}] Send key = [{' '.join([ f'%ld' for _ in range(self.key_size)])}] values = " + 
                                 f"[{' '.join([ f'%ld' for _ in range(self.value_size)])}] to lane %ld' {'X0'} {' '.join(key)} {' '.join(values)} {dest_nwid}")
        set_ev_label(combine_tran, ev_word, self.__combine_ev_label, new_thread = True)
        combine_tran.writeAction(f"ev {ev_word}  {ev_word}  {dest_nwid} {dest_nwid} 8")
        combine_tran.writeAction(f"sendops_wcont {ev_word} EQT {key[0]} {self.cache_entry_size}")
        combine_tran.writeAction(f"yieldt")

        key = key[0]
        key_lm_addr = regs[0]
        cached_key  = regs[1]
        buffer_addr = regs[2]
        masked_key  = regs[3]
        saved_cont  = regs[4]
        ev_word     = regs[5]
        cached_values   = [regs[6+i] for i in range(self.value_size)]
        result_regs     = [regs[6+i] for i in range(self.value_size)]
        scratch = [regs[6+i+self.value_size] for i in range(2)]

        cache_active_hit_label = "cache_active_hit"
        cache_hit_label     = "cache_hit"
        cache_evict_label   = "cache_evict"
        get_fail_label      = "get_fail"
        combine_fail_label  = "combine_fail"

        '''
        Event:      Check if the scratchpad caches the value. 
                    If so, combine the incoming values with the cached values. 
                    If not, retrieve the latest values.
        Operands:   X8: Key
                    X9 ~ Xn: Values
        Return:     X1: return event
                    X8: Flag, -1 if fails, otherwise equals to key
                    X9: key
        '''
        if self.debug_flag:
            __combine_tran.writeAction(f"print ' '")
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.__combine_ev_label}> key = %ld, " + 
                                     f"values = {' '.join(['%ld' for _ in range(self.value_size)])}' {'X0'} {key} {' '.join(values)}")
        # check if the local scratchpad stores the value or a pending update for the input key.
        # __combine_tran.writeAction(f"movir {masked_key} {self.hash_seed}")
        # __combine_tran.writeAction(f"hash {key} {masked_key}")
        if self.power_of_two_cache_size:
            __combine_tran.writeAction(f"andi {key} {masked_key} {self.cache_size - 1}")
        else:
            __combine_tran.writeAction(f"movir {scratch[0]} {self.cache_size}")
            __combine_tran.writeAction(f"mod {key} {scratch[0]} {masked_key}")
        __combine_tran.writeAction(f"sli {masked_key} {key_lm_addr} {int(log2(self.cache_entry_bsize))}")
        __combine_tran.writeAction(f"add {'X7'} {key_lm_addr} {key_lm_addr}")
        if self.off_imm_flag:
            __combine_tran.writeAction(f"move {self.cache_offset}({key_lm_addr}) {cached_key} 0 8")
        else:
            __combine_tran.writeAction(f"addi {key_lm_addr} {key_lm_addr} {self.cache_offset}")
            __combine_tran.writeAction(f"move {0}({key_lm_addr}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Merge incoming key = %ld Cached key = %ld at cache index %ld " + 
                                     f"lm_addr = %lu(0x%lx)' {'X0'} {key} {cached_key} {masked_key} {key_lm_addr}")
        # Check if the cached key matches the incoming key
        __combine_tran.writeAction(f"beq {cached_key} {key} {cache_active_hit_label}")
        __combine_tran.writeAction(f"movir {masked_key} {1}")
        __combine_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        __combine_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 4:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Masked key = %lu(0x%lx)' {'X0'} {masked_key} {masked_key}")
        __combine_tran.writeAction(f"beq {masked_key} {cached_key} {cache_hit_label}")
        # If not, check if the data cached has been written back. If so, evict the current entry.
        __combine_tran.writeAction(f"rshift {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        __combine_tran.writeAction(f"beqi {scratch[0]} 1 {cache_evict_label}")

        # If all conditions failed, the entry is occupied and cannot be evicted for now, push the event back to the queue.
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"sli {cached_key} {scratch[1]} {1}")
            __combine_tran.writeAction(f"sri {scratch[1]} {scratch[1]} {1}")
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Cache entry occupied by key = %lu, push back to queue key = %ld values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {scratch[1]} {key} {' '.join(values)}")
        __combine_tran.writeAction(f"evi {'X2'} {ev_word} {NEW_THREAD_ID} {0b0100}")
        __combine_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key} {self.cache_entry_size}")
        __combine_tran.writeAction(f"yieldt")

        # Still waiting for a previous get return, merge locally
        __combine_tran.writeAction(f"{cache_active_hit_label}: move {WORD_SIZE + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) {cached_values[0]} 1 8")
        for i in range(self.value_size - 1):
            __combine_tran.writeAction(f"move {WORD_SIZE * (i+1) + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) {cached_values[i+1]} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Cache active hit key = %ld, cached values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {key} {' '.join(cached_values)}")
        self.combine_func(__combine_tran, key, values, cached_values, result_regs, scratch, combine_fail_label, cache_active_hit_label)
        for i in range(self.value_size):
            __combine_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Store key = %ld result values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(result_regs)}")
        __combine_tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {key} {key}")
        __combine_tran.writeAction(f"yieldt")

        # The value is cached in the scratchpad, merge and immediate write back the newest value (write through policy)
        __combine_tran.writeAction(f"{cache_hit_label}: move {WORD_SIZE + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) {cached_values[0]} 1 8")
        for i in range(self.value_size - 1):
            __combine_tran.writeAction(f"move {WORD_SIZE * (i+1) + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) {cached_values[i+1]} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Cache hit key = %ld, cached values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {key} {' '.join(cached_values)}")
        self.combine_func(__combine_tran, key, values, cached_values, result_regs, scratch, combine_fail_label, cache_hit_label)
        # Store back the updated values 
        set_ev_label(__combine_tran, ev_word, self.__comb_put_ack_ev_label)
        __combine_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        if self.debug_flag:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Put key = %ld values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {key} {' '.join(result_regs)}")
        self.data_store.put_pair(__combine_tran, ev_word, key, result_regs, buffer_addr, scratch)
        for i in range(self.value_size):
            __combine_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) 0 8")
        __combine_tran.writeAction(f"addi {key} {cached_key} 0")
        __combine_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        __combine_tran.writeAction("yield")

        # Current entry has been written back, (i.e., can be evicted). Insert the new entry.
        __combine_tran.writeAction(f"{cache_evict_label}: move {key} {(self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) 1 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Cache miss evict old entry %lu. Get value for key = %ld' {'X0'} {cached_key} {key}")
        # Retrieve the current value.
        set_ev_label(__combine_tran, ev_word, self.__comb_get_ev_label)
        __combine_tran = self.data_store.get_pair(tran=__combine_tran, cont_evw=ev_word, key=key, regs=scratch)
        # Store the new entry to the cache
        for i in range(self.value_size):
            __combine_tran.writeAction(f"move {values[i]} {WORD_SIZE * i + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) 0 8")
        __combine_tran.writeAction(f"addi {key} {cached_key} 0")
        __combine_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        __combine_tran.writeAction(f"yield")
        
        __combine_tran.writeAction(f"{combine_fail_label}: movir {scratch[0]} {self.cache_ival}")
        __combine_tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {scratch[0]} {key}")
        if self.debug_flag:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Combine fail key = %ld, cached values [{' '.join(['%ld' for _ in range(self.value_size)])}] update value = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}] return failure.' {'X0'} {key} {' '.join(cached_values)} {' '.join(values)}")
        __combine_tran.writeAction(f"yieldt")

        '''
        Event:      Get pair returns, merge with cached values.
        Operands:   X8 ~ Xn: Values retrieved.
        '''
        # Value is retrieved and ready for merging with the (accumulated) updates
        get_pair_ops = self.data_store.get_pair_ops()
        __combine_get_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_get_ev_label)
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print ' '")
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Event word = %lu Cached key = %ld return ops = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(len(get_pair_ops))])}]' {'X0'} {'EQT'} {cached_key} {' '.join(get_pair_ops)}")
        # Read the accumulated cached value 
        for i in range(self.value_size):
            __combine_get_tran.writeAction(f"move {WORD_SIZE * i + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) {cached_values[i]} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Cached key = %ld values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(cached_values)} ")

        # Check if the get is successful
        self.data_store.check_get_pair(__combine_get_tran, cached_key, get_pair_ops, get_fail_label)
        
        # Load the cached value
        ld_values = self.data_store.get_pair_value_ops()
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Get pair success, return values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(ld_values))])}]' {'X0'} {' '.join(ld_values)}")
        # Apply the accumulated updates based on user-defined reduce funtion
        self.combine_func(__combine_get_tran, cached_key, cached_values, ld_values, result_regs, scratch, combine_fail_label, cache_evict_label)
        # Store back the updated values 
        set_ev_label(__combine_get_tran, ev_word, self.__comb_put_ack_ev_label)
        __combine_get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Put key = %ld values = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(result_regs)}")
        self.data_store.put_pair(__combine_get_tran, ev_word, cached_key, result_regs, buffer_addr, scratch)
        # Store the updated value back to the cache
        for i in range(self.value_size):
            __combine_get_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i + (self.cache_offset if self.off_imm_flag else 0)}({key_lm_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Store masked key = %lu(0x%lx) to addr = 0x%lx' " + 
                                         f"{'X0'} {masked_key} {masked_key} {key_lm_addr}")
        __combine_get_tran.writeAction(f"move {masked_key} {(self.cache_offset if self.off_imm_flag else 0) - WORD_SIZE}({key_lm_addr}) 0 8")
        __combine_get_tran.writeAction(f"yield")
        
        # Key not exist store the incoming value.
        set_ev_label(__combine_get_tran, ev_word, self.__comb_put_ack_ev_label, label=get_fail_label)
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Key not exist store the incoming value: " + 
                                         f"key = %ld values = {' '.join(['%ld' for _ in range(self.value_size)])}' {'X0'} {cached_key} {' '.join(cached_values)}")
        __combine_get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        self.data_store.put_pair(__combine_get_tran, ev_word, cached_key, cached_values, buffer_addr, scratch)
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Put key = %ld values = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(cached_values)}")
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_get_ev_label}] Store masked key = %lu(0x%lx) to addr = " + 
                                         f"0x%lx' {'X0'} {masked_key} {masked_key} {key_lm_addr}")
        __combine_get_tran.writeAction(f"move {masked_key} {(self.cache_offset if self.off_imm_flag else 0) - WORD_SIZE}({key_lm_addr}) 0 8")
        __combine_get_tran.writeAction(f"yield")
        
        __combine_get_tran.writeAction(f"{combine_fail_label}: movir {scratch[0]} {self.cache_ival}")
        __combine_get_tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {scratch[0]} {cached_key}")
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Combine fail key = %ld, loaded values [{' '.join(['%ld' for _ in range(self.value_size)])}] update values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}] return failure.' {'X0'} {key} {' '.join(ld_values)} {' '.join(cached_values)}")
        __combine_get_tran.writeAction(f"yieldt")
        
        '''
        Event:      Put pair ack, return to user passed in continuation.
        Operands:   X8: status
        '''
        put_pair_ops = self.data_store.put_pair_ops()
        __combine_put_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_put_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            __combine_put_ack_tran.writeAction(f"print ' '")
            __combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_put_ack_ev_label}] Event word = %lu put pair key = %ld return " + 
                                             f"operands = [{''.join(['%lu, ' for _ in range(len(put_pair_ops))])}]' {'X0'} {'EQT'} {cached_key} {' '.join(put_pair_ops)}")
        __combine_put_ack_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {cached_key} {cached_key} ")
        __combine_put_ack_tran.writeAction("yieldt")

        return
    
    def __gen_combine_value(self):
        
        '''
        Atomic operation using scratchpad. Similar to combine but only merge when the latest value is available.
        Return the value after combine to the user continuation. 
        '''
        
        combine_tran            = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_val_ev_label)
        
        __combine_tran          = self.state.writeTransition("eventCarry", self.state, self.state, self.__combine_val_ev_label)
        
        __combine_get_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_get_ev_label)
        
        __combine_put_ack_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_put_ack_ev_label)

        key     = [f'X{OB_REG_BASE + i}' for i in range(self.key_size)]
        values  = [f'X{OB_REG_BASE + self.key_size + n}' for n in range(self.value_size)]

        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        
        nwid_mask_addr = regs[0]
        num_lanes_mask = regs[1]
        dest_nwid   = regs[2]
        base_nwid   = regs[3]
        ev_word     = regs[-1]
        if self.debug_flag:
            combine_tran.writeAction(f"print ' '")
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_val_ev_label}] Event <{self.combine_val_ev_label}> ev_word = %lu key = " + 
                                   f"[{' '.join([ f'%ld' for _ in range(self.key_size)])}], cont = %lu' {'X0'} {'EQT'} {' '.join(key)} {'X1'}")
        combine_tran.writeAction(f"addi {'X7'} {nwid_mask_addr} {self.nwid_mask_offset}")
        combine_tran.writeAction(f"movlr {0}({nwid_mask_addr}) {num_lanes_mask} 0 8")
        combine_tran.writeAction(f"movlr {self.nwid_base_offset - self.nwid_mask_offset}({nwid_mask_addr}) {base_nwid} 0 8")
        self.__get_cache_loc(combine_tran, key, num_lanes_mask, base_nwid, dest_nwid)
        if self.debug_flag:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_val_ev_label}] Send key = [{' '.join([ f'%ld' for _ in range(self.key_size)])}] values = " + 
                                 f"[{' '.join([ f'%ld' for _ in range(self.value_size)])}] to lane %ld' {'X0'} {' '.join(key)} {' '.join(values)} {dest_nwid}")
        set_ev_label(combine_tran, ev_word, self.__combine_val_ev_label, new_thread = True)
        combine_tran.writeAction(f"ev {ev_word}  {ev_word}  {dest_nwid} {dest_nwid} 8")
        combine_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key[0]} {self.cache_entry_size}")
        combine_tran.writeAction(f"yieldt")

        key = key[0]
        key_lm_addr = regs[0]
        cached_key  = regs[1]
        buffer_addr = regs[2]
        masked_key  = regs[3]
        saved_cont  = regs[4]
        ev_word     = regs[5]
        cached_values   = [regs[6+i] for i in range(self.value_size)]
        result_regs     = [regs[6+i] for i in range(self.value_size)]
        scratch = [regs[6+i+self.value_size] for i in range(2)]

        pending_value_label = "pending_value"
        cache_hit_label     = "cache_hit"
        cache_evict_label   = "cache_evict"
        get_fail_label      = "get_fail"
        combine_fail_label  = "combine_fail"

        '''
        Event:      Check if the scratchpad caches the value. 
                    If so, combine the incoming values with the cached values. 
                    If not, retrieve the latest values.
        Operands:   X8: Key
                    X9 ~ Xn: Values
        Return:     X1: return event
                    X8: Flag, -1 if fails, otherwise equals to key
                    X9: Values after combine
        '''
        if self.debug_flag:
            __combine_tran.writeAction(f"print ' '")
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Event <{self.__combine_val_ev_label}> key = %ld, " + 
                                     f"values = {' '.join(['%ld' for _ in range(self.value_size)])}' {'X0'} {key} {' '.join(values)}")
        # check if the local scratchpad stores the value or a pending update for the input key.
        # __combine_tran.writeAction(f"movir {masked_key} {self.hash_seed}")
        # __combine_tran.writeAction(f"hash {key} {masked_key}")
        if self.power_of_two_cache_size:
            __combine_tran.writeAction(f"andi {key} {masked_key} {self.cache_size - 1}")
        else:
            __combine_tran.writeAction(f"movir {scratch[0]} {self.cache_size}")
            __combine_tran.writeAction(f"mod {key} {scratch[0]} {masked_key}")
        __combine_tran.writeAction(f"sli {masked_key} {key_lm_addr} {int(log2(self.cache_entry_bsize))}")
        __combine_tran.writeAction(f"add {'X7'} {key_lm_addr} {key_lm_addr}")
        __combine_tran.writeAction(f"addi {key_lm_addr} {key_lm_addr} {self.cache_offset}")
        __combine_tran.writeAction(f"move {0}({key_lm_addr}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Merge incoming key = %ld Cached key = %ld at cache index %ld " + 
                                     f"lm_addr = %lu(0x%lx)' {'X0'} {key} {cached_key} {masked_key} {key_lm_addr}")
        # Check if the cached key matches the incoming key
        # __combine_tran.writeAction(f"beq {cached_key} {key} {pending_value_label}")
        __combine_tran.writeAction(f"movir {masked_key} {1}")
        __combine_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        __combine_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 4:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Masked key = %lu(0x%lx)' {'X0'} {masked_key} {masked_key}")
        __combine_tran.writeAction(f"beq {masked_key} {cached_key} {cache_hit_label}")
        # If not, check if the data cached has been written back. If so, evict the current entry.
        __combine_tran.writeAction(f"rshift {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        __combine_tran.writeAction(f"beqi {scratch[0]} 1 {cache_evict_label}")

        # If all conditions failed, the entry is occupied and cannot be evicted for now, push the event back to the queue.
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"sli {cached_key} {scratch[1]} {1}")
            __combine_tran.writeAction(f"sri {scratch[1]} {scratch[1]} {1}")
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Cache entry occupied by key = %lu (cached=%lu), push back to queue key = %ld values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {scratch[1]} {cached_key} {key} {' '.join(values)}")
        __combine_tran.writeAction(f"evi {'X2'} {ev_word} {NEW_THREAD_ID} {0b0100}")
        __combine_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key} {self.cache_entry_size}")
        __combine_tran.writeAction(f"yieldt")

        # The value is cached in the scratchpad, merge and immediate write back the newest value (write through policy)
        __combine_tran.writeAction(f"{cache_hit_label}: move {WORD_SIZE}({key_lm_addr}) {cached_values[0]} 1 8")
        for i in range(self.value_size - 1):
            __combine_tran.writeAction(f"move {WORD_SIZE * (i+1)}({key_lm_addr}) {cached_values[i+1]} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Cache hit key = %ld, cached values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {key} {' '.join(cached_values)}")
        self.combine_func(__combine_tran, key, values, cached_values, result_regs, scratch, combine_fail_label, cache_hit_label)
        # Store back the updated values 
        set_ev_label(__combine_tran, ev_word, self.__comb_val_put_ack_ev_label, new_thread=True)
        __combine_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        if self.debug_flag:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Put key = %ld values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {key} {' '.join(result_regs)}")
        self.data_store.put_pair(__combine_tran, ev_word, key, result_regs, buffer_addr, scratch)
        for i in range(self.value_size):
            __combine_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_addr}) 0 8")
        __combine_tran.writeAction(f"subi {key_lm_addr} {key_lm_addr} {WORD_SIZE}")
        __combine_tran.writeAction(f"movrl {key} {0}({key_lm_addr}) 0 8")
        __combine_tran.writeAction(f"send_reply {key_lm_addr} {self.cache_entry_size} {scratch[0]}")
        __combine_tran.writeAction(f"movrl {masked_key} {0}({key_lm_addr}) 0 8")
        __combine_tran.writeAction("yieldt")

        # Current entry has been written back, (i.e., can be evicted). Insert the new entry.
        __combine_tran.writeAction(f"{cache_evict_label}: move {key} {0}({key_lm_addr}) 1 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Cache miss evict key = %lu. Get key = %ld value' {'X0'} {cached_key} {key}")
        # Retrieve the current value.
        set_ev_label(__combine_tran, ev_word, self.__comb_val_get_ev_label)
        __combine_tran = self.data_store.get_pair(tran=__combine_tran, cont_evw=ev_word, key=key, regs=scratch)
        # Store the new entry to the cache
        for i in range(self.value_size):
            __combine_tran.writeAction(f"move {values[i]} {WORD_SIZE * i}({key_lm_addr}) 0 8")
        __combine_tran.writeAction(f"addi {key} {cached_key} 0")
        __combine_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        __combine_tran.writeAction(f"yield")
        
        __combine_tran.writeAction(f"{combine_fail_label}: movir {scratch[0]} {self.cache_ival}")
        __combine_tran.writeAction(f"sendr_reply {scratch[0]} {key} {scratch[1]}")
        if self.debug_flag:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Combine fail key = %ld, cached values [{' '.join(['%ld' for _ in range(self.value_size)])}] update value = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}] return failure.' {'X0'} {key} {' '.join(cached_values)} {' '.join(values)}")
        __combine_tran.writeAction(f"yieldt")

        '''
        Event:      Get pair returns, merge with cached values.
        Operands:   X8 ~ Xn: Values retrieved.
        '''
        # Value is retrieved and ready for merging with the (accumulated) updates
        get_pair_ops = self.data_store.get_pair_ops()
        __combine_get_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_get_ev_label)
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print ' '")
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Event word = %lu Cached key = %ld return ops = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(len(get_pair_ops))])}]' {'X0'} {'EQT'} {cached_key} {' '.join(get_pair_ops)}")
        # Read the accumulated cached value 
        for i in range(self.value_size):
            __combine_get_tran.writeAction(f"move {WORD_SIZE * i}({key_lm_addr}) {cached_values[i]} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Cached key = %ld values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(cached_values)} ")

        # Check if the get is successful
        self.data_store.check_get_pair(__combine_get_tran, cached_key, get_pair_ops, get_fail_label)
        
        # Load the cached value
        ld_values = self.data_store.get_pair_value_ops()
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Get key = %ld success, return values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(ld_values))])}]' {'X0'} {cached_key} {' '.join(ld_values)}")
        # Apply the accumulated updates based on user-defined reduce funtion
        self.combine_func(__combine_get_tran, cached_key, cached_values, ld_values, result_regs, scratch, combine_fail_label, cache_evict_label)
        # Store back the updated values 
        set_ev_label(__combine_get_tran, ev_word, self.__comb_val_put_ack_ev_label, new_thread=True)
        __combine_get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Put key = %ld (masked_key = %lu) values = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {masked_key} {' '.join(result_regs)}")
        self.data_store.put_pair(__combine_get_tran, ev_word, cached_key, result_regs, buffer_addr, scratch)
        # Store the updated value back to the cache
        for i in range(self.value_size):
            __combine_get_tran.writeAction(f"move {result_regs[i]} {WORD_SIZE * i}({key_lm_addr}) 0 8")
        __combine_get_tran.writeAction(f"subi {key_lm_addr} {key_lm_addr} {WORD_SIZE}")
        set_ignore_cont(__combine_get_tran, ev_word)
        __combine_get_tran.writeAction(f"send_wcont {saved_cont} {ev_word} {key_lm_addr} {self.cache_entry_size}")
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Store masked key = %lu(0x%lx) to addr = 0x%lx' " + 
                                         f"{'X0'} {masked_key} {masked_key} {key_lm_addr}")
        __combine_get_tran.writeAction(f"move {masked_key} {0}({key_lm_addr}) 0 8")
        __combine_get_tran.writeAction(f"yieldt")
        
        # Key not exist store the incoming value.
        set_ev_label(__combine_get_tran, ev_word, self.__comb_val_put_ack_ev_label, label=get_fail_label, new_thread=True)
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Key not exist store the incoming value: " + 
                                         f"key = %ld values = {' '.join(['%ld' for _ in range(self.value_size)])}' {'X0'} {cached_key} {' '.join(cached_values)}")
        __combine_get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        self.data_store.put_pair(__combine_get_tran, ev_word, cached_key, cached_values, buffer_addr, scratch)
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Put key = %ld values = " + 
                                         f"[{' '.join(['%ld, ' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(cached_values)}")
        __combine_get_tran.writeAction(f"subi {key_lm_addr} {key_lm_addr} {WORD_SIZE}")
        set_ignore_cont(__combine_get_tran, ev_word)
        __combine_get_tran.writeAction(f"send_wcont {saved_cont} {ev_word} {key_lm_addr} {self.cache_entry_size} ")
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Store masked key = %lu(0x%lx) to addr = " + 
                                         f"0x%lx' {'X0'} {masked_key} {masked_key} {key_lm_addr}")
        __combine_get_tran.writeAction(f"move {masked_key} {0}({key_lm_addr}) 0 8")
        __combine_get_tran.writeAction(f"yieldt")
        
        __combine_get_tran.writeAction(f"{combine_fail_label}: movir {scratch[0]} {self.cache_ival}")
        set_ignore_cont(__combine_get_tran, ev_word)
        __combine_get_tran.writeAction(f"sendr_wcont {saved_cont} {ev_word} {scratch[0]} {cached_key}")
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Combine fail key = %ld, loaded values [{' '.join(['%ld' for _ in range(self.value_size)])}] update values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}] return failure.' {'X0'} {key} {' '.join(ld_values)} {' '.join(cached_values)}")
        __combine_get_tran.writeAction(f"yieldt")
        
        '''
        Event:      Put pair ack, return to user passed in continuation.
        Operands:   X8: status
        '''
        put_pair_ops = self.data_store.put_pair_ops()
        __combine_put_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_put_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            __combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_put_ack_ev_label}] Event word = %lu put pair return " + 
                                             f"operands = [{''.join(['%lu, ' for _ in range(len(put_pair_ops))])}]' {'X0'} {'EQT'} {' '.join(put_pair_ops)}")
        # __combine_put_ack_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {cached_key} {cached_key} ")
        __combine_put_ack_tran.writeAction("yieldt")

        return
    
    def __gen_wb_get(self):
        
        get_tran        = self.state.writeTransition("eventCarry", self.state, self.state, self.get_ev_label)
        
        __get_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_ev_label)
        
        __get_ret_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_ret_ev_label)
        
        __get_put_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_put_ack_ev_label)
        
        key         = [f'X{OB_REG_BASE + i}' for i in range(self.key_size)]
        value_ops   = [f'X{OB_REG_BASE + self.key_size + n}' for n in range(self.value_size)]
        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        
        nwid_mask_addr = regs[0]
        num_lanes_mask = regs[1]
        dest_nwid   = regs[2]
        base_nwid   = regs[3]
        ev_word     = regs[-1]
        if self.debug_flag:
            get_tran.writeAction(f"print ' '")
            get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.get_ev_label}> ev_word = %lu income_cont = %lu' {'X0'} {'EQT'} {'X1'}")
        get_tran.writeAction(f"addi {'X7'} {nwid_mask_addr} {self.nwid_mask_offset}")
        get_tran.writeAction(f"movlr {0}({nwid_mask_addr}) {num_lanes_mask} 0 8")
        get_tran.writeAction(f"movlr  {self.nwid_base_offset - self.nwid_mask_offset}({nwid_mask_addr}) {base_nwid} 0 8")
        self.__get_cache_loc(get_tran, key, num_lanes_mask, base_nwid, dest_nwid)
        if self.debug_flag:
            get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Send key = [{' '.join([ f'%ld' for _ in range(self.key_size)])}] to lane %ld' {'X0'} {' '.join(key)} {dest_nwid}")
        set_ev_label(get_tran, ev_word, self.__get_ev_label, new_thread = True)
        get_tran.writeAction(f"ev {ev_word}  {ev_word}  {dest_nwid} {dest_nwid} {8}")
        get_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key[0]} {2}")
        get_tran.writeAction(f"yieldt")

        key_addr    = regs[0]
        cached_key  = regs[1]
        buffer_addr = regs[2]
        masked_key  = regs[3]
        pending_ack = regs[3]
        saved_cont  = regs[4]
        get_key     = regs[5]
        values  = [regs[6+i] for i in range(self.value_size)]
        scratch = [regs[6+i+self.value_size] for i in range(2)]
        ev_word = regs[-1]

        wait_update_label   = "cache_active_miss"
        cache_hit_label     = "cache_get_hit"
        cache_miss_label    = "cache_get_miss"
        get_fail_label      = "get_fail"
        skip_flush_label    = "skip_flush"
        continue_label      = "continue"

        key = key[0]
        '''
        Event:      Check if the scratchpad caches the value. If so, combine the incoming values with the cached values. If not, retrieve it from output key-value set.
        Operands:   X8: Key
        Return:     X1: return event
                    X8: Flag, -1 if get fails, otherwise equals to key
                    X9 ~ Xn: Values if get succeeds, otherwise returns key
        '''
        if self.debug_flag:
            __get_tran.writeAction(f"print ' '")
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Event <{self.__get_ev_label}> key = %ld cont = %lu' {'X0'} {key} {'X1'}")
        # check if the local scratchpad caches the value for the input key.
        # __get_tran.writeAction(f"movir {masked_key} {self.hash_seed}")
        # __get_tran.writeAction(f"hash {key} {masked_key}")
        if self.power_of_two_cache_size:
            __get_tran.writeAction(f"andi {key} {masked_key} {self.cache_size - 1}")
        else:
            __get_tran.writeAction(f"movir {scratch[0]} {self.cache_size}")
            __get_tran.writeAction(f"mod {key} {scratch[0]} {masked_key}")
        if self.power_of_two_entry_size:
            __get_tran.writeAction(f"sli {masked_key} {key_addr} {int(log2(self.cache_entry_bsize))}")
        else:
            __get_tran.writeAction(f"muli {masked_key} {key_addr} {self.cache_entry_bsize}")
        __get_tran.writeAction(f"add {'X7'} {key_addr} {key_addr}")
        if self.cache_offset >> 15 > 0:
            __get_tran.writeAction(f"movir {scratch[0]} {self.cache_offset}")
            __get_tran.writeAction(f"add {key_addr} {scratch[0]} {key_addr}")
        else:
            __get_tran.writeAction(f"addi {key_addr} {key_addr} {self.cache_offset}")
        __get_tran.writeAction(f"movlr {0}({key_addr}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Get incoming key = %ld Cached key = %ld " + 
                                   f"at cache index %ld lm_addr = %lu(0x%lx)' {'X0'} {key} {cached_key} {masked_key} {key_addr}")
        __get_tran.writeAction(f"sri {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        __get_tran.writeAction(f"beqi {scratch[0]} {0} {wait_update_label}")
        __get_tran.writeAction(f"movir {masked_key} {1}")
        __get_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        __get_tran.writeAction(f"add {masked_key} {key} {masked_key}")
        if self.debug_flag and self.print_level > 4:
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Masked key = %lu(0x%lx)' {'X0'} {masked_key} {masked_key}")
        __get_tran.writeAction(f"beq {masked_key} {cached_key} {cache_hit_label}")
        # If not, check if the data cached has been written back to DRAM. If so, evict the current entry.
        # Before evicting the current entry, check if there is available thread.
        if (self.num_threads_offset >> 15) > 0:
            __get_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __get_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __get_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __get_tran.writeAction(f"movlr {self.max_threads_offset - self.num_threads_offset}({buffer_addr}) {scratch[1]} 0 8")
        __get_tran.writeAction(f"bgt {scratch[1]} {scratch[0]} {cache_miss_label}")
        if self.debug_flag and self.print_level > 2:
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Not enough thread to evict key = %ld, " + 
                                   f"push the cache_get request back to event queue' {'X0'} {key}")
        # __get_tran.writeAction(f"jmp {cache_miss_label}")

        # Pending for an unmerged update to the values with the same key
        __get_tran.writeAction(f"{wait_update_label}: evi {'X2'} {ev_word} {NEW_THREAD_ID} {0b0100}")
        __get_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key} {self.key_size if self.key_size > 1 else 2}")
        if self.debug_flag and self.print_level > 2:
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Cache get miss key = %ld, " + 
                                   f"cache entry occupied/pending on an update.' {'X0'} {key}")
        if self.cache_stats_flag:
            __get_tran.writeAction(f"perflog 1 716 '[CACHE_GET]: Cache miss, entry occupied by key = %ld' {cached_key}")
        __get_tran.writeAction(f"yieldt")

        # The value is cached in the scratchpad, return the newest value
        __get_tran.writeAction(f"{cache_hit_label}: move {key} {0}({key_addr}) 0 8")
        if self.cache_stats_flag:
            __get_tran.writeAction(f"perflog 1 716 '[CACHE_GET]: Cache hit, value is at LM addr = %ld' {key_addr}")
        if self.debug_flag and self.print_level > 2:
            for i in range(self.value_size):
                __get_tran.writeAction(f"move {WORD_SIZE * (i+1)}({key_addr}) {values[i]} 0 8")
            __get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] Cache hit key = %ld, cached values = " + 
                                   f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {key} {' '.join(values)}")
        # Return the cached value
        set_ignore_cont(__get_tran, ev_word)
        __get_tran.writeAction(f"send_wcont {'X1'} {ev_word} {key_addr} {self.cache_entry_size}")
        __get_tran.writeAction(f"move {masked_key} {0}({key_addr}) 0 8")
        __get_tran.writeAction("yieldt")

        # Cache miss, retrieve the current value.
        if self.debug_flag and self.print_level > 2:
            __get_tran.writeAction(f"{cache_miss_label}: print '[DEBUG][NWID %ld][{self.__get_ev_label}] Cache miss. Get values for key = %ld' {'X0'} {key}")
            set_ev_label(__get_tran, ev_word, self.__get_ret_ev_label)
        else:
            set_ev_label(__get_tran, ev_word, self.__get_ret_ev_label, label=cache_miss_label)
        if self.cache_stats_flag:
            __get_tran.writeAction(f"perflog 1 716 '[CACHE_GET]: Cache miss, evict key = %ld from LM addr = %ld, put new key = %ld' {cached_key} {key_addr} {key}")
        # Update the thread counts in scratchpad 
        __get_tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
        __get_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        # Retrieve the current value.
        __get_tran = self.data_store.get_pair(tran=__get_tran, cont_evw=ev_word, key=key, regs=scratch)
        __get_tran.writeAction(f"addi {key} {get_key} 0")
        __get_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        __get_tran.writeAction(f"yield")

        '''
        Event:      Get pair returns.
        Operands:   X8 ~ Xn: Values retrieved.
        '''
        get_pair_ops = self.data_store.get_pair_ops()
        cache_occupied_label = "cache_occupied"
        key_existed_label = "key_updated"
        
        __get_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__get_ret_ev_label)
        if self.debug_flag and self.print_level > 2:
            __get_ret_tran.writeAction(f"print ' '")
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Event word = %lu get key = %ld return ops = " + 
                                     f"[{' '.join(['%ld, ' for _ in range(len(get_pair_ops))])}]' {'X0'} {'EQT'} {get_key} {' '.join(get_pair_ops)}")
        # Check if the get is successful (i.e., if the value corresponding to the key exists)
        self.data_store.check_get_pair(__get_ret_tran, get_key, get_pair_ops, get_fail_label)
        
        # Store the returned values
        ld_key = 'X8'
        ld_values = self.data_store.get_pair_value_ops()
        if self.debug_flag and self.print_level > 2:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Get pair success, return key = %ld values = " + 
                                       f"[{''.join(['%ld, ' for _ in range(len(ld_values))])}]' {'X0'} {ld_key} {' '.join(ld_values)}")
        # Check cached key status
        __get_ret_tran.writeAction(f"movlr {0}({key_addr}) {cached_key} 0 8")
        __get_ret_tran.writeAction(f"beqi {cached_key} {self.cache_ival} {skip_flush_label}")
        __get_ret_tran.writeAction(f"sli {cached_key} {scratch[0]} {1}")
        __get_ret_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {1}")
        __get_ret_tran.writeAction(f"beq {scratch[0]} {ld_key} {key_existed_label}")
        __get_ret_tran.writeAction(f"sri {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        __get_ret_tran.writeAction(f"beqi {scratch[0]} {0} {cache_occupied_label}")
        
        # Flush the current entry
        __get_ret_tran.writeAction(f"movir {pending_ack} {0}")
        __get_ret_tran.writeAction(f"sli {cached_key} {cached_key} {1}")
        __get_ret_tran.writeAction(f"sri {cached_key} {cached_key} {1}")
        if self.debug_flag:
            for i in range(self.value_size):
                __get_ret_tran.writeAction(f"movlr {WORD_SIZE * (i+1)}({key_addr}) {values[i]} 0 8")
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Evict cached key = %ld, values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(values)}")
        __get_ret_tran.writeAction(f"addi {key_addr} {key_addr} {WORD_SIZE}")
        if (self.send_buffer_offset >> 15) > 0:
            __get_ret_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
            __get_ret_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __get_ret_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        set_ev_label(__get_ret_tran, ev_word, self.__get_put_ack_ev_label)
        self.data_store.flush_pair(__get_ret_tran, ev_word, cached_key, key_addr, buffer_addr, pending_ack, scratch)
        __get_ret_tran.writeAction(f"subi {key_addr} {key_addr} {self.cache_entry_bsize}")
        # __combine_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        if self.debug_flag:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Flush cached key = %ld values = " + 
                                       f"[{''.join(['%ld, ' for _ in range(len(values))])}]' {'X0'} {cached_key} {' '.join(values)}")
        # Store the loaded value to cache
        __get_ret_tran.writeAction(f"movrl {get_key} {0}({key_addr}) 0 8")
        for i in range(self.value_size):
            __get_ret_tran.writeAction(f"movrl {ld_values[i]} {WORD_SIZE * (i+1)}({key_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Cache key = %lu loaded values = " + 
                                       f"[{''.join(['%ld, ' for _ in range(len(ld_values))])}] at addr = 0x%lx' {'X0'} {get_key} {' '.join(ld_values)} {key_addr}")
        __get_ret_tran.writeAction(f"yield")
        
        # Invalid key in the cache, store the loaded value to cache directly
        __get_ret_tran.writeAction(f"{skip_flush_label}: movrl {get_key} {0}({key_addr}) 0 8")
        for i in range(self.value_size):
            __get_ret_tran.writeAction(f"movrl {ld_values[i]} {WORD_SIZE * (i+1)}({key_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Cache key = %lu loaded values = " + 
                                       f"[{''.join(['%ld, ' for _ in range(len(ld_values))])}] at addr = 0x%lx' {'X0'} {get_key} {' '.join(ld_values)} {key_addr}")
        set_ignore_cont(__get_ret_tran, ev_word)
        __get_ret_tran.writeAction(f"send_wcont {saved_cont} {ev_word} {key_addr} {self.cache_entry_size}")
        __get_ret_tran.writeAction(f"movir {masked_key} {1}")
        __get_ret_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        __get_ret_tran.writeAction(f"add {masked_key} {get_key} {masked_key}")
        __get_ret_tran.writeAction(f"move {masked_key} {0}({key_addr}) 0 8")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __get_ret_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __get_ret_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __get_ret_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __get_ret_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __get_ret_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __get_ret_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __get_ret_tran.writeAction(f"yieldt")
        
        __get_ret_tran.writeAction(f"{cache_occupied_label}: addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        __get_ret_tran.writeAction(f"movrl {get_key} {0}({buffer_addr}) 0 8")
        for i in range(self.value_size):
            __get_ret_tran.writeAction(f"move {ld_values[i]} {WORD_SIZE * (i+1)}({buffer_addr}) 0 8")
        set_ignore_cont(__get_ret_tran, ev_word)
        __get_ret_tran.writeAction(f"send_wcont {saved_cont} {ev_word} {buffer_addr} {self.cache_entry_size}")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __get_ret_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __get_ret_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __get_ret_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __get_ret_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __get_ret_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __get_ret_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __get_ret_tran.writeAction(f"yieldt")
        
        # Key not exist. Return failure.
        __get_ret_tran.writeAction(f"{get_fail_label}: movir {scratch[0]} {self.cache_ival}")
        set_ignore_cont(__get_ret_tran, ev_word)
        __get_ret_tran.writeAction(f"sendr_wcont {saved_cont} {ev_word} {scratch[0]} {cached_key}")
        if self.debug_flag:
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ret_ev_label}] Key = %ld not exist, return failure.' {'X0'} {cached_key}")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __get_ret_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __get_ret_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __get_ret_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __get_ret_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __get_ret_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __get_ret_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __get_ret_tran.writeAction(f"yieldt")

        # Key is updated, return the cached value
        __get_ret_tran.writeAction(f"{key_existed_label}: movrl {key} {0}({key_addr}) 0 8")
        set_ignore_cont(__get_ret_tran, ev_word)
        __get_ret_tran.writeAction(f"send_wcont {'X1'} {ev_word} {key_addr} {self.cache_entry_size}")
        if self.debug_flag and self.print_level > 2:
            for i in range(self.value_size):
                __get_ret_tran.writeAction(f"move {WORD_SIZE * (i+1)}({key_addr}) {values[i]} 0 8")
            __get_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_ev_label}] While loading the values, key = %ld is updated in cache, cached values = " + 
                                   f"[{' '.join(['%ld' for _ in range(self.value_size)])}], return directly' {'X0'} {ld_key} {' '.join(values)}")
        __get_ret_tran.writeAction(f"movrl {cached_key} {0}({key_addr}) 0 8")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __get_ret_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __get_ret_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __get_ret_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __get_ret_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __get_ret_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __get_ret_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __get_ret_tran.writeAction("yieldt")
        
        '''
        Event:      Flush evited cache entry ack, return to user passed in continuation.
        Operands:   X8: status
        '''
        if self.debug_flag:
            __get_put_ack_tran.writeAction(f"print ' '")
            __get_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__get_put_ack_ev_label}] Flush pair return status = %lu addr = %lu(0x%lx)' {'X0'} {'X8'} {'X9'} {'X9'}")
        __get_put_ack_tran.writeAction(f"subi {pending_ack} {pending_ack} 1")
        __get_put_ack_tran.writeAction(f"bgti {pending_ack} {0} {continue_label}")
        set_ignore_cont(__get_put_ack_tran, ev_word)
        __get_put_ack_tran.writeAction(f"send_wcont {saved_cont} {ev_word} {key_addr} {self.cache_entry_size}")
        __get_put_ack_tran.writeAction(f"movir {masked_key} {1}")
        __get_put_ack_tran.writeAction(f"sli {masked_key} {masked_key} {self.INACTIVE_MASK_SHIFT}")
        __get_put_ack_tran.writeAction(f"add {masked_key} {get_key} {masked_key}")
        __get_put_ack_tran.writeAction(f"move {masked_key} {0}({key_addr}) 0 8")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __get_put_ack_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __get_put_ack_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __get_put_ack_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __get_put_ack_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __get_put_ack_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __get_put_ack_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __get_put_ack_tran.writeAction(f"{continue_label}: yieldt")
        
        return
    
    def __gen_wb_combine_value(self):
        
        combine_tran            = self.state.writeTransition("eventCarry", self.state, self.state, self.combine_val_ev_label)
        
        __combine_tran          = self.state.writeTransition("eventCarry", self.state, self.state, self.__combine_val_ev_label)
        
        __combine_get_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_get_ev_label)
        
        __combine_put_ack_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_put_ack_ev_label)

        key     = [f'X{OB_REG_BASE + i}' for i in range(self.key_size)]
        values  = [f'X{OB_REG_BASE + self.key_size + n}' for n in range(self.value_size)]

        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        
        nwid_mask_addr = regs[0]
        num_lanes_mask = regs[1]
        dest_nwid   = regs[2]
        base_nwid   = regs[3]
        ev_word     = regs[-1]
        if self.debug_flag:
            combine_tran.writeAction(f"print ' '")
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_val_ev_label}] Event <{self.combine_val_ev_label}> ev_word = %lu key = " + 
                                   f"[{' '.join([ f'%ld' for _ in range(self.key_size)])}], cont = %lu' {'X0'} {'EQT'} {' '.join(key)} {'X1'}")
        combine_tran.writeAction(f"addi {'X7'} {nwid_mask_addr} {self.nwid_mask_offset}")
        combine_tran.writeAction(f"movlr {0}({nwid_mask_addr}) {num_lanes_mask} 0 8")
        combine_tran.writeAction(f"movlr {self.nwid_base_offset - self.nwid_mask_offset}({nwid_mask_addr}) {base_nwid} 0 8")
        self.__get_cache_loc(combine_tran, key, num_lanes_mask, base_nwid, dest_nwid)
        if self.debug_flag:
            combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.combine_val_ev_label}] Send key = [{' '.join([ f'%ld' for _ in range(self.key_size)])}] values = " + 
                                 f"[{' '.join([ f'%ld' for _ in range(self.value_size)])}] to lane %ld' {'X0'} {' '.join(key)} {' '.join(values)} {dest_nwid}")
        set_ev_label(combine_tran, ev_word, self.__combine_val_ev_label, new_thread = True)
        combine_tran.writeAction(f"ev {ev_word}  {ev_word}  {dest_nwid} {dest_nwid} 8")
        combine_tran.writeAction(f"sendops_wcont {ev_word} {'X1'} {key[0]} {self.cache_entry_size}")
        combine_tran.writeAction(f"yieldt")
        

        key     = 'X8'
        values  = [f'X{n+9}' for n in range(self.value_size)]

        key_addr    = regs[0]
        cached_key  = regs[1]
        buffer_addr = regs[2]
        pending_ack = regs[3]
        saved_cont  = regs[4]
        temp_evw    = regs[5]
        key_mask    = regs[6]
        cached_values_offset = regs[7]
        cached_values   = [regs[7+i] for i in range(self.value_size)]
        result_regs = [regs[7+i] for i in range(self.value_size)]
        # scratch     = [regs[7+i+self.value_size] for i in range(2)]
        scratch     = [regs[i] for i in range(7+self.value_size, 16)]

        hit_label   = "cache_hit"
        evict_label = "cache_evict"
        occupy_label    = "cache_occupied"
        continue_label  = "contiue"
        finish_label    = "finish_write_back"
        get_fail_label  = "get_fail"
        skip_flush_label = "skip_flush"
        combine_fail_label  = "combine_fail"

        '''
        Event:      Check if the scratchpad caches the value. 
                    If so, combine the incoming values with the cached values. 
                    If not, retrieve the latest values.
        Operands:   X8: Key
                    X9 ~ Xn: Values
        Return:     X1: return event
                    X8: Flag, -1 if fails, otherwise equals to key
                    X9: Values after combine
        '''
        if self.debug_flag:
            __combine_tran.writeAction(f"print ' '")
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Event <{self.__combine_val_ev_label}> key = %ld, values =" + 
                                     f" {' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}' {'X0'} {key} {' '.join(values)}")
        # check if the local scratchpad stores a pending update to the same key or a copy of the newest output kvpair with that key.
        # __combine_tran.writeAction(f"movir {key_mask} {self.hash_seed}")
        # __combine_tran.writeAction(f"hash {key} {key_mask}")
        if self.power_of_two_cache_size:
            __combine_tran.writeAction(f"andi {key} {key_mask} {self.cache_size - 1}")
        else:
            __combine_tran.writeAction(f"movir {scratch[0]} {self.cache_size}")
            __combine_tran.writeAction(f"mod {key} {scratch[0]} {key_mask}")
        if self.power_of_two_entry_size:
            __combine_tran.writeAction(f"sli {key_mask} {key_addr} {int(log2(self.cache_entry_bsize))}")
        else:
            __combine_tran.writeAction(f"muli {key_mask} {key_addr} {self.cache_entry_bsize}")
        __combine_tran.writeAction(f"add {'X7'} {key_addr} {key_addr}")
        if self.cache_offset >> 15 > 0:
            __combine_tran.writeAction(f"movir {scratch[0]} {self.cache_offset}")
            __combine_tran.writeAction(f"add {key_addr} {scratch[0]} {key_addr}")
        else:
            __combine_tran.writeAction(f"addi {key_addr} {key_addr} {self.cache_offset}")
        __combine_tran.writeAction(f"movlr {0}({key_addr}) {cached_key} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Merge incoming key = %ld Cached key = %lu(0x%lx) at " + 
                                     f"cache addr %lu(0x%lx) offset %ld' {'X0'} {key} {cached_key} {cached_key} {key_addr} {key_addr} {key_mask}")
        __combine_tran.writeAction(f"sri {cached_key} {scratch[0]} {self.INACTIVE_MASK_SHIFT}")
        __combine_tran.writeAction(f"beqi {scratch[0]} {0} {occupy_label}")
        __combine_tran.writeAction(f"movir {key_mask} {1}")
        __combine_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        __combine_tran.writeAction(f"or {key_mask} {key} {scratch[1]}")
        if self.debug_flag and self.print_level > 3:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] key = %ld masked key = %lu(0x%lx) cached key = %lu(0x%lx)' " + 
                                     f"{'X0'} {key} {scratch[1]} {scratch[1]} {cached_key} {cached_key}")
        __combine_tran.writeAction(f"beq {scratch[1]} {cached_key} {hit_label}")
        # If not, check if the data cached has been written back. If so, evict the current entry.
        # Before evicting the current entry, check if there is available thread.
        if (self.num_threads_offset >> 15) > 0:
            __combine_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __combine_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __combine_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __combine_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __combine_tran.writeAction(f"movlr {self.max_threads_offset - self.num_threads_offset}({buffer_addr}) {scratch[1]} 0 8")
        __combine_tran.writeAction(f"bgt {scratch[1]} {scratch[0]} {evict_label}")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Not enough thread to evict key = %ld, " + 
                                   f"push the cache_combine request back to event queue' {'X0'} {key}")
        # __combine_tran.writeAction(f"jmp {evict_label}")

        # If all conditions failed, the entry is occupied and cannot be evicted for now, push the event back to the queue.
        __combine_tran.writeAction(f"{occupy_label}: evi {'X2'} {temp_evw} {NEW_THREAD_ID} {0b0100}")
        if self.debug_flag and self.print_level > 3:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Cache entry occupied by key = %lu, push back to queue key = %ld " + 
                                     f"values = [{''.join(['%ld, ' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {cached_key} {key} {' '.join(values)}")
        __combine_tran.writeAction(f"sendops_wcont {temp_evw} X1 {key} {self.cache_entry_size}")
        if self.cache_stats_flag:
            __combine_tran.writeAction(f"perflog 1 717 '[CACHE_COMBINE]: Cache miss, entry occupied by key = %ld' {cached_key}")
        __combine_tran.writeAction("yieldt")

        # Still waiting for the read to the output kv pair on DRAM coming back, merge locally
        __combine_tran.writeAction(f"{hit_label}: move {WORD_SIZE}({key_addr}) {cached_values[0]} 0 8")
        if self.cache_stats_flag:
            __combine_tran.writeAction(f"perflog 1 717 '[CACHE_COMBINE]: Cache hit, entry at LM addr = %ld is free' {key_addr}")
        for i in range(self.value_size - 1):
            __combine_tran.writeAction(f"move {WORD_SIZE * (i+2)}({key_addr}) {cached_values[i+1]} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Cache hit key = %ld, cached values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {key} {' '.join(cached_values)}")
        self.combine_func(__combine_tran, key, values, cached_values, result_regs, scratch, combine_fail_label, hit_label)
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Cache key = %ld combine result values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(result_regs))])}] at addr %lu(0x%lx)' {'X0'} {key} {' '.join(result_regs)} {key_addr} {key_addr}")
        for i in range(self.value_size):
            __combine_tran.writeAction(f"movrl {result_regs[i]} {WORD_SIZE * (i+1)}({key_addr}) 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Combine key = %ld, result values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {key} {' '.join(result_regs)}")
        __combine_tran.writeAction(f"movrl {key} {0}({key_addr}) 0 8")
        if self.wf4k4_patch_flag:
            __combine_tran.writeAction(f"movlr {WORD_SIZE * 2}({key_addr}) {scratch[0]} 0 8")
            __combine_tran.writeAction(f"movlr {WORD_SIZE * 3}({key_addr}) {scratch[3]} 0 8")
            __combine_tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE * 2}({key_addr}) 0 8")
            __combine_tran.writeAction(f"movrl {scratch[2]} {WORD_SIZE * 3}({key_addr}) 0 8")
        set_ignore_cont(__combine_tran, temp_evw)
        __combine_tran.writeAction(f"send_wcont {'X1'} {temp_evw} {key_addr} {self.cache_entry_size} ")
        __combine_tran.writeAction(f"movrl {cached_key} {0}({key_addr}) 0 8")
        if self.wf4k4_patch_flag:
            __combine_tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE * 2}({key_addr}) 0 8")
            __combine_tran.writeAction(f"movrl {scratch[3]} {WORD_SIZE * 3}({key_addr}) 0 8")
        __combine_tran.writeAction(f"yieldt")
        
        # Current entry can be evited. Store the dirty entry and insert the new entry.
        __combine_tran.writeAction(f"{evict_label}: movrl {key} {0}({key_addr}) 0 8")
        if self.cache_stats_flag:
            __combine_tran.writeAction(f"perflog 1 717 '[CACHE_COMBINE]: Cache miss, evict key = %ld from LM addr = %ld, put new key = %ld' {cached_key} {key_addr} {key}")
        # Update the thread counts in scratchpad 
        __combine_tran.writeAction(f"addi {scratch[0]} {scratch[0]} 1")
        __combine_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        # Retrieve the current value.
        if self.debug_flag and self.print_level > 2:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Cache miss evict old key %lu. Get value for " + 
                                     f"key = %ld from output key value set' {'X0'} {cached_key} {key}")
        __combine_tran.writeAction(f"movir {pending_ack} {0}")
        __combine_tran.writeAction(f"beqi {cached_key} {self.cache_ival} {skip_flush_label}")
        __combine_tran.writeAction(f"sub {cached_key} {key_mask} {cached_key}")
        # Store the evicted key-value pair to output key value set
        if self.debug_flag:
            for i in range(self.value_size):
                __combine_tran.writeAction(f"movlr {WORD_SIZE * (i+1)}({key_addr}) {cached_values[i]} 0 8")
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Evict cached key = %ld, values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}]' {'X0'} {cached_key} {' '.join(cached_values)}")
        __combine_tran.writeAction(f"addi {key_addr} {cached_values_offset} {WORD_SIZE}")
        if (self.send_buffer_offset >> 15) > 0:
            __combine_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
            __combine_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __combine_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        set_ev_label(__combine_tran, temp_evw, self.__comb_val_put_ack_ev_label)
        self.data_store.flush_pair(__combine_tran, temp_evw, cached_key, cached_values_offset, buffer_addr, pending_ack, scratch)
        # __combine_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        # Retrieve the current value.
        if self.debug_flag:
            __combine_tran.writeAction(f"jmp {continue_label}")
            __combine_tran.writeAction(f"{skip_flush_label}: print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Invalid cached_key = %ld(0x%lx) skip put pair' {'X0'} {cached_key} {cached_key}")
            set_ev_label(__combine_tran, temp_evw, self.__comb_val_get_ev_label, label=continue_label)
        else:
            set_ev_label(__combine_tran, temp_evw, self.__comb_val_get_ev_label, label=skip_flush_label)
        # __combine_tran.writeAction(f"{skip_flush_label}: evlb {temp_evw} {self.__comb_val_get_ev_label}")
        self.data_store.get_pair(__combine_tran, temp_evw, key, scratch)
        if self.debug_flag:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Get pair key = %ld from output key value set' {'X0'} {key}")
        # Store the incoming key-value pair to the cache
        for i in range(self.value_size):
            __combine_tran.writeAction(f"move {values[i]} {WORD_SIZE * (i+1)}({key_addr}) 0 8")
        __combine_tran.writeAction(f"addi {key} {cached_key} 0")
        __combine_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        __combine_tran.writeAction(f"addi {pending_ack} {pending_ack} 1")
        __combine_tran.writeAction(f"yield")
        
        # Combine fail, return failure to user passed in continuation.
        __combine_tran.writeAction(f"{combine_fail_label}: movir {scratch[0]} {self.cache_ival}")
        __combine_tran.writeAction(f"sendr_reply {scratch[0]} {key} {scratch[1]}")
        if self.debug_flag:
            __combine_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__combine_val_ev_label}] Combine fail key = %ld, cached values [{' '.join(['%ld' for _ in range(self.value_size)])}] update value = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}] return failure.' {'X0'} {key} {' '.join(cached_values)} {' '.join(values)}")
        __combine_tran.writeAction(f"yieldt")

        '''
        Event:      Get pair returns, merge with cached values.
        Operands:   X8: Key
                    X9 ~ Xn: Values in output kv set
        '''
        # Value is retrieved and ready for merging with the (accumulated) updates
        get_pair_ops = self.data_store.get_pair_ops()
        __combine_get_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_get_ev_label)
        if self.debug_flag and self.print_level > 3:
            __combine_get_tran.writeAction(f"print ' '")
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Event word = %lu Get key = %ld return ops = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(get_pair_ops))])}]' {'X0'} {'EQT'} {cached_key} {' '.join(get_pair_ops)}")
            
        # Check if the get is successful
        self.data_store.check_get_pair(__combine_get_tran, cached_key, get_pair_ops, get_fail_label)
        
        # Read the accumulated cached value 
        for i in range(len(cached_values)):
            __combine_get_tran.writeAction(f"movlr {WORD_SIZE * (i+1)}({key_addr}) {cached_values[i]} 0 8")
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Cached key = %ld values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(cached_values))])}]' {'X0'} {cached_key} {' '.join(cached_values)} ")

        # Load the cached value
        ld_values = self.data_store.get_pair_value_ops()
        if self.debug_flag and self.print_level > 3:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Get pair success, return values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(ld_values))])}]' {'X0'} {' '.join(ld_values)}")
        # Apply the accumulated updates based on user-defined reduce funtion
        self.combine_func(__combine_get_tran, cached_key, cached_values, ld_values, result_regs, scratch, combine_fail_label, evict_label)
        if self.debug_flag and self.print_level > 2:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Store key = %ld combine result values = " + 
                                         f"[{''.join(['%ld, ' for _ in range(len(result_regs))])}] at addr %lu(0x%lx)' {'X0'} {cached_key} {' '.join(result_regs)} {key_addr} {key_addr}")
        # Store the updated value back to the cache
        for i in range(self.value_size):
            __combine_get_tran.writeAction(f"movrl {result_regs[i]} {WORD_SIZE * (i+1)}({key_addr}) 0 8")
        # Merged with the loaded value, check for synchronization
        __combine_get_tran.writeAction(f"{get_fail_label}: subi {pending_ack} {pending_ack} 1")
        __combine_get_tran.writeAction(f"beqi {pending_ack} 0 {finish_label}")
        __combine_get_tran.writeAction(f"yield")
        
        # Finish combine, return to user passed in continuation.
        __combine_get_tran.writeAction(f"{finish_label}: movir {key_mask} {1}")
        __combine_get_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        __combine_get_tran.writeAction(f"or {key_mask} {cached_key} {cached_key}")
        if self.wf4k4_patch_flag:
            __combine_get_tran.writeAction(f"movlr {WORD_SIZE * 2}({key_addr}) {scratch[0]} 0 8")
            __combine_get_tran.writeAction(f"movlr {WORD_SIZE * 3}({key_addr}) {scratch[3]} 0 8")
            __combine_get_tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE * 2}({key_addr}) 0 8")
            __combine_get_tran.writeAction(f"movrl {scratch[2]} {WORD_SIZE * 3}({key_addr}) 0 8")
        set_ignore_cont(__combine_get_tran, temp_evw)
        __combine_get_tran.writeAction(f"send_wcont {saved_cont} {temp_evw} {key_addr} {self.cache_entry_size} ")
        __combine_get_tran.writeAction(f"movrl {cached_key} {0}({key_addr}) 0 8")    # flip the highest bit indicating the value is written back
        if self.wf4k4_patch_flag:
            __combine_get_tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE * 2}({key_addr}) 0 8")
            __combine_get_tran.writeAction(f"movrl {scratch[3]} {WORD_SIZE * 3}({key_addr}) 0 8")
        if self.debug_flag and self.print_level > 3:
            __combine_get_tran.writeAction(f"sli {cached_key} {scratch[0]} {1}")
            __combine_get_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {1}")
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_get_ev_label}] Finish write back store key = %ld (masked = %lu) " + 
                                         f"to lm addr = 0x%lx' {'X0'} {cached_key} {scratch[0]} {key_addr}")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __combine_get_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __combine_get_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __combine_get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __combine_get_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __combine_get_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __combine_get_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __combine_get_tran.writeAction(f"yieldt")
        
        __combine_get_tran.writeAction(f"{combine_fail_label}: movir {scratch[0]} {self.cache_ival}")
        __combine_get_tran.writeAction(f"sendr_wcont {'X1'} {'X2'} {scratch[0]} {cached_key}")
        if self.debug_flag:
            __combine_get_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Combine fail key = %ld, loaded values [{' '.join(['%ld' for _ in range(self.value_size)])}] update values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.value_size)])}] return failure.' {'X0'} {key} {' '.join(ld_values)} {' '.join(cached_values)}")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __combine_get_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __combine_get_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __combine_get_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __combine_get_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __combine_get_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __combine_get_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __combine_get_tran.writeAction(f"yieldt")
        
        '''
        Event:      Put pair ack, return to user passed in continuation.
        Operands:   X8: status
        '''
        put_pair_ops = self.data_store.put_pair_ops()
        __combine_put_ack_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.__comb_val_put_ack_ev_label)
        if self.debug_flag and self.print_level > 3:
            __combine_put_ack_tran.writeAction(f"print ' '")
            __combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_put_ack_ev_label}] Event word = %lu put pair return operands = " + 
                                             f"[{''.join(['%lu, ' for _ in range(len(put_pair_ops))])}]' {'X0'} {'EQT'} {' '.join(put_pair_ops)}")
        __combine_put_ack_tran.writeAction(f"subi {pending_ack} {pending_ack} 1")
        __combine_put_ack_tran.writeAction(f"beqi {pending_ack} 0 {finish_label}")
        __combine_put_ack_tran.writeAction(f"yield")
        
        # Finish combine, return to user passed in continuation.
        __combine_put_ack_tran.writeAction(f"{finish_label}: movir {key_mask} {1}")
        __combine_put_ack_tran.writeAction(f"sli {key_mask} {key_mask} {self.INACTIVE_MASK_SHIFT}")
        if self.wf4k4_patch_flag:
            __combine_put_ack_tran.writeAction(f"movlr {WORD_SIZE * 2}({key_addr}) {scratch[0]} 0 8")
            __combine_put_ack_tran.writeAction(f"movlr {WORD_SIZE * 3}({key_addr}) {scratch[3]} 0 8")
            __combine_put_ack_tran.writeAction(f"movrl {scratch[1]} {WORD_SIZE * 2}({key_addr}) 0 8")
            __combine_put_ack_tran.writeAction(f"movrl {scratch[2]} {WORD_SIZE * 3}({key_addr}) 0 8")
        set_ignore_cont(__combine_put_ack_tran, temp_evw)
        __combine_put_ack_tran.writeAction(f"send_wcont {saved_cont} {temp_evw} {key_addr} {self.cache_entry_size}")
        __combine_put_ack_tran.writeAction(f"or {key_mask} {cached_key} {cached_key}")
        __combine_put_ack_tran.writeAction(f"movrl {cached_key} {0}({key_addr}) 0 8")    # flip the highest bit indicating the value is written back
        if self.wf4k4_patch_flag:
            __combine_put_ack_tran.writeAction(f"movrl {scratch[0]} {WORD_SIZE * 2}({key_addr}) 0 8")
            __combine_put_ack_tran.writeAction(f"movrl {scratch[3]} {WORD_SIZE * 3}({key_addr}) 0 8")
        if self.debug_flag and self.print_level > 4:
            __combine_put_ack_tran.writeAction(f"sli {cached_key} {scratch[0]} {1}")
            __combine_put_ack_tran.writeAction(f"sri {scratch[0]} {scratch[0]} {1}")
            __combine_put_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__comb_val_put_ack_ev_label}] Store masked key = %lu (key = %ld) to addr = 0x%lx' {'X0'} {cached_key} {scratch[0]} {key_addr}")
        # Update the thread counts in scratchpad
        if (self.num_threads_offset >> 15) > 0:
            __combine_put_ack_tran.writeAction(f"movir {buffer_addr} {self.num_threads_offset}")
            __combine_put_ack_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            __combine_put_ack_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.num_threads_offset}")
        __combine_put_ack_tran.writeAction(f"movlr {0}({buffer_addr}) {scratch[0]} 0 8")
        __combine_put_ack_tran.writeAction(f"subi {scratch[0]} {scratch[0]} 1")
        __combine_put_ack_tran.writeAction(f"movrl {scratch[0]} {0}({buffer_addr}) 0 8")
        __combine_put_ack_tran.writeAction(f"yieldt")

    def __gen_flush_cache(self):

        cache_flush_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.cache_flush_ev_label)
        
        ln_flush_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.__flush_lane_ev_label)

        flush_ack_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.__flush_ack_ev_label)
        
        flush_fin_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.__flush_fin_ev_label)

        '''
        Event:      Flush all lanes' cache to data store.
        Operands:   X8: number of lanes
        Return:     X1: return event
        '''
        saved_cont  = f"X{GP_REG_BASE}"
        send_buffer = f"X{GP_REG_BASE + 1}"
        lane_evw    = f"X{GP_REG_BASE + 2}"
        ret_evw     = f"X{GP_REG_BASE + 3}"
        ev_word     = f"X{GP_REG_BASE + 4}"
        temp_lm_ptr = f"X{GP_REG_BASE + 5}"
        num_lanes   = f"X{GP_REG_BASE + 6}"
        base_nwid   = f"X{GP_REG_BASE + 7}"
        
        if self.debug_flag:
            cache_flush_tran.writeAction(f"print ' '")
            cache_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.cache_flush_ev_label}> ev_word=%ld' {'X0'} {'EQT'}")
        cache_flush_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        cache_flush_tran.writeAction(f"addi {'X2'} {ret_evw} 0")
        if self.nwid_base_offset >> 11 > 0:
            cache_flush_tran.writeAction(f"movir {temp_lm_ptr} {self.nwid_base_offset}")
            cache_flush_tran.writeAction(f"add {'X7'} {temp_lm_ptr} {temp_lm_ptr}")
            cache_flush_tran.writeAction(f"movlr {self.nwid_base_offset}({temp_lm_ptr}) {base_nwid} 0 8")
            cache_flush_tran.writeAction(f"movlr {self.nwid_mask_offset - self.nwid_base_offset}({temp_lm_ptr}) {num_lanes} 0 8")
        else:
            cache_flush_tran.writeAction(f"movlr {self.nwid_base_offset}({'X7'}) {base_nwid} 0 8")
            cache_flush_tran.writeAction(f"movlr {self.nwid_mask_offset}({'X7'}) {num_lanes} 0 8")
        cache_flush_tran.writeAction(f"addi {num_lanes} {num_lanes} 1")
        cache_flush_tran.writeAction(f"evlb {ret_evw} {self.__flush_fin_ev_label}")
        set_ev_label(cache_flush_tran, ev_word, self.cache_broadcast.get_broadcast_ev_label(), new_thread = True)
        cache_flush_tran.writeAction(f"addi {'X7'} {send_buffer} {self.send_buffer_offset}")
        cache_flush_tran.writeAction(f"movrl {num_lanes} 0({send_buffer}) 0 8")
        cache_flush_tran.writeAction(f"addi {'X2'} {lane_evw} 0")
        cache_flush_tran.writeAction(f"evlb {lane_evw} {self.__flush_lane_ev_label}")
        cache_flush_tran.writeAction(f"movrl {lane_evw} {WORD_SIZE}({send_buffer}) 0 8")
        cache_flush_tran.writeAction(f"send_wcont {ev_word} {ret_evw} {send_buffer} {self.SEND_BUFFER_SIZE}")
        cache_flush_tran.writeAction(f"yield")
        
        '''
        Finish flushing the cache, return to user continuation
        '''
        if self.debug_flag:
            flush_fin_tran.writeAction(f"print ' '")
            flush_fin_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_fin_ev_label}] Finish flushing the cache on %ld lanes. " + 
                                       f"Return to user continuation %lu' {'X0'} {num_lanes} {saved_cont}")
        set_ignore_cont(flush_fin_tran, ev_word)
        flush_fin_tran.writeAction(f"sendr_wcont {saved_cont} {ev_word} {num_lanes} {num_lanes}")
        flush_fin_tran.writeAction(f"yieldt")
        
        regs        = [f'X{GP_REG_BASE + i}' for i in range(16)]
        cache_bound = regs[0]
        saved_cont  = regs[1] 
        buffer_addr = regs[2]
        pending_ack = regs[3]
        cache_offset= regs[4]
        temp_key    = regs[5]
        temp_reg    = regs[5]
        invalid_key = regs[6]
        ack_evw     = regs[7]
        scratch     = [regs[8+i] for i in range(max(2, self.cache_entry_size - 1))]

        break_label     = "break_flush_loop"
        continue_label  = "continue_flush_loop"
        flush_loop_label    = "flush_loop"
        empty_cache_label   = "empty_cache"
        
        '''
        Event:      Flush the lane-private cache to DRAM.
        '''
        if self.debug_flag and self.print_level > 3:
            ln_flush_tran.writeAction(f"print ' '")
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_lane_ev_label}] Flush the cache at offset {self.cache_offset} to DRAM' {'X0'}")
        ln_flush_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        if self.cache_offset >> 15 > 0:
            ln_flush_tran.writeAction(f"movir {cache_offset} {self.cache_offset}")
            ln_flush_tran.writeAction(f"add {'X7'} {cache_offset} {cache_offset}")
        else:
            ln_flush_tran.writeAction(f"addi {'X7'} {cache_offset} {self.cache_offset}")
        ln_flush_tran.writeAction(f"movir {cache_bound} {self.cache_size}")
        if self.power_of_two_entry_size:
            ln_flush_tran.writeAction(f"sli {cache_bound} {cache_bound} {int(log2(self.cache_entry_bsize))}")
        else:
            ln_flush_tran.writeAction(f"muli {cache_bound} {cache_bound} {self.cache_entry_bsize}")
        ln_flush_tran.writeAction(f"add {cache_bound} {cache_offset} {cache_bound}")
        if self.debug_flag and self.print_level > 3:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_lane_ev_label}] Flush cache from offset = %lu(0x%lx) to offset = %lu(0x%lx) " + 
                                      f"(X7 = %lu(0x%lx))' {'X0'} {cache_offset} {cache_offset} {cache_bound} {cache_bound} {'X7'}")
        ln_flush_tran.writeAction(f"movir {pending_ack} {0}")
        ln_flush_tran.writeAction(f"movir {invalid_key} {self.cache_ival}")
        set_ev_label(ln_flush_tran, ack_evw, self.__flush_ack_ev_label)
        if (self.send_buffer_offset >> 15) > 0:
            ln_flush_tran.writeAction(f"movir {buffer_addr} {self.send_buffer_offset}")
            ln_flush_tran.writeAction(f"add {'X7'} {buffer_addr} {buffer_addr}")
        else:
            ln_flush_tran.writeAction(f"addi {'X7'} {buffer_addr} {self.send_buffer_offset}")
        ln_flush_tran.writeAction(f"{flush_loop_label}: bge {cache_offset} {cache_bound} {break_label}")
        ln_flush_tran.writeAction(f"movlr {0}({cache_offset}) {temp_key} 0 8")
        ln_flush_tran.writeAction(f"beq {temp_key} {invalid_key} {continue_label}")
        if self.debug_flag:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_lane_ev_label}] Flush key = %ld at lm_addr = %lu(0x%lx)' {'X0'} {temp_key} {cache_offset} {cache_offset}")
        ln_flush_tran.writeAction(f"sli {temp_key} {temp_key} 1")
        ln_flush_tran.writeAction(f"sri {temp_key} {temp_key} 1")
        if self.debug_flag and self.print_level > 2:
            for i in range(self.cache_entry_size - 1):
                ln_flush_tran.writeAction(f"movlr {WORD_SIZE * (i+1)}({cache_offset}) {scratch[i]} 0 8")
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_lane_ev_label}] Flush key = %lu at lm_addr = %lu(0x%lx), values = " + 
                                     f"[{' '.join(['%ld' for _ in range(self.cache_entry_size - 1)])}]' {'X0'} {temp_key} {cache_offset} {cache_offset} {' '.join(scratch)}")
        ln_flush_tran.writeAction(f"addi {cache_offset} {cache_offset} {WORD_SIZE}")
        self.data_store.flush_pair(ln_flush_tran, ack_evw, temp_key, cache_offset, buffer_addr, pending_ack, scratch)
        # ln_flush_tran.writeAction(f"addi {counter} {counter} 1")
        ln_flush_tran.writeAction(f"jmp {flush_loop_label}")
        ln_flush_tran.writeAction(f"{continue_label}: addi {cache_offset} {cache_offset} {self.cache_entry_bsize}")
        if self.debug_flag and self.print_level > 3:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_lane_ev_label}] Invalid key %ld, skip flush' {'X0'} {temp_key}")
        ln_flush_tran.writeAction(f"jmp {flush_loop_label}")
        # Finish sending all the cached key-value pairs.
        ln_flush_tran.writeAction(f"{break_label}: beqi {pending_ack} {0} {empty_cache_label}")
        ln_flush_tran.writeAction(f"yield")
        
        # Immediately return if cache is empty
        set_ignore_cont(ln_flush_tran, temp_reg, label=empty_cache_label)
        ln_flush_tran.writeAction(f"sendr_wcont {saved_cont} {temp_reg} {'X2'} {cache_bound} ")
        if self.debug_flag and self.print_level > 5:
            ln_flush_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_ack_ev_label}] Flush complete, empty cache, return to continuation %lu' {'X0'} {saved_cont}")
        ln_flush_tran.writeAction(f"yieldt")
        
        '''
        Event:      Flush ack, return to user passed in continuation.
        '''
        flush_ack_tran.writeAction(f"subi {pending_ack} {pending_ack} 1")
        flush_ack_tran.writeAction(f"bnei {pending_ack} 0 {continue_label}")
        set_ignore_cont(flush_ack_tran, temp_reg)
        flush_ack_tran.writeAction(f"sendr_wcont {saved_cont} {temp_reg} {'X2'} {cache_bound} ")
        if self.debug_flag and self.print_level > 3:
            flush_ack_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.__flush_ack_ev_label}] Flush complete, return to global master %lu' {'X0'} {saved_cont}")
        flush_ack_tran.writeAction(f"yieldt")
        flush_ack_tran.writeAction(f"{continue_label}: yield")
        
        return
    
    def __combine_func(self, tran: EFAProgram.Transition, key: str, values: list, cached_values: list, result_regs: list, scratch_regs: list, combine_fail_label: str, label_prefix: str):
        '''
        Default combine function.
        Parameters:
            tran:               EFAProgram.Transition
            key:                Register name of the key to be updated
            values:             list of Register names of the values to be updated. List length equals to value_size.
            cached_values:      list of Register names of the cached values. List length equals to value_size.
            result_regs:        list of Register names for storing the combined results. List length equals to value_size.
            combine_fail_label: Branch label for failure.
            label_prefix:       Prefix for the branch labels. 
        '''
        
        for i in range(self.value_size):
            tran.writeAction(f"bge {values[0]} {cached_values[0]} {combine_fail_label}")
            tran.writeAction(f"add {values[i]} {cached_values[i]} {result_regs[i]}")
            
        return tran
        
    def __get_cache_loc(self, tran: EFAProgram.Transition, key: list, num_lanes_mask: str, base_nwid: str, dest_id: str):
        
        tran.writeAction(f"movir {dest_id} {self.hash_seed}")
        for k in key:
            tran.writeAction(f"hash {k} {dest_id}")
        tran.writeAction(f"and {dest_id} {num_lanes_mask} {dest_id}")
        tran.writeAction(f"add {dest_id} {base_nwid} {dest_id}")
        
        return tran

@efaProgram
def GenLinkableLMCache(efa: EFAProgram):
    
    efa.code_level = 'machine'
    state = efa.State()
    efa.add_initId(state.state_id)
    
    LMCache(state=state, identifier="linkable_lm_cache", cache_offset = CACHE_LM_OFFSET, num_entries = CACHE_NUM_ENTRIES, policy=LMCache.Policy.WRITE_BACK, 
            entry_size = CACHE_ENTRY_SIZE, data_store = DATA_STORE, metadata_offset = SEND_BUFFER_OFFSET, debug_flag = DEBUG_FLAG)
    
    
    return efa
