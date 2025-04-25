from linker.EFAProgram import efaProgram, EFAProgram
from KVMSRMachineConfig import *
from Macro import *

class Broadcast:
    
    def __init__(self, state: EFAProgram.State, identifier: str, debug_flag: bool = False):
        
        self.id = identifier
        self.state = state
        self.debug_flag = debug_flag
        self.print_level = 1 if self.debug_flag else 0
        self.multiple_label = "modular_eq_zero"
        
        self.glb_bcst_ev_label      = get_event_label(self.id, "broadcast_global")
        self.node_bcst_ev_label     = get_event_label(self.id, "broadcast_node")
        self.ud_bcst_ev_label       = get_event_label(self.id, "broadcast_ud")
        self.ud_bcst_fin_ev_label   = get_event_label(self.id, "broadcast_ud_fin")
        self.node_bcst_fin_ev_label = get_event_label(self.id, "broadcast_node_fin")
        self.glb_bcst_fin_ev_label  = get_event_label(self.id, "broadcast_global_fin")
        
        self.bcst_val_sp_ev_label   = get_event_label(self.id, "broadcast_value_to_scratchpad")
        
        self.__gen_broadcast()
        self.__gen_broadcast_lm()

    def get_broadcast_ev_label(self):
        return self.glb_bcst_ev_label

    def get_broadcast_value_sp_ev_label(self):
        return self.bcst_val_sp_ev_label
    
    def gen_broadcast(self):
        pass
    
    def __gen_broadcast(self):
        
        glb_bcst_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_bcst_ev_label)

        node_bcst_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.node_bcst_ev_label)

        ud_bcst_tran     = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_bcst_ev_label)

        ud_bcst_fin_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_bcst_fin_ev_label)

        node_bcst_fin_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.node_bcst_fin_ev_label)

        glb_bcst_fin_tran    = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_bcst_fin_ev_label)
        
        self.scratch    = [f"X{GP_REG_BASE+0}", f"X{GP_REG_BASE+1}", f"X{GP_REG_BASE+2}", f"X{GP_REG_BASE+3}"]
        init_ev_word    = f"X{GP_REG_BASE+4}"
        self.num_child  = f"X{GP_REG_BASE+9}"
        num_finished    = f"X{GP_REG_BASE+10}"
        self.num_lane_reg   = f"X{GP_REG_BASE+11}"
        self.ev_word    = f"X{GP_REG_BASE+12}"
        self.saved_cont = f"X{GP_REG_BASE+13}"
        ignore_cont     = f"X{GP_REG_BASE+14}"
        
        '''
        Event:      Broadcast routine entry point.
        Operands:   X8: number of lanes
                    X9: event label
                    X10 ~ Xn: data
        '''
        if self.debug_flag:
            glb_bcst_tran.writeAction(f"print ' '")
            glb_bcst_tran.writeAction(f"addi {'X9'} {init_ev_word} 0")
            glb_bcst_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.glb_bcst_ev_label}> ev_word = %lu num_lanes = %ld init_ev_word = %lu' {'X0'} {'EQT'} {'X8'} {init_ev_word}")
        glb_bcst_tran.writeAction(f"addi {'X8'} {self.num_lane_reg} 0")
        get_num_node(glb_bcst_tran, self.num_lane_reg, self.num_child, self.multiple_label, self.scratch[0])
        glb_bcst_tran = set_ev_label(glb_bcst_tran, self.ev_word, self.node_bcst_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag and self.print_level > 3:
            glb_bcst_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Broadcast to %ld nodes' {'X0'} {self.num_child}")
        glb_bcst_tran = broadcast(glb_bcst_tran, self.ev_word, self.num_child, self.glb_bcst_fin_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"X8 8", self.scratch, 'ops')
        glb_bcst_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        glb_bcst_tran.writeAction("yield")

        '''
        Event:      Broadcast node
        Operands:   X8: number of lanes
                    X9: event label
                    X10 ~ Xn: data
        '''
        if self.debug_flag and self.print_level > 3:
            node_bcst_tran.writeAction(f"print ' '")
            node_bcst_tran.writeAction(f"addi {'X9'} {init_ev_word} 0")
            node_bcst_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.node_bcst_ev_label}> ev_word = %lu  num_lanes = %ld init_ev_word = %lu' {'X0'} {'EQT'} {'X8'} {init_ev_word}")
        node_bcst_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        get_num_ud_per_node(node_bcst_tran, 'X8', self.num_child, self.multiple_label, self.scratch[0])
        node_bcst_tran = set_ev_label(node_bcst_tran, self.ev_word, self.ud_bcst_ev_label, new_thread = True, label=self.multiple_label)
        if self.debug_flag:
            node_bcst_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Broadcast to %ld updowns' {'X0'} {self.num_child}")
        node_bcst_tran = broadcast(node_bcst_tran, self.ev_word, self.num_child, self.node_bcst_fin_ev_label, \
            (LOG2_LANE_PER_UD), f"X8 8", self.scratch, 'ops')
        node_bcst_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        node_bcst_tran.writeAction("yield")

        '''
        Event:      Broadcast updown
        Operands:   X8: number of lanes
                    X9: event label
                    X10 ~ Xn: data
        '''
        if self.debug_flag and self.print_level > 3:
            ud_bcst_tran.writeAction(f"print ' '")
            ud_bcst_tran.writeAction(f"addi {'X9'} {init_ev_word} 0")
            ud_bcst_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.ud_bcst_ev_label}> ev_word = %lu init_ev_word = %lu' {'X0'} {'EQT'} {init_ev_word}")
        ud_bcst_tran.writeAction(f"addi X1 {self.saved_cont} 0")
        get_num_lane_per_ud(ud_bcst_tran, 'X8', self.num_child, self.multiple_label)
        ud_bcst_tran.writeAction(f"{self.multiple_label}: evi {'X2'} {self.ev_word} {255} {0b0100}")
        ud_bcst_tran.writeAction(f"ev {self.ev_word} {self.ev_word} {'X9'} {'X9'} {0b0001}")
        
        if self.debug_flag and self.print_level > 3:
            ud_bcst_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Broadcast to %ld lanes' {'X0'} {self.num_child}")
        ud_bcst_tran = broadcast(ud_bcst_tran, self.ev_word, self.num_child, self.ud_bcst_fin_ev_label, 0, \
            f"X10 6", self.scratch, 'ops')
        ud_bcst_tran.writeAction(f"mov_imm2reg {num_finished} 0")
        ud_bcst_tran.writeAction("yield")

        continue_label  = "continue"
        bcst_fin_label = "global_bcst_finish"
        '''
        Event:      Updown lane scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        if self.debug_flag and self.print_level > 3:
            ud_bcst_fin_tran.writeAction(f"print ' '")
            ud_bcst_fin_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.ud_bcst_fin_ev_label}> ev_word = %lu num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        ud_bcst_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        ud_bcst_fin_tran.writeAction(f"blt {num_finished} {self.num_child} {continue_label}")
        set_ignore_cont(ud_bcst_fin_tran, ignore_cont)
        ud_bcst_fin_tran.writeAction(f"sendr_wcont {self.saved_cont} {ignore_cont} X0 X2 ")
        if self.debug_flag and self.print_level > 3:
            ud_bcst_fin_tran.writeAction(f"print ' '")
            ud_bcst_fin_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.ud_bcst_fin_ev_label}> ev_word = %lu init_ev_word = %lu finish broadcast %ld lanes' {'X0'} {'EQT'} {init_ev_word} {num_finished}")
        ud_bcst_fin_tran.writeAction("yield_terminate")
        ud_bcst_fin_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Node updown scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        if self.debug_flag and self.print_level > 3:
            node_bcst_fin_tran.writeAction(f"print ' '")
            node_bcst_fin_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.node_bcst_fin_ev_label}> ev_word = %lu num_finished=%ld init_ev_word = %lu' {'X0'} {'EQT'} {num_finished} {init_ev_word}")
        node_bcst_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        node_bcst_fin_tran.writeAction(f"blt {num_finished} {self.num_child} {continue_label}")
        node_bcst_fin_tran.writeAction(f"sendr_reply X0 X2 {self.scratch[0]}")
        node_bcst_fin_tran.writeAction("yield_terminate")
        node_bcst_fin_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Node scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        if self.debug_flag and self.print_level > 3:
            glb_bcst_fin_tran.writeAction(f"print ' '")
            glb_bcst_fin_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.glb_bcst_fin_ev_label}> ev_word = %lu num_finished=%ld' {'X0'} {'EQT'} {num_finished}")
        glb_bcst_fin_tran.writeAction(f"addi {num_finished} {num_finished} 1")
        glb_bcst_fin_tran.writeAction(f"beq {num_finished} {self.num_child} {bcst_fin_label}")
        glb_bcst_fin_tran.writeAction(f"yield")
        glb_bcst_fin_tran.writeAction(f"{bcst_fin_label}: sendr_reply X0 X2 {self.scratch[0]}")
        if self.debug_flag:
            glb_bcst_fin_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Finish broadcast init_ev_word = %lu, return to continuation %ld.' {'X0'} {init_ev_word} {self.saved_cont} ")
        glb_bcst_fin_tran.writeAction(f"yieldt")
        
        return

    def __gen_broadcast_lm(self):
        
        '''
        Broadcast argument to all the lanes.
        X8:     Scratchpad offset [31:63] | number of operands [0:31]
        X9~X15  Data to be stored in scratchpad at offset X8[31:63]
        '''
        lm_addr     = 'X16'
        num_ops     = 'X17'
        init_lane_sp_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.bcst_val_sp_ev_label)
        init_lane_sp_tran.writeAction(f"sri {'X8'} {lm_addr} 32")
        init_lane_sp_tran.writeAction(f"add {'X7'} {lm_addr} {lm_addr}")
        init_lane_sp_tran.writeAction(f"andi {'X8'} {num_ops} {0x10 - 1}") # 15
        if self.debug_flag:
            init_lane_sp_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.bcst_val_sp_ev_label}> copy %ld words to lm_addr = %lu(0x%lx)' {'X0'} {num_ops} {lm_addr} {lm_addr}")
        init_lane_sp_tran.writeAction(f"bcpyol {'X9'} {lm_addr} {num_ops}")
        init_lane_sp_tran.writeAction(f"sendr_reply {'X1'} {'X2'} {lm_addr}")
        init_lane_sp_tran.writeAction(f"yieldt")
        
    

class GlobalSync:
    NUM_DELAYS = 10

    def __init__(self, state: EFAProgram.State, identifier: str, ev_word_reg: str, lm_offsets: int, scratch_regs: list, debug_flag = False, print_level = 0, send_temp_reg_flag = True):
        self.state      = state
        self.id         = identifier
        self.ev_word    = ev_word_reg
        self.offsets    = lm_offsets
        self.scratch    = scratch_regs
        self.debug_flag = debug_flag
        self.print_level = print_level
        self.send_temp_reg_flag = send_temp_reg_flag
        
        self.glb_sync_init_ev_label = f"{self.id}::init_global_snyc"
        self.nd_sync_init_ev_label  = f"{self.id}::init_node_sync"
        self.ud_entry_ev_label      = f"{self.id}::ud_entry"
        self.ud_accum_ev_label      = f"{self.id}::ud_accumulate"
        self.ud_loop_ev_label       = f"{self.id}::ud_delay"
        self.glb_sync_ret_ev_label  = f"{self.id}::global_sync_return"
        self.nd_sync_ret_ev_label   = f"{self.id}::node_sync_return"
        
        self.global_init_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_sync_init_ev_label)

        self.node_init_tran     = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_sync_init_ev_label)

        self.ud_accum_tran      = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_accum_ev_label)

        self.global_sync_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_sync_ret_ev_label)

        self.node_sync_tran     = self.state.writeTransition("eventCarry", self.state, self.state, self.nd_sync_ret_ev_label)
        
    def global_sync(self, continuation, sync_value, num_lanes):

        num_nodes       = f"X{GP_REG_BASE+0}"
        num_ud_per_nd   = f"X{GP_REG_BASE+1}"
        num_ln_per_ud   = f"X{GP_REG_BASE+2}"
        self.saved_cont = f"X{GP_REG_BASE+3}"
        lm_base         = f"X{GP_REG_BASE+4}"
        
        max_node_label  = "max_node"
        max_ud_label    = "max_ud_per_nd"
        max_ln_label    = "max_ln_per_ud"
        self.sync_fin_label  = "sync_finish"

        if self.debug_flag and self.print_level > 5:
            self.global_init_tran.writeAction(f"print ' '")
            self.global_init_tran.writeAction(f"print '[DEBUG][NWID %lld] Event <{self.glb_sync_init_ev_label}> ev_word = %lu' {'X0'} {'EQT'}")
        
        get_num_node(self.global_init_tran, num_lanes, num_nodes, max_node_label, self.scratch[0])
        self.global_init_tran.writeAction(f"{max_node_label}: addi {num_nodes} {num_nodes} 0")
        get_num_ud_per_node(self.global_init_tran, num_lanes, num_ud_per_nd, max_ud_label, self.scratch[0])
        self.global_init_tran.writeAction(f"{max_ud_label}: addi {num_ud_per_nd} {num_ud_per_nd} 0")
        get_num_lane_per_ud(self.global_init_tran, num_lanes, num_ln_per_ud, max_ln_label)
        self.global_init_tran.writeAction(f"{max_ln_label}: addi {num_ln_per_ud} {num_ln_per_ud} 0")
        if self.debug_flag:
            self.global_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] init global synchronization num_nodes = %ld, num_ud_per_node = %ld, num_ln_per_ud = %ld' \
                {'X0'} {num_nodes} {num_ud_per_nd} {num_ln_per_ud}")
            
        if isinstance(continuation, str):
            self.global_init_tran.writeAction(f"mov_reg2reg {continuation} {self.saved_cont}")
        if isinstance(continuation, int):
            self.global_init_tran.writeAction(f"mov_imm2reg {self.saved_cont} 0")
            self.global_init_tran.writeAction(f"addi {'X7'} {lm_base} 0")
            self.global_init_tran.writeAction(f"move {self.saved_cont} {continuation}({lm_base}) 0 8")
            
        if sync_value[0:2] == "OB" or (sync_value[0] == 'X' and sync_value[1:].isdigit() and (int(sync_value[1:]) >= 8 or int(sync_value[1:]) < 16)):
            self.saved_sync_value   = f"X{GP_REG_BASE+ 5}"
            self.curr_values        = [f"X{GP_REG_BASE + n + 6}" for n in range(len(self.offsets))]
            self.global_init_tran.writeAction(f"mov_reg2reg {sync_value} {self.saved_sync_value}")
        else: 
            self.saved_sync_value   = sync_value
            self.curr_values        = [f"X{GP_REG_BASE + n + 5}" for n in range(len(self.offsets))]
        if self.debug_flag:
            self.global_init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] init global synchronization saved_sync_value = %ld' {'X0'} {self.saved_sync_value}")
        
        self.all_reduce(num_nodes, num_ud_per_nd, num_ln_per_ud)
    
        if isinstance(continuation, str):
            # Finish global synchonization, send reply to the source
            set_ignore_cont(self.global_sync_tran, self.ev_word, label=self.sync_fin_label)
            self.global_sync_tran.writeAction(f"sendr_wcont {self.saved_cont} {self.ev_word} {self.curr_values[0]} {self.curr_values[0]}")
        if isinstance(continuation, int):
            # Finish global synchonization, set the flag in scratchpad
            self.global_sync_tran.writeAction(f"{self.sync_fin_label}: mov_imm2reg {self.scratch[0]} {FLAG}")
            self.global_sync_tran.writeAction(f"move {self.scratch[0]} {continuation}({lm_base}) 0 8")
        if self.debug_flag or self.print_level == 1:
            self.global_sync_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Global sync terminates, sync_value = %ld, curr_value = %ld' {'X0'} {self.saved_sync_value} {self.curr_values[0]}")
        self.global_sync_tran.writeAction("yield_terminate")

        return 

    def all_reduce(self, num_nodes, num_ud_per_nd, num_ln_per_ud):
        
        init_tran   = self.global_init_tran
        sync_tran   = self.global_sync_tran
        node_ctr    = f"X{GP_REG_BASE+4}"

        # Broadcast to all the nodes, start all reduce
        init_tran = set_ev_label(init_tran, self.ev_word, self.nd_sync_init_ev_label, new_thread = True)
        init_tran = self.__broadcast(init_tran, self.ev_word, num_nodes, self.glb_sync_ret_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_nd} {num_ln_per_ud} ")
        init_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        # Initialize the temp sync values
        for i in range(len(self.offsets)):
            init_tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")
        
        init_tran.writeAction("yield")
        
        self.node_sync('X8', 'X9')
        self.updown_accumulate('X8')

        if self.debug_flag:
            sync_tran.writeAction(f"print ' '")
        sync_tran.writeAction(f"addi {node_ctr} {node_ctr} 1")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"add {f'X{OB_REG_BASE+i}'} {self.curr_values[i]} {self.curr_values[i]}")
        if self.debug_flag:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.glb_sync_ret_ev_label}> node_ctr = %ld, sync_value = %ld, curr_value = %ld' {'X0'} {node_ctr} {self.saved_sync_value} {self.curr_values[0]}")
        sync_tran.writeAction(f"blt {node_ctr} {num_nodes} continue")
        sync_tran.writeAction(f"bge {self.curr_values[0]} {self.saved_sync_value} {self.sync_fin_label}")

        sync_tran = self.__broadcast(sync_tran, self.ev_word, num_nodes, self.glb_sync_ret_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_nd} {num_ln_per_ud} ")
        sync_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")

        sync_tran.writeAction("continue: yield")
        
        return 

    def node_sync(self, num_ud_per_nd, num_lane_per_ud):
        
        init_tran = self.node_init_tran
        sync_tran = self.node_sync_tran
                
        num_ud_per_nd_reg   = f"X{GP_REG_BASE+1}"
        ud_ctr              = f"X{GP_REG_BASE+4}"

        '''
        X8:   Number of UpDowns per node
        X9:   Global sync init event word
        '''
        if self.debug_flag:
            init_tran.writeAction(f"print ' '")
            init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.nd_sync_init_ev_label}> ev_word = %lu :' {'X0'} {'EQT'}")
        init_tran.writeAction(f"mov_reg2reg {num_ud_per_nd} {num_ud_per_nd_reg}")
        init_tran = set_ev_label(init_tran, self.ev_word, self.ud_entry_ev_label, new_thread=True)
        init_tran = self.__broadcast(init_tran, self.ev_word, num_ud_per_nd_reg, self.nd_sync_ret_ev_label, \
            LOG2_LANE_PER_UD, f"{num_lane_per_ud} EQT ")
        init_tran.writeAction(f"mov_imm2reg {ud_ctr} 0")
        for i in range(len(self.offsets)):
            init_tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")
        init_tran.writeAction(f"mov_reg2reg X1 {self.saved_cont}")
        if self.debug_flag:
            init_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] init node synchronization num_ud = %ld, self.saved_cont = %ld' {'X0'} {num_ud_per_nd_reg} {self.saved_cont}")
        init_tran.writeAction("yield")

        '''
        X8:   Number of updates generated on source UD
        X9:   Number of updates consumed on source UD
        X10:   Source updown nwid
        '''
        if self.debug_flag:
            sync_tran.writeAction(f"print ' '")
        sync_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        for i in range(len(self.offsets)):
            sync_tran.writeAction(f"add {f'X{OB_REG_BASE+i}'} {self.curr_values[i]} {self.curr_values[i]}")
        if self.debug_flag:
            sync_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.nd_sync_ret_ev_label}> ev_word=%lu ud_ctr = %ld, curr_value = %ld' {'X0'} {'EQT'} {ud_ctr} {self.curr_values[0]}")
        sync_tran.writeAction(f"blt {ud_ctr} {num_ud_per_nd_reg} continue")
        sync_tran.writeAction(f"sendr_wcont {self.saved_cont} EQT {self.curr_values[0]} {self.curr_values[0]}")
        sync_tran.writeAction(f"yield_terminate")
        sync_tran.writeAction("continue: yield")

        return

    def updown_accumulate(self, num_lane_per_ud):
        
        # tran = self.ud_accum_tran
        
        # lane_base_addr  = f"X{GP_REG_BASE+1}"
        # lane_ctr        = f"X{GP_REG_BASE+4}"
        # temp = self.scratch[0]

        # # if self.debug_flag:
        #     # tran.writeAction(f"print ' '")
        #     # tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] Event <{self.ud_accum_ev_label}> ev_word = %lu :' {'X0'} {'EQT'}")
        # tran.writeAction(f"mov_imm2reg {lane_ctr} 0")
        # for i in range(len(self.offsets)):
        #     tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")
        # tran.writeAction(f"{accum_loop_label}: lshift {lane_ctr} {lane_base_addr} 16")
        # tran.writeAction(f"add X7 {lane_base_addr} {lane_base_addr}")
        # for i in range(len(self.offsets)):
        #     tran.writeAction(f"addi {lane_base_addr} {lane_base_addr} {self.offsets[i]}")
        #     tran.writeAction(f"move {0}({lane_base_addr}) {temp} 0 8")
        #     tran.writeAction(f"add {temp} {self.curr_values[i]} {self.curr_values[i]}")
        # tran.writeAction(f"addi {lane_ctr} {lane_ctr} 1")
        # tran.writeAction(f"blt {lane_ctr} {num_lane_per_ud} {accum_loop_label}")
        # if self.debug_flag:
        #     tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] ud synchronization curr_value = %ld, self.saved_cont = %ld' {'X0'} {self.curr_values[0]} {'X1'}")
        # tran.writeAction(format_pseudo(f"sendr_reply {self.curr_values[0]} {self.curr_values[0]}", self.scratch[0], self.send_temp_reg_flag))
        # tran.writeAction("yield_terminate")

        num_ln_per_ud   = "UDPR_0"
        bank_base_addr  = "UDPR_1"
        lane_ctr    = "UDPR_2"
        num_iters   = "UDPR_5"
        # saved_cont  = "UDPR_6"
        accum_evw   = "UDPR_7"
        ev_word     = "UDPR_8"
        temp = self.scratch[0]
        accum_loop_label = "accumulate_loop"
        POLICY_SHORTEST = 1
        POLICY_LONGEST = 6
        
        entry_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_entry_ev_label)
        if self.debug_flag:
            entry_tran.writeAction(f"print ' '")
            entry_tran.writeAction(f"print '[DEBUG][NWID %d] Event <{self.ud_entry_ev_label}> ev_word=%d:' {'X0'} {'EQT'}")
        entry_tran.writeAction(f"mov_imm2reg {num_iters} {self.NUM_DELAYS}")
        set_ev_label(entry_tran, ev_word, self.ud_loop_ev_label, new_thread=True)
        entry_tran.writeAction(f"movir {lane_ctr} {POLICY_LONGEST}")
        # Create send policy (shortest within 64 lanes) to loop
        entry_tran.writeAction(f"sli {lane_ctr} {lane_ctr} {27}")
        entry_tran.writeAction(f"or {'X0'} {lane_ctr} {lane_ctr}")
        set_nwid(entry_tran, ev_word, lane_ctr, src_ev=ev_word)
        # set_ev_label(entry_tran, accum_evw, self.ud_accum_ev_label)
        entry_tran.writeAction(f"sendr3_wcont {ev_word} {'X1'} {num_iters} {ev_word} {'X7'}")
        # entry_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        entry_tran.writeAction("yieldt")

        '''
        UpDown local counter accumulation routine
        OB_0:   Number of iterations = 0
        OB_1:   Loop event word
        OB_2:   UD scratchpad base address
        X1:     Saved continuation
        '''
        accum_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_accum_ev_label)
        # if self.debug_flag:
        #     tran.writeAction(f"print ' '")
        #     tran.writeAction(f"print '[DEBUG][NWID %d] Event <ud_accumulate> ev_word=%d:' {'X0'} {'EQT'}")
        accum_tran.writeAction(f"movir {num_ln_per_ud} {LANE_PER_UD}")
        accum_tran.writeAction(f"mov_imm2reg {lane_ctr} 0")
        for i in range(len(self.offsets)):
            accum_tran.writeAction(f"mov_imm2reg {self.curr_values[i]} 0")
        accum_tran.writeAction(f"{accum_loop_label}: lshift {lane_ctr} {bank_base_addr} 16")
        accum_tran.writeAction(f"add {'X10'} {bank_base_addr} {bank_base_addr}")
        for i in range(len(self.offsets)):
            accum_tran.writeAction(f"addi {bank_base_addr} {bank_base_addr} {self.offsets[i]}")
            accum_tran.writeAction(f"move {0}({bank_base_addr}) {temp} 0 8")
            accum_tran.writeAction(f"add {temp} {self.curr_values[i]} {self.curr_values[i]}")
        accum_tran.writeAction(f"addi {lane_ctr} {lane_ctr} 1")
        accum_tran.writeAction(f"blt {lane_ctr} {num_ln_per_ud} {accum_loop_label}")
        if self.debug_flag:
            accum_tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] ud synchronization curr_value = %ld, self.saved_cont = %ld' {'X0'} {self.curr_values[0]} {'X1'}")
        accum_tran.writeAction(f"sendr_reply {self.curr_values[0]} {self.curr_values[0]} {self.scratch[0]}")
        accum_tran.writeAction("yield_terminate")

        
        '''
        Loop transition. Return to the ud sync thread when counter goes down to 0
        OB_0:   Number of iterations
        OB_1:   Loop event word
        OB_2:   UD scratchpad base address
        X1:     Saved continuation
        '''
        loop_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_loop_ev_label)
        if self.debug_flag:
            loop_tran.writeAction(f"print ' '")
            loop_tran.writeAction(f"print '[DEBUG][NWID %d] Event <ud_loop> num_iter=%ld ud_sync_lane_nwid=%ld curr_nwid=%ld loop_evw=%lu' {'X0'} {'X8'} {'X10'} {'X0'} {'X9'}")
        loop_tran.writeAction(f"beqi {'X8'} 0 ud_loop_term")
        loop_tran.writeAction(f"subi {'X8'} {num_iters} 1")
        loop_tran.writeAction(f"sendr3_wcont {'X9'} {'X1'} {num_iters} {'X9'} {'X10'}")
        loop_tran.writeAction("yieldt")

        # Create send policy (shortest within 64 lanes) to do the accumulation
        loop_tran.writeAction(f"ud_loop_term: movir {lane_ctr} {POLICY_SHORTEST}")
        loop_tran.writeAction(f"sli {lane_ctr} {lane_ctr} {27}")
        loop_tran.writeAction(f"or {'X0'} {lane_ctr} {lane_ctr}")
        set_ev_label(loop_tran, ev_word, self.ud_accum_ev_label, new_thread=True)
        set_nwid(loop_tran, ev_word, lane_ctr, src_ev=ev_word)
        loop_tran.writeAction(f"sendr3_wcont {ev_word} {'X1'} {'X8'} {'X9'} {'X10'}")
        loop_tran.writeAction("yieldt")

        return

    def __broadcast(self, tran: EFAProgram.Transition, ev_word, num_dst, ret_label, log2_stride, data) -> EFAProgram.Transition:
        counter     = self.scratch[1]
        dst_nwid    = self.scratch[0]

        # if self.debug_flag:
        #     if isinstance(num_dst, int) or num_dst.isdigit():
        #         tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] broadcase to {num_dst} destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} ")
        #     else:
        #         tran.writeAction(f"print '[DEBUG][NWID %ld][{self.id}] broadcase to %ld destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} {num_dst}")
                
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
    

@efaProgram
def GenLinkableBroadcast(efa: EFAProgram):
    
    efa.code_level = 'machine'
    state = efa.State()
    efa.add_initId(state.state_id)
    
    Broadcast(state, "Broadcast")

    return efa