from linker.EFAProgram import EFAProgram, efaProgram
from math import log2
from Macro import *

WORD_SIZE           = 8
LOG2_WORD_SIZE      = int(log2(WORD_SIZE))
LANE_PER_UD         = 64
UD_PER_NODE         = 32
LOG2_LANE_PER_UD    = int(log2(LANE_PER_UD))
LOG2_UD_PER_NODE    = int(log2(UD_PER_NODE))

FLAG                = 1
NUM_DELAYS          = 16

TERMINATE_DEBUG_FLAG = True

class GlobalSync:

    def __init__(self, identifier, state: EFAProgram.state, ev_word, lm_offsets, scratch_regs, debug_flag = False):
        self.id = identifier
        self.state = state
        self.ev_word = ev_word
        if len(lm_offsets) < 4:
            self.num_updates_offset, self.num_consume_offset, self.top_flag_offset = lm_offsets
            self.top_val_offset = None
        else:
            self.num_updates_offset, self.num_consume_offset, self.top_flag_offset, self.top_val_offset = lm_offsets
        self.scratch = scratch_regs
        self.debug_flag_term = debug_flag

    def set_labels(self, global_init, global_sync, node_init, node_sync, ud_accum):
        self.global_init_ev_label   = global_init
        self.global_sync_ev_label   = global_sync
        self.node_init_ev_label     = node_init
        self.node_sync_ev_label     = node_sync
        self.ud_accum_ev_label      = ud_accum
        
        self.ud_entry_ev_label = get_event_label(self.id, "ud_entry")
        self.ud_loop_ev_label = get_event_label(self.id, "ud_delay")

    def global_sync(self):

        num_nodes       = "UDPR_0"
        num_ud_per_node = "UDPR_1"
        node_ctr        = "UDPR_2"
        num_updates     = "UDPR_3"
        num_consume     = "UDPR_4"
        num_iter        = "UDPR_5"
        lm_base_addr    = "UDPR_6"
        saved_cont      = "UDPR_7"

        '''
        OB_0:   Number of nodes
        OB_1:   Number of updowns per node
        OB_2:   iteration number
        '''
        init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.global_init_ev_label)
        if self.debug_flag_term:
            init_tran.writeAction(f"print ' '")
            init_tran.writeAction(f"print '[DEBUG][NWID %d] Event <init_global_sync> ev_word=%d:' {'X0'} {'EQT'}")
        init_tran.writeAction(f"addi {f'X{OB_REG_BASE+0}'} {num_nodes} 0")
        init_tran.writeAction(f"addi {f'X{OB_REG_BASE+1}'} {num_ud_per_node} 0")
        init_tran.writeAction(f"addi {f'X{OB_REG_BASE+2}'} {num_iter} 0")
        init_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        init_tran = set_ev_label(init_tran, self.ev_word, self.node_init_ev_label, new_thread = True)

        init_tran = self.__broadcast(init_tran, self.ev_word, num_nodes, self.global_sync_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_node} EQT ")
        init_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        init_tran.writeAction(f"mov_imm2reg {num_updates} 0")
        init_tran.writeAction(f"mov_imm2reg {num_consume} 0")
        init_tran.writeAction(f"addi {'X7'} {lm_base_addr} 0")
        init_tran.writeAction(f"move {node_ctr} {self.top_flag_offset}({lm_base_addr}) 0 8")
        if self.debug_flag_term:
            init_tran.writeAction(f"print '[DEBUG][NWID %d] init global synchronization num_ud = %d, num_nodes = %d, iteration %d' {'X0'} {num_ud_per_node} {num_nodes} {num_iter}")
        init_tran.writeAction("yield")

        '''
        OB_0:   Number of updates generated on source UD
        OB_1:   Number of updates consumed on source UD
        '''
        sync_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.global_sync_ev_label)
        # if self.debug_flag_term:
        #     sync_tran.writeAction(f"print ' '")
        #     sync_tran.writeAction(f"print '[DEBUG][NWID %d] Event <global_sync> ev_word=%d:' {'X0'} {'EQT'}")
        sync_tran.writeAction(f"addi {node_ctr} {node_ctr} 1")
        sync_tran.writeAction(f"add {num_updates} {f'X{OB_REG_BASE+0}'} {num_updates}")
        sync_tran.writeAction(f"add {num_consume} {f'X{OB_REG_BASE+1}'} {num_consume}")
        if self.debug_flag_term:
            sync_tran.writeAction(f"print '[DEBUG][NWID %d] Event <global_sync>  global synchronization node_ctr = %d, num_updates = %d, num_consumes = %d' {'X0'} {node_ctr} {num_updates} {num_consume}")
        sync_tran.writeAction(f"blt {node_ctr} {num_nodes} continue")
        sync_tran.writeAction(f"beq {num_updates} {num_consume} bfs_sync_fin")
        # sync_tran.writeAction(f"beq {num_consume} {prev_num_consume} bfs_hang")
        # sync_tran.writeAction(f"mov_reg2reg {num_consume} {prev_num_consume}")
        sync_tran = set_ev_label(sync_tran, self.ev_word, self.node_init_ev_label, new_thread = True)
        sync_tran = self.__broadcast(sync_tran, self.ev_word, num_nodes, self.global_sync_ev_label, \
            (LOG2_LANE_PER_UD + LOG2_UD_PER_NODE), f"{num_ud_per_node} EQT ")
        sync_tran.writeAction(f"mov_imm2reg {node_ctr} 0")
        sync_tran.writeAction(f"mov_imm2reg {num_updates} 0")
        sync_tran.writeAction(f"mov_imm2reg {num_consume} 0")
        sync_tran.writeAction("continue: yield")
        if self.debug_flag_term:
            sync_tran.writeAction(f"bfs_hang: print '[DEBUG][NWID %d][{self.global_sync_ev_label}] bfs looping, num_updates = %d, num_consumes = %d' {'X0'} {num_updates} {num_consume}")
        # Synchronization finishes, start next iteration
        sync_tran.writeAction(f"bfs_sync_fin: sendr3_wcont {saved_cont} EQT {num_nodes} {num_ud_per_node} {num_iter}")
        # sync_tran.writeAction(f"bfs_sync_fin: mov_imm2reg {self.scratch[0]} {FLAG}")
        # sync_tran.writeAction(f"move {self.scratch[0]} {self.top_flag_offset}({lm_base_addr}) 0 8")
        # if self.top_val_offset:
        #     sync_tran.writeAction(f"move {num_consume} {self.top_val_offset}({lm_base_addr}) 0 8")
        if TERMINATE_DEBUG_FLAG:
            sync_tran.writeAction(f"print '[DEBUG][NWID %d][{self.global_sync_ev_label}] bfs iteration %d synchronization finishes, num_updates = %d, num_consumes = %d' {'X0'} {num_iter} {num_updates} {num_consume}")
        sync_tran.writeAction(f"perflog 1 {1} 'BFS iteration %d synchronization finishes, num_updates = %ld, num_consumes = %ld' {num_iter} {num_updates} {num_consume}")
        sync_tran.writeAction("yield_terminate")

        return init_tran, sync_tran

    def node_sync(self):
        saved_cont      = "UDPR_0"
        num_ud_per_node = "UDPR_1"
        ud_ctr          = "UDPR_2"
        num_updates     = "UDPR_3"
        num_consume     = "UDPR_4"
        self.ev_word    = "UDPR_11"

        '''
        OB_0:   Number of UpDowns per node
        OB_1:   Global sync init event word
        '''
        init_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.node_init_ev_label)
        if self.debug_flag_term and False:
            init_tran.writeAction(f"print ' '")
            init_tran.writeAction(f"print '[DEBUG][NWID %d] Event <init_node_sync> ev_word=%d:' {'X0'} {'EQT'}")
        init_tran.writeAction(f"addi {f'X{OB_REG_BASE+0}'} {num_ud_per_node} 0")
        init_tran = set_ev_label(init_tran, self.ev_word, self.ud_entry_ev_label, new_thread=True)
        init_tran = self.__broadcast(init_tran, self.ev_word, num_ud_per_node, self.node_sync_ev_label, \
            LOG2_LANE_PER_UD, f"EQT EQT ")
        init_tran.writeAction(f"mov_imm2reg {ud_ctr} 0")
        init_tran.writeAction(f"mov_imm2reg {num_updates} 0")
        init_tran.writeAction(f"mov_imm2reg {num_consume} 0")
        init_tran.writeAction(f"addi X1 {saved_cont} 0")
        if self.debug_flag_term:
            init_tran.writeAction(f"print '[DEBUG][NWID %d] init node synchronization num_ud = %d, saved_cont = %d' {'X0'} {num_ud_per_node} {saved_cont}")
        init_tran.writeAction("yield")

        '''
        OB_0:   Number of updates generated on source UD
        OB_1:   Number of updates consumed on source UD
        OB_2:   Source updown nwid
        '''
        sync_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.node_sync_ev_label)
        # if self.debug_flag_term:
        #     sync_tran.writeAction(f"print ' '")
        #     sync_tran.writeAction(f"print '[DEBUG][NWID %d] Event <node_sync> ev_word=%d:' {'X0'} {'EQT'}")
        sync_tran.writeAction(f"addi {ud_ctr} {ud_ctr} 1")
        sync_tran.writeAction(f"add {num_updates} {f'X{OB_REG_BASE+0}'} {num_updates}")
        sync_tran.writeAction(f"add {num_consume} {f'X{OB_REG_BASE+1}'} {num_consume}")
        if self.debug_flag_term:
            sync_tran.writeAction(f"print '[DEBUG][NWID %d] node synchronization ud_ctr = %d, num_updates = %d, num_consumes = %d' {'X0'} {ud_ctr} {num_updates} {num_consume}")
        sync_tran.writeAction(f"blt {ud_ctr} {num_ud_per_node} continue")
        sync_tran.writeAction(f"sendr3_wcont {saved_cont} EQT {num_updates} {num_consume} NWID")
        sync_tran.writeAction(f"yield_terminate")
        sync_tran.writeAction("continue: yield")

        return init_tran, sync_tran

    def updown_accumulate(self):
        num_ln_per_ud   = "UDPR_0"
        bank_base_addr  = "UDPR_1"
        lane_ctr    = "UDPR_2"
        num_updates = "UDPR_3"
        num_consume = "UDPR_4"
        num_iters   = "UDPR_5"
        saved_cont  = "UDPR_6"
        accum_evw   = "UDPR_7"
        temp = self.scratch[0]
        
        entry_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_entry_ev_label)
        entry_tran.writeAction(f"mov_imm2reg {num_iters} {NUM_DELAYS}")
        set_ev_label(entry_tran, self.ev_word, self.ud_loop_ev_label, new_thread=True)
        entry_tran.writeAction(f"movir {lane_ctr} 6")
        # Create send policy (shortest within 64 lanes)
        entry_tran.writeAction(f"sli {lane_ctr} {lane_ctr} {27}")
        entry_tran.writeAction(f"or {'X0'} {lane_ctr} {lane_ctr}")
        set_nwid(entry_tran, self.ev_word, lane_ctr, src_ev=self.ev_word)
        set_ev_label(entry_tran, accum_evw, self.ud_accum_ev_label)
        entry_tran.writeAction(f"sendr3_wcont {self.ev_word} {accum_evw} {num_iters} {self.ev_word} {'X0'}")
        entry_tran.writeAction(f"addi {'X1'} {saved_cont} 0")
        entry_tran.writeAction("yield")

        accum_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_accum_ev_label)
        if self.debug_flag_term and False:
            accum_tran.writeAction(f"print ' '")
            accum_tran.writeAction(f"print '[DEBUG][NWID %d] Event <ud_accumulate> ev_word=%d:' {'X0'} {'EQT'}")
        accum_tran.writeAction(f"movir {num_ln_per_ud} {LANE_PER_UD}")
        accum_tran.writeAction(f"movir {lane_ctr} 0")
        accum_tran.writeAction(f"movir {num_updates} 0")
        accum_tran.writeAction(f"movir {num_consume} 0")
        accum_tran.writeAction(f"accumulate_loop: lshift {lane_ctr} {bank_base_addr} 16")
        accum_tran.writeAction(f"add X7 {bank_base_addr} {bank_base_addr}")
        accum_tran.writeAction(f"move {self.num_updates_offset}({bank_base_addr}) {temp} 0 8")
        accum_tran.writeAction(f"add {temp} {num_updates} {num_updates}")
        accum_tran.writeAction(f"move {self.num_consume_offset}({bank_base_addr}) {temp} 0 8")
        accum_tran.writeAction(f"add {temp} {num_consume} {num_consume}")
        accum_tran.writeAction(f"addi {lane_ctr} {lane_ctr} 1")
        accum_tran.writeAction(f"blt {lane_ctr} {num_ln_per_ud} accumulate_loop")
        if self.debug_flag_term:
            accum_tran.writeAction(f"print '[DEBUG][NWID %d] ud synchronization num_updates = %d, num_consumes = %d, saved_cont = %d' {'X0'} {num_updates} {num_consume} {'X1'}")
        accum_tran.writeAction(f"sendr3_reply {num_updates} {num_consume} NWID {self.scratch[2]}")
        accum_tran.writeAction("yield_terminate")
        
        '''
        Loop transition. Return to the ud sync thread when counter goes down to 0
        OB_0:   Number of iterations
        OB_1:   Loop event word
        OB_2:   UD sync nwid. 
        '''
        loop_tran = self.state.writeTransition("eventCarry", self.state, self.state, self.ud_loop_ev_label)
        if self.debug_flag_term and False:
            loop_tran.writeAction(f"print ' '")
            loop_tran.writeAction(f"print '[DEBUG][NWID %d] Event <ud_loop> num_iter=%ld ud_sync_lane_nwid=%ld curr_nwid=%ld loop_evw=%lu' {'X0'} {'X8'} {'X10'} {'X0'} {'X9'}")
        loop_tran.writeAction(f"beqi {'X8'} 0 ud_loop_term")
        loop_tran.writeAction(f"subi {'X8'} {num_iters} 1")
        loop_tran.writeAction(f"sendr3_wcont {'X9'} {'X1'} {num_iters} {'X9'} {'X10'}")
        loop_tran.writeAction("yieldt")
        loop_tran.writeAction(f"ud_loop_term: sendr3_reply X8 X0 X10 {temp}")
        loop_tran.writeAction("yieldt")

        return accum_tran

    def __broadcast(self, tran: EFAProgram.Transition, ev_word, num_dst, ret_label, log2_stride, data):
        counter     = self.scratch[1]
        dst_nwid    = self.scratch[0]
        
        if self.debug_flag_term:
            if isinstance(num_dst, int) or num_dst.isdigit():
                tran.writeAction(f"print '[DEBUG][NWID %d] broadcase to {num_dst} destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} ")
            else:
                tran.writeAction(f"print '[DEBUG][NWID %d] broadcase to %d destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} {num_dst}")

        tran.writeAction(f"mov_imm2reg {counter} 0")
        tran.writeAction(f"broadcast_loop: lshift {counter} {dst_nwid} {log2_stride}")
        tran.writeAction(f"add {'X0'} {dst_nwid} {dst_nwid}")
        tran = set_nwid(tran, self.ev_word, dst_nwid, src_ev=ev_word)
        tran.writeAction(f"sendr_wret {ev_word} {ret_label} {data} {self.scratch[2]}")
        tran.writeAction(f"addi {counter} {counter} 1")
        if isinstance(num_dst, int) or num_dst.isdigit():
            tran.writeAction(f"blti {counter} {num_dst} broadcast_loop")
        else:
            tran.writeAction(f"blt {counter} {num_dst} broadcast_loop")

        return tran