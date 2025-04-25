from typing import Tuple
from EFA_v2 import *
from abc import ABCMeta
from abc import abstractmethod

class KeyValueSetTemplate(metaclass=ABCMeta):
    
    def __init__(self, name: str, key_size: int, value_size: int):
        self.name = name
        self.key_size = key_size
        self.value_size = value_size
        self.pair_size = key_size + value_size
        self.meta_data_size = 0
        print(f"{self.name} kvset: key size = {key_size}, value size = {value_size}, pair size = {self.pair_size}")
    
    '''
    size: size of the metadata in words
    offset: offset of the metadata in bytes
    '''
    def set_meta_data(self, size: int, offset: int):
        self.meta_data_size = size
        self.meta_data_offset = offset
        print(f"{self.name} kvset: metadata size = {size}, offset = {offset}")
    
    @abstractmethod
    def get_next_pair(self, tran: Transition, curr_pair: str, regs: list) -> Tuple[Transition, str]:
        pass
    
    @abstractmethod
    def get_pair(self, tran: Transition, key: str, addr_reg: str, regs: list) -> Transition:
        pass
    
    @abstractmethod
    def generate_partitions(self, tran: Transition, num_partitions: int, part_arry_base: str):
        pass