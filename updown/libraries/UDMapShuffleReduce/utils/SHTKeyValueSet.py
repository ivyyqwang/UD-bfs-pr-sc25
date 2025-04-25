from linker.EFAProgram import EFAProgram
from LinkableKeyValueSetTPL import KeyValueSetInterface
from libraries.ScalableHashTable.linkable.sht_ext_call_macros import SHTExt
from libraries.ScalableHashTable.linkable.sht_call_macros import SHT
from Macro import *

class SHTKeyValueSet(KeyValueSetInterface):
    '''
    Multi-word-value Scalable Hash Table (SHT_ext)
    '''
    SHT_DESC_SIZE = 4
    ITERATOR_SIZE = 2
    
    def __init__(self, name: str, key_size: int = 1, value_size: int = 1, argument_size: int = 0):
        '''
        Initialize the one dimensional key value set.
        Parameters:
            name:           identifier of the  key value set
            key_size:       size of the SHT key (in words)
            value_size:     size of the SHT values (in words)
        '''
        super().__init__(name.replace(' ', '_'), key_size, value_size if value_size <= DRAM_MSG_SIZE else DRAM_MSG_SIZE, self.SHT_DESC_SIZE + argument_size, self.ITERATOR_SIZE)
        self.num_get_status_ops = 2
        self.num_get_next_ops = 2
        self.add_trans_flag = False
    
    def get_pair_ops(self) -> list:
        return [f"X{OB_REG_BASE + i}" for i in range(self.num_get_status_ops)]
    
    def put_pair_ops(self) -> list:
        return [f"X{OB_REG_BASE + i}" for i in range(self.num_get_status_ops)]
    
    def get_pair_value_ops(self) -> list:
        return [f"X{OB_REG_BASE + i + self.num_get_status_ops}" for i in range(self.value_size)]
    
    def get_next_pair(self, tran: EFAProgram.Transition, cont_evw: str, map_ev_word: str, map_ev_label: str, iterator: list, regs: list, reach_end_label: str) -> EFAProgram.Transition:
        
        self.get_next_ret_ev_label  = get_event_label(self.name, "receive_next_pair")
        self.rd_values_ev_label     = get_event_label(self.name, "read_sht_values")
        
        tran.writeAction(f"sari {iterator[1]} {regs[0]} 32")
        tran.writeAction(f"blti {regs[0]} {0} {reach_end_label}")
        if self.value_size > 0: tran.writeAction(f"evlb {map_ev_word} {self.get_next_ret_ev_label}")
        SHTExt.get_next_split_wcont(tran, cont_evw, regs[0], iterator[0], iterator[1], map_ev_word)
        
        if not self.add_trans_flag: self.get_values(map_ev_label)
        
        return tran
    
    def get_values(self, map_ev_label: str):
        
        self.add_trans_flag = True
        
        get_next_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.get_next_ret_ev_label)
        
        rd_values_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.rd_values_ev_label)
        
        get_next_ops = [f"X{OB_REG_BASE + i}" for i in range(self.num_get_next_ops)]
        
        '''
        Event:      Initialize map thread
        Operands:   X8: Key
                    X9: Value address
        '''
        saved_key   = [f'X{GP_REG_BASE + k}' for k in range(self.key_size)]
        temp_evw    = f'X{GP_REG_BASE + self.key_size + 1}'
        lm_addr     = f'X{GP_REG_BASE + self.key_size + 2}'
        if self.debug_flag :
            get_next_ret_tran.writeAction(f"print ' '")
            get_next_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.name}] Event <{self.get_next_ret_ev_label}> " + 
                                         f"key = %ld, value_addr = %lu(0x%lx)' {'X0'} {'X8'} {'X9'} {'X9'}")
        get_next_ret_tran.writeAction(f"addi {'X2'} {temp_evw} 0")
        get_next_ret_tran.writeAction(f"evlb {temp_evw} {self.rd_values_ev_label}")
        get_next_ret_tran.writeAction(f"send_dmlm_ld {get_next_ops[1]} {temp_evw} {self.value_size}")
        for k in range(self.key_size):
            get_next_ret_tran.writeAction(f"addi {get_next_ops[k]} {saved_key[k]} {0}")
        get_next_ret_tran.writeAction(f"evlb {temp_evw} {map_ev_label}")
        get_next_ret_tran.writeAction(f"yield")

        '''
        Event:      Read the values of the assigned key-value pair
        Operands:   X8 ~ Xn: Values
        '''
        if self.debug_flag:
            rd_values_tran.writeAction(f"print ' '")
            rd_values_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.name}] Event <{self.rd_values_ev_label}> key = [{' '.join([ f'%ld' for _ in range((self.key_size))])}] values = " + 
                                       f"[{' '.join([ f'%ld' for _ in range((self.value_size))])}]' {'X0'} {' '.join(saved_key)} {' '.join([f'X{OB_REG_BASE + n}' for n in range(self.value_size)])}")
        if self.send_buffer_offset >> 15 > 0:
            rd_values_tran.writeAction(f"movir {lm_addr} {self.send_buffer_offset}")
            rd_values_tran.writeAction(f"add {lm_addr} {'X7'} {lm_addr}")
        else:
            rd_values_tran.writeAction(f"addi {'X7'} {lm_addr} {self.send_buffer_offset}")
        for k in range(self.key_size):
            rd_values_tran.writeAction(f"movrl {saved_key[k]} {k * WORD_SIZE}({lm_addr}) 0 8")
        for k in range(self.value_size):
            rd_values_tran.writeAction(f"movrl {f'X{OB_REG_BASE + k}'} {(k + self.key_size) * WORD_SIZE}({lm_addr}) 0 8")
        rd_values_tran.writeAction(f"send_wcont {temp_evw} {'X2'} {lm_addr} {self.value_size + 1}")
        rd_values_tran.writeAction(f"yield")
        
        return
    
    def get_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movir {regs[0]} {self.meta_data_offset}")
        SHTExt.get_wcont(tran, cont_evw, regs[1], regs[0], key)
        return tran
    
    def put_pair(self, tran: EFAProgram.Transition, cont_evw: str,  key: str, values: list, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        temp_val = regs[0]
        buffer_offset = regs[1]
        tran.writeAction(f"sub {buffer_addr} {'X7'} {buffer_offset}")
        tran.writeAction(f"sli {buffer_offset} {temp_val} {32}")
        tran.writeAction(f"ori {temp_val} {temp_val} {self.meta_data_offset}")
        tran.writeAction(f"movrl {temp_val} 0({buffer_addr}) 0 8")
        tran.writeAction(f"movrl {key} 8({buffer_addr}) 0 8")
        tran.writeAction(f"addi {buffer_addr} {temp_val} {16}")
        for v in values:
            tran.writeAction(f"movrl {v} 0({temp_val}) 1 8")
        SHTExt.update_wcont(tran, cont_evw, temp_val, buffer_addr, self.value_size)
        return tran
    
    def flush_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, value_addr: str, buffer_addr: str, num_acks: str, regs: list) -> EFAProgram.Transition:
        temp_val = regs[0]
        buffer_offset = regs[1]
        tran.writeAction(f"sub {buffer_addr} {'X7'} {buffer_offset}")
        tran.writeAction(f"sli {buffer_offset} {temp_val} {32}")
        tran.writeAction(f"ori {temp_val} {temp_val} {self.meta_data_offset}")
        tran.writeAction(f"movrl {temp_val} 0({buffer_addr}) 0 8")
        tran.writeAction(f"movrl {key} 8({buffer_addr}) 0 8")
        tran.writeAction(f"addi {buffer_addr} {temp_val} {16}")
        tran.writeAction(f"bcpylli {value_addr} {temp_val} {self.value_size << LOG2_WORD_SIZE}")
        SHTExt.update_wcont(tran, cont_evw, temp_val, buffer_addr, self.value_size)
        # tran.writeAction(f"subi {value_addr} {value_addr} {self.element_bsize}")
        tran.writeAction(f"addi {num_acks} {num_acks} {1}")
        return tran
    
    def generate_partitions(self, tran: EFAProgram.Transition, cont_evw: str, part_arry_base: str, num_partitions: str, num_lanes: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movir {regs[1]} {self.meta_data_offset}")
        SHTExt.get_iterators_wcont(tran, cont_evw, regs[0], regs[1], part_arry_base)
        return tran
        
    def check_iter(self, tran: EFAProgram.Transition, iterator: list, regs: list, pass_end_label: str) -> EFAProgram.Transition:
        tran.writeAction(f"sari {iterator[1]} {regs[0]} 32")
        tran.writeAction(f"blti {regs[0]} {-1} {pass_end_label}")
        return tran
        
    def check_get_pair(self, tran: EFAProgram.Transition, key: str, get_return_ops: list, get_fail_label: str) -> EFAProgram.Transition:
        tran.writeAction(f"beqi {get_return_ops[1]} {0} {get_fail_label}")
        return tran
    
class SingleWordSHTKeyValueSet(KeyValueSetInterface):
    '''
    Single-word-value Scalable Hash Table (SHT)
    '''
    KEY_SIZE        = 1
    VALUE_SIZE      = 1
    SHT_DESC_SIZE   = 5
    ITERATOR_SIZE   = 2
    
    def __init__(self, name: str, ):
        '''
        Initialize the one dimensional key value set.
        Parameters:
            name:           identifier of the  key value set
        '''
        super().__init__(name.replace(' ', '_'), self.KEY_SIZE, self.VALUE_SIZE, self.SHT_DESC_SIZE, self.ITERATOR_SIZE)
        self.num_get_status_ops = 2
        
    def get_pair_ops(self) -> list:
        return [f"X{OB_REG_BASE + i}" for i in range(self.num_get_status_ops)]
    
    def put_pair_ops(self) -> list:
        return [f"X{OB_REG_BASE + i}" for i in range(self.num_get_status_ops)]
    
    def get_pair_value_ops(self) -> list:
        return [f"X{OB_REG_BASE + i + self.num_get_status_ops}" for i in range(self.value_size)]
    
    def get_next_pair(self, tran: EFAProgram.Transition, cont_evw: str, map_ev_word: str, map_ev_label: str, iterator: list, regs: list, reach_end_label: str) -> EFAProgram.Transition:
        
        tran.writeAction(f"sari {iterator[1]} {regs[0]} 32")
        tran.writeAction(f"blti {regs[0]} {0} {reach_end_label}")
        SHT.get_next_split_wcont(tran=tran, ret=cont_evw, tmp_reg=regs[0], iter_word0_reg=iterator[0], iter_word1_reg=iterator[1], key_val_cont_reg=map_ev_word)
                
        return tran
    
    def get_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movir {regs[0]} {self.meta_data_offset}")
        SHT.get_wcont(tran=tran, ret=cont_evw, tmp_reg=regs[1], desc_lm_offset_reg=regs[0], key_reg=key)
        return tran
    
    def put_pair(self, tran: EFAProgram.Transition, cont_evw: str,  key: str, values: list, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        temp_val = regs[0]
        buffer_offset = regs[1]
        tran.writeAction(f"sub {buffer_addr} {'X7'} {buffer_offset}")
        tran.writeAction(f"movrl {buffer_offset} 0({buffer_addr}) 0 8")
        tran.writeAction(f"movir {temp_val} {self.meta_data_offset}")
        tran.writeAction(f"movrl {temp_val} 8({buffer_addr}) 0 8")
        tran.writeAction(f"movrl {key} 16({buffer_addr}) 0 8")
        tran.writeAction(f"addi {buffer_addr} {temp_val} {16}")
        for v in values:
            tran.writeAction(f"movrl {v} 0({temp_val}) 1 8")
        SHT.update_wcont(tran=tran, ret=cont_evw, tmp_reg0=temp_val, arg_lm_addr_reg=buffer_addr)
        return tran
    
    def flush_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, value_addr: str, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        temp_val = regs[0]
        buffer_offset = regs[1]
        tran.writeAction(f"sub {buffer_addr} {'X7'} {buffer_offset}")
        tran.writeAction(f"movrl {buffer_offset} 0({buffer_addr}) 0 8")
        tran.writeAction(f"movir {temp_val} {self.meta_data_offset}")
        tran.writeAction(f"movrl {temp_val} 8({buffer_addr}) 0 8")
        tran.writeAction(f"movrl {key} 16({buffer_addr}) 0 8")
        tran.writeAction(f"addi {buffer_addr} {temp_val} {16}")
        tran.writeAction(f"bcpylli {value_addr} {temp_val} {self.value_size << LOG2_WORD_SIZE}")
        SHTExt.update_wcont(tran, cont_evw, temp_val, buffer_addr, self.value_size)
        # tran.writeAction(f"subi {value_addr} {value_addr} {self.element_bsize}")
        return tran
    
    def generate_partitions(self, tran: EFAProgram.Transition, cont_evw: str, part_arry_base: str, num_partitions: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movir {regs[1]} {self.meta_data_offset}")
        SHT.get_iterators_wcont(tran=tran, ret=cont_evw, tmp_reg=regs[0], desc_lm_offset_reg=regs[1], iter_dram_addr_reg=part_arry_base)
        return tran
        
    def check_iter(self, tran: EFAProgram.Transition, iterator: list, regs: list, pass_end_label: str) -> EFAProgram.Transition:
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][{self.name}] Event <check_iter> iterator = %ld' {iterator[1]}")
        tran.writeAction(f"blti {iterator[1]} {-1} {pass_end_label}")
        return tran
        
    def check_get_pair(self, tran: EFAProgram.Transition, key: str, get_return_ops: list, get_fail_label: str) -> EFAProgram.Transition:
        tran.writeAction(f"beqi {get_return_ops[0]} {0} {get_fail_label}")
        return tran