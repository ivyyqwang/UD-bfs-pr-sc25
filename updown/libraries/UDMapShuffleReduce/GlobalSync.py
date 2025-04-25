from EFA_v2 import *
from Macro import *
from KVMSRMachineConfig import *

class GlobalSync:

    def __init__(self, identifier: str, state: State, ev_word_reg: str, lm_offsets: int, scratch_regs: list, debug_flag = False, print_level = 0, send_temp_reg_flag = True):
        self.id = identifier
        self.state = state
        self.ev_word = ev_word_reg
        self.offsets = lm_offsets
        self.scratch = scratch_regs
        self.debug_flag = debug_flag
        self.print_level = print_level
        self.send_temp_reg_flag = send_temp_reg_flag

    def set_labels(self, global_init, global_sync, node_init, node_sync, ud_accum):
        self.glb_sync_init_ev_label = global_init
        self.global_sync_ev_label   = global_sync
        self.node_init_ev_label     = node_init
        self.node_sync_ev_label     = node_sync
        self.ud_accum_ev_label      = ud_accum
    
    def global_sync(self, continuation, sync_value, num_lanes):

        num_nodes       = "UDPR_0"
        num_ud_per_nd   = "UDPR_1"
        num_ln_per_ud   = "UDPR_2"
        self.saved_cont = "UDPR_3"
        lm_base         = "UDPR_4"
        
        max_node_label  = "max_node"
        max_ud_label    = "max_ud_per_nd"
        max_ln_label    = "max_ln_per_ud"
        self.sync_fin_label  = "sync_finish"

        self.global_init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_sync_init_ev_label)
        if self.debug_flag:
            self.global_init_tran.writeAction(f"print ' '")
            self.global_init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_global_sync> ev_word = %lu' {'X0'} {'EQT'}")
        
        get_num_node(self.global_init_tran, num_lanes, num_nodes, max_node_label, self.scratch[0])
        self.global_init_tran.writeAction(f"{max_node_label}: addi {num_nodes} {num_nodes} 0")
        get_num_ud_per_node(self.global_init_tran, num_lanes, num_ud_per_nd, max_ud_label, self.scratch[0])
        self.global_init_tran.writeAction(f"{max_ud_label}: addi {num_ud_per_nd} {num_ud_per_nd} 0")
        get_num_lane_per_ud(self.global_init_tran, num_lanes, num_ln_per_ud, max_ln_label)
        self.global_init_tran.writeAction(f"{max_ln_label}: addi {num_ln_per_ud} {num_ln_per_ud} 0")
        if self.debug_flag:
            self.global_init_tran.writeAction(f"print '[DEBUG][NWID %ld] init global synchronization num_nodes = %ld, num_ud_per_node = %ld, num_ln_per_ud = %ld' \
                {'X0'} {num_nodes} {num_ud_per_nd} {num_ln_per_ud}")
            
        if isinstance(continuation, str):
            self.global_init_tran.writeAction(f"mov_reg2reg {continuation} {self.saved_cont}")
        if isinstance(continuation, int):
            self.global_init_tran.writeAction(f"mov_imm2reg {self.saved_cont} 0")
            self.global_init_tran.writeAction(f"addi {'X7'} {lm_base} 0")
            self.global_init_tran.writeAction(f"move {self.saved_cont} {continuation}({lm_base}) 0 8")
            
        if sync_value[0:2] == "OB" or (sync_value[0] == 'X' and sync_value[1:].isdigit() and (int(sync_value[1:]) >= 8 or int(sync_value[1:]) < 16)):
            self.saved_sync_value   = "UDPR_5"
            self.curr_values        = [f"UDPR_{n+6}" for n in range(len(self.offsets))]
            self.global_init_tran.writeAction(f"mov_reg2reg {sync_value} {self.saved_sync_value}")
        else: 
            self.saved_sync_value   = sync_value
            self.curr_values        = [f"UDPR_{n+5}" for n in range(len(self.offsets))]
        if self.debug_flag:
            self.global_init_tran.writeAction(f"print '[DEBUG][NWID %ld] init global synchronization saved_sync_value = %ld' {'X0'} {self.saved_sync_value}")
        
        self.global_sync_tran = self.all_reduce(num_nodes, num_ud_per_nd, num_ln_per_ud)
    
        if isinstance(continuation, str):
            # Finish global synchonization, send reply to the source
            self.global_sync_tran.writeAction(f"{self.sync_fin_label}: sendr_wcont {self.saved_cont} EQT {self.curr_values[0]} {self.curr_values[0]}")
        if isinstance(continuation, int):
            # Finish global synchonization, set the flag in scratchpad
            self.global_sync_tran.writeAction(f"{self.sync_fin_label}: mov_imm2reg {self.scratch[0]} {FLAG}")
            self.global_sync_tran.writeAction(f"move {self.scratch[0]} {continuation}({lm_base}) 0 8")
        if self.debug_flag or self.print_level == 1:
            self.global_sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Global sync terminates, sync_value = %ld, curr_value = %ld' {'X0'} {self.saved_sync_value} {self.curr_values[0]}")
        self.global_sync_tran.writeAction("yield_terminate")

        return 

    def all_reduce(self, num_nodes, num_ud_per_nd, num_ln_per_ud):
        
        init_tran   = self.global_init_tran
        node_ctr    = "UDPR_4"

        # Broadcast to all the nodes, start all reduce
        init_tran = set_ev_label(init_tran, self.ev_word, self.node_init_ev_label, new_thread = True)
        init_tran = self.__broadcast(init_tran, self.ev_word, num_nodes, self.global_sync_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_nd} {num_ln_per_ud} ")
        init_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        # Initialize the temp sync values
        for i in range(len(self.offsets)):
            init_tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")
        
        init_tran.writeAction("yield")
        
        self.node_sync('X8', 'X9')
        self.updown_accumulate('X8')
        
        sync_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.global_sync_ev_label)
        if self.debug_flag:
            sync_tran.writeAction(f"print ' '")
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <global_sync> ev_word = %lu:' {'X0'} {'EQT'}")
        sync_tran.writeAction(f"addi {node_ctr} {node_ctr} 1")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"add {f'X{OB_REG_BASE+i}'} {self.curr_values[i]} {self.curr_values[i]}")
        if self.debug_flag:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] global synchronization node_ctr = %ld, sync_value = %ld, curr_value = %ld' {'X0'} {node_ctr} {self.saved_sync_value} {self.curr_values[0]}")
        sync_tran.writeAction(f"blt {node_ctr} {num_nodes} continue")
        sync_tran.writeAction(f"beq {self.curr_values[0]} {self.saved_sync_value} {self.sync_fin_label}")

        sync_tran = self.__broadcast(sync_tran, self.ev_word, num_nodes, self.global_sync_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_nd} {num_ln_per_ud} ")
        sync_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")

        sync_tran.writeAction("continue: yield")
        
        return sync_tran

    def node_sync(self, num_ud_per_nd, num_lane_per_ud):
                
        num_ud_per_nd_reg   = "UDPR_1"
        ud_ctr              = "UDPR_4"

        '''
        X8:   Number of UpDowns per node
        X9:   Global sync init event word
        '''
        init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.node_init_ev_label)
        if self.debug_flag:
            init_tran.writeAction(f"print ' '")
            init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_node_sync> ev_word=%ld:' {'X0'} {'EQT'}")
        init_tran.writeAction(f"mov_reg2reg {num_ud_per_nd} {num_ud_per_nd_reg}")
        init_tran = set_ev_label(init_tran, self.ev_word, self.ud_accum_ev_label, new_thread=True)
        init_tran = self.__broadcast(init_tran, self.ev_word, num_ud_per_nd_reg, self.node_sync_ev_label, \
            LOG2_LANE_PER_UD, f"{num_lane_per_ud} EQT ")
        init_tran.writeAction(f"mov_imm2reg {ud_ctr} 0")
        for i in range(len(self.offsets)):
            init_tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")
        init_tran.writeAction(f"mov_reg2reg X1 {self.saved_cont}")
        if self.debug_flag:
            init_tran.writeAction(f"print '[DEBUG][NWID %ld] init node synchronization num_ud = %ld, self.saved_cont = %ld' {'X0'} {num_ud_per_nd_reg} {self.saved_cont}")
        init_tran.writeAction("yield")

        '''
        X8:   Number of updates generated on source UD
        X9:   Number of updates consumed on source UD
        X10:   Source updown nwid
        '''
        sync_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.node_sync_ev_label)
        if self.debug_flag:
            sync_tran.writeAction(f"print ' '")
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <node_sync> ev_word=%ld:' {'X0'} {'EQT'}")
        sync_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"add {f'X{OB_REG_BASE+i}'} {self.curr_values[i]} {self.curr_values[i]}")
        if self.debug_flag:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] node synchronization ud_ctr = %ld, curr_value = %ld' {'X0'} {ud_ctr} {self.curr_values[0]}")
        sync_tran.writeAction(f"blt {ud_ctr} {num_ud_per_nd_reg} continue")
        sync_tran.writeAction(f"sendr_wcont {self.saved_cont} EQT {self.curr_values[0]} {self.curr_values[0]}")
        sync_tran.writeAction(f"yield_terminate")
        sync_tran.writeAction("continue: yield")

        return

    def updown_accumulate(self, num_lane_per_ud):
        
        lane_base_addr  = "UDPR_1"
        lane_ctr        = "UDPR_4"
        temp = self.scratch[0]
        
        accum_loop_label = "accumulate_loop"
        
        tran= self.state.writeTransition("eventCarry", self.state, self.state, self.ud_accum_ev_label)
        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %ld] Event <ud_accumulate> ev_word=%ld:' {'X0'} {'EQT'}")
        tran.writeAction(f"mov_imm2reg {lane_ctr} 0")
        for i in range(len(self.offsets)):
            tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")
        tran.writeAction(f"{accum_loop_label}: lshift {lane_ctr} {lane_base_addr} 16")
        tran.writeAction(f"add X7 {lane_base_addr} {lane_base_addr}")
        for i in range(len(self.offsets)):
            tran.writeAction(f"move {self.offsets[i]}({lane_base_addr}) {temp} 0 8")
            tran.writeAction(f"add {temp} {self.curr_values[i]} {self.curr_values[i]}")
        tran.writeAction(f"addi {lane_ctr} {lane_ctr} 1")
        tran.writeAction(f"blt {lane_ctr} {num_lane_per_ud} {accum_loop_label}")
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] ud synchronization curr_value = %ld, self.saved_cont = %ld' {'X0'} {self.curr_values[0]} {'X1'}")
        tran.writeAction(format_pseudo(f"sendr_reply {self.curr_values[0]} {self.curr_values[0]}", self.scratch[0], self.send_temp_reg_flag))
        tran.writeAction("yield_terminate")

        return

    def __broadcast(self, tran: Transition, ev_word, num_dst, ret_label, log2_stride, data) -> Transition:
        counter     = self.scratch[1]
        dst_nwid    = self.scratch[0]

        # if self.debug_flag_term:
        #     if isinstance(num_dst, int) or num_dst.isdigit():
        #         tran.writeAction(f"print '[DEBUG][NWID %ld] broadcase to {num_dst} destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} ")
        #     else:
        #         tran.writeAction(f"print '[DEBUG][NWID %ld] broadcase to %ld destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} {num_dst}")

        tran.writeAction(f"mov_imm2reg {counter} 0")
        if log2_stride > 0:
            tran.writeAction(f"broadcast_loop: lshift {counter} {dst_nwid} {log2_stride}")
            tran.writeAction(f"add {'X0'} {dst_nwid} {dst_nwid}")
        else:
            tran.writeAction(f"broadcast_loop: add {'X0'} {counter} {dst_nwid}")
        tran = set_nwid(tran, ev_word, dst_nwid, src_ev=ev_word)
        tran.writeAction(format_pseudo(f"sendr_wret {ev_word} {ret_label} {data}", dst_nwid, self.send_temp_reg_flag))
        tran.writeAction(f"addi {counter} {counter} 1")
        if isinstance(num_dst, int) or num_dst.isdigit():
            tran.writeAction(f"blti {counter} {num_dst} broadcast_loop")
        else:
            tran.writeAction(f"blt {counter} {num_dst} broadcast_loop")

        return tran


class GlobalSyncBKP:

    def __init__(self, identifier, ev_word, lm_offsets, scratch_regs, debug_flag = False, print_level = 0, send_temp_reg_flag = False):
        self.id = identifier
        self.ev_word = ev_word
        self.offsets = lm_offsets
        self.scratch = scratch_regs
        self.debug_flag = debug_flag
        self.print_level = print_level
        self.send_temp_reg_flag = send_temp_reg_flag

    def set_labels(self, global_sync, node_init, node_sync, ud_accum):
        self.global_sync_ev_label   = global_sync
        self.node_init_ev_label     = node_init
        self.node_sync_ev_label     = node_sync
        self.ud_accum_ev_label      = ud_accum

    def global_sync(self, init_tran: Transition, sync_tran: Transition, continuation, sync_value, num_nodes, num_ud_per_nd=UD_PER_NODE):

        num_nodes_reg   = "UDPR_0"
        num_ud_per_nd_reg = "UDPR_1"
        node_ctr        = "UDPR_2"
        saved_cont      = "UDPR_3"
        curr_values     = [f"UDPR_{n+4}" for n in range(len(self.offsets))]
        
        sync_fin_label = "sync_finish"

        '''
        OB_0:   Number of nodes
        OB_1:   Number of updowns per node
        '''
        if self.debug_flag:
            init_tran.writeAction(f"print ' '")
            init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_global_sync> ev_word = %lu' {'X0'} {'EQT'}")
        if isinstance(num_nodes, int) or num_nodes.isdigit():
            init_tran.writeAction(f"mov_imm2reg {num_nodes_reg} {num_nodes}")
        else:
            init_tran.writeAction(f"mov_reg2reg {num_nodes} {num_nodes_reg}")
        if isinstance(num_ud_per_nd, int) or num_ud_per_nd.isdigit():
            init_tran.writeAction(f"mov_imm2reg {num_ud_per_nd_reg} {num_ud_per_nd}")
        else:
            init_tran.writeAction(f"mov_reg2reg {num_ud_per_nd} {num_ud_per_nd_reg}")
        init_tran = self.__set_ev_label(init_tran, self.ev_word, self.node_init_ev_label, new_thread = True)

        init_tran = self.__broadcast(init_tran, self.ev_word, num_nodes_reg, self.global_sync_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_nd_reg} {num_ud_per_nd_reg} ")
        init_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        for i in range(len(self.offsets)):
            init_tran.writeAction(f"mov_imm2reg {curr_values[i]} 0")
        
        if sync_value[0:2] == "OB" or (sync_value[1:].isdigit() and (int(sync_value[1:]) >= 8 or int(sync_value[1:]) < 16)):
            saved_sync_value = "UDPR_5"
            init_tran.writeAction(f"mov_reg2reg {sync_value} {saved_sync_value}")
        else: saved_sync_value = sync_value
        
        if isinstance(continuation, str):
            init_tran.writeAction(f"mov_reg2reg {continuation} {saved_cont}")
        if isinstance(continuation, int):
            init_tran.writeAction(f"move {node_ctr} {continuation}(X7) 0 8")
        if self.debug_flag:
            init_tran.writeAction(f"print '[DEBUG][NWID %ld] init global synchronization num_ud = %ld, num_nodes_reg = %ld' {'X0'} {num_ud_per_nd_reg} {num_nodes_reg}")
        init_tran.writeAction("yield")

        '''
        OB_0:   Number of updates generated on source UD
        OB_1:   Number of updates consumed on source UD
        '''
        if self.debug_flag:
            sync_tran.writeAction(f"print ' '")
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <global_sync> ev_word = %lu:' {'X0'} {'EQT'}")
        sync_tran.writeAction(f"addi {node_ctr} {node_ctr} 1")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"add {f'OB_{i}'} {curr_values[i]} {curr_values[i]}")
        if self.debug_flag:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] global synchronization node_ctr = %ld, sync_value = %ld, curr_value = %ld' {'X0'} {node_ctr} {saved_sync_value} {curr_values[0]}")
        sync_tran.writeAction(f"blt {node_ctr} {num_nodes_reg} continue")
        sync_tran.writeAction(f"bge {curr_values[0]} {saved_sync_value} {sync_fin_label}")

        sync_tran = self.__broadcast(sync_tran, self.ev_word, num_nodes_reg, self.global_sync_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_nd_reg} {num_ud_per_nd_reg} ")
        sync_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"mov_imm2reg {curr_values[i]} 0")

        sync_tran.writeAction("continue: yield")
        if isinstance(continuation, str):
            # Finish global synchonization, send reply to the source
            sync_tran.writeAction(f"{sync_fin_label}: sendr_wcont {saved_cont} EQT {curr_values[0]} {curr_values[0]}")
        if isinstance(continuation, int):
            # Finish global synchonization, set the flag in scratchpad
            sync_tran.writeAction(f"{sync_fin_label}: mov_imm2reg {self.scratch[0]} {FLAG}")
            sync_tran.writeAction(f"move {self.scratch[0]} {continuation}(X7) 0 8")
        if self.debug_flag or self.print_level == 1:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Global sync terminates, sync_value = %ld, curr_value = %ld' {'X0'} {saved_sync_value} {curr_values[0]}")
        sync_tran.writeAction("yield_terminate")

        return 

    def node_sync(self, init_tran: Transition, sync_tran: Transition, num_ud_per_nd=UD_PER_NODE, num_lane_per_ud=LANE_PER_UD):
        saved_cont      = "UDPR_0"
        num_ud_per_nd_reg = "UDPR_1"
        num_lane_per_ud_reg = "UDPR_2"
        ud_ctr          = "UDPR_3"
        curr_values     = [f"UDPR_{n+4}" for n in range(len(self.offsets))]
        self.ev_word    = "UDPR_11"

        '''
        OB_0:   Number of UpDowns per node
        OB_1:   Global sync init event word
        '''
        if self.debug_flag:
            init_tran.writeAction(f"print ' '")
            init_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <init_node_sync> ev_word=%ld:' {'X0'} {'EQT'}")
        if isinstance(num_ud_per_nd, int) or num_ud_per_nd.isdigit():
            init_tran.writeAction(f"mov_imm2reg {num_ud_per_nd_reg} {num_ud_per_nd}")
        else:
            init_tran.writeAction(f"mov_reg2reg {num_ud_per_nd} {num_ud_per_nd_reg}")
        if isinstance(num_lane_per_ud, int) or num_lane_per_ud.isdigit():
            init_tran.writeAction(f"mov_imm2reg {num_lane_per_ud_reg} {num_lane_per_ud}")
        else:
            init_tran.writeAction(f"mov_reg2reg {num_lane_per_ud} {num_lane_per_ud_reg}")
        init_tran = self.__set_ev_label(init_tran, self.ev_word, self.ud_accum_ev_label, new_thread=True)
        init_tran = self.__broadcast(init_tran, self.ev_word, num_ud_per_nd_reg, self.node_sync_ev_label, \
            LOG2_LANE_PER_UD, f"EQT {num_lane_per_ud_reg} ")
        init_tran.writeAction(f"mov_imm2reg {ud_ctr} 0")
        for i in range(len(self.offsets)):
            init_tran.writeAction(f"mov_imm2reg {curr_values[i]} 0")
        init_tran.writeAction(f"mov_reg2reg X1 {saved_cont}")
        if self.debug_flag:
            init_tran.writeAction(f"print '[DEBUG][NWID %ld] init node synchronization num_ud = %ld, saved_cont = %ld' {'X0'} {num_ud_per_nd_reg} {saved_cont}")
        init_tran.writeAction("yield")

        '''
        OB_0:   Number of updates generated on source UD
        OB_1:   Number of updates consumed on source UD
        OB_2:   Source updown nwid
        '''
        if self.debug_flag:
            sync_tran.writeAction(f"print ' '")
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] Event <node_sync> ev_word=%ld:' {'X0'} {'EQT'}")
        sync_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"add {f'OB_{i}'} {curr_values[i]} {curr_values[i]}")
        if self.debug_flag:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld] node synchronization ud_ctr = %ld, curr_value = %ld' {'X0'} {ud_ctr} {curr_values[0]}")
        sync_tran.writeAction(f"blt {ud_ctr} {num_ud_per_nd_reg} continue")
        sync_tran.writeAction(f"sendr_wcont {saved_cont} EQT {curr_values[0]} {curr_values[0]}")
        sync_tran.writeAction(f"yield_terminate")
        sync_tran.writeAction("continue: yield")

        return

    def updown_accumulate(self, tran: Transition, num_lane_per_ud):
        num_lane_per_ud_reg = "UDPR_0"
        bank_base_addr  = "UDPR_1"
        lane_ctr        = "UDPR_2"
        curr_values     = [f"UDPR_{n+4}" for n in range(len(self.offsets))]
        temp = self.scratch[0]

        if self.debug_flag:
            tran.writeAction(f"print ' '")
            tran.writeAction(f"print '[DEBUG][NWID %ld] Event <ud_accumulate> ev_word=%ld:' {'X0'} {'EQT'}")
        tran.writeAction(f"mov_imm2reg {lane_ctr} 0")
        if isinstance(num_lane_per_ud, int) or num_lane_per_ud.isdigit():
            tran.writeAction(f"mov_imm2reg {num_lane_per_ud_reg} {num_lane_per_ud}")
        else:
            tran.writeAction(f"mov_reg2reg {num_lane_per_ud} {num_lane_per_ud_reg}")
        for i in range(len(self.offsets)):
            tran.writeAction(f"mov_imm2reg {curr_values[i]} 0")
        tran.writeAction(f"accumulate_loop: lshift {lane_ctr} {bank_base_addr} 16")
        tran.writeAction(f"add X7 {bank_base_addr} {bank_base_addr}")
        for i in range(len(self.offsets)):
            tran.writeAction(f"move {self.offsets[i]}({bank_base_addr}) {temp} 0 8")
            tran.writeAction(f"add {temp} {curr_values[i]} {curr_values[i]}")
        tran.writeAction(f"addi {lane_ctr} {lane_ctr} 1")
        tran.writeAction(f"blt {lane_ctr} {num_lane_per_ud_reg} accumulate_loop")
        if self.debug_flag:
            tran.writeAction(f"print '[DEBUG][NWID %ld] ud synchronization curr_value = %ld, saved_cont = %ld' {'X0'} {curr_values[0]} {'X1'}")
        tran.writeAction(format_pseudo(f"sendr_reply {curr_values[0]} {curr_values[0]}", self.scratch[0], self.send_temp_reg_flag))
        tran.writeAction("yield_terminate")

        return

    def __broadcast(self, tran: Transition, ev_word, num_dst, ret_label, log2_stride, data) -> Transition:
        counter     = self.scratch[1]
        dst_nwid    = self.scratch[0]

        if self.debug_flag:
            if isinstance(num_dst, int) or num_dst.isdigit():
                tran.writeAction(f"print '[DEBUG][NWID %ld] broadcase to {num_dst} destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} ")
            else:
                tran.writeAction(f"print '[DEBUG][NWID %ld] broadcase to %ld destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} {num_dst}")

        tran.writeAction(f"mov_imm2reg {counter} 0")
        tran.writeAction(f"broadcast_loop: lshift {counter} {dst_nwid} {log2_stride}")
        tran = self.__set_nwid(tran, self.ev_word, dst_nwid, src_ev=ev_word)
        tran.writeAction(format_pseudo(f"sendr_wret {ev_word} {ret_label} {data}", dst_nwid, self.send_temp_reg_flag))
        tran.writeAction(f"addi {counter} {counter} 1")
        if isinstance(num_dst, int) or num_dst.isdigit():
            tran.writeAction(f"blti {counter} {num_dst} broadcast_loop")
        else:
            tran.writeAction(f"blt {counter} {num_dst} broadcast_loop")

        return tran


    def __set_nwid(self, tran: Transition, ev_word, new_nwid, src_ev="EQT", new_thread=False) -> Transition:
        if isinstance(new_nwid, int) or new_nwid.isdigit():
            if new_thread and (src_ev not in "EQT|X2"):
                tran.writeAction(f"ev_update_2 {ev_word} {255} {new_nwid} {0b1100}")
            else:
                tran.writeAction(f"ev_update_1 {src_ev} {ev_word} {new_nwid} {0b1000}")
                tran.writeAction(f"ev_update_1 {ev_word} {ev_word} {255} {0b0100}")
        else:
            tran.writeAction(f"ev_update_reg_2 {src_ev} {ev_word} {new_nwid} {new_nwid} {0b1000}")
            if new_thread:
                tran.writeAction(f"ev_update_1 {ev_word} {ev_word} {255} {0b0100}")
        return tran

    def __set_ev_label(self, tran: Transition, ev_word, new_label, src_ev="EQT", new_thread=False) -> Transition:
        if src_ev == "EQT" and new_thread:
            tran.writeAction(f"ev_update_2 {ev_word} {new_label} 255 {0b0101}")
        else:
            tran.writeAction(f"ev_update_1 {src_ev} {ev_word} {new_label} {0b0001}")
            if new_thread:
                tran.writeAction(f"ev_update_1 {src_ev} {ev_word} 255 {0b0100}")
        return tran