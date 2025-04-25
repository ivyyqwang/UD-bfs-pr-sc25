# ==============================================================
# 10x10 - Systematic Heterogenous Architecture
# https://sites.google.com/site/uchicagolssg/lssg/research/10x10
# Copyright (C) 2016 University of Chicago.
# See license.txt in top-level directory.
# ==============================================================

from enum import Enum, auto
import sys
import pdb
import struct

from EfaUtil_v2 import *

UNDEFINED = 0XFFFFFFFF

class PerfLogPayload(Enum):
    '''
    Payload selection enum for perflog
    '''
    UD_CYCLE_STATS = auto()
    UD_ACTION_STATS = auto()
    UD_TRANS_STATS = auto()
    UD_QUEUE_STATS = auto()
    UD_LOCAL_MEM_STATS = auto()
    UD_MEM_INTF_STATS = auto()
    SYS_MEM_INTF_STATS = auto()


# ====== internal helper function ======
def GetAction(asm_inst):
    ActionClass, operand = ParseAction(asm_inst)
    if ActionClass == "IAction":
        action = IAction(operand.opcode, 
                         operand.dst, 
                         operand.src, 
                         operand.imm, 
                         operand.label, 
                         1)
    elif ActionClass == "I2Action":
        action = I2Action(operand.opcode, operand.dst, operand.src, operand.imm, operand.imm2, operand.label, 1, operand.lm_mode)
    elif ActionClass == "I3Action":
        action = I3Action(operand.opcode, operand.dst, operand.op1, operand.op2,operand.op3, operand.label, 1, operand.lm_mode)
    elif ActionClass == "EAction":
        action = EAction(operand.opcode, operand.src, operand.dst, operand.op1, operand.op2, operand.imm, operand.label)
    elif ActionClass == "RAction":
        action = RAction(operand.opcode, operand.dst, operand.src, operand.rt, operand.label, 1, operand.imm, operand.lm_mode)
    # Marziyeh
    elif ActionClass == "FPAction":
        action = FPAction(operand.opcode, operand.dst, operand.src, operand.rt, operand.mode, operand.mask, operand.precision, operand.label)
    # Marziyeh
    elif ActionClass == "VAction":
        action = VAction(operand.opcode, operand.dst, operand.src, operand.rt, operand.mode, operand.mask, operand.precision, operand.label)
    elif ActionClass == "BAction":
        action = BAction(
            operand.opcode,
            operand.dst,
            operand.op1,
            operand.op2,
            operand.op1_ob_or_reg,
            operand.op2_ob_or_reg_or_imm,
            operand.dst_issb,
            operand.funct,
            operand.unsigned,
            operand.label,
        )
    elif ActionClass == "SAction":
        action = SAction(
            operand.opcode,
            operand.event,
            operand.dst,
            operand.cont,
            operand.op1,
            operand.op2,
            operand.op3,
            operand.addr_mode,
            operand.size,
            operand.label,
            operand.tmp_reg1,
        )
    elif ActionClass == "SPAction":
        action = SPAction(
            operand.opcode, 
            operand.event, 
            operand.dst, 
            operand.cont, 
            operand.op1, 
            operand.reglist, 
            operand.addr_mode, 
            operand.label, 
            operand.tmp_reg1
        )
    elif ActionClass == "YAction":
        action = YAction(operand.opcode, operand.label)
    elif ActionClass == "PAction":
        action = PAction(operand.opcode, operand.formatstr, operand.reglist, operand.print_id, operand.label)
    elif ActionClass == "PerflogAction":
        action = PerflogAction(operand.opcode, operand.perflog_mode, operand.perflog_payload_list, operand.perflog_msg_id, operand.formatstr, operand.reglist, operand.print_id, operand.label)
    elif ActionClass == "InsTransAction":
        #action = InsTransAction(operand.opcode, operand.mask, operand.vbase, operand.size, operand.pbase, operand.access, operand.label)
        action = InsTransAction(operand.opcode, operand.op1, operand.op2, operand.op3, operand.size, operand.mode, operand.op4, operand.label)
    elif ActionClass == "UserCounterAction":
        action = UserCounterAction(operand.opcode, operand.userctr_mode, operand.userctr_num, operand.userctr_arg, operand.label)
    elif ActionClass == "LMMemcheckAction":
        action = LMMemcheckAction(operand.opcode, operand.mode, operand.op1, operand.op2, operand.label)
    else:
        print(f"Action class {ActionClass} operand {operand}")
        print("Cannot parse the action:\t" + asm_inst)
        exit()
    return action, operand.maxudp, operand.maxop

# ==============================


class Event:
    '''
    Defining a class event that is very similar to transition for now. Could potentially merge with Transition
    '''
    global_id = 0

    def __init__(self, event_label, num_ops):
        self.exe_count = 0
        self.event_id = Event.global_id
        Event.global_id += 1
        self.num_operands = num_ops
        self.event_label = event_label
        self.lane_num = 0
        self.network_id = 0
        self.thread_id = 0xFF  # to be assigned later
        self.cycle = 0
        self.mode = 0 # 0 - LM, 1 - SB
        # event_word - PTID[31:24]|TID[23:16]|EBASE[15:8]|ELABEL[7:0]
        self.event_word = (
            ((int(self.network_id) << 32) & 0xFFFFFFFF00000000)
            | ((int(self.thread_id) << 24) & 0x0FF000000)
            | ((int(self.mode) << 23) & 0x800000)
            | ((int(self.num_operands - 2) << 20) & 0x0700000)
            | (int(self.event_label) & 0x0FFFFF)
        )

    def __str__(self):
        return f"Event( ID: {self.event_id}, NetworkID: {self.network_id}, ThreadID: {self.thread_id}, NumOperands:{self.num_operands}, EventLabel: {self.event_label})"

    def setnetworkid(self, nwid):
        self.network_id = nwid
        self.event_word = (self.event_word & 0x00000000FFFFFFFF) | ((int(self.network_id) & 0x00000000FFFFFFFF) << 32)
        # self.printOutStr("Set Network Id", stage_trace)

    def setmode(self, mode):
        self.mode = mode
        self.event_word = self.event_word | (int(self.mode) << 23)
        # self.printOutStr("Set Thread Mode", stage_trace)


    #def setlanenum(self, lane_num):
    #    self.lane_num = lane_num
    #    self.event_word = (self.event_word & 0x00FFFFFF) | ((int(self.lane_num) << 24) & 0xFF000000)

    def setthreadid(self, thread_id):
        self.thread_id = thread_id
        self.event_word = (self.event_word & 0xFFFFFFFF00FFFFFF) | ((int(self.thread_id) << 24) & 0x0FF000000)
        # self.printOutStr("Set Thread Id", stage_trace)

    def printOut(self, LEVEL, TSTAMP=0):
        printd(
            f"Event( ID: {self.event_id}, NetworkID: {self.network_id}, ThreadID: {self.thread_id}, NumOperands:{self.num_operands}, eventLabel: {self.event_label})",
            LEVEL,
        )

    def printOutStr(self, str, LEVEL):
        printd(
            f"{str} Event( ID: {self.event_id}, NetworkID: {self.network_id}, ThreadID: {self.thread_id}, NumOperands:{self.num_operands}, eventLabel: {self.event_label})",
            LEVEL,
        )

    def getEventID(self):
        return self.event_id

    def getEventlabel(self):
        return self.event_label
    
    def numOps(self):
        return self.num_operands

    def set_cycle(self, cyc):
        self.cycle = cyc


class State:
    global_id = 0

    def __init__(self):
        self.exe_count = 0
        self.EFA_id = UNDEFINED     #used by the assembler
        self.state_id = State.global_id
        State.global_id += 1
        self.trans = []
        self.trans_label_dict = dict()
        self.trans_name_dict = dict()
        # we don't use state alphabet if it is empty
        # if not empty, we state.alphabet instead of efa.alphabet
        self.alphabet = []
        self.marked = 0             #used for EFA traversal algorithms

    def __str__(self):
        return f"state_id: {self.state_id}"

    def add_tran(self, transition):
        self.trans.append(transition)
        self.trans_label_dict[transition.label] = transition
        self.trans_name_dict[transition.name] = transition

    def get_tran(self, label, dst=None):
        # Merge two get_tran functions together (Modify by Lang Yu)
        res = []

        if dst is None:
            # find transition list by label
            for tr in self.trans:
                if tr.label == label:
                    res.append(tr)
            # add epsilon transition if dst state has any
            epsilon_tran = []
            for tr in res:
                res_dst = tr.dst
                for dst_tr in res_dst.trans:
                    if dst_tr.anno_type == "epsilon":
                        epsilon_tran.append(dst_tr)
            for ele in epsilon_tran:
                res.append(ele)
            return res
        else:
            # find transition list by destination and label
            if label != -1:
                for tr in self.trans:
                    if tr.dst == dst and tr.label == label:
                        res.append(tr)
            else:
                # Lang Yu add this to faciliate upper level construction
                # find all transitions to dst state
                for tr in self.trans:
                    if tr.dst == dst:
                        res.append(tr)
            return res

    # ====== get transition list by annotation type
    def get_tran_byAnnotation(self, anno_type):
        res = []
        for tr in self.trans:
            if tr.anno_type == anno_type:
                res.append(tr)
        return res

    # ====== get transition by pure label. No epsilon transition even dst state has
    def get_tran_byLabel(self, label):
        res = []
        # find transition list by label
        for tr in self.trans:
            if tr.label == label:
                res.append(tr)
        return res

    def get_event(self, label):
        res = []
        # find transition list by label
        for tr in self.events:
            if tr.label == label:
                res.append(tr)
        return res

    # ====== get transitions by destination state
    def get_tran_byDest(self, dst):
        res = []
        for tr in self.trans:
            if tr.dst == dst:
                res.append(tr)
        return res

    # ====== get transition's destination state list by label
    def get_dst(self, label):
        res = []
        for tr in self.trans:
            if tr.label == label:
                res.append(tr.dst)
        return res

    def printOut(self, LEVEL, TSTAMP=0):
        printd("state_id: " + str(self.state_id) + "\n", LEVEL, TSTAMP)
        for tr in self.trans:
            tr.printOut(LEVEL, TSTAMP)
    
    #def emitbin(self, fd):
    #    for tr in self.trans:
    #        tr.emitbin(fd)

    def getSize(self):
        tran_size = len(self.trans)
        action_size = 0
        for tr in self.trans:
            action_size += tr.getSize()
        return tran_size, action_size

    # ====== API expose externally, to write machine code level UDP program
    def writeTransition(self, Type, src_state, dst_state, label, refill_val=None):
        if src_state is not self:
            print("WARNING: writeTransition src state is not current state?!", file=sys.stderr)
        # # if the state exists, return None
        if isinstance(label, int) and label in self.trans_label_dict:
            return None
        elif label in self.trans_name_dict:
            return None
        if refill_val is not None:
            tran = Transition(src_state, dst_state, label, Type, None, refill_val)
        else:
            tran = Transition(src_state, dst_state, label, Type)
        if isinstance(label, int):
            tran.name = f"{label}"
        else:
            tran.name = label
            tran.label = tran.trans_id
        self.add_tran(tran)
        return tran

    def writeEvents(self, Type, src_state, dst_state, label):
        event = Event(src_state, dst_state, label, Type)
        self.add_event(event)
        return event

    def getTranLabelByName(self, tran_name):
        if tran_name in self.trans_name_dict:
            return self.trans_name_dict[tran_name].label
        else:
            return None

    def getTranByName(self, tran_name):
        if tran_name in self.trans_name_dict:
            return self.trans_name_dict[tran_name]
        else:
            return None


class Transition:
    global_id = 10000

    # ====== actions associated with the transition constructor can be a singleton object or a list of actions
    def __init__(self, src, dst, label, anno_type="labeled", action=None, refill_val=None):
        self.exe_count = 0
        self.name = None
        self.trans_id = Transition.global_id
        Transition.global_id += 1
        self.src = src
        self.dst = dst
        self.label = label
        self.anno_type = anno_type
        self.actions = []
        self.opsize = 0
        self.maxop = 0
        self.maxudp = 0
        self.labeldict = {}

        if refill_val is None:
            self.refill_val = 0
        else:
            self.refill_val = refill_val
        if action is not None:
            self.actions = concatSet(self.actions, action)
        for act in self.actions:
            act.last = 0
        if len(self.actions) > 0:
            self.actions[-1].last = 1

    def __str__(self):
        return f"tran(src: {self.src.state_id}, label: {self.label}, dst: {self.dst.state_id}, {self.anno_type})"

    def printOut(self, LEVEL, TSTAMP=0):
        printd(
            "tran( src: " + str(self.src.state_id)
            + ", label: " + str(self.label)
            + ", dst: " + str(self.dst.state_id) + ", "
            + self.anno_type + ", ",
            LEVEL, TSTAMP,
        )
        for act in self.actions:
            act.printOut(LEVEL, TSTAMP)
        printd(")\n", LEVEL, TSTAMP)
    
    #def emitbin(self, fd):
    #    # Note: need to dump transition as well eventually
    #    for act in self.actions:
    #        act.emitbin(fd)

    def hasActions(self):
        if self.actions == []:
            return False
        else:
            return True

    # ====== API expose externally, to write machine code level UDP program
    def writeAction(self, asm_inst):
        action, maxudp, maxop = GetAction(asm_inst)
        self.addAction(action)
        if action.label is not None:
            self.labeldict[action.label] = str(len(self.actions) - 1)
        if maxudp > self.maxudp:
            self.maxudp = maxudp
        if maxop > self.maxop:
            self.maxop = maxop
        return action

    def getSize(self):
        return len(self.actions)

    def addAction(self, action):
        if self.hasActions():
            self.actions[-1].last = 0
        if action.opcode == "goto":
            action.last = 0
        self.actions.append(action)

    def getAction(self, seqnum):
        return self.actions[int(seqnum)]

    def getMaxOp(self):
        return self.maxop

    def getMaxUdp(self):
        return self.maxudp

    def getLabel(self):
        return self.label

    def getName(self):
        return self.name


class SharedBlock:
    def __init__(self, efa, blockid):
        self.efa = efa
        self.blockid = blockid

    def writeAction(self, inst):
        self.efa.appendBlockAction(self.blockid, inst)

    def getLabel(self):
        return self.blockid


class EFA:
    def __init__(self, alphabet=range(0, 256)):
        self.names = dict()

        self.states = []

        # set of initial state
        self.init_state_id = []

        # set of state whose activation you want to export to a file after loading
        self.export_state_id = []

        # ====== sharedBlock[key] = [action1][action2]...
        # key is 'block_i'  value is an action list
        self.sharedBlock = dict()
        self.sharedBlocklabels = dict()

        self.EFA_sharedblocks = dict()            #used and filled by UD assembler
        self.sharedBlock_state_links = dict()       #filled by the programmer used by assembler to support HW triggered sharedblocks for each EFA

        # ====== Overall alphabet
        self.alphabet = alphabet

        # ====== efa's signature to tell whether it is in Assembly level or Machine code level
        # ====== By default, it is in Assembly level
        self.code_level = "assembly"

        # Andronicus adding udprsize, opsize
        self.udpsize = 0
        self.opsize = 0
        self.progbase = 0

        # clear up the counters for a new EFA
        State.global_id = 0
        Transition.global_id = 10000
        Event.global_id = 0

    def dump_execution_count(self, dump_path):
        # print('Dumping instruction execution stats to {}'.format(dump_path))
        with open(dump_path, 'w') as f:
            f.write('TYPE\tBLK_ACTION\tSTATE\tTRAN.NAME\tTRAN.LABEL\tTRAN.SRC\tTRAN.DST\tINSTRUCTION\tEXECUTION_COUNT\tDETAIL\n')
            for state in self.states:
                f.write(f'State\tN/A\t{state.state_id}\tN/A\tN/A\tN/A\tN/A\tN/A\t{state.exe_count}\t{str(state)}\n')
                for tran in state.trans:
                    f.write(f'Transition\tN/A\t{state.state_id}\t{tran.name}\t{tran.label}\t{tran.src.state_id}\t{tran.dst.state_id}\tN/A\t{tran.exe_count}\t{str(tran)}\n')
                    for action in tran.actions:
                        action_str = str(action)
                        insn_str = action_str.split(' ')[0][1:]
                        f.write(f'Action\tN/A\t{state.state_id}\t{tran.name}\t{tran.label}\t{tran.src.state_id}\t{tran.dst.state_id}\t{insn_str}\t{action.exe_count}\t{action_str}\n')
            for k, v in self.sharedBlock.items():
                for action in v:
                    action_str = str(action)
                    insn_str = action_str.split(' ')[0][1:]
                    f.write(f'BlockAction\t{k}\tN/A\tN/A\tN/A\tN/A\tN/A\t{insn_str}\t{action.exe_count}\t{action_str}\n')

    def reset_execution_count(self):
        for state in self.states:
            state.exe_count = 0
            for tran in state.trans:
                tran.exe_count = 0
                for action in tran.actions:
                    action.exe_count = 0
        for k, v in self.sharedBlock.items():
            for action in v:
                action.exe_count = 0

    def combine_execution_count(self, efa):
        for i, state in enumerate(self.states):
            efa_state = efa.states[i]
            state.exe_count += efa_state.exe_count
            for j, tran in enumerate(state.trans):
                efa_trans = efa_state.trans[j]
                tran.exe_count += efa_trans.exe_count
                for k, action in enumerate(tran.actions):
                    action.exe_count += efa_trans.actions[k].exe_count
        for k, v in self.sharedBlock.items():
            efa_v = efa.sharedBlock[k]
            for i, action in enumerate(v):
                action.exe_count += efa_v[i].exe_count

    def appendBlockAction(self, blockid, inst):
        # inst can be assembly(string format) or deserialized action
        if (
            not isinstance(inst, IAction)
            and not isinstance(inst, I2Action)
            and not isinstance(inst, I3Action)
            and not isinstance(inst, BAction)
            and not isinstance(inst, YAction)
            and not isinstance(inst, RAction)
            # Marziyeh
            and not isinstance(inst, FPAction)
            and not isinstance(inst, VAction)
        ):
            action, maxudp, maxop = GetAction(inst)
            if maxudp > self.udpsize:
                self.udpsize = maxudp
        else:
            action = inst

        action.last = 1
        if blockid not in self.sharedBlock:
            self.sharedBlock[blockid] = [action]
            self.sharedBlocklabels[blockid] = dict()
            if action.label is not None:
                self.sharedBlocklabels[blockid][action.label] = str(len(self.sharedBlock[blockid]) - 1)
        else:
            self.sharedBlock[blockid][-1].last = 0
            self.sharedBlock[blockid].append(action)
            if action.label is not None:
                self.sharedBlocklabels[blockid][action.label] = str(len(self.sharedBlock[blockid]) - 1)

    def linkBlocktoState(self, blockid, state):
        if blockid not in self.sharedBlock_state_links:
            self.sharedBlock_state_links[blockid] = [state]
        else:
            self.sharedBlock_state_links[blockid].append(state)


    def writeSharedBlock(self, blockid):
        if blockid not in self.sharedBlock:
            return SharedBlock(self, blockid)

    def add_state(self, state):
        self.states.append(state)

    def get_state(self, state_id):
        for s in self.states:
            if s.state_id == state_id:
                return s
        return None

    def add_name(self, id, name):
        self.names[id] = name

    def get_name(self):
        return self.names

    def get_init_state(self):
        return self.init_state_id

    def get_tran(self, trans_id):
        for s in self.states:
            for tr in s.trans:
                if tr.trans_id == trans_id:
                    return tr
        return None

    def add_initId(self, init_id):
        self.init_state_id.append(init_id)

    def printOut(self, LEVEL, TSTAMP=0):
        printd("==================Shared Action Blocks =================\n", LEVEL, TSTAMP)
        for k, v in self.sharedBlock.items():
            printd(k, LEVEL, TSTAMP)
            for act in v:
                act.printOut(LEVEL, TSTAMP)
            printd("\n===================================\n", LEVEL, TSTAMP)
        printd("==================Transitions =================\n", LEVEL, TSTAMP)
        for s in self.states:
            s.printOut(LEVEL, TSTAMP)
            printd("===================================\n", LEVEL, TSTAMP)

    def getSize(self):
        total_tran = 0
        total_action = 0
        total_shared = 0
        for st in self.states:
            tran_size, action_size = st.getSize()
            total_tran += tran_size
            total_action += action_size
        for k, v in self.sharedBlock.iteritems():
            total_shared += len(v)
        return total_tran, total_action, total_shared

    def cleanEFAglobal(self):
        State.global_id = 0
        Transition.global_id = 0

    def calcUdpSize(self):
        for state in self.states:
            for tran in state.trans:
                if tran.maxudp > self.udpsize:
                    self.udpsize = tran.maxudp
        self.udpsize += 1

    def getUdpSizeonly(self):
        return self.udpsize

    def getUdpSize(self):
        for state in self.states:
            for tran in state.trans:
                if tran.maxudp > self.udpsize:
                    self.udpsize = tran.maxudp
        return self.udpsize

    def fixlabels(self):
        try:
            for state in self.states:
                for tran in state.trans:
                    for action in tran.actions:
                        if type(action).__name__ == "BAction":
                            if action.dst_issb == 2:
                                action.dst = tran.labeldict[action.dst]  # Assign seq num to dst
            for k, v in self.sharedBlock.items():
                for action in v:
                    if type(action).__name__ == "BAction":
                        if action.dst_issb == 2:
                            action.dst = self.sharedBlocklabels[k][action.dst]  # Assign seq num to dst
        except KeyError as ke:
            sys.exit(f"Cannot resolving branch label {ke} in program!")
   
    # This should be replaced by a more accurate Effclip packing 
    # Progbase needs to be defined and as per A will be different for different EFAs. 
    #def writeBinary(self, binfile):
    #    with open(binfile, "w+b") as fd:
    #        val = struct.pack('I', self.progbase)
    #        fd.write(val)
    #        for k, v in self.sharedBlock.items():
    #            for act in v:
    #                word = act.emitbin(fd)
    #        for s in self.states:
    #            s.emitbin(fd)
    #    fd.close()
       


class IAction(object):
    def __init__(self, opcode, dst, src, imm, label, last):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.src = src
        self.imm = imm
        self.last = last
        self.label = label

    def __str__(self):
        return f"[{self.opcode} {self.src},{self.dst},${self.imm},{self.last}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd("[" + self.opcode + " " + str(self.src) + "," + str(self.dst) + ",$" + str(self.imm) + "," + str(self.last) + "]", LEVEL, TSTAMP)

    def getSeqnum(self):
        return self.seqnum

    def fieldsEqual(self, ref):
        if self.opcode == ref.opcode and self.src == ref.src and self.dst == ref.dst and self.imm == ref.imm and self.last == ref.last:
            return True
        else:
            return False
    
    #def emitbin(self, fd):
    #    src = reverse_map(self.src)
    #    dst = reverse_map(self.dst) - 16
    #    encoded_ins = ((int(self.imm) & {unsigned_max_16}) << 16) | ((dst & 0xF) << 12) | ((src & 0x1F) << 7) | (self.opcode_bits & 0x7F)
    #    print(encoded_ins)
    #    val = struct.pack('I', encoded_ins)
    #    fd.write(val)



class I2Action(object):
    def __init__(self, opcode, dst, src, imm, imm2, label, last, lm_mode="EMPTY"):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.src = src
        self.imm = imm
        self.imm2 = imm2
        self.label = label
        self.last = last
        self.lm_mode = lm_mode

    def __str__(self):
        return f"[{self.opcode} {self.lm_mode},{self.src},{self.dst},${self.imm},${self.imm2},{self.last}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd(
            "["
            + self.opcode + " " + self.lm_mode + " "
            + str(self.src) + ","
            + str(self.dst)
            + ",$" + str(self.imm)
            + ",$" + str(self.imm2) + ","
            + str(self.last)
            + "]",
            LEVEL, TSTAMP,
        )

    def fieldsEqual(self, ref):
        if (
            self.opcode == ref.opcode
            and self.src == ref.src
            and self.dst == ref.dst
            and self.imm == ref.imm
            and self.imm2 == ref.imm2
            and self.last == ref.last
        ):
            return True
        else:
            return False


class I3Action(object):
    def __init__(self, opcode, dst,op1, op2, op3, label, last, lm_mode="EMPTY"):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3
        self.label = label
        self.last = last
        self.lm_mode = lm_mode

    def __str__(self):
        return f"[{self.opcode} {self.lm_mode},{self.dst},${self.op1},${self.op2},${self.op3},{self.last}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd(
            "["
            + self.opcode + " " + self.lm_mode + " "
            + str(self.dst)
            + ",$" + str(self.op1)
            + ",$" + str(self.op2)
            + ",$" + str(self.op3) + ","
            + str(self.last)
            + "]",
            LEVEL, TSTAMP,
        )

    def fieldsEqual(self, ref):
        if (
            self.opcode == ref.opcode
            and self.dst == ref.dst
            and self.op1 == ref.op1
            and self.op2 == ref.op2
            and self.op3 == ref.op3
            and self.last == ref.last
        ):
            return True
        else:
            return False

class EAction(object):
    def __init__(self, opcode, src, dst, op1, op2, imm, label):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.src = src
        self.imm = imm
        self.op1 = op1
        self.op2 = op2
        self.label = label

    def __str__(self):
        return f"[{self.opcode} {self.src},{self.dst},${self.imm},{self.op1},{self.op2}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd(
            "["
            + self.opcode + " "
            + str(self.src) + ","
            + str(self.dst)
            + ",$" + str(self.imm) + ","
            + str(self.op1) + ","
            + str(self.op2)
            + "]",
            LEVEL, TSTAMP,
        )

    def fieldsEqual(self, ref):
        if (
            self.opcode == ref.opcode
            and self.src == ref.src
            and self.dst == ref.dst
            and self.imm == ref.imm
            and self.op1 == ref.op1
            and self.op2 == ref.op2
        ):
            return True
        else:
            return False


class RAction(object):
    def __init__(self, opcode, dst, src, rt, label, last, imm, lm_mode="EMPTY"):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.src = src
        self.last = last
        self.rt = rt
        self.label = label
        self.lm_mode = lm_mode
        self.imm = imm

    def __str__(self):
        return f"[{self.opcode} {self.src},{self.rt},{self.dst},{self.last}]"

    def printOut(self, LEVEL, TSTAMP=0):
        if self.opcode == "move_word":
            printd(f"[{self.opcode}_{self.lm_mode} {self.src},{self.rt},{self.dst},{self.imm},{self.last}]", stage_trace, TSTAMP)
        else:
            printd("[" + self.opcode + " " + str(self.src) + "," + str(self.rt) + "," + str(self.dst) + "," + str(self.last) + "]", LEVEL, TSTAMP)

    def fieldsEqual(self, ref):
        if self.opcode == ref.opcode and self.src == ref.src and self.dst == ref.dst and self.rt == ref.rt and self.last == ref.last:
            return True
        else:
            return False
    
class BAction(object):
    def __init__(self, opcode, dst, op1, op2, op1_ob_or_reg, op2_ob_or_reg_or_imm, dst_issb, funct, unsigned,label):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.dst_issb = dst_issb
        self.op1 = op1
        self.op2 = op2
        self.imm = "Empty"
        self.op1_ob_or_reg = op1_ob_or_reg
        self.op2_ob_or_reg_or_imm = op2_ob_or_reg_or_imm
        if funct[-1] == "c":
            funct = funct[:-1] + "i"
        self.funct = funct
        self.unsigned = unsigned
        self.label = label

    def __str__(self):
        return f"[{self.opcode} {self.dst},{self.op1},{self.op2}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd("[" + self.opcode + " " + str(self.dst) + "," + str(self.op1) + "," + str(self.op2) + "]", LEVEL, TSTAMP)

    def fieldsEqual(self, ref):
        if (
            self.opcode == ref.opcode
            and self.dst == ref.dst
            and self.op1 == ref.op1
            and self.op2 == ref.op2
            and self.op1_ob_or_reg == ref.op1_ob_or_reg
            and self.op2_ob_or_reg_or_imm == ref.dst_ob_or_reg_or_imm
        ):
            return True
        else:
            return False


# Message Action

class SAction(object):
    def __init__(self, opcode, event, dst, cont, op1, op2, op3, addr_mode, size, label,tmp_reg1):
        self.exe_count = 0
        self.opcode = opcode
        self.event = event
        self.dst = dst
        self.cont = cont
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3
        self.tmp_reg1 = tmp_reg1
        self.addr_mode = addr_mode
        self.size = size
        self.label = label

    def __str__(self):
        return f"[{self.opcode} {self.event},{self.dst},{self.addr_mode},{self.cont},{self.op1},{self.op2},{self.tmp_reg1}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd(
            "["
            + self.opcode + " "
            + str(self.event) + ","
            + str(self.dst) + ","
            + str(self.addr_mode) + ","
            + str(self.cont) + ","
            + str(self.op1) + ","
            + str(self.op2) + ","
            + str(self.tmp_reg1)
            + "]",
            LEVEL, TSTAMP,
        )

    def fieldsEqual(self, ref):
        if (
            self.opcode == ref.opcode
            and self.dst == ref.dst
            and self.cont == ref.cont
            and self.op1 == ref.op1
            and self.op2 == ref.op2
            and self.tmp_reg1 == ref.tmp_reg1
            and self.addr_mode == ref.addr_mode
            and self.event == ref.event
        ):
            return True
        else:
            return False


class SPAction(object):
    def __init__(self, opcode, event, dst, cont, op1, reglist, addr_mode, label, tmp_reg1):
        self.exe_count = 0
        self.opcode = opcode
        self.event = event
        self.dst = dst
        self.cont = cont
        self.op1 = op1
        self.reglist = reglist
        self.addr_mode = addr_mode
        self.label = label
        self.tmp_reg1 = tmp_reg1

    def __str__(self):
        return f"[{self.opcode} {self.event},{self.dst},{self.addr_mode},{self.cont},{self.op1}, RegNum:{len(self.reglist)}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd(
            "["
            + self.opcode + " "
            + str(self.event) + ","
            + str(self.dst) + ","
            + str(self.addr_mode) + ","
            + str(self.cont) + ","
            + str(self.op1)
            + ", RegNum:" + str(len(self.reglist)) + ","
            + "]",
            LEVEL, TSTAMP,
        )

    def fieldsEqual(self, ref):
        if (
            self.opcode == ref.opcode
            and self.dst == ref.dst
            and self.cont == ref.cont
            and self.reglist == ref.reglist
            and self.addr_mode == ref.addr_mode
            and self.event == ref.event
        ):
            return True
        else:
            return False


class PAction(object):
    def __init__(self, opcode, fmtstr, reglist, print_id, label):
        self.exe_count = 0
        self.opcode = opcode
        self.fmtstr = fmtstr
        self.reglist = reglist
        self.print_id = print_id
        self.label = label

    def __str__(self):
        regstrlist = ",".join(self.reglist)
        return f"[{self.opcode} {self.fmtstr},{regstrlist}]"

    def printOut(self, LEVEL, TSTAMP=0):
        regstrlist = ",".join(self.reglist)
        printd("[" + self.opcode + "," + str(self.fmtstr) + "," + str(regstrlist) + "]", LEVEL, TSTAMP)


class PerflogAction(object):
    def __init__(self, opcode, mode, payload_list, msg_id, fmtstr, reglist, print_id, label):
        self.exe_count = 0
        self.opcode = opcode
        # mode: 0 - stats dump
        # mode: 1 - message log
        self.mode = mode
        self.payload_list = payload_list
        self.msg_id = msg_id
        self.fmtstr = fmtstr
        self.reglist = reglist
        self.print_id = print_id
        self.label = label

    def __str__(self):
        if self.mode == 0:
            return f"[{self.opcode} {self.mode},{self.payload_list}]"
        elif self.mode == 1:
            regstrlist = ",".join(self.reglist)
            return f"[{self.opcode} {self.mode},{self.msg_id},{self.fmtstr},{regstrlist}]"
        elif self.mode == 2:
            regstrlist = ",".join(self.reglist)
            return f"[{self.opcode} {self.mode},{self.payload_list},{self.msg_id},{self.fmtstr},{regstrlist}]"

    def printOut(self, LEVEL, TSTAMP=0):
        if self.mode == 0:
            printd("[" + self.opcode + " " + str(self.mode) + "," + str(self.payload_list) + "]", LEVEL, TSTAMP)
        elif self.mode == 1:
            regstrlist = ",".join(self.reglist)
            printd("[" + self.opcode + " " + str(self.mode) + "," + str(self.msg_id) + "," + str(self.fmtstr) + "," + str(regstrlist) + "]", LEVEL, TSTAMP)
        elif self.mode == 2:
            regstrlist = ",".join(self.reglist)
            printd("[" + self.opcode + " " + str(self.mode) + "," + str(self.payload_list) + "," + str(self.msg_id) + "," + str(self.fmtstr) + "," + str(regstrlist) + "]", LEVEL, TSTAMP)

class InsTransAction(object):
    def __init__(self, opcode, op1, op2, op3, size, mode, op4,label):
        self.exe_count = 0
        self.opcode = opcode
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3
        self.size = size
        self.mode = mode
        self.op4 = op4
        self.label = label
    
    def __str__(self):
        return f"[{self.opcode} {self.op1},{self.op2},{self.op3},{self.size},{self.mode},{self.op4} ,{self.label}]"
    
    def printOut(self, LEVEL, TSTAMP=0):
        printd(f"[{self.opcode} {self.op1},{self.op2},{self.op3},{self.size},{self.mode},{self.op4} ,{self.label}]", LEVEL, TSTAMP)

class UserCounterAction(object):
    def __init__(self, opcode, userctr_mode, userctr_num, userctr_arg, label):
        self.exe_count = 0
        self.opcode = opcode
        self.mode = userctr_mode
        self.ctr_num = userctr_num
        self.arg = userctr_arg
        self.label = label

    def __str__(self):
        return f"[{self.opcode} {self.mode},{self.ctr_num},{self.arg}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd("[" + self.opcode + " " + str(self.mode) + "," + str(self.ctr_num) + "," + str(self.arg) + "]", LEVEL, TSTAMP)


class LMMemcheckAction(object):
    def __init__(self, opcode, mode, op1, op2, label):
        self.exe_count = 0
        self.opcode = opcode
        self.mode = mode
        self.start_addr = op1
        self.size = op2
        self.label = label

    def __str__(self):
        return f"[{self.opcode} {self.mode},{self.start_addr},{self.size}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd(f"[{self.opcode} {self.mode},{self.start_addr},{self.size}]", LEVEL, TSTAMP)


class YAction(object):
    def __init__(self, opcode, label):
        self.exe_count = 0
        self.opcode = opcode
        self.label = label
        self.imm = 0 #(required to match the I-type fields) this filed is unused
        self.dst = 'NWID' #(the string corresponds to 0 and is required to match the I-type fields) this filed is unused
        self.src = 'NWID' #(the string corresponds to 0 and is required to match the I-type fields) this filed is unused

    def __str__(self):
        return f"[{self.opcode} ]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd("[" + self.opcode + "," + "]", LEVEL, TSTAMP)
    
    #def emitbin(self, fd):
    #    encoded_ins = (self.opcode_bits & 0x7F) & 0xFFFFFFFF
    #    print(encoded_ins)
    #    val = struct.pack('I', encoded_ins)
    #    fd.write(val)

#Marziyeh
class FPAction(object):
    def __init__(self, opcode, dst, src, rt, mode, mask, precision, label):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.src = src
        self.rt = rt
        self.mode = mode
        self.mask = mask
        self.label = label
        self.precision = precision

    def __str__(self):
        return f"[{self.opcode} {self.src},{self.rt},{self.dst},{self.mode},{self.mask}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd("[" + self.opcode + " " + str(self.src) + "," + str(self.rt) + "," + str(self.dst) + "," + str(self.precision) + "," + str(self.mode) + "," + str(self.mask) + "]", LEVEL, TSTAMP)

    def fieldsEqual(self, ref):
        if self.opcode == ref.opcode and self.src == ref.src and self.dst == ref.dst and self.rt == ref.rt and self.mode == ref.mode and self.mask == ref.mask:
            return True
        else:
            return False


class VAction(object):
    def __init__(self, opcode, dst, src, rt, mode ,mask, precision, label):
        self.exe_count = 0
        self.opcode = opcode
        self.dst = dst
        self.src = src
        self.rt = rt
        self.mode = mode
        self.mask = mask
        self.precision = precision
        self.label = label

    def __str__(self):
        return f"[{self.opcode} {self.src},{self.rt},{self.dst},{self.mode},{self.mask}]"

    def printOut(self, LEVEL, TSTAMP=0):
        printd("[" + self.opcode + " " + str(self.src) + "," + str(self.rt) + "," + str(self.dst) + "," + str(self.precision) + "," + str(self.mode) + "," + str(self.mask) + "]", LEVEL, TSTAMP)

    def fieldsEqual(self, ref):
        if self.opcode == ref.opcode and self.src == ref.src and self.dst == ref.dst and self.rt == ref.rt and self.mode == ref.mode and self.mask == ref.mask:
            return True
        else:
            return False
