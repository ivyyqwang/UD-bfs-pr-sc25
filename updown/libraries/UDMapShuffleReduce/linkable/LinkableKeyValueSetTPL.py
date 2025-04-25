from linker.EFAProgram import EFAProgram
from abc import ABCMeta, abstractmethod

class KeyValueSetInterface(metaclass=ABCMeta):
    
    def __init__(self, name: str, key_size: int, value_size: int, meta_data_size: int = 0, iter_size: int = 1):
        self.name = name
        self.key_size = key_size
        self.value_size = value_size
        self.pair_size = key_size + value_size
        self.iter_size = iter_size
        self.meta_data_size = meta_data_size
    
    def setup_kvset(self, state: EFAProgram.State, lm_offset: int, send_buffer_offset: int, debug_flag: bool = False):
        self.state = state
        self.meta_data_offset = lm_offset
        self.send_buffer_offset = send_buffer_offset
        self.debug_flag = debug_flag
        if self.debug_flag:
            print(f"{self.name} kvset: key size = {self.key_size}, value size = {self.value_size}, pair size = {self.pair_size}, meta data size = {self.meta_data_size}, iterator size = {self.iter_size}")
            print(f"Setting up {self.name} kvset at offset {self.meta_data_offset}")
    
    @abstractmethod
    def get_pair_ops(self) -> list:
        pass
    
    @abstractmethod
    def put_pair_ops(self) -> list:
        pass
    
    def get_pair_value_ops(self) -> list:
        return self.get_pair_ops()
    
    @abstractmethod
    def get_next_pair(self, tran: EFAProgram.Transition, cont_evw: str, map_ev_word: str, map_ev_label: str, iterator: list, regs: list, reach_end_label: str) -> EFAProgram.Transition:
        pass
    
    @abstractmethod
    def get_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, regs: list) -> EFAProgram.Transition:
        pass
    
    @abstractmethod
    def put_pair(self, tran: EFAProgram.Transition, cont_evw: str,  key: str, values: list, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        pass
    
    @abstractmethod
    def flush_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, value_addr: str, buffer_addr: str, num_acks: str, regs: list) -> EFAProgram.Transition:
        pass
    
    @abstractmethod
    def generate_partitions(self, tran: EFAProgram.Transition, cont_evw: str, part_arry_base: str, num_partitions: str, num_lanes: str, regs: list) -> EFAProgram.Transition:
        pass
    
    @abstractmethod
    def check_iter(self, tran: EFAProgram.Transition, iterator: list, regs: list, pass_end_label: str) -> EFAProgram.Transition:
        pass
    
    @abstractmethod
    def check_get_pair(self, tran: EFAProgram.Transition, key: str, get_return_ops: list, get_fail_label: str) -> EFAProgram.Transition:
        pass