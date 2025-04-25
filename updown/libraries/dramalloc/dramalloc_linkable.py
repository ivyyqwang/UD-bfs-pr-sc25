from Macro import *
from linker.EFAProgram import efaProgram

NUM_UD_PER_NODE = 32

DRAMALLOC_REQ_PTR = 0x200000000

NUM_DRAM_ALLOC_REQ_ARGS = 6
NUM_DRAM_FREE_REQ_ARGS = 2
NUM_DRAM_FINISH_REQ_ARGS = 2

class TranslationEntryInstaller:
    def __init__(self, state, enable_debug=False):
        self.state = state
        self.debug_flag = enable_debug
        self.print_level = 0
        
        self.glb_bcst_ev_label = "DRAMalloc::global_broadcast"
        self.node_bcst_ev_label = "DRAMalloc::node_broadcast"
        self.ud_install_ev_label = "DRAMalloc::updown_translation_install"
        self.node_bcst_ret_ev_label = "DRAMalloc::node_broadcast_return"
        self.glb_bcst_ret_ev_label = "DRAMalloc::global_broadcast_return"

        self.__gen_bcst()
        
    def __gen_bcst(self):
        
        glb_bcst_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_bcst_ev_label)

        node_bcst_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.node_bcst_ev_label)

        ud_install_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_install_ev_label)

        node_bcst_ret_tran  = self.state.writeTransition("eventCarry", self.state, self.state, self.node_bcst_ret_ev_label)

        glb_bcst_ret_tran   = self.state.writeTransition("eventCarry", self.state, self.state, self.glb_bcst_ret_ev_label)
        
        num_child   = "X16"
        ev_word     = "X17"
        cont        = "X18"
        self.scratch = ["X19", "X20", "X21", "X22", "X23"]
        
        '''
        Event:      Broadcast the translation to all nodes
        Operands:   X8: virtual base address
                    X9: size of the segment
                    X10: swizzle mask
                    X11: physical base address
                    X12: number of nodes
                    X13: allocation success flag
                    X14: continuation

        '''
        alloc_fail_label = "alloc_fail"
        if self.debug_flag:
            glb_bcst_tran.writeAction(f"print ' '")
            glb_bcst_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc_global_broadcast> Broadcast translation va=0x%lx pa=0x%lx to num_nodes=%ld' {'X0'} {'X8'} {'X11'} {'X12'}")
        glb_bcst_tran.writeAction(f"beqi {'X13'} {0} {alloc_fail_label}")
        glb_bcst_tran.writeAction(f"addi {'X12'} {num_child} {0}")
        set_ev_label(glb_bcst_tran, ev_word, self.node_bcst_ev_label, new_thread = True)
        set_ev_label(glb_bcst_tran, cont, self.glb_bcst_ret_ev_label, src_ev="X2")
        broadcast(glb_bcst_tran, ev_word, num_child, cont, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{'X8'} 7", self.scratch, 'ops')
        glb_bcst_tran.writeAction(f"addi {'X14'} {cont} 0")
        glb_bcst_tran.writeAction("yield")
        set_ignore_cont(glb_bcst_tran, self.scratch[0], label=alloc_fail_label)
        glb_bcst_tran.writeAction(f"sendr_wcont {'X14'} {self.scratch[0]} {'X13'} {'X8'}")
        if self.debug_flag:
            glb_bcst_tran.writeAction(f"print '[DEBUG][NWID %d] Allocation failed, return to user continuation %lu.' {'X0'} {cont}")
        glb_bcst_tran.writeAction(f"yieldt")

        '''
        Event:      Broadcast the translation to all updowns in the node
        Operands:   X8: virtual base address
                    X9: size of the segment
                    X10: swizzle mask
                    X11: physical base address
                    X12: number of nodes
                    X13: allocation success flag
                    X14: continuation
        '''
        if self.debug_flag and self.print_level > 1:
            node_bcst_tran.writeAction(f"print ' '")
            node_bcst_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc_node_broadcast> Broadcast to {NUM_UD_PER_NODE} updowns' {'X0'}")
        node_bcst_tran.writeAction(f"movir {num_child} {NUM_UD_PER_NODE}")
        set_ev_label(node_bcst_tran, ev_word, self.ud_install_ev_label, new_thread = True)
        set_ev_label(node_bcst_tran, cont, self.node_bcst_ret_ev_label, src_ev="X2")
        broadcast(node_bcst_tran, ev_word, num_child, cont, (LOG2_LANE_PER_UD), f"X8 7", self.scratch, 'ops')
        node_bcst_tran.writeAction(f"addi X1 {cont} 0")
        node_bcst_tran.writeAction("yield")

        '''
        Event:      Install the translation entry to the updown
        Operands:   X8: virtual base address
                    X9: size of the segment
                    X10: swizzle mask
                    X11: physical base address
                    X12: number of nodes
                    X13: allocation success flag
                    X14: continuation
        '''
        local_trans_label = "local_translation"
        continue_label  = "continue"
        if self.debug_flag and self.print_level > 1:
            ud_install_tran.writeAction(f"print ' '")
            ud_install_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc_updown_translation_install>  " + 
                                        f"Install translation entry va_base = %lu(0x%lx) pa_base = %lu(0x%lx) size = %lu swizzle_mask = %lu' " + 
                                        f"{'X0'} {'X8'} {'X8'} {'X11'} {'X11'} {'X9'} {'X10'}")
        ud_install_tran.writeAction(f"beqi {'X10'} {0} {local_trans_label}")
        ud_install_tran.writeAction(f"instrans X8 X11 X9 X10 1 {0b11}")
        ud_install_tran.writeAction(f"jmp {continue_label}")
        ud_install_tran.writeAction(f"{local_trans_label}: instrans X8 X11 X9 X10 0 {0b11}")
        ud_install_tran.writeAction(f"{continue_label}: sendr_reply X8 X14 {self.scratch[0]}")
        ud_install_tran.writeAction("yield_terminate")


        '''
        Event:      Node updown scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        node_bcst_ret_tran.writeAction(f"subi {num_child} {num_child} 1")
        node_bcst_ret_tran.writeAction(f"bnei {num_child} {0} {continue_label}")
        if self.debug_flag and self.print_level > 1:
            node_bcst_ret_tran.writeAction(f"print ' '")
            node_bcst_ret_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc_node_broadcast_return> " + 
                                           f"ev_word=%d num_pending=%d' {'X0'} {'EQT'} {num_child}")
        node_bcst_ret_tran.writeAction(f"sendr_reply X8 X9 {self.scratch[0]}")
        node_bcst_ret_tran.writeAction("yield_terminate")
        node_bcst_ret_tran.writeAction(f"{continue_label}: yield")

        '''
        Event:      Node scratchpad initialized return event
        Operands:   X8 ~ X9: sender event word
        '''
        top_sync_label = "top_sync"
        if self.debug_flag:
            glb_bcst_ret_tran.writeAction(f"print ' '")
            glb_bcst_ret_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc_glb_broadcast_return> ev_word=%d num_pending=%d' {'X0'} {'EQT'} {num_child}")
        glb_bcst_ret_tran.writeAction(f"subi {num_child} {num_child} 1")
        glb_bcst_ret_tran.writeAction(f"bnei {num_child} {0} {continue_label}")
        # glb_bcst_ret_tran.writeAction(f"move {self.user_cont_offset}(X7) {self.saved_cont} 0 8")
        set_ignore_cont(glb_bcst_ret_tran, self.scratch[0])
        glb_bcst_ret_tran.writeAction(f"beq {'X9'} {self.scratch[0]} {top_sync_label}")
        glb_bcst_ret_tran.writeAction(f"sendr_wcont {cont} {self.scratch[0]} {'X8'} {'X9'}")
        if self.debug_flag:
            glb_bcst_ret_tran.writeAction(f"print '[DEBUG][NWID %d] Finish broadcast and install translation" + 
                                          f", return dram_base_addr = %lu(0x%lx) to user continuation %lu.' {'X0'} {'X8'} {'X8'} {cont}")
        glb_bcst_ret_tran.writeAction(f"yieldt")
        glb_bcst_ret_tran.writeAction(f"{top_sync_label}: movir {self.scratch[0]} -1")
        glb_bcst_ret_tran.writeAction(f"addi {'X7'} {self.scratch[1]} 0")
        glb_bcst_ret_tran.writeAction(f"movrl {self.scratch[0]} 0({self.scratch[1]}) 0 8") 
        if self.debug_flag or True:
            glb_bcst_ret_tran.writeAction(f"print '[DEBUG][NWID %d] Finish broadcast and install translation for va=0x%lx" + 
                                          f", return to top' {'X0'} {'X8'}")
        glb_bcst_ret_tran.writeAction(f"yieldt")
        glb_bcst_ret_tran.writeAction(f"{continue_label}: yield")
        
        return
    
class DRAMalloc:

    def __init__(self, state, enable_debug=False):
        self.state = state
        self.debug_flag = enable_debug

        self.dramalloc_ev_label = "DRAMalloc::dramalloc"
        self.dramalloc_ret_ev_label = "DRAMalloc::dramalloc_write_param_return"

        self.__gen_dramalloc()
    
    def __gen_dramalloc(self):

        dramalloc_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.dramalloc_ev_label)

        dramalloc_ret_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.dramalloc_ret_ev_label)

        DRAM_ALLOC_FLAG = 1
        DRAM_FREE_FLAG = 2
        DRAM_FINISH_FLAG = 3

        '''
        Event:      DRAM allocation event
        Operands:   X8: flag 1: allocate, 0: free
                    X9: user continuation
                    X10: block size
                    X11: segment size
                    X12: num_nodes
                    X13: starting node id
        '''
        req_ptr  = "X16"
        dram_ack = "X17"
        free_label = "free_label"
        finish_label = "finish_label"
        dramalloc_tran.writeAction(f"movir {req_ptr} {DRAMALLOC_REQ_PTR >> 16}") # 0b 0010 0000 0000 0000 0000
        dramalloc_tran.writeAction(f"sli {req_ptr} {req_ptr} 16")
        set_ev_label(dramalloc_tran, dram_ack, self.dramalloc_ret_ev_label)
        dramalloc_tran.writeAction(f"beqi {'X8'} {DRAM_FREE_FLAG} {free_label}")
        dramalloc_tran.writeAction(f"beqi {'X8'} {DRAM_FINISH_FLAG} {finish_label}")
        if self.debug_flag:
            dramalloc_tran.writeAction(f"print ' '")
            dramalloc_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc> flag=%ld user_cont=%lu " + 
                                       f"block_size=%ld segment_size=%ld num_nodes=%ld starting_node=%ld' " +
                                       f"{'X0'} {'X8'} {'X9'} {'X10'} {'X11'} {'X12'} {'X13'}")
        dramalloc_tran.writeAction(f"sendmops {req_ptr} {dram_ack} {'X8'} {NUM_DRAM_ALLOC_REQ_ARGS} {0}")
        if self.debug_flag:
            dramalloc_tran.writeAction(f"print '[DEBUG][NWID %d] Send DRAM allocation request to DRAMalloc at addr %lu(0x%lx)' {'X0'} {req_ptr} {req_ptr}")
        dramalloc_tran.writeAction(f"yield")
        dramalloc_tran.writeAction(f"{free_label}: sendmops {req_ptr} {dram_ack} {'X8'} {NUM_DRAM_FREE_REQ_ARGS} 0")
        if self.debug_flag:
            dramalloc_tran.writeAction(f"print ' '")
            dramalloc_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc> flag=%ld user_cont=%lu " + 
                                       f"segment_pointer=%lu(0x%lx)' {'X0'} {'X8'} {'X9'} {'X10'} {'X10'}")
            dramalloc_tran.writeAction(f"print '[DEBUG][NWID %d]  Send DRAM free request to DRAMalloc at addr %lu(0x%lx)' {'X0'} {req_ptr} {req_ptr}")
        dramalloc_tran.writeAction(f"yield")
        dramalloc_tran.writeAction(f"{finish_label}: sendmops {req_ptr} {dram_ack} {'X8'} {NUM_DRAM_FINISH_REQ_ARGS} 0")
        if self.debug_flag:
            dramalloc_tran.writeAction(f"print ' '")
            dramalloc_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc> flag=%ld user_cont=%lu' {'X0'} {'X8'} {'X9'}")
            dramalloc_tran.writeAction(f"print '[DEBUG][NWID %d] Send DRAM finish request to DRAMalloc at addr %lu(0x%lx)' {'X0'} {req_ptr} {req_ptr}")
        dramalloc_tran.writeAction(f"yield")

        '''
        Event:      DRAM allocation write request return event
        Operands:   X8 ~ X9: Request pointer
        '''
        if self.debug_flag:
            dramalloc_ret_tran.writeAction(f"print ' '")
            dramalloc_ret_tran.writeAction(f"print '[DEBUG][NWID %d] Event <dramalloc_write_param_return> req_ptr=%lu' {'X0'} {'X8'}")
        dramalloc_ret_tran.writeAction(f"yield_terminate")
    
@efaProgram
def dramalloc_linkable(efa):
    efa.code_level = 'machine'
    state = efa.State() 
    efa.add_initId(state.state_id)
    DRAMalloc(state, enable_debug=True)
    TranslationEntryInstaller(state, enable_debug=False)
    return efa