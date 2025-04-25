from linker.EFAProgram import EFAProgram

from LinkableGlobalSync import Broadcast
from libraries.UDMapShuffleReduce.linkable.LinkableKeyValueSetTPL import KeyValueSetInterface
from KVMSRMachineConfig import WORD_SIZE, LOG2_WORD_SIZE, OB_REG_BASE
from math import log2
from Macro import *
import itertools

class OneDimKeyValueSet(KeyValueSetInterface):
    ITERATOR_SIZE = 2
    '''
    Implementation of an one dimensional key value set.
    '''

    def __init__(self, name: str, element_size: int, metadata_size: int = 2, argument_size: int = 0, bypass_gen_partition: bool = False):
        '''
        Initialize the one dimensional key value set.
        Parameters:
            name:           identifier of the  key value set
            element_size:   size of each element (in words) in the key value set
            metadata_size:  size of the metadata (in words) stored on each lane's scratchpad. Default is 2.
                            First word for array base address, second for size of the array.
            argument_size:  size of user argument (in words) stored on each lane's scratchpad in addition to the metadata. Default is 0.
            state:          EFA state to add transition. Required if partition array is generated on UpDown. Default is None.
        '''
        super().__init__(name.replace(' ', '_'), 0, element_size, metadata_size + argument_size, self.ITERATOR_SIZE)
        self.element_size       = element_size
        self.log2_element_size  = int(log2(element_size))
        self.element_bsize      = element_size * WORD_SIZE
        self.log2_element_bsize = int(log2(self.element_bsize))
        self.iter_bsize         = self.iter_size * WORD_SIZE
        self.log2_iter_bsize    = int(log2(self.iter_bsize))
        self.num_get_next_ops   = 2
        self.bypass_gen_partition = bypass_gen_partition
        self.power_of_two    = element_size & (element_size - 1) == 0
    
    def setup_kvset(self, state: EFAProgram.State, lm_offset: int, send_buffer_offset: int, debug_flag: bool = False):
        
        super().setup_kvset(state, lm_offset, send_buffer_offset, debug_flag)
        self.gen_part_ev_label     = get_event_label(self.name, "generate_partition_array")
        self.write_part_ev_label     = get_event_label(self.name, "write_partition_array")
        self.write_part_ret_ev_label = get_event_label(self.name, "write_partition_array_return")
        self.gen_part_sync_ev_label = get_event_label(self.name, "generate_partition_array_sync")

    def get_pair_ops(self) -> list:
        return [f"X{OB_REG_BASE + i}" for i in range(self.pair_size)]
    
    def put_pair_ops(self) -> list:
        return [f"X{OB_REG_BASE + i}" for i in range(1)]

    def get_next_pair(self, tran: EFAProgram.Transition, cont_evw: str, map_ev_word: str, map_ev_label: str, iterator: list, regs: list, reach_end_label: str) -> EFAProgram.Transition:
        tran.writeAction(f"bge {iterator[0]} {iterator[1]} {reach_end_label}")
        tran.writeAction(f"addi {iterator[0]} {regs[0]} {self.element_bsize}")
        tran.writeAction(f"sendr_wcont {cont_evw} {cont_evw} {regs[0]} {iterator[1]}")
        tran.writeAction(f"send_dmlm_ld {iterator[0]} {map_ev_word} {self.element_size}")
        return tran
    
    def get_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"move {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")
        if self.power_of_two:
            tran.writeAction(f"lshift {key} {regs[1]} {self.log2_element_size + LOG2_WORD_SIZE}")
        else:
            tran.writeAction(f"muli {key} {regs[1]} {self.element_bsize * WORD_SIZE}")
        tran.writeAction(f"add {regs[1]} {regs[0]} {regs[0]}")
        tran.writeAction(f"send_dmlm_ld {regs[0]} {cont_evw} {self.element_size}")
        return tran

    def put_pair(self, tran: EFAProgram.Transition, cont_evw: str,  key: str, values: list, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movlr {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")
        if self.power_of_two:
            tran.writeAction(f"lshift {key} {regs[1]} {self.log2_element_size + LOG2_WORD_SIZE}")
        else:
            tran.writeAction(f"muli {key} {regs[1]} {self.element_bsize * WORD_SIZE}")
        tran.writeAction(f"add {regs[1]} {regs[0]} {regs[0]}")
        for val in values:
            tran.writeAction(f"movrl {val} 0({buffer_addr}) 1 {WORD_SIZE}")
        tran.writeAction(f"subi {buffer_addr} {buffer_addr} {self.element_bsize}")
        tran.writeAction(f"send_dmlm {regs[0]} {cont_evw} {buffer_addr} {self.element_size}")
        return tran
    
    def flush_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, value_addr: str, buffer_addr: str, num_acks: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movlr {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")
        if self.power_of_two:
            tran.writeAction(f"lshift {key} {regs[1]} {self.log2_element_size + LOG2_WORD_SIZE}")
        else:
            tran.writeAction(f"muli {key} {regs[1]} {self.element_bsize * WORD_SIZE}")
        tran.writeAction(f"add {regs[1]} {regs[0]} {regs[0]}")
        tran.writeAction(f"send_dmlm {regs[0]} {cont_evw} {value_addr} {self.element_size}")
        tran.writeAction(f"addi {value_addr} {value_addr} {self.element_bsize}")
        tran.writeAction(f"addi {num_acks} {num_acks} {1}")
        return tran

    def generate_partitions(self, tran: EFAProgram.Transition, cont_evw: str, part_arry_base: str, num_partitions: str, num_lanes: str, regs: list) -> EFAProgram.Transition:
        if self.bypass_gen_partition:
            tran.writeAction(f"sendr_wcont {cont_evw} {cont_evw} {part_arry_base} {num_partitions} ")
        else:
            set_ev_label(tran, regs[0], self.gen_part_ev_label, new_thread=True)
            tran.writeAction(f"sendr3_wcont {regs[0]} {cont_evw} {part_arry_base} {num_partitions} {num_lanes}")
            self.__generate_partition()
            
        return tran

    def check_iter(self, tran: EFAProgram.Transition, iterator: list, regs: list, pass_end_label: str) -> EFAProgram.Transition:
        # No operation needed for one dimensional array
        pass
    
    def check_get_pair(self, tran: EFAProgram.Transition, key: str, get_return_ops: list, get_fail_label: str) -> EFAProgram.Transition:
        # No operation needed for one dimensional array
        pass
    
    def __generate_partition(self):
        
        gen_part_broadcast = Broadcast(self.state, self.name, self.debug_flag)
        
        gen_part_tran: EFAProgram.Transition = self.state.writeTransition("eventCarry", self.state, self.state, self.gen_part_ev_label)

        write_part_tran: EFAProgram.Transition = self.state.writeTransition("eventCarry", self.state, self.state, self.write_part_ev_label)
        
        write_part_ret_tran: EFAProgram.Transition = self.state.writeTransition("eventCarry", self.state, self.state, self.write_part_ret_ev_label)

        gen_part_sync_tran: EFAProgram.Transition = self.state.writeTransition("eventCarry", self.state, self.state, self.gen_part_sync_ev_label)
        
        part_array_base_op = "X8"
        num_lanes_ops       = 'X10'
        self.send_buffer_offset = self.meta_data_offset - 8 * WORD_SIZE
        self.SEND_BUFFER_SIZE = 8
        
        regs: list  = [f'X{GP_REG_BASE + i}' for i in range(16)]
        saved_cont      = regs[0]
        array_end_addr  = regs[1]
        part_array_ptr  = regs[2]
        array_ptr       = regs[3]
        num_elements    = regs[4]
        num_partitions  = regs[5]
        num_ele_per_part    = regs[6]
        part_stride     = regs[7]
        part_array_end_addr = regs[8]
        send_buffer_ptr = regs[9]
        next_part_ptr   = regs[9]
        lane_nwid_offset    = regs[10]
        write_ret_ev_word   = regs[11]
        write_part_ev_word  = regs[11]
        num_part_per_lane   = regs[12]
        
        scratch = regs[-3:]
        
        mod_zero_label  = "modular_eq_zero"
        write_loop_label= "write_partition_array_loop"
        break_label     = "loop_break"
        continue_label  = "continue"
        
        '''
        Event:      Generate the partition array based on number of partitions and number of elements in the array.
        Operands:   X8:   Pointer to the partition array (64-bit DRAM address)
                    X9:   Number of partitions
                    X10:  Number of lanes
        '''
        gen_part_tran.writeAction(f"addi {'X9'} {num_partitions} 0")
        if self.debug_flag:
            gen_part_tran.writeAction(f"print ' '")
            gen_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.gen_part_ev_label}] Event <{self.gen_part_ev_label}> ev_word = %lu income_cont = %lu " + 
                             f"partition_array_base = %lu(0x%lx) num_partitions = %ld num_lanes = %d' {'X0'} {'EQT'} {'X1'} {part_array_base_op} {part_array_base_op} {num_partitions} {num_lanes_ops}")
        gen_part_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        # Read array base address and size from scratchpad
        if self.meta_data_offset >> 15 > 0:
            gen_part_tran.writeAction(f"movir {scratch[0]} {self.meta_data_offset}")
            gen_part_tran.writeAction(f"add {scratch[0]} {'X7'} {scratch[0]}")
        else:
            gen_part_tran.writeAction(f"addi {'X7'} {scratch[0]} {self.meta_data_offset}")
        gen_part_tran.writeAction(f"movlr 0({scratch[0]}) {array_ptr} 1 {WORD_SIZE}")
        gen_part_tran.writeAction(f"movlr 0({scratch[0]}) {num_elements} 1 {WORD_SIZE}")
        # Calculate the end address of the array
        if self.power_of_two:
            gen_part_tran.writeAction(f"sli {num_elements} {array_end_addr} {self.log2_element_bsize}")
        else:
            gen_part_tran.writeAction(f"muli {num_elements} {array_end_addr} {self.element_bsize}")
        gen_part_tran.writeAction(f"add {array_ptr} {array_end_addr} {array_end_addr}")
        if self.debug_flag:
            gen_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.gen_part_ev_label}] Calculate {self.name} partition array addresses array_base = %lu(0x%lx) " + 
                                        f"array_end_addr = %lu(0x%lx)' {'X0'} {array_ptr} {array_ptr} {array_end_addr} {array_end_addr}")
        # Calculate number of pairs per partition
        gen_part_tran.writeAction(f"div {num_elements} {num_partitions} {num_ele_per_part}")
        gen_part_tran.writeAction(f"mul {num_ele_per_part} {num_partitions} {scratch[1]}")
        gen_part_tran.writeAction(f"beq {scratch[1]} {num_elements} {mod_zero_label}")
        gen_part_tran.writeAction(f"addi {num_ele_per_part} {num_ele_per_part} {1}")
        if self.power_of_two:
            gen_part_tran.writeAction(f"{mod_zero_label}: sli {num_ele_per_part} {part_stride} {self.log2_element_bsize}")
        else:
            gen_part_tran.writeAction(f"{mod_zero_label}: muli {num_ele_per_part} {part_stride} {self.element_bsize}")
        if self.debug_flag:
            gen_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.gen_part_ev_label}] Calculate number of pairs per partition num_elements = %ld num_partitions = %ld " + 
                             f"num_pair_per_part = %ld part_stride = %lu(0x%lx)' {'X0'} {num_elements} {num_partitions} {num_ele_per_part} {part_stride} {part_stride}")
        set_ev_label(gen_part_tran, scratch[0], gen_part_broadcast.get_broadcast_ev_label(), new_thread=True)
        gen_part_tran.writeAction(f"movir {send_buffer_ptr} {self.send_buffer_offset}")
        gen_part_tran.writeAction(f"add {'X7'} {send_buffer_ptr} {send_buffer_ptr}")
        gen_part_tran.writeAction(f"movrl {num_lanes_ops} 0({send_buffer_ptr}) 0 8")
        gen_part_tran.writeAction(f"movir {write_part_ev_word} 0")
        gen_part_tran.writeAction(f"evlb {write_part_ev_word} {self.write_part_ev_label}")
        gen_part_tran.writeAction(f"movrl {write_part_ev_word} {WORD_SIZE}({send_buffer_ptr}) 0 8")
        gen_part_tran.writeAction(f"movrl {part_array_base_op}  {WORD_SIZE * 2}({send_buffer_ptr}) 0 8")
        gen_part_tran.writeAction(f"movrl {array_ptr}  {WORD_SIZE * 3}({send_buffer_ptr}) 0 8")
        gen_part_tran.writeAction(f"movrl {num_ele_per_part} {WORD_SIZE * 4}({send_buffer_ptr}) 0 8")
        gen_part_tran.writeAction(f"div {num_partitions} {num_lanes_ops} {num_part_per_lane}")
        gen_part_tran.writeAction(f"movrl {num_part_per_lane} {WORD_SIZE * 5}({send_buffer_ptr}) 0 8")
        gen_part_tran.writeAction(f"movrl {num_elements} {WORD_SIZE * 6}({send_buffer_ptr}) 0 8")
        gen_part_tran.writeAction(f"movrl {'X0'} {WORD_SIZE * 7}({send_buffer_ptr}) 0 8")
        set_ev_label(gen_part_tran, write_part_ev_word, gen_part_broadcast.get_broadcast_ev_label(), new_thread=True)
        gen_part_tran.writeAction(f"send_wret {write_part_ev_word} {self.gen_part_sync_ev_label} {send_buffer_ptr} {self.SEND_BUFFER_SIZE} {scratch[0]}")
        gen_part_tran.writeAction(f"yield")


        '''
        Event:      Write to the partition array based on number of partitions and number of elements in the array.
        Operands:   X8:   Pointer to the partition array (64-bit DRAM address)
                    X9:   Pointer to the KVSet array
                    X10:  Number of elements per partition
                    X11:  Number of partitions per lane
                    X12:  Number of elements in the array
                    X13:  Base lane nwid
        '''
        array_base_op = "X9"
        num_ele_per_part_op = "X10"
        num_elements_op = "X12"
        # Write to the partition array
        write_part_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        write_part_tran.writeAction(f"addi {'X11'} {num_part_per_lane} 0")
        if self.debug_flag:
            write_part_tran.writeAction(f"print ' '")
            write_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ev_label}] Event <{self.write_part_ev_label}> partition_array_base = %lu(0x%lx) array_base = %lu(0x%lx) num_elements = %d " + 
                             f"num_elements_per_part = %ld num_part_per_lane = %d ' {'X0'} {part_array_base_op} {part_array_base_op} {array_base_op} {array_base_op} {num_elements_op} {num_ele_per_part_op} {num_part_per_lane}")
        if self.power_of_two:
            write_part_tran.writeAction(f"sli {num_ele_per_part_op} {part_stride} {self.log2_element_bsize}")
        else:
            write_part_tran.writeAction(f"muli {num_ele_per_part_op} {part_stride} {self.element_bsize}")
        set_ev_label(write_part_tran, write_ret_ev_word, self.write_part_ret_ev_label)

        # Calculate the partition array addresses
        write_part_tran.writeAction(f"sub {'X0'} {'X13'} {lane_nwid_offset}")
        write_part_tran.writeAction(f"mul {lane_nwid_offset} {num_part_per_lane} {num_partitions}")
        write_part_tran.writeAction(f"sli {num_partitions} {part_array_ptr} {self.log2_iter_bsize}")
        write_part_tran.writeAction(f"add {part_array_base_op} {part_array_ptr} {part_array_ptr}")
        write_part_tran.writeAction(f"sli {num_part_per_lane} {part_array_end_addr} {self.log2_iter_bsize}")
        write_part_tran.writeAction(f"add {part_array_ptr} {part_array_end_addr} {part_array_end_addr}")
        if self.debug_flag:
            write_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ev_label}] Starting from partition %ld. Calculate partition array addresses part_array_ptr = %lu(0x%lx) " + 
                                        f"lane_part_array_end_addr = %lu(0x%lx)' {'X0'} {num_partitions} {part_array_ptr} {part_array_ptr} {part_array_end_addr} {part_array_end_addr}")

        # Calculate the KVSet array addresses
        write_part_tran.writeAction(f"mul {num_ele_per_part_op} {num_partitions} {array_ptr}")
        if self.power_of_two:
            write_part_tran.writeAction(f"sli {array_ptr} {array_ptr} {self.log2_element_bsize}")
            write_part_tran.writeAction(f"add {array_base_op} {array_ptr} {array_ptr}")
            write_part_tran.writeAction(f"sli {num_elements_op} {array_end_addr} {self.log2_element_bsize}")
        else:
            write_part_tran.writeAction(f"muli {array_ptr} {array_ptr} {self.element_bsize}")
            write_part_tran.writeAction(f"add {array_base_op} {array_ptr} {array_ptr}")
            write_part_tran.writeAction(f"muli {num_elements_op} {array_end_addr} {self.element_bsize}")
        write_part_tran.writeAction(f"add {array_base_op} {array_end_addr} {array_end_addr}")
        if self.debug_flag:
            write_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ev_label}] Calculate array addresses array_ptr = %lu(0x%lx) " + 
                                        f"array_end_addr = %lu(0x%lx)' {'X0'} {array_ptr} {array_ptr} {array_end_addr} {array_end_addr}")
        write_part_tran.writeAction(f"ble {array_ptr} {array_end_addr} {write_loop_label}")
        write_part_tran.writeAction(f"addi {array_end_addr} {array_ptr} {0}")
        if self.debug_flag:
            write_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ev_label}] Reach array end array_ptr = %lu(0x%lx) array_end_addr = %lu(0x%lx)' " + 
                                        f"{'X0'} {array_ptr} {array_ptr} {array_end_addr} {array_end_addr}")
        # Write iterations to the partition array
        write_part_tran.writeAction(f"{write_loop_label}: bge {part_array_ptr} {part_array_end_addr} {break_label}")
        write_part_tran.writeAction(f"add {array_ptr} {part_stride} {next_part_ptr}")
        if self.debug_flag:
            write_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ev_label}] Calculate next_part_ptr = %lu(0x%lx)' " + 
                                        f"{'X0'} {next_part_ptr} {next_part_ptr} ")
        write_part_tran.writeAction(f"ble {next_part_ptr} {array_end_addr} {continue_label}")
        if self.debug_flag:
            write_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ev_label}] Reach array end next_part_ptr = %lu(0x%lx) array_end_addr = %lu(0x%lx)' " + 
                                        f"{'X0'} {next_part_ptr} {next_part_ptr} {array_end_addr} {array_end_addr}")
        write_part_tran.writeAction(f"addi {array_end_addr} {next_part_ptr} {0}")
        write_part_tran.writeAction(f"{continue_label}: sendr2_dmlm {part_array_ptr} {write_ret_ev_word} {array_ptr} {next_part_ptr}")
        if self.debug_flag:
            write_part_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ev_label}] Event <{self.write_part_ev_label}> write iterator [%lu(0x%lx), %lu(0x%lx)] " + 
                                        f"to part_array_ptr = %lu(%lx)' {'X0'} {array_ptr} {array_ptr} {next_part_ptr} {next_part_ptr} {part_array_ptr} {part_array_ptr}")
        write_part_tran.writeAction(f"addi {part_array_ptr} {part_array_ptr} {self.iter_bsize}")
        write_part_tran.writeAction(f"addi {next_part_ptr} {array_ptr} 0")
        write_part_tran.writeAction(f"jmp {write_loop_label}")
        write_part_tran.writeAction(f"{break_label}: yield")
        
        '''
        Event:      Write to the partition array acknowledgement
        Operands:   X8:   Pointer to the partition array (64-bit DRAM address)
        '''
        write_part_ret_tran.writeAction(f"subi {num_part_per_lane} {num_part_per_lane} {1}")
        write_part_ret_tran.writeAction(f"bnei {num_part_per_lane} {0} {continue_label}")
        if self.debug_flag:
            write_part_ret_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.write_part_ret_ev_label}] Finish generate the partition array return to " + 
                             f"%lu number of partition array write pending = %ld' {'X0'} {saved_cont} {num_part_per_lane}")
        write_part_ret_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {part_array_ptr} {num_partitions}")
        write_part_ret_tran.writeAction(f"yieldt")
        write_part_ret_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Finish generate the partition array
        '''
        gen_part_sync_tran.writeAction(f"sendr_wcont {saved_cont} {'X2'} {part_array_ptr} {num_partitions}")
        if self.debug_flag:
            gen_part_sync_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.gen_part_sync_ev_label}] Finish generate the partition array return to " + 
                             f"continuation = %lu' {'X0'} {saved_cont}")
        gen_part_sync_tran.writeAction(f"yieldt")
    
class MaskedOneDimKeyValueSet(OneDimKeyValueSet):
    
    def __init__(self, name: str, element_size: int, mask: str, argument_size: int = 0):
        metadata_size = 2
        super().__init__(name, element_size, metadata_size, argument_size)
        if len(mask) != element_size:
            raise ValueError(f"Mask length {len(mask)} does not match element size {element_size}")
        # left to right order, val_0 is the leftmost bit
        self.mask = mask
        self.mask_offset = list(itertools.compress([(k * WORD_SIZE) for k in range(element_size)], [int(i) for i in self.mask]))
        
        self.put_pair_sync_ev_label = get_event_label(self.name, "put_pair_sync")
        self.add_sync_tran_flag = False

    def get_pair_value_ops(self) -> list:
        ops = self.get_pair_ops()
        return list(itertools.compress(ops, [int(i) for i in self.mask]))
    
    def put_pair(self, tran: EFAProgram.Transition, cont_evw: str,  key: str, values: list, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movlr {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")
        if self.power_of_two:
            tran.writeAction(f"lshift {key} {regs[1]} {self.log2_element_size + LOG2_WORD_SIZE}")
        else:
            tran.writeAction(f"muli {key} {regs[1]} {self.element_bsize * WORD_SIZE}")
        tran.writeAction(f"add {regs[1]} {regs[0]} {regs[0]}")
        tran.writeAction(f"addi {'X2'} {regs[1]} {0}")
        tran.writeAction(f"evlb {regs[1]} {self.put_pair_sync_ev_label}")
        for offset, val in zip(self.mask_offset, values):
            tran.writeAction(f"addi {regs[0]} {buffer_addr} {offset}")
            tran.writeAction(f"sendr_dmlm {buffer_addr} {regs[1]} {val}")
        tran.writeAction(f"movir {regs[1]} {len(values)}")
        
        if not self.add_sync_tran_flag: self.put_pair_sync(tran, cont_evw, key, regs[1], regs)
        return tran

    def put_pair_sync(self, tran: EFAProgram.Transition, cont_evw: str, key: str, count: str, regs: list) -> EFAProgram.Transition:
        
        self.add_sync_tran_flag = True
        
        continue_label = "continue"
        sync_tran: EFAProgram.Transition = self.state.writeTransition("eventCarry", self.state, self.state, self.put_pair_sync_ev_label)
        if self.debug_flag:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.put_pair_sync_ev_label}] Event <{self.put_pair_sync_ev_label}> ev_word = %lu income_cont = %lu " + 
                             f"key = %lu count = %lu' {'X0'} {'EQT'} {'X1'} {key} {count}")
        sync_tran.writeAction(f"subi {count} {count} {1}")
        sync_tran.writeAction(f"bnei {count} {0} {continue_label}")
        sync_tran.writeAction(f"sendr_wcont {cont_evw} {cont_evw} {key} {count}")
        sync_tran.writeAction(f"{continue_label}: yield")

        return sync_tran
    
    def flush_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, value_addr: str, buffer_addr: str, num_acks: str, regs: list) -> EFAProgram.Transition:
        tran.writeAction(f"movlr {self.meta_data_offset}(X7) {regs[0]} 0 {WORD_SIZE}")
        if self.power_of_two:
            tran.writeAction(f"lshift {key} {regs[1]} {self.log2_element_size + LOG2_WORD_SIZE}")
        else:
            tran.writeAction(f"muli {key} {regs[1]} {self.element_bsize * WORD_SIZE}")
        tran.writeAction(f"add {regs[1]} {regs[0]} {regs[0]}")
        for offset in self.mask_offset:
            tran.writeAction(f"addi {regs[0]} {regs[1]} {offset}")
            tran.writeAction(f"send_dmlm {regs[1]} {cont_evw} {value_addr} {1}")
            tran.writeAction(f"addi {value_addr} {value_addr} {WORD_SIZE}")
            tran.writeAction(f"addi {num_acks} {num_acks} {1}")
        return tran