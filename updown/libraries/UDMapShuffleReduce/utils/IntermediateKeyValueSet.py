from linker.EFAProgram import efaProgram, EFAProgram

from libraries.UDMapShuffleReduce.linkable.LinkableKeyValueSetTPL import KeyValueSetInterface

class IntermediateKeyValueSet(KeyValueSetInterface):
    '''
    Example implementation of an non-materialized key value set for intermediate output of kv_map.
    '''

    def __init__(self, name: str, key_size: int, value_size: int):
        super().__init__(name, key_size, value_size)
        
    def get_pair_ops(self) -> list:
        pass
    
    def put_pair_ops(self) -> list:
        pass

    def get_next_pair(self, tran: EFAProgram.Transition, cont_evw: str, map_init_ev_word: str, iterator: list, regs: list, reach_end_label: str) -> EFAProgram.Transition:
        pass
    
    def get_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, regs: list) -> EFAProgram.Transition:
        pass
    
    def put_pair(self, tran: EFAProgram.Transition, cont_evw: str,  key: str, values: list, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        pass
    
    def flush_pair(self, tran: EFAProgram.Transition, cont_evw: str, key: str, value_addr: str, buffer_addr: str, regs: list) -> EFAProgram.Transition:
        pass
    
    def generate_partitions(self, tran: EFAProgram.Transition, cont_evw: str, part_arry_base: str, num_partitions: str, num_lanes: str, regs: list) -> EFAProgram.Transition:
        pass
    
    def check_iter(self, tran: EFAProgram.Transition, iterator: list, regs: list, pass_end_label: str) -> EFAProgram.Transition:
        pass
    
    def check_get_pair(self, tran: EFAProgram.Transition, key: str, get_return_ops: list, get_fail_label: str) -> EFAProgram.Transition:
        pass