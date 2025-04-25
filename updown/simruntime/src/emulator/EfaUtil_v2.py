import copy
import re

UNUSED_reg = "X0"
UNUSED_imm = "0"

# ====== Control the printing ======
PrintSwitch = 5
PrintThreshold = 0
# ====== Printing Option Level ======
full_trace = 0
stage_trace = 1
progress_trace = 2
error = 100


def printLevel(p):
    global PrintSwitch
    PrintSwitch = p


def printThreshold(tstamp):
    global PrintThreshold
    PrintThreshold = tstamp


def printd(obj, LEVEL, TSTAMP=0):
    if LEVEL >= PrintSwitch and TSTAMP >= PrintThreshold:
        print(obj, flush=True)


# ====== Printing Color Facility ======
class bcolors:
    HEADER = "\033[35m"
    OKBLUE = "\033[34m"
    OKGREEN = "\033[32m"
    WARNING = "\033[33m"
    FAIL = "\033[31m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def find_underscore(str, pos):
    cur = 0
    curidx = 0
    index = 0
    while cur < pos:
        index = str.find("_", index, len(str))
        cur += 1
        index += 1
    return index


def strip_precision(str):
    precision = 0
    strips = str.split(".")
    opcode = strips[0]
    if len(strips) > 1:
        if strips[1] == "64":
            precision = 0
        elif strips[1] == "32":
            precision = 1
        elif strips[1] == "b16":
            precision = 2
        elif strips[1] == "i32":
            precision = 3
    return opcode, precision


def get_precision(str):
    strips = str.split(".")
    if len(strips) == 1:
        return 0
    precision = strips[1]
    return precision


def concatSet(InSet1, InSet2):
    res = []
    # ======quick path
    if isinstance(InSet1, list) is True and isinstance(InSet2, list) is True:
        if len(InSet1) == 0:
            return InSet2
        elif len(InSet2) == 0:
            return InSet1
    elif isinstance(InSet1, list) is True:
        if len(InSet1) == 0:
            return [InSet2]
    elif isinstance(InSet2, list) is True:
        if len(InSet2) == 0:
            return [InSet1]
    # ====== slow path
    if isinstance(InSet1, list):
        for j in InSet1:
            ele = copy.deepcopy(j)
            res.append(ele)
    else:
        ele = copy.deepcopy(InSet1)
        res.append(ele)
    if isinstance(InSet2, list):
        for j in InSet2:
            ele = copy.deepcopy(j)
            res.append(ele)
    else:
        ele = copy.deepcopy(InSet2)
        res.append(ele)
    return res


# OpCodes!


def reverse_map(reg, mode=0):
    revmap = {
        "NWID": 0,
        "X1": 1,
        "EQT": 2,
        "X3": 3,
        "FSCR": 4,
        "X5": 5,
        "X6": 6,
        "X7": 7,
        "OB_0": 8,
        "OB_1": 9,
        "OB_2": 10,
        "OB_3": 11,
        "OB_4": 12,
        "OB_5": 13,
        "OB_6": 14,
        "OB_7": 15,
        "UDPR_0": 16,
        "UDPR_1": 17,
        "UDPR_2": 18,
        "UDPR_3": 19,
        "UDPR_4": 20,
        "UDPR_5": 21,
        "UDPR_6": 22,
        "UDPR_7": 23,
        "UDPR_8": 24,
        "UDPR_9": 25,
        "UDPR_10": 26,
        "UDPR_11": 27,
        "UDPR_12": 28,
        "UDPR_13": 29,
        "UDPR_14": 30,
        "UDPR_15": 31,
        "EMPTY": 0,
    }

    return revmap[reg]


# Simple Register map (mapping back into old names as synonyms)
def register_map(reg, mode=0):
    if mode == 0:
        regmap = {
            "X0": "NWID",
            "X1": "X1",
            "X2": "EQT",
            "X3": "X3",
            "X4": "FSCR",
            "X5": "X5",
            "X6": "X6",
            "X7": "X7",
            "X8": "OB_0",
            "X9": "OB_1",
            "X10": "OB_2",
            "X11": "OB_3",
            "X12": "OB_4",
            "X13": "OB_5",
            "X14": "OB_6",
            "X15": "OB_7",
            "X16": "UDPR_0",
            "X17": "UDPR_1",
            "X18": "UDPR_2",
            "X19": "UDPR_3",
            "X20": "UDPR_4",
            "X21": "UDPR_5",
            "X22": "UDPR_6",
            "X23": "UDPR_7",
            "X24": "UDPR_8",
            "X25": "UDPR_9",
            "X26": "UDPR_10",
            "X27": "UDPR_11",
            "X28": "UDPR_12",
            "X29": "UDPR_13",
            "X30": "UDPR_14",
            "X31": "UDPR_15",
        }
    elif mode == 1:
        regmap = {
            "X0": "NWID",
            "X1": "X1",
            "X2": "EQT",
            "X3": "X3",
            "X4": "SBP",
            "X5": "SBCR",
            "X6": "X6",
            "X7": "X7",
            "X8": "OB_0",
            "X9": "OB_1",
            "X10": "OB_2",
            "X11": "OB_3",
            "X12": "OB_4",
            "X13": "OB_5",
            "X14": "OB_6",
            "X15": "OB_7",
            "X16": "UDPR_0",
            "X17": "UDPR_1",
            "X18": "UDPR_2",
            "X19": "UDPR_3",
            "X20": "UDPR_4",
            "X21": "UDPR_5",
            "X22": "UDPR_6",
            "X23": "UDPR_7",
            "X24": "UDPR_8",
            "X25": "UDPR_9",
            "X26": "UDPR_10",
            "X27": "UDPR_11",
            "X28": "UDPR_12",
            "X29": "UDPR_13",
            "X30": "UDPR_14",
            "X31": "UDPR_15",
        }
    else:
        print("Mode %s is not supported" % mode)
        exit(1)
    return regmap[reg]


def calc_maxudp_maxob(reglist):
    maxudp = 0
    maxob = 0
    for reg in reglist:
        if reg[0] == "U":
            udp = int(reg[5:])
            if udp > maxudp:
                maxudp = udp
        elif reg[0] == "O" and reg.count("O") == 1:
            ob = int(reg[3:])
            if ob > maxob:
                maxob = ob
        elif reg[0] == "O" and reg.count("O") == 2:
            pos = find_underscore(reg, 2)
            ob = int(reg[pos:])
            if ob > maxob:
                maxob = ob
    return maxudp, maxob


class Operand:
    def __init__(self):
        self.opcode = "Unknown"
        self.opcode_bits = "Unknown"
        self.dst = "EMPTY"
        self.src = "EMPTY"
        self.imm = "EMPTY"
        self.imm2 = "EMPTY"
        self.rt = "EMPTY"
        self.op1 = "EMPTY"
        self.op2 = "EMPTY"
        self.op3 = "EMPTY"
        self.op4 = "EMPTY"
        self.unsigned = "EMPTY"
        self.op1_ob_or_reg = "EMPTY"
        self.op2_ob_or_reg_or_imm = "EMPTY"
        self.event_label = "EMPTY"
        self.event = "EMPTY"
        self.addr = "EMPTY"
        self.addr_mode = "EMPTY"
        self.size = "EMPTY"
        self.rw = "EMPTY"
        self.dst_issb = "EMPTY"
        self.funct = "EMPTY"
        self.cont = "EMPTY"
        self.lm_mode = "EMPTY"
        self.tmp_reg1 = "EMPTY"
        self.tmp_reg2 = "EMPTY"
        self.reglist = []
        self.maxop = 0
        self.maxudp = 0
        self.label = None
        self.formatstr = None
        self.perflog_mode = 0
        self.perflog_payload_list = 0
        self.perflog_msg_id = 0
        self.userctr_mode = 0
        self.userctr_num = 0
        self.userctr_arg = 0
        self.print_id = 0
        #Floating point/vector comp
        self.mode = 0
        self.mask = 0
        self.print_id = None
        self.vbase = None
        self.pbase = None
        self.access = None
        self.tmp_reg1 = None
        self.precision = None

class print_counter:
    counter = 0
    def __init__(self):
        print_counter.counter += 1
        self.counter = print_counter.counter - 1
    def reset_counter(self):
        print_counter.counter = 0
    def get_counter(self):
        return self.counter

def ParseAction(asm_inst):
    templabel = None
    prepart = asm_inst.split()
    if prepart[0][-1] == ":":
        part = prepart[1:]
        templabel = prepart[0][:-1]
    else:
        part = prepart[:]
    # part = asm_inst.split()
    for i, p in enumerate(part):
        part[i] = part[i].rstrip(",")

    # opcode, precision = strip_precision(part[0])
    opcode = part[0]
    precision = get_precision(part[0])
    for i in range(1, len(part)):
        if part[i][0] == "X" and "(" not in part[i]:
            part[i] = register_map(part[i])
    ActionClass = ""
    operand = Operand()
    operand.opcode = opcode
    operand.precision = precision
    maxudp = 0
    maxop = 0
    if templabel is not None:
        operand.label = templabel
    # ====== Action Part ======
    if (
        opcode == "hash_sb32"
        or opcode == "hashsb32"
        or opcode == "mov_imm2reg"
        or opcode == "movir"
        or opcode == "evlb"
    ):
        ActionClass = "IAction"
        operand.dst = part[1]
        operand.imm = part[2]
        operand.src = UNUSED_reg
        maxudp, maxop = calc_maxudp_maxob([operand.dst])

    elif (
        opcode == "mov_sb2reg"
        or opcode == "movsbr"
        or opcode == "mov_uip2reg"
        or opcode == "movipr"
    ):
        ActionClass = "IAction"
        operand.dst = part[1]
        operand.imm = UNUSED_imm
        operand.src = "X16"
        maxudp, maxop = calc_maxudp_maxob([operand.dst])

    elif opcode == "mov_lm2sb" or opcode == "movlsb":
        ActionClass = "IAction"
        operand.src = part[1]
        operand.imm = UNUSED_imm
        operand.dst = "X16"
        maxudp, maxop = calc_maxudp_maxob([operand.src])

    elif (
        opcode == "goto"
        or opcode == "tranCarry_goto"
        or opcode == "siw"
        or opcode == "set_issue_width"
        or opcode == "set_complete"
        or opcode == "refill"
    ):  # added by Marzi
        ActionClass = "IAction"
        operand.imm = part[1]
        operand.dst = "X16"
        operand.src = UNUSED_reg
        maxudp, maxop = calc_maxudp_maxob([operand.imm])

    elif (
        opcode == "put_2byte_imm"
        or opcode == "movil2"
        or opcode == "put_1byte_imm"
        or opcode == "movil1"
    ):
        ActionClass = "IAction"
        operand.src = part[1]
        operand.imm = part[2]
        operand.dst = "X16"
        maxudp, maxop = calc_maxudp_maxob([operand.src])

    # Note: in real UDP, only has copy
    # added by Marzi (xor bellow)
    # """I dont' see following instructions in the ISA
    # DO NOT DELETE THIS LIST, I have removed them until we see an error - Andronicus
    #    get_bytes_from_out
    #    swap_bytes
    #    mask_or
    #    bitwise_xor_imm
    #    set_complete
    #    copy_from_out_imm
    #    mov_lml2reg_blk
    #    mov_eqt2reg
    #    block_compare
    #    block_compare_i
    #    cmpswp_ri
    #    cmpswp_i
    #    copy_ob_lm
    #    copy_from_out
    #    compare_string_from_out
    # """
    elif (
        opcode == "subi"
        or opcode == "addi"
        or opcode == "muli"
        or opcode == "divi"
        or opcode == "put_bytes"
        or opcode == "get_bytes"
        or opcode == "get_bytes_from_out"
        or opcode == "swap_bytes"
        or opcode == "comp_lt"
        or opcode == "clti"
        or opcode == "comp_gt"
        or opcode == "cgti"
        or opcode == "comp_eq"
        or opcode == "ceqi"
        or opcode == "lshift_or"
        or opcode == "slori"
        or opcode == "rshift_or"
        or opcode == "srori"
        or opcode == "lshift_and"
        or opcode == "slandi"
        or opcode == "rshift_and"
        or opcode == "srandi"
        or opcode == "mask_or"
        or opcode == "bitwise_and_imm"
        or opcode == "andi"
        or opcode == "modi"
        or opcode == "bitwise_or_imm"
        or opcode == "ori"
        or opcode == "bitwise_xor_imm"
        or opcode == "xori"
        or opcode == "copy_imm"
        or opcode == "bcpylli"
        or opcode == "copy_from_out_imm"
        # or opcode == "mov_lm2reg"
        or opcode == "mov_lm2ear"
        or opcode == "mov_ear2lm"
        # or opcode == "mov_reg2lm"
        or opcode == "rshift"
        or opcode == "sri"
        or opcode == "lshift"
        or opcode == "sli"
        or opcode == "mov_lm2reg_blk"
        or opcode == "arithrshift"
        or opcode == "sari"
    ):  # added by Marziyeh (arithrshifts)
        ActionClass = "IAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = part[3]
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])
    elif opcode == "hash_lm" or opcode == "hashl":
        ActionClass = "IAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = str(int(part[3]) - 1)
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])
    elif opcode == "set_state_property" or opcode == "ssprop":
        ActionClass = "IAction"
        operand.src = UNUSED_reg
        operand.dst = "X16"
        '''
        operand.imm = str(
            ((int(part[2]) & 0b111111111111) << 4) | (int(part[1]) & 0b1111)
        )
        '''
        operand.imm = part[1]

        # ActionClass = "Action"
        # if part[1] == "flag":
        #     operand.imm = "flag"
        # elif part[1] == "common":
        #     operand.imm = "common"
        # elif part[1] == "null":  # added by Marziyeh
        #     operand.imm = "null"
        # elif part[1] == "majority":
        #     operand.imm = "majority" + "::" + part[2]
        # elif part[1] == "flag_majority":
        #     operand.imm = "flag_majority" + "::" + part[2]
        # elif part[1] == "default":
        #     operand.imm = "default" + "::" + part[2]
        # elif part[1] == "flag_default":
        #     operand.imm = "flag_default" + "::" + part[2]
        # elif part[1] == "event":
        #     operand.imm = "event"  # Andronicus for event

    elif (
        opcode == "mov_reg2reg"
        or opcode == "movrr"
        or opcode == "mov_ob2reg"
        or opcode == "mov_eqt2reg"
        or opcode == "mov_ob2ear"
    ):
        ActionClass = "RAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.rt = UNUSED_reg
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif (
        opcode == "hash_sb64"
        or opcode == "hashsb64"
        or opcode == "hash_lm64"
        or opcode == "hashl64"
        or opcode == "hash"
    ):
        ActionClass = "IAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = UNUSED_imm
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

        # ====== JAction Part ======
    elif (
        opcode == "lshift_add_imm"
        or opcode == "sladdii"
        or opcode == "rshift_add_imm"
        or opcode == "sraddii"
        or opcode == "lshift_or_imm"
        or opcode == "slorii"
        or opcode == "rshift_or_imm"
        or opcode == "srorii"
        or opcode == "lshift_sub_imm"
        or opcode == "slsubii"
        or opcode == "rshift_sub_imm"
        or opcode == "srsubii"
        or opcode == "lshift_and_imm"
        or opcode == "slandii"
        or opcode == "rshift_and_imm"
        or opcode == "srandii"
        or opcode == "ev_update_1"
        or opcode == "evi"
        or opcode == "ev_update_reg_imm"
        or opcode == "cmpswp_ri"
        or opcode == "cmpswp_i"
        or opcode == "cswpi"
    ):
        ActionClass = "I2Action"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = part[3]
        operand.imm2 = part[4]
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif opcode == "ev_update_2" or opcode == "evii":
        ActionClass = "I3Action"
        # operand.src = part[1]
        operand.dst = part[1]
        operand.op1 = part[2]
        operand.op2 = part[3]
        operand.op3 = part[4]
        maxudp, maxop = calc_maxudp_maxob([operand.dst])

    elif opcode == "cmpswp" or opcode == "cswp":
        ActionClass = "EAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.imm = UNUSED_imm
        maxudp, maxop = calc_maxudp_maxob(
            [operand.src, operand.dst, operand.op1, operand.op2]
        )

    elif opcode == "put_bits" or opcode == "movbil":
        ActionClass = "I2Action"
        operand.src = part[1]
        operand.imm = part[2]
        operand.imm2 = part[3]
        operand.dst = "X16"
        maxudp, maxop = calc_maxudp_maxob([operand.src])

    elif opcode == "get_bits" or opcode == "movblr":
        ActionClass = "I2Action"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = part[3]
        operand.imm2 = UNUSED_imm
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif opcode == "fork_state" or opcode == "fstate":
        ActionClass = "I2Action"
        operand.src = UNUSED_reg
        operand.dst = UNUSED_reg
        operand.imm2 = part[1]
        operand.imm = part[2]
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif opcode == "swizzle" or opcode == "swiz":
        ActionClass = "I2Action"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = UNUSED_imm
        operand.imm2 = UNUSED_imm
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif opcode == "bcopy_opsi" or opcode == "bcpyoli":
        ActionClass = "I2Action"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = part[3]
        operand.imm2 = UNUSED_imm
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif (
        opcode == "move"
        or opcode == "movlr"
        or opcode == "movrl"
        or opcode == "movrl"
        or opcode == "movlr"
    ):
        ActionClass = "I2Action"
        if "(" in part[1]:
            subparts = part[1][:-1].replace("(", ",").split(",")
            operand.lm_mode = "ld"
            subparts = [
                register_map(p) if p[0] == "X" else p for p in filter(None, subparts)
            ]
            operand.src = subparts[1]
            operand.dst = part[2]
            operand.imm = part[4]
            operand.imm2 = subparts[0]
        elif "(" in part[2]:
            subparts = part[2][:-1].replace("(", ",").split(",")
            operand.lm_mode = "st"
            subparts = [
                register_map(p) if p[0] == "X" else p for p in filter(None, subparts)
            ]
            operand.dst = subparts[1]
            operand.src = part[1]
            operand.imm = part[4]
            operand.imm2 = subparts[0]
        if part[3] == "1":
            operand.lm_mode += "_inc"
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    ## do we still need support for these 2?
    elif opcode == "mov_lm2reg" or opcode == "mov_reg2lm":
        ActionClass = "I2Action"
        operand.src = part[1]
        operand.dst = part[2]
        operand.imm = part[3]
        operand.imm2 = "0"
        if opcode == "mov_lm2reg":
            operand.lm_mode = "ld"
        elif opcode == "mov_reg2lm":
            operand.lm_mode = "st"
        # operand.lm_mode += '_inc'
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif opcode == "move_word" or opcode == "movwlr" or opcode == "movwrl":
        ActionClass = "RAction"
        if "(" in part[1]:
            subparts = part[1][:-1].replace("(", ",").split(",")
            operand.lm_mode = "ld"
            subparts = [
                register_map(p) if p[0] == "X" else p for p in filter(None, subparts)
            ]
            operand.rt = subparts[0]
            operand.src = subparts[1]
            operand.dst = part[2]
            operand.imm = subparts[3]
        elif "(" in part[2]:
            subparts = part[2][:-1].replace("(", ",").split(",")
            operand.lm_mode = "st"
            subparts = [
                register_map(p) if p[0] == "X" else p for p in filter(None, subparts)
            ]
            operand.rt = subparts[0]
            operand.dst = subparts[1]
            operand.src = part[1]
            operand.imm = subparts[3]
        if subparts[2] == "1":
            operand.lm_mode += "_inc"
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

        # ======  TAction Part ======
    # added by Marzi (xor bellow)
    # What are TActions?
    elif (
        opcode == "add"
        or opcode == "compare_string"
        or opcode == "cstr"
        or opcode == "compare_string_from_out"
        or opcode == "copy"
        or opcode == "bcpyll"
        or opcode == "copy"
        or opcode == "bcpyll"
        or opcode == "copy_ob_lm"
        or opcode == "copy_from_out"
        or opcode == "sub"
        or opcode == "mul"
        or opcode == "div"
        or opcode == "mod"
        or opcode == "compreg"
        or opcode == "compreg_eq"
        or opcode == "ceq"
        or opcode == "compreg_lt"
        or opcode == "clt"
        or opcode == "compreg_gt"
        or opcode == "cgt"
        or opcode == "bitwise_or"
        or opcode == "orr"
        or opcode == "or"
        or opcode == "bitwise_and"
        or opcode == "andr"
        or opcode == "and"
        or opcode == "bitwise_xor"
        or opcode == "xorr"
        or opcode == "xor"
        or opcode == "rshift_t"
        or opcode == "sr"
        or opcode == "lshift_t"
        or opcode == "sl"
        or opcode == "bitclr"
        or opcode == "bitset"
        or opcode == "fp_div"
        or opcode == "fp_add"
        or opcode == "arithrshift_t"
        or opcode == "sar"
    ):  # added by Marziyeh (arithrshifts)
        # Ivy added fp_div and fp_add

        ActionClass = "RAction"
        operand.src = part[1]
        operand.rt = part[2]
        operand.dst = part[3]
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst, operand.rt])

    elif opcode == "bcopy_ops" or opcode == "bcpyol":
        ActionClass = "RAction"
        operand.src = part[1]
        operand.rt = part[3]
        operand.dst = part[2]
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst, operand.rt])

    elif (
        opcode == "bne"
        or opcode == "beq"
        or opcode == "blt"
        or opcode == "bgt"
        or opcode == "bge"
        or opcode == "ble"
        or opcode == "bnec"
        or opcode == "beqc"
        or opcode == "bltc"
        or opcode == "bgtc"
        or opcode == "bgec"
        or opcode == "blec"
        or opcode == "bneu"
        or opcode == "bequ"
        or opcode == "bgtu"
        or opcode == "bleu"
        or opcode == "bneiu"
        or opcode == "beqiu"
        or opcode == "bgtiu"
        or opcode == "bleiu"
        or opcode == "bltiu"
        or opcode == "bgeiu"
        or opcode == "bnei"
        or opcode == "beqi"
        or opcode == "blti"
        or opcode == "bgti"
        or opcode == "bgei"
        or opcode == "blei"
    ):
        ActionClass = "BAction"
        operand.funct = opcode
        operand.opcode = "branch"

        if part[3][0] == "#":  # seqnum
            operand.dst = part[3][1:]
            operand.dst_issb = 0
        elif part[3][0:5] == "block":  # shared block
            operand.dst = part[3]
            operand.dst_issb = 1
        else:  # label
            operand.dst = part[3]
            operand.dst_issb = 2

        if (
            part[1][0] == "U"
            or part[1][0] == "N"
            or part[1][0] == "L"
            or part[1][0] == "X"
        ):  # "UDPR"
            operand.op1_ob_or_reg = 1
        else:
            operand.op1_ob_or_reg = 0
        if (
            part[2][0] == "U"
            or part[2][0] == "N"
            or part[2][0] == "L"
            or part[1][0] == "X"
        ):  # "UDPR":
            operand.op2_ob_or_reg_or_imm = 1
        elif part[2][0] == "O":  # "OB":
            operand.op2_ob_or_reg_or_imm = 0
        else:
            operand.op2_ob_or_reg_or_imm = 2
            # if(int(part[2]) > 31):
            #    print("%d > supported imm value (0-31)" % int(part[2]))
            #    error(1)
        operand.op1 = part[1]
        operand.op2 = part[2]
        if (
            opcode == "bneu"
            or opcode == "bequ"
            or opcode == "bgtu"
            or opcode == "bleu"
            or opcode == "bneiu"
            or opcode == "beqiu"
            or opcode == "bgtiu"
            or opcode == "bleiu"
            or opcode == "bltiu"
            or opcode == "bgeiu"
        ):
            operand.unsigned = 1
        else:
            operand.unsigned = 0

        maxudp, maxop = calc_maxudp_maxob([operand.op1, operand.op2])

    elif opcode == "jmp":
        ActionClass = "BAction"
        if part[1][0] == "#":  # seqnum
            operand.dst = part[1][1:]
            operand.dst_issb = 0
        elif part[1][0:5] == "block":  # shared block
            operand.dst = part[1]
            operand.dst_issb = 1
        else:  # label
            operand.dst = part[1]
            operand.dst_issb = 2

    elif opcode == "ev_update_reg_2" or opcode == "ev":
        ActionClass = "EAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.imm = part[5]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.src, operand.dst, operand.op1, operand.op2]
        )

    elif (
        opcode == "yield"
        or opcode == "yield_terminate"
        or opcode == "yieldt"
        or opcode == "lastact"
    ):
        ActionClass = "YAction"

    elif opcode == "send":
        # M1: send data using (ptr + size) to a N/W ID
        ActionClass = "SAction"
        operand.event = part[1]
        # operand.dst = (int(part[1]) >> 32) & (0xffffffff) # Extract dst from the event_word
        # operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.addr_mode = part[5]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.event, operand.dst, operand.cont, operand.op1, operand.op2]
        )

    elif opcode == "sendm" or opcode == "sendmops":
        # M2: send data using (ptr + size) to a memory
        ActionClass = "SAction"
        operand.event = "Empty"
        operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.addr_mode = part[5]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.event, operand.dst, operand.cont, operand.op1, operand.op2]
        )
    elif opcode == "sendmr2":
        ActionClass = "SAction"
        operand.event = "Empty"
        operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.event, operand.dst, operand.cont, operand.op1, operand.op2]
        )

    elif opcode == "sendmr":
        ActionClass = "SAction"
        operand.event = "Empty"
        operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.event, operand.dst, operand.cont, operand.op1]
        )

    elif (opcode == "send4" and len(part) == 6) or opcode == "sendr3":
        # M3: send register values to N/W ID or mem
        ActionClass = "SAction"
        operand.event = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.op3 = part[5]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.event, operand.cont, operand.op1, operand.op2, operand.op3]
        )
    elif (opcode == "send4" and len(part) == 5) or opcode == "sendr":
        # M3: send register values to N/W ID or mem
        ActionClass = "SAction"
        operand.event = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.event, operand.cont, operand.op1, operand.op2]
        )
    elif opcode == "sendops":
        # M4: send operands values to N/W ID or mem
        ActionClass = "SAction"
        operand.event = part[1]
        if opcode == "sendops":
            # operand.dst = (int(part[1]) >> 32) & (0xffffffff) # extract dst from event_word
            operand.cont = part[2]
            operand.op1 = part[3]
            operand.op2 = part[4]
            operand.addr_mode = part[5]
        maxudp, maxop = calc_maxudp_maxob(
            [operand.event, operand.dst, operand.cont, operand.op1, operand.op2]
        )

    # Retired send instruction interface  """
    # elif opcode == "send" or opcode == "send4" or opcode == "sendr" or opcode == "sendops":
    #    ActionClass = "SAction"
    #    operand.event = part[1]
    #    operand.dst = part[2]
    #    operand.cont = part[3]
    #    operand.op1 = part[4]
    #    opcode = opcode.replace("sendr", "send4")
    #    if opcode[4] != "4" or (opcode[4] == "4" and len(part) > 6):
    #        operand.op2 = part[5]
    #        operand.addr_mode = part[6]
    #    else:
    #        operand.addr_mode = part[5]
    #    maxudp, maxop = calc_maxudp_maxob([operand.event,
    #                                      operand.dst,
    #                                      operand.cont,
    #                                      operand.op1,
    #                                      operand.op2])

    elif (
        opcode == "send_wcont"
        or opcode == "sendr_wcont"
        or (opcode == "send4_wcont" and len(part) == 5)
        or opcode == "sendops_wcont"
    ):
        #   send_wcont          event   cont    op1     op2
        #   sendr_wcont         event   cont    op1     op2
        #   sendops_wcont       event   cont    op1     op2
        opcode.replace("send4", "sendr")
        ActionClass = "SAction"
        operand.event = part[1]
        operand.dst = None
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.op3 = None
        operand.tmp_reg1 = None

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif opcode == "sendr3_wcont" or (opcode == "send4_wcont" and len(part) == 6):
        #   sendr3_wcont        event   cont    op1     op2         op3
        opcode.replace("send4", "sendr3")
        ActionClass = "SAction"
        operand.event = part[1]
        operand.dst = None
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.op3 = part[5]
        operand.tmp_reg1 = None

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif opcode == "sendr3_wret" or (opcode == "send4_wret" and len(part) == 7):
        #   sendr3_wret         event   cont    op1     op2         op3         tmp_reg1
        opcode.replace("send4", "sendr3")
        ActionClass = "SAction"
        operand.event = part[1]
        operand.dst = None
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.op3 = part[5]
        operand.tmp_reg1 = part[6]

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif (
        opcode == "send_wret"
        or opcode == "sendr_wret"
        or (opcode == "send4_wret" and len(part) == 6)
        or opcode == "sendops_wret"
    ):
        #   send_wret           event   cont    op1     op2         tmp_reg1
        #   sendr_wret          event   cont    op1     op2         tmp_reg1
        #   sendops_wret        event   cont    op1     op2         tmp_reg1
        opcode.replace("send4", "sendr")
        ActionClass = "SAction"
        operand.event = part[1]
        operand.dst = None
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.op3 = None
        operand.tmp_reg1 = part[5]

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif (
        opcode == "send_dmlm_ld"
        or opcode == "sendr_dmlm"
        or (opcode == "send4_dmlm" and len(part) == 4)
    ):
        #   send_dmlm_ld        dst     cont    op1
        #   sendr_dmlm          dst     cont    op1
        opcode.replace("send4", "sendr")
        ActionClass = "SAction"
        operand.event = None
        operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        if len(part) > 4:
            operand.op2 = part[4]
        operand.op3 = None
        operand.tmp_reg1 = None

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif (
        opcode == "send_dmlm_ld_wret"
        or opcode == "sendr_dmlm_wret"
        or (opcode == "send4_dmlm_wret" and len(part) == 5)
    ):
        #   send_dmlm_ld_wret   dst     cont    op1     tmp_reg1
        #   sendr_dmlm_wret     dst     cont    op1     tmp_reg1
        opcode.replace("send4", "sendr")
        ActionClass = "SAction"
        operand.event = None
        operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = None
        operand.op3 = None
        operand.tmp_reg1 = part[4]

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif (
        opcode == "send_dmlm"
        or opcode == "sendr2_dmlm"
        or (opcode == "send4_dmlm" and len(part) == 5)
    ):
        #   send_dmlm           dst     cont    op1     op2
        #   sendr2_dmlm         dst     cont    op1     op2
        opcode.replace("send4", "sendr2")
        ActionClass = "SAction"
        operand.event = None
        operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.op3 = None
        operand.tmp_reg1 = None

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif (
        opcode == "send_dmlm_wret"
        or opcode == "sendr2_dmlm_wret"
        or (opcode == "send4_dmlm_wret" and len(part) == 6)
        or opcode == "sendops_dmlm_wret"
    ):
        #   send_dmlm_wret      dst     cont    op1     op2         tmp_reg1
        #   sendr2_dmlm_wret    dst     cont    op1     op2         tmp_reg1
        #   sendops_dmlm_wret   dst     cont    op1     op2         tmp_reg1
        opcode.replace("send4", "sendr2")
        ActionClass = "SAction"
        operand.event = None
        operand.dst = part[1]
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.op2 = part[4]
        operand.op3 = None
        operand.tmp_reg1 = part[5]

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif (
        opcode == "send_reply"
        or opcode == "sendr_reply"
        or (opcode == "send4_reply" and len(part) == 4)
    ):
        #   send_reply          op1     op2     tmp_reg1
        #   sendr_reply         op1     op2     tmp_reg1
        opcode.replace("send4", "sendr")
        ActionClass = "SAction"
        operand.event = None
        operand.dst = None
        operand.cont = None
        operand.op1 = part[1]
        operand.op2 = part[2]
        operand.op3 = None
        operand.tmp_reg1 = part[3]

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif opcode == "sendr3_reply" or (opcode == "send4_reply" and len(part) == 5):
        #   sendr3_reply        op1     op2     op3     tmp_reg1
        opcode.replace("send4", "sendr3")
        ActionClass = "SAction"
        operand.event = None
        operand.dst = None
        operand.cont = None
        operand.op1 = part[1]
        operand.op2 = part[2]
        operand.op3 = part[3]
        operand.tmp_reg1 = part[4]

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])
    elif opcode == "send_any_wcont" or opcode == "send_any_wret":
        #   send_any_wcont      event   cont    op1     reglist     tmp_reg1
        #   send_any_wret       event   cont    op1     reglist     tmp_reg1
        ActionClass = "SPAction"
        operand.event = part[1]
        operand.dst = None
        operand.cont = part[2]
        operand.op1 = part[3]
        operand.reglist = part[5:]
        operand.tmp_reg1 = part[4]

        for i in range(1, len(part)):
            if "UDPR" in part[i]:
                if int(part[i][5:]) > maxudp:
                    maxudp = int(part[i][5:])
            elif "OB" in part[i]:
                if int(part[i][3:]) > maxop:
                    maxop = int(part[i][3:])

    # elif opcode == "send4_wret" or opcode == "sendr_wret" or opcode == "send_wret" or opcode == "send4_wcont" or opcode == "sendr_wcont" or opcode == "send_wcont" or opcode == "sendops_wcont" or opcode == "sendops_wret":
    #     #Sends to N/w ID
    #     ActionClass = "SAction"
    #     operand.op3 = None
    #     operand.event = part[1]
    #     #operand.dst = (int(part[1]) >> 32) & (0xffffffff) # extract dst from event_word
    #     #operand.dst = part[2]
    #     operand.cont = part[2]
    #     operand.op1 = part[3]
    #     opcode = opcode.replace("sendr", "send4")
    #     if opcode[4] != "4" or (opcode[4] == "4" and len(part) > 4):
    #         operand.op2 = part[4]
    #     if opcode[4] == "4":
    #         if opcode == "send4_wret":
    #             if len(part) > 7:
    #                 operand.op3 = part[5]
    #         elif len(part) > 5:
    #             operand.op3 = part[5]
    #     for i in range(1, len(part)):
    #         if "UDPR" in part[i]:
    #             if int(part[i][5:]) > maxudp:
    #                 maxudp = int(part[i][5:])
    #         elif "OB" in part[i]:
    #             if int(part[i][3:]) > maxop:
    #                 maxop = int(part[i][3:])
    #     if opcode == "send4_wret" or opcode == "sendr_wret" or opcode == "send_wret" or opcode == "sendops_wret":
    #         #operand.tmp_reg1 = part[-2]
    #         #operand.tmp_reg2 = part[-1]
    #         operand.tmp_reg1 = part[-1]

    # elif opcode == "send_dmlm" or opcode == "send_dmlm_wret" or opcode == "send4_dmlm" or opcode == "send4_dmlm_wret" or opcode == "sendr_dmlm" or opcode == "sendr_dmlm_wret" or opcode == "sendops_dmlm" or opcode == "sendops_dmlm_wret":
    #     ActionClass = "SAction"
    #     operand.op2 = None
    #     operand.event = "Empty"  # No event label required for destination in DRAM/LM
    #     operand.dst = part[1]
    #     operand.cont = part[2]
    #     operand.op1 = part[3]
    #     operand.tmp_reg1 = part[-1]
    #     opcode = opcode.replace("sendr", "send4")
    #     if opcode[4] != '4' or (opcode[4] == '4' and len(part) > 4):
    #         operand.op2 = part[4]
    #     for i in range(1, len(part)):
    #         if "UDPR" in part[i]:
    #             if int(part[i][5:]) > maxudp:
    #                 maxudp = int(part[i][5:])
    #         elif "OB" in part[i]:
    #             if int(part[i][3:]) > maxop:
    #                 maxop = int(part[i][3:])

    # elif opcode == "send_dmlm_ld" or opcode == "send_dmlm_ld_wret":
    #     ActionClass = "SAction"
    #     operand.op3 = None
    #     operand.event = "Empty"  # No event label required for destination in DRAM/LM
    #     operand.dst = part[1]
    #     operand.cont = part[2]
    #     operand.op2 = part[3]
    #     operand.tmp_reg1 = part[-1]
    #     for i in range(1, len(part)):
    #         if "UDPR" in part[i]:
    #             if int(part[i][5:]) > maxudp:
    #                 maxudp = int(part[i][5:])
    #         elif "OB" in part[i]:
    #             if int(part[i][3:]) > maxop:
    #                 maxop = int(part[i][3:])

    # elif opcode == "send_reply" or opcode == "send4_reply" or opcode == "sendr_reply":
    #     ActionClass = "SAction"
    #     operand.op3 = None
    #     operand.event = "Empty"
    #     operand.op1 = part[1]
    #     operand.tmp_reg1 = part[-1]
    #     opcode = opcode.replace("sendr", "send4")
    #     if opcode[4] != "4" or (opcode[4] == "4" and len(part) > 2):
    #         operand.op2 = part[2]
    #     if (opcode[4] == "4" and len(part) > 3):
    #         operand.op3 = part[3]
    #     for i in range(2, len(part)):
    #         if "UDPR" in part[i]:
    #             if int(part[i][5:]) > maxudp:
    #                 maxudp = int(part[i][5:])
    #         elif "OB" in part[i]:
    #             if int(part[i][3:]) > maxop:
    #                 maxop = int(part[i][3:])

    # # Check this soon
    # elif opcode == "send_any_wcont" or opcode == "send_any_wret" or opcode == "send_any":
    #     ActionClass = "SPAction"
    #     operand.op3 = None
    #     operand.event = part[1]
    #     #operand.dst = part[2]
    #     if len(part) > 2:
    #         operand.cont = part[2]
    #     if len(part) > 3:
    #         operand.op1 = part[3]
    #     if len(part) > 4:
    #         #operand.reglist = part[4:]
    #         operand.tmp_reg1 = part[4]
    #     if len(part) > 5:
    #         operand.reglist = part[5:]

    #     for i in range(1, len(part)):
    #         if "UDPR" in part[i]:
    #             if int(part[i][5:]) > maxudp:
    #                 maxudp = int(part[i][5:])
    #         elif "OB" in part[i]:
    #             if int(part[i][3:]) > maxop:
    #                 maxop = int(part[i][3:])

    elif opcode == "print":
        ActionClass = "PAction"
        match = re.search(r"print\s*'(.*)'(.*)", asm_inst)
        if match:
            count = print_counter().get_counter()
            operand.formatstr = match.group(1)
            operand.reglist = match.group(2).split()
            operand.print_id = count
        else:
            print("Error parsing 'print'.")
            exit(1)

    elif opcode == "perflog":
        ActionClass = "PerflogAction"
        operand.perflog_mode = int(part[1])
        if operand.perflog_mode == 0:
            count = print_counter().get_counter()
            operand.perflog_payload_list = part[2:]
            operand.perflog_msg_id = 0xFFFFFFFF
            operand.formatstr = ""
            operand.reglist = []
            operand.print_id = count
        elif operand.perflog_mode == 1:
            operand.perflog_msg_id = part[2]
            match = re.search(r"perflog\s*1\s*([0-9]+)\s*'(.*)'(.*)", asm_inst)
            if match:
                count = print_counter().get_counter()
                operand.perflog_msg_id = int(match.group(1))
                operand.formatstr = match.group(2)
                operand.reglist = match.group(3).split()
                operand.print_id = count
            else:
                print("Error parsing 'perflog' mode 1.")
                exit(1)
        elif operand.perflog_mode == 2:
            operand.perflog_msg_id = part[2]
            match = re.search(r"perflog\s*2\s*'(.*)'\s*([0-9]+)\s*'(.*)'(.*)", asm_inst)
            if match:
                count = print_counter().get_counter()
                operand.perflog_payload_list = match.group(1).split()
                operand.perflog_payload_list = [
                    int(p) for p in operand.perflog_payload_list
                ]
                operand.perflog_msg_id = int(match.group(2))
                operand.formatstr = match.group(3)
                operand.reglist = match.group(4).split()
                operand.print_id = count
            else:
                print("Error parsing 'perflog' mode 2.")
                exit(1)
        else:
            print("Invalid 'perflog' mode.")
            exit(1)

    elif opcode == "userctr":
        ActionClass = "UserCounterAction"
        operand.userctr_mode = int(part[1])
        operand.userctr_num = int(part[2])
        operand.userctr_arg = int(part[3])

    elif opcode == "lmmemcheck":
        ActionClass = "LMMemcheckAction"
        operand.mode = part[1]
        operand.op1 = part[2]
        operand.op2 = part[3]

    elif opcode == "instrans":
        ActionClass = "InsTransAction"
        operand.op1 = part[1]
        operand.op2 = part[2]
        operand.op3 = part[3]
        operand.op4 = part[4]
        operand.mode = part[5]
        operand.size = part[6]

    # Marziyeh: FP &Vector compare
    elif (
        (opcode.split("."))[0] == "fmadd"
        or (opcode.split("."))[0] == "fadd"
        or (opcode.split("."))[0] == "fsub"
        or (opcode.split("."))[0] == "fmul"
        or (opcode.split("."))[0] == "fdiv"
    ):
        ActionClass = "FPAction"
        # operand.funct = opcode
        # opcode = "fp"
        operand.src = part[1]
        operand.rt = part[2]
        operand.dst = part[3]
        # operand.mask = part[4]
        operand.mask = UNUSED_imm

        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst, operand.rt])
    elif (
        opcode.split(".")[0] == "vmadd"
        or opcode.split(".")[0] == "vadd"
        or opcode.split(".")[0] == "vsub"
        or opcode.split(".")[0] == "vmul"
        or opcode.split(".")[0] == "vdiv"
    ):
        ActionClass = "FPAction"
        # operand.funct = opcode.replace("v", "f")
        # opcode = "fp"
        operand.src = part[1]
        operand.rt = part[2]
        operand.dst = part[3]
        operand.mask = part[4]

        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst, operand.rt])

    elif (opcode.split("."))[0] == "fsqrt" or (opcode.split("."))[0] == "fexp":
        # operand.funct = opcode
        # opcode = "fp"
        ActionClass = "FPAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.rt = UNUSED_reg
        # operand.mask = part[3]
        """
        if precision == 0:
            operand.mask = 0xf
        elif precision == 1 or precision == 3: 
            operand.mask = 0x3
        elif precision == 2: 
            operand.mask = 0x1
        """
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif (opcode.split("."))[0] == "vsqrt" or (opcode.split("."))[0] == "vexp":
        operand.funct = opcode.replace("v", "f")
        opcode = "fp"
        ActionClass = "FPAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.mask = part[3]
        operand.rt = UNUSED_reg
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    elif (opcode.split("."))[0] == "vfill":
        ActionClass = "IAction"
        operand.dst = part[1]
        operand.imm = part[2]
        maxudp, maxop = calc_maxudp_maxob([operand.dst])

    elif (
        (opcode.split("."))[0] == "vgt"
        or (opcode.split("."))[0] == "vlt"
        or (opcode.split("."))[0] == "veq"
    ):
        ActionClass = "VAction"
        # operand.funct = opcode
        # opcode = "vcomp"
        operand.src = part[1]
        operand.rt = part[2]
        operand.dst = part[3]
        operand.mask = part[4]
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst, operand.rt])

    elif (opcode.split("."))[0] == "fcnvt":
        # operand.funct = opcode
        # opcode = "fp"
        ActionClass = "FPAction"
        operand.src = part[1]
        operand.dst = part[2]
        operand.rt = UNUSED_reg
        operand.funct = (opcode.split("."))[2]
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    # depricated
    elif opcode == "fcnvt_i2f" or opcode == "fcnvt_f2i":
        operand.funct = opcode
        opcode = "fp"
        ActionClass = "FPAction"
        operand.src = part[1]
        operand.dst = part[2]
        # operand.mask = part[3]
        if precision == 0:
            operand.mask = 0xF
        elif precision == 1 or precision == 3:
            operand.mask = 0x3
        elif precision == 2:
            operand.mask = 0x1
        maxudp, maxop = calc_maxudp_maxob([operand.src, operand.dst])

    operand.maxudp = maxudp
    operand.maxop = maxop
    return ActionClass, operand


def Transition_eq(tr1, tr2):
    if isinstance(tr1, tr2.__class__):
        primitiveEQ = False
        if (
            tr1.dst == tr2.dst
            and tr1.label == tr2.label
            and tr1.src == tr2.src
            and tr1.anno_type == tr2.anno_type
        ):
            primitiveEQ = True
        actionEQ = True
        if len(tr1.actions) != len(tr2.actions):
            actionEQ = False
        else:
            for idx in range(len(tr1.actions)):
                if not tr1.actions[idx] == tr2.actions[idx]:
                    actionEQ = False
                    break

        if actionEQ and primitiveEQ:
            return True
        else:
            return False
    else:
        return False


def State_eq(s1, s2):
    if isinstance(s1, s2.__class__):
        if s1.state_id == s2.state_id:
            return True
        else:
            return False
    else:
        return False


def Taction_eq(t_a1, t_a2):
    if isinstance(t_a1, t_a2.__class__):
        if (
            t_a1.opcode == t_a2.opcode
            and t_a1.dst == t_a2.dst
            and t_a1.src == t_a2.src
            and t_a1.rt == t_a2.rt
        ):
            return True
        else:
            return False
    else:
        return False


def Jaction_eq(j_a1, j_a2):
    if isinstance(j_a1, j_a2.__class__):
        if (
            j_a1.opcode == j_a2.opcode
            and j_a1.dst == j_a2.dst
            and j_a1.src == j_a2.src
            and j_a1.imm == j_a2.imm
            and j_a1.imm2 == j_a2.imm2
        ):
            return True
        else:
            return False
    else:
        return False


def Action_eq(a_a1, a_a2):
    if isinstance(a_a1, a_a2.__class__):
        if (
            a_a1.opcode == a_a2.opcode
            and a_a1.dst == a_a2.dst
            and a_a1.src == a_a2.src
            and a_a1.imm == a_a2.imm
        ):
            return True
        else:
            return False
    else:
        return False


def logical_rshift(val, n):
    result = (val % 0x100000000) >> n
    # print "looooooooooooooooooooooooooooooog rshift->  "+str(val)+">>>"+str(n)+"="+str(result)+"\n"
    return result


# value is an n-bit number to be shifted m times
def arithmetic_rshift(value, n, m):
    if value & 2 ** (n - 1) != 0:  # MSB is 1, i.e. value is negative
        filler = int("1" * m + "0" * (n - m), 2)
        value = (value >> m) | filler  # fill in 0's with 1's
        return value
    else:
        return value >> m
