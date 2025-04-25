from KVMSRMachineConfig import *

'''
Macros for UpDown - a mid-level abstraction between UpDown assembly and high-level language.

The goals for these macros are promoting code reuse, easing programming UpDown, demonstrating 
good coding practice, and helping composing larger programs from smaller building blocks. 
Most of these macros are short code snippets common in all kinds of programs, and hence can 
also be used as programming reference.


All the macros defined below should follow the format:

def func(transitions, regs, imms, scratch_regs, labels, mode):
	tran1, tran2, … = transitions
	data1, data2, … = regs
	imm1, imm2, …   = imms
	tmp1, tmp2, …   = scratch_regs
	ev1, label1, …  = labels
	tran1.writeAction(“...”)
	……
	return transitions

where transitions are a set of transitions in which code will be inserted,
      regs are a set of register names for input parameters 
      imms are set of immediates values
      
'''

def fetch_elements(tran, regs, imms, scratch_regs, mode):
    if "ret" in mode: 
        addr, num_elements, stride = regs
        size, stride, cont = imms
        send = "send_dmlm_ld_wret"
    else: 
        addr, num_elements, stride, cont = regs
        size, stride = imms[0]
        send = "send_dmlm_ld"
    ctr = scratch_regs[0]
    tran.writeAction(f"mov_imm2reg {ctr} 0")
    tran.writeAction(f"macro_fetch_loop: {send} {addr} {cont} {size}")
    tran.writeAction(f"addi {addr} {addr} {stride}")
    tran.writeAction(f"addi {ctr} {ctr} 1")
    tran.writeAction(f"blt {ctr} {num_elements} macro_fetch_loop")
    return tran

def send_lane_data(tran, dest, cont, data1, data2, scratch_regs, mode):
    # dest, data1, data2, cont
    send = "send"
    if "lm" not in mode: send += "r"
    if "ret" in mode: send += "_wret"
    else: send += "_wcont"
    if type(dest) == list:
        nwid, tid, label = dest
        dest_event = scratch_regs[0]
        if tid.isdigit() :
            tran.writeAction(f"ev_update_2 {dest_event} {label} {tid} 5")
            tran.writeAction(f"ev_update_reg_2 {dest_event} {dest_event} {nwid} {nwid} 8")
        else:
            tran.writeAction(f"ev_update_1 EQT {dest_event} {label} 1")
            tran.writeAction(f"ev_update_reg_2 {dest_event} {dest_event} {tid} {nwid} 12")
    else: 
        dest_event = dest
        nwid = scratch_regs[0]
        tran.writeAction(f"rshift {dest_event} {nwid} 32")
    tran.writeAction(f"{send} {dest_event} {nwid} {cont} {data1} {data2}")
    return tran

def proc_call(tran, regs, imms, scratch_regs, labels, mode):
    tid = 0xff if len(imms)==0 else imms[0]
    if (mode & 1): send = "sendr"
    else: send = "send"
    if (mode & 2):
        if (mode & 4):
            dest_event, dest_id, data1, data2, cont_event = regs
            tran.writeAction(f"{send}_wcont {dest_event} {dest_id} {cont_event} {data1} {data2}")
        else:
            dest_event, dest_id, data1, data2 = regs
            cont_event = labels[0]
            tran.writeAction(f"{send}_wret {dest_event} {dest_id} {cont_event} {data1} {data2}")
    else:
        dest_event = scratch_regs[0] 
        if (mode & 4):
            dest_id, data1, data2, cont_event = regs
            tran.writeAction(f"evii {dest_event} {dest_label} {tid} 5")
            tran.writeAction(f"ev {dest_event} {dest_event} {dest_id} {dest_id} 8")
            tran.writeAction(f"{send}_wcont {dest_event} {dest_id} {cont_event} {data1} {data2}")
        else:
            dest_id, data1, data2 = regs
            dest_label, cont_event = labels[0]
            tran.writeAction(f"evii {dest_event} {dest_label} {tid} 5")
            tran.writeAction(f"ev {dest_event} {dest_event} {dest_id} {dest_id} 8")
            tran.writeAction(f"{send}_wret {dest_event} {dest_id} {cont_event} {data1} {data2}")
    return tran

def spin_lock(tran, lm_addr: str, value: str, op: str, result: str, scratch_regs: list):
    tmp1, tmp2 = scratch_regs[0:2]
    tran.writeAction(f"macro_lock_loop: movlr 0({lm_addr}) {tmp1} 0 8")
    tran.writeAction(f"{op} {tmp1} {value} {result}")
    tran.writeAction(f"cswp {lm_addr} {tmp2} {tmp1} {result}")
    # tran.writeAction(f"print '[DEBUG] spin_lock X1=%lu(0x%lx) X2=%lu(lm_val) X3=%lu(old) X4=%lu(new)' {lm_addr} {lm_addr} {tmp2} {tmp1} {result}")
    tran.writeAction(f"bne {tmp1} {tmp2} macro_lock_loop")
    return tran

def set_nwid(tran, ev_word, new_nwid, src_ev="X2", new_thread=False, label = ""):
    if label: label = f"{label}: "
    if isinstance(new_nwid, int) or new_nwid.isdigit():
        if new_thread and (src_ev in "EQT|X2"):
            tran.writeAction(f"{label}evii {ev_word} {255} {new_nwid} {0b1100}")
        else:
            tran.writeAction(f"{label}evi {src_ev} {ev_word} {new_nwid} {0b1000}")
            tran.writeAction(f"evi {ev_word} {ev_word} {255} {0b0100}")
    else:
        tran.writeAction(f"{label}ev {src_ev} {ev_word} {new_nwid} {new_nwid} {0b1000}")
        if new_thread:
            tran.writeAction(f"evi {ev_word} {ev_word} {255} {0b0100}")
    return tran

def set_ev_label(tran, ev_word, new_label, src_ev="X2", new_thread=False, label = ""):
    if label: label = f"{label}: "
    if new_thread:
        tran.writeAction(f"{label}evi {src_ev} {ev_word} 255 {0b0100}")
    else :
        tran.writeAction(f"{label}addi {src_ev} {ev_word} 0")
    tran.writeAction(f"evlb {ev_word} {new_label}")
    return tran

def broadcast(tran, ev_word, num_dst, ret_label, log2_stride, data, scratch, mode='r', send_temp_reg_flag=True):
        counter     = scratch[1]
        dst_nwid    = scratch[0]

        # if self.debug_flag_term:
        #     if isinstance(num_dst, int) or num_dst.isdigit():
        #         tran.writeAction(f"print '[DEBUG][NWID %d] broadcase to {num_dst} destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} ")
        #     else:
        #         tran.writeAction(f"print '[DEBUG][NWID %d] broadcase to %d destination ret_label = {ret_label} stride = {1 << log2_stride}' {'X0'} {num_dst}")

        tran.writeAction(f"mov_imm2reg {counter} 0")
        if log2_stride > 0:
            tran.writeAction(f"broadcast_loop: lshift {counter} {dst_nwid} {log2_stride}")
            tran.writeAction(f"add {'X0'} {dst_nwid} {dst_nwid}")
        else:
            tran.writeAction(f"broadcast_loop: add {'X0'} {counter} {dst_nwid}")
        tran = set_nwid(tran, ev_word, dst_nwid, src_ev=ev_word)
        if ret_label[0] == 'X' or ret_label[0:2] == 'OB' or ret_label[0:4] == 'UDPR':
            tran.writeAction(f"send{mode}{'_wcont'} {ev_word} {ret_label} {data}")
        else:
            tran.writeAction(format_pseudo(f"send{mode}_wret {ev_word} {ret_label} {data}", dst_nwid, send_temp_reg_flag))
        tran.writeAction(f"addi {counter} {counter} 1")
        if isinstance(num_dst, int) or num_dst.isdigit():
            tran.writeAction(f"blti {counter} {num_dst} broadcast_loop")
        else:
            tran.writeAction(f"blt {counter} {num_dst} broadcast_loop")

        return tran

def format_pseudo(command: str, temp_reg: str, flag: bool = True):
    return f"{command} {temp_reg if flag else ''}"

def send_dram_write(tran, dest_addr: str, cont, data: str, suffix: str = ''):
    
    if isinstance(cont, int) or cont.isdigit(): mode = 1
    elif (cont[0] == 'X' or cont[0:2] == 'OB' or cont[0:4] == 'UDPR') and cont[-1].isdigit(): mode = 0
    else: mode = 1
    
    if suffix == 'r':
        tran.writeAction(f"sendmr{'2' if len(data.split(' ')) > 1 else ''} {dest_addr} {cont} {data}")
    elif suffix == 'ops':
        tran.writeAction(f"sendmops {dest_addr} {cont} {data} {mode}")
    else:
        mode = mode << 1 | 1
        tran.writeAction(f"sendm {dest_addr} {cont} {data} {mode}")
    return tran

def send_dram_read(tran, dest_addr: str, cont, num_words: int):
    
    if isinstance(cont, int) or cont.isdigit(): mode = 1
    elif (cont[0] == 'X' or cont[0:2] == 'OB' or cont[0:4] == 'UDPR') and cont[-1].isdigit(): mode = 0
    else: mode = 1
    mode = mode << 1 | 0
    tran.writeAction(f"sendm {dest_addr} {cont} {num_words} {num_words} {mode}")
    return tran

def send_lane(tran, evw: str, cont, data: list, suffix: str = ''):
    
    if isinstance(cont, int) or cont.isdigit(): mode = 1
    elif (cont[0] == 'X' or cont[0:2] == 'OB' or cont[0:4] == 'UDPR') and cont[-1].isdigit(): mode = 0
    else: mode = 1
    
    if suffix == 'r':
        tran.writeAction(f"sendr{'3' if len(data.split(' ')) > 2 else ''} {evw} {cont} {data}")
    elif suffix == 'ops':
        tran.writeAction(f"sendops {evw} {cont} {data} {mode}")
    else:
        tran.writeAction(f"send {evw} {cont} {data} {mode}")
    return tran

def get_num_child(tran, total_num_lanes: str, result: str, max_child: int, num_lane_per_child: int, label: str, reg: str):
    
    max_child_label = f"max_child_{label}"
    tran.writeAction(f"sri {total_num_lanes} {result} {int(log2(num_lane_per_child))}")
    if isinstance(max_child, int) or max_child.isdigit(): 
        if max_child >= 32:
            tran.writeAction(f"movir {reg} {max_child}")
            tran.writeAction(f"bgt {result} {reg} {max_child_label}")
        else:
            tran.writeAction(f"bgti {result} {max_child} {max_child_label}")
    else: tran.writeAction(f"bgt {result} {max_child} {max_child_label}")
    tran.writeAction(f"andi {total_num_lanes} {reg} {num_lane_per_child - 1}")
    tran.writeAction(f"beqi {reg} 0 {label}")
    tran.writeAction(f"addi {result} {result} 1")
    tran.writeAction(f"jmp {label}")
    tran.writeAction(f"{max_child_label}: mov_imm2reg {result} {max_child}")
    return tran

def get_num_node(tran, total_num_lanes: str, result: str, label: str, reg: str):
    return get_num_child(tran, total_num_lanes, result, MAX_NUM_NODES, LANE_PER_UD * UD_PER_NODE, label, reg)

def get_num_ud_per_node(tran, total_num_lanes: str, result: str, label: str, reg: str):
    return get_num_child(tran, total_num_lanes, result, UD_PER_NODE, LANE_PER_UD, label, reg)

def get_num_lane_per_ud(tran, total_num_lanes: str, result: str, label: str):
    
    tran.writeAction(f"movir {result} {LANE_PER_UD}")
    tran.writeAction(f"bgt {total_num_lanes} {result} {label}")
    tran.writeAction(f"addi {total_num_lanes} {result} 0")
    return tran

def get_event_label(id: str, label: str) -> str:
    return f"{id}::{label}"

def set_ignore_cont(tran, ev_word: str, label: str = ""):
    if label: label = f"{label}: "
    tran.writeAction(f"{label}movir {ev_word} {-1}")
    tran.writeAction(f"sri {ev_word} {ev_word} 1")
    return tran