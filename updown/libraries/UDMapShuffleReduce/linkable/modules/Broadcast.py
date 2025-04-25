from linker.EFAProgram import efaProgram
from linker.EFAsections.StaticDataSection import staticDataType

@efaProgram
def efaProgram_Broadcast(efa):

    ## init_null_state
    init_null_state = efa.State("init_null_state")
    efa.add_state(init_null_state)
    efa.add_initId(init_null_state.state_id)

    ## Broadcast__broadcast_global
    Broadcast__broadcast_global = init_null_state.writeTransition("eventCarry", init_null_state, init_null_state, "Broadcast__broadcast_global")
    Broadcast__broadcast_global.writeAction("addi X8 X27 0")
    Broadcast__broadcast_global.writeAction("sri X27 X25 11")
    Broadcast__broadcast_global.writeAction("movir X16 128")
    Broadcast__broadcast_global.writeAction("bgt X25 X16 GenLinkableBroadcast_aorqr_max_child_modular_eq_zero")
    Broadcast__broadcast_global.writeAction("andi X27 X16 2047")
    Broadcast__broadcast_global.writeAction("beqi X16 0 GenLinkableBroadcast_aorqr_modular_eq_zero")
    Broadcast__broadcast_global.writeAction("addi X25 X25 1")
    Broadcast__broadcast_global.writeAction("jmp GenLinkableBroadcast_aorqr_modular_eq_zero")
    Broadcast__broadcast_global.writeAction("GenLinkableBroadcast_aorqr_max_child_modular_eq_zero: mov_imm2reg X25 128")
    Broadcast__broadcast_global.writeAction("GenLinkableBroadcast_aorqr_modular_eq_zero: evi X2 X28 255 4")
    Broadcast__broadcast_global.writeAction("evlb X28 Broadcast__broadcast_node")
    Broadcast__broadcast_global.writeAction("mov_imm2reg X17 0")
    Broadcast__broadcast_global.writeAction("GenLinkableBroadcast_aorqr_broadcast_loop: lshift X17 X16 11")
    Broadcast__broadcast_global.writeAction("add X0 X16 X16")
    Broadcast__broadcast_global.writeAction("ev X28 X28 X16 X16 8")
    Broadcast__broadcast_global.writeAction("sendops_wret X28 Broadcast__broadcast_global_fin X8 8 X16")
    Broadcast__broadcast_global.writeAction("addi X17 X17 1")
    Broadcast__broadcast_global.writeAction("blt X17 X25 GenLinkableBroadcast_aorqr_broadcast_loop")
    Broadcast__broadcast_global.writeAction("mov_imm2reg X26 0")
    Broadcast__broadcast_global.writeAction("yield")

    ## Broadcast__broadcast_node
    Broadcast__broadcast_node = init_null_state.writeTransition("eventCarry", init_null_state, init_null_state, "Broadcast__broadcast_node")
    Broadcast__broadcast_node.writeAction("addi X1 X29 0")
    Broadcast__broadcast_node.writeAction("sri X8 X25 6")
    Broadcast__broadcast_node.writeAction("movir X16 32")
    Broadcast__broadcast_node.writeAction("bgt X25 X16 GenLinkableBroadcast_aorqr_max_child_modular_eq_zero")
    Broadcast__broadcast_node.writeAction("andi X8 X16 63")
    Broadcast__broadcast_node.writeAction("beqi X16 0 GenLinkableBroadcast_aorqr_modular_eq_zero")
    Broadcast__broadcast_node.writeAction("addi X25 X25 1")
    Broadcast__broadcast_node.writeAction("jmp GenLinkableBroadcast_aorqr_modular_eq_zero")
    Broadcast__broadcast_node.writeAction("GenLinkableBroadcast_aorqr_max_child_modular_eq_zero: mov_imm2reg X25 32")
    Broadcast__broadcast_node.writeAction("GenLinkableBroadcast_aorqr_modular_eq_zero: evi X2 X28 255 4")
    Broadcast__broadcast_node.writeAction("evlb X28 Broadcast__broadcast_ud")
    Broadcast__broadcast_node.writeAction("mov_imm2reg X17 0")
    Broadcast__broadcast_node.writeAction("GenLinkableBroadcast_aorqr_broadcast_loop: lshift X17 X16 6")
    Broadcast__broadcast_node.writeAction("add X0 X16 X16")
    Broadcast__broadcast_node.writeAction("ev X28 X28 X16 X16 8")
    Broadcast__broadcast_node.writeAction("sendops_wret X28 Broadcast__broadcast_node_fin X8 8 X16")
    Broadcast__broadcast_node.writeAction("addi X17 X17 1")
    Broadcast__broadcast_node.writeAction("blt X17 X25 GenLinkableBroadcast_aorqr_broadcast_loop")
    Broadcast__broadcast_node.writeAction("mov_imm2reg X26 0")
    Broadcast__broadcast_node.writeAction("yield")

    ## Broadcast__broadcast_ud
    Broadcast__broadcast_ud = init_null_state.writeTransition("eventCarry", init_null_state, init_null_state, "Broadcast__broadcast_ud")
    Broadcast__broadcast_ud.writeAction("addi X1 X29 0")
    Broadcast__broadcast_ud.writeAction("movir X25 64")
    Broadcast__broadcast_ud.writeAction("bgt X8 X25 GenLinkableBroadcast_aorqr_modular_eq_zero")
    Broadcast__broadcast_ud.writeAction("addi X8 X25 0")
    Broadcast__broadcast_ud.writeAction("GenLinkableBroadcast_aorqr_modular_eq_zero: evi X2 X28 255 4")
    Broadcast__broadcast_ud.writeAction("ev X28 X28 X9 X9 1")
    Broadcast__broadcast_ud.writeAction("mov_imm2reg X17 0")
    Broadcast__broadcast_ud.writeAction("GenLinkableBroadcast_aorqr_broadcast_loop: add X0 X17 X16")
    Broadcast__broadcast_ud.writeAction("ev X28 X28 X16 X16 8")
    Broadcast__broadcast_ud.writeAction("sendops_wret X28 Broadcast__broadcast_ud_fin X10 6 X16")
    Broadcast__broadcast_ud.writeAction("addi X17 X17 1")
    Broadcast__broadcast_ud.writeAction("blt X17 X25 GenLinkableBroadcast_aorqr_broadcast_loop")
    Broadcast__broadcast_ud.writeAction("mov_imm2reg X26 0")
    Broadcast__broadcast_ud.writeAction("yield")

    ## Broadcast__broadcast_ud_fin
    Broadcast__broadcast_ud_fin = init_null_state.writeTransition("eventCarry", init_null_state, init_null_state, "Broadcast__broadcast_ud_fin")
    Broadcast__broadcast_ud_fin.writeAction("addi X26 X26 1")
    Broadcast__broadcast_ud_fin.writeAction("blt X26 X25 GenLinkableBroadcast_aorqr_continue")
    Broadcast__broadcast_ud_fin.writeAction("sendr_reply X0 X2 X16")
    Broadcast__broadcast_ud_fin.writeAction("yield_terminate")
    Broadcast__broadcast_ud_fin.writeAction("GenLinkableBroadcast_aorqr_continue: yield")

    ## Broadcast__broadcast_node_fin
    Broadcast__broadcast_node_fin = init_null_state.writeTransition("eventCarry", init_null_state, init_null_state, "Broadcast__broadcast_node_fin")
    Broadcast__broadcast_node_fin.writeAction("addi X26 X26 1")
    Broadcast__broadcast_node_fin.writeAction("blt X26 X25 GenLinkableBroadcast_aorqr_continue")
    Broadcast__broadcast_node_fin.writeAction("sendr_reply X0 X2 X16")
    Broadcast__broadcast_node_fin.writeAction("yield_terminate")
    Broadcast__broadcast_node_fin.writeAction("GenLinkableBroadcast_aorqr_continue: yield")

    ## Broadcast__broadcast_global_fin
    Broadcast__broadcast_global_fin = init_null_state.writeTransition("eventCarry", init_null_state, init_null_state, "Broadcast__broadcast_global_fin")
    Broadcast__broadcast_global_fin.writeAction("addi X26 X26 1")
    Broadcast__broadcast_global_fin.writeAction("beq X26 X25 GenLinkableBroadcast_aorqr_global_bcst_finish")
    Broadcast__broadcast_global_fin.writeAction("yield")
    Broadcast__broadcast_global_fin.writeAction("GenLinkableBroadcast_aorqr_global_bcst_finish: sendr_reply X0 X2 X16")
    Broadcast__broadcast_global_fin.writeAction("yieldt")

    ## Broadcast__broadcast_value_to_scratchpad
    Broadcast__broadcast_value_to_scratchpad = init_null_state.writeTransition("eventCarry", init_null_state, init_null_state, "Broadcast__broadcast_value_to_scratchpad")
    Broadcast__broadcast_value_to_scratchpad.writeAction("sri X8 X16 32")
    Broadcast__broadcast_value_to_scratchpad.writeAction("add X7 X16 X16")
    Broadcast__broadcast_value_to_scratchpad.writeAction("andi X8 X17 15")
    Broadcast__broadcast_value_to_scratchpad.writeAction("bcpyol X9 X16 X17")
    Broadcast__broadcast_value_to_scratchpad.writeAction("sendr_reply X1 X2 X16")
    Broadcast__broadcast_value_to_scratchpad.writeAction("yieldt")