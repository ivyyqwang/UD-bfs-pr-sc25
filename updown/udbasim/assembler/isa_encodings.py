NUM_TRANSITION_TYPES = 16

transition_type_enc = {
    "eventCarry": "0000",
    "event": "0001",
    "refill": "0010",
    "majorityCarry": "0011",
    "defaultCarry": "0100",
    "flagCarry": "0101",
    "commonCarry": "0110",
    "epsilonCarry_with_action": "0111",
    "flagmajorityCarry": "1000",
    "flagdefaultCarry": "1001",
    "basic_with_action": "1010",
    "refill_with_action": "1011",
    "flagCarry_with_action": "1100",
    "commonCarry_with_action": "1101",
    "basic": "1110",
    "epsilonCarry": "1111",
}

transition_type_enc_rev = {
    0:  "eventCarry",
    1:  "event",
    2:  "refillCarry",
    3:  "majorityCarry",
    4:  "defaultCarry",
    5:  "flagCarry",
    6:  "commonCarry",
    7:  "epsilonCarry_with_action",
    8:  "flagmajorityCarry",
    9:  "flagdefaultCarry",
    10: "basic_with_action",
    11: "refillCarry_with_action",
    12: "flagCarry_with_action",
    13: "commonCarry_with_action",
    14: "basic",
    15: "epsilonCarry",
}

NUM_STATE_PROPERTIES = 12

state_property_enc = {
    "EVENT": 0,
    "DEFAULT": 1,
    "COMMON": 2,
    "MAJORITY": 3,
    "FLAG": 4,
    "PERSIST": 5,
    "FLAG_MAJORITY": 6,
    "FLAG_DEFAULT": 7,
    "REFILL": 8,            #TODO: remove this
    "EPSILON": 9,
    "NUL": 10,  # using NUL instead of NULL because NULL is a keyword in C
    "BASIC": 11,
}

state_property_enc_rev = {
    0:  "EVENT",
    1:  "DEFAULT",
    2:  "COMMON",
    3:  "MAJORITY",
    4:  "FLAG",
    5:  "PERSIST",
    6:  "FLAG_MAJORITY",
    7:  "FLAG_DEFAULT",
    8:  "REFILL",
    9:  "EPSILON",
    10: "NUL",  # using NUL instead of NULL because NULL is a keyword in C
    11: "BASIC",
}

NUM_REGISTERS = 32

register_enc = {
    "X0": "00000",
    "X1": "00001",
    "X2": "00010",
    "X3": "00011",
    "X4": "00100",
    "X5": "00101",
    "X6": "00110",
    "X7": "00111",
    "X8": "01000",
    "X9": "01001",
    "X10": "01010",
    "X11": "01011",
    "X12": "01100",
    "X13": "01101",
    "X14": "01110",
    "X15": "01111",
    "X16": "10000",
    "X17": "10001",
    "X18": "10010",
    "X19": "10011",
    "X20": "10100",
    "X21": "10101",
    "X22": "10110",
    "X23": "10111",
    "X24": "11000",
    "X25": "11001",
    "X26": "11010",
    "X27": "11011",
    "X28": "11100",
    "X29": "11101",
    "X30": "11110",
    "X31": "11111",
    "NWID": "00000",
    "Cont": "00001",
    "EQT": "00010",
    "FSCR": "00100",
    "state_property": "00110",
    "LMBase": "00111",
    "OB_0": "01000",
    "OB_1": "01001",
    "OB_2": "01010",
    "OB_3": "01011",
    "OB_4": "01100",
    "OB_5": "01101",
    "OB_6": "01110",
    "OB_7": "01111",
    "UDPR_0": "10000",
    "UDPR_1": "10001",
    "UDPR_2": "10010",
    "UDPR_3": "10011",
    "UDPR_4": "10100",
    "UDPR_5": "10101",
    "UDPR_6": "10110",
    "UDPR_7": "10111",
    "UDPR_8": "11000",
    "UDPR_9": "11001",
    "UDPR_10": "11010",
    "UDPR_11": "11011",
    "UDPR_12": "11100",
    "UDPR_13": "11101",
    "UDPR_14": "11110",
    "UDPR_15": "11111",
}

register_enc_rev = {
    0:  "X0",
    1:  "X1",
    2:  "X2",
    3:  "X3",
    4:  "X4",
    5:  "X5",
    6:  "X6",
    7:  "X7",
    8:  "X8",
    9:  "X9",
    10: "X10",
    11: "X11",
    12: "X12",
    13: "X13",
    14: "X14",
    15: "X15",
    16: "X16",
    17: "X17",
    18: "X18",
    19: "X19",
    20: "X20",
    21: "X21",
    22: "X22",
    23: "X23",
    24: "X24",
    25: "X25",
    26: "X26",
    27: "X27",
    28: "X28",
    29: "X29",
    30: "X30",
    31: "X31",
}

precision_enc = {"64": "001", "32": "010", "b16": "011", "i32": "111", "i64": "110", "FP64": "001", "FP32": "010", "BF16": "011", "I32": "111", "I64": "110","UNUSED": "000"}

func_enc = {
    "0": "000",
    "1": "001",
    "2": "010",
    "3": "011",
    "4": "100",
    "5": "101",
    "6": "110",
    "7": "",  # these are "undefined"
}

name_func_mapping = {
    # B TYPE
    "bne": "0",
    "beq": "1",
    "bgt": "2",
    "ble": "3",
    "bneu": "0",
    "bequ": "1",
    "bgtu": "2",
    "bleu": "3",
    "bnei": "0",
    "beqi": "1",
    "bgti": "2",
    "blei": "3",
    "blti": "4",
    "bgei": "5",
    "bneiu": "0",
    "beqiu": "1",
    "bgtiu": "2",
    "bleiu": "3",
    "bltiu": "4",
    "bgeiu": "5",

    # R TYPE
    "add": "0",
    "sub": "1",
    "mul": "2",
    "div": "3",
    "mod": "4",
    "and": "0",
    "or": "1",
    "xor": "2",
    "clt": "0",
    "cgt": "1",
    "ceq": "2",
    "cstr": "3",
    "sr": "0",
    "sl": "1",
    "sar": "2",
    "bcpyll": "0",
    "movrr": "0",
    "movwlr": "0",
    "movwrl": "0",
    "bcpyol": "0",

    "fmadd.64": "0",
    "fadd.64": "1",
    "fsub.64": "2",
    "fmul.64": "3",
    "fdiv.64": "4",
    "fsqrt.64": "5",
    "fexp.64": "6",

    "fmadd.32": "0",
    "fadd.32": "1",
    "fsub.32": "2",
    "fmul.32": "3",
    "fdiv.32": "4",
    "fsqrt.32": "5",
    "fexp.32": "6",

    "fmadd.b16": "0",
    "fadd.b16": "1",
    "fsub.b16": "2",
    "fmul.b16": "3",
    "fdiv.b16": "4",
    "fsqrt.b16": "5",
    "fexp.b16": "6",

    "fcnvt.64.i64": "0",
    "fcnvt.32.i32": "0",
    "fcnvt.i64.64": "0",
    "fcnvt.i32.32": "0",
    "fcnvt.64.32": "1",
    "fcnvt.64.b16": "2",
    "fcnvt.32.64": "1",
    "fcnvt.32.b16": "2",
    "fcnvt.b16.64": "1",
    "fcnvt.b16.32": "2",

    "vmadd.32": "0",
    "vadd.32": "1",
    "vsub.32": "2",
    "vmul.32": "3",
    "vdiv.32": "4",
    "vsqrt.32": "5",
    "vexp.32": "6",

    "vmadd.b16": "0",
    "vadd.b16": "1",
    "vsub.b16": "2",
    "vmul.b16": "3",
    "vdiv.b16": "4",
    "vsqrt.b16": "5",
    "vexp.b16": "6",

    "vmadd.i32": "0",
    "vadd.i32": "1",
    "vsub.i32": "2",
    "vmul.i32": "3",
    "vdiv.i32": "4",
    "vsqrt.i32": "5",
    "vexp.i32": "6",

    "vgt.32": "0",
    "vgt.b16": "0",
    "vgt.i32": "0",

    # P TYPE
    "print": "0",
    "perflog": "1",
}

# fmt: off
# opcodes should all be 7 bits
I_opcode_enc = {
    "addi":     "0001001",  # 0x09
    "subi":     "0001010",  # 0x0a
    "muli":     "0001011",  # 0x0b
    "divi":     "0001100",  # 0x0c
    "modi":     "1111100",  # 0x7c
    "clti":     "0000011",  # 0x03
    "cgti":     "0000100",  # 0x04
    "ceqi":     "0000101",  # 0x05
    "andi":     "0000110",  # 0x06
    "ori":      "0000111",  # 0x07
    "xori":     "1111011",  # 0x7b
    "movil2":   "0001110",  # 0x0e
    "movil1":   "0001111",  # 0x0f
    "yield":    "0000001",  # 0x01
    "yieldt":   "0000010",  # 0x02
    "lastact":  "1111101",  # 0x7d
    "sli":      "1010000",  # 0x50
    "sri":      "1010001",  # 0x51
    "slori":    "1010010",  # 0x52
    "srori":    "1010011",  # 0x53
    "slandi":   "1010100",  # 0x54
    "srandi":   "1010101",  # 0x55
    "sari":     "1010110",  # 0x56
    "hashsb32": "1010111",  # 0x57
    "hashsb64": "1011000",  # 0x58
    "hashl64":  "1011001",  # 0x59
    "hash":     "1011010",  # 0x5a
    "hashl":    "1011011",  # 0x5b
    "bcpylli":  "1011100",  # 0x5c
    "movsbr":   "1011101",  # 0x5d
    "movipr":   "1011110",  # 0x5e
    "movlsb":   "1011111",  # 0x5f
    "siw":      "1111001",  # 0x79
    "refill":   "1111010",  # 0x7a
    "ssprop":   "1111000",  # 0x78
    #"movir":    "0001000",  # 0x08
}

LI_opcode_enc = {
    "evlb":     "1000010",  # 0x42
    "movir":    "0001000",  # 0x08
}

S_opcode_enc = {
    "sladdii": "0100010",  # 0x22
    "slsubii": "0100011",  # 0x23
    "sraddii": "0101000",  # 0x28
    "srsubii": "0101111",  # 0x2f
    "slorii":  "0100101",  # 0x25
    "srorii":  "0100110",  # 0x26
    "slandii": "0100111",  # 0x27
    "srandii": "0101001",  # 0x29
    "movbil":  "0101010",  # 0x2a
    "movblr":  "0101011",  # 0x2b
    "fstate":  "0101100",  # 0x2c
    "cswpi":   "0101101",  # 0x2d
    "movlr":   "0100000",  # 0x20
    "movrl":   "0100001",  # 0x21
    "swiz":    "0101110",  # 0x2e
    "bcpyoli": "0100100",  # 0x24
}

R_opcode_enc = {
    "add":    "0110011",  # 0x33
    "sub":    "0110011",  # 0x33
    "mul":    "0110011",  # 0x33
    "div":    "0110011",  # 0x33
    "mod":    "0110011",  # 0x33
    "and":    "0110100",  # 0x34
    "or":     "0110100",  # 0x34
    "xor":    "0110100",  # 0x34
    "clt":    "0110101",  # 0x35
    "cgt":    "0110101",  # 0x35
    "ceq":    "0110101",  # 0x35
    "cstr":   "0110101",  # 0x35
    "sr":     "0110110",  # 0x36
    "sl":     "0110110",  # 0x36
    "sar":    "0110110",  # 0x36
    "bcpyll": "0110111",  # 0x37
    "movrr":  "0111000",  # 0x38 FIXME: remove this instruction?
    "movwlr": "0110001",  # 0x31
    "movwrl": "0110010",  # 0x32
    "bcpyol": "0110000",  # 0x30
    "bcpyol": "0110000",  # 0x30

    "fmadd.64":  "1100000",  # 0x60
    "fadd.64":   "1100000",  # 0x60
    "fsub.64":   "1100000",  # 0x60
    "fmul.64":   "1100000",  # 0x60
    "fdiv.64":   "1100000",  # 0x60
    "fsqrt.64":  "1100000",  # 0x60
    "fexp.64":   "1100000",  # 0x60
    "fmadd.32":  "1100000",  # 0x60
    "fadd.32":   "1100000",  # 0x60
    "fsub.32":   "1100000",  # 0x60
    "fmul.32":   "1100000",  # 0x60
    "fdiv.32":   "1100000",  # 0x60
    "fsqrt.32":  "1100000",  # 0x60
    "fexp.32":   "1100000",  # 0x60
    "fmadd.b16": "1100000",  # 0x60
    "fadd.b16":  "1100000",  # 0x60
    "fsub.b16":  "1100000",  # 0x60
    "fmul.b16":  "1100000",  # 0x60
    "fdiv.b16":  "1100000",  # 0x60
    "fsqrt.b16": "1100000",  # 0x60
    "fexp.b16":  "1100000",  # 0x60

    "fcnvt.64.i64": "1100001",  # 0x61
    "fcnvt.32.i32": "1100001",  # 0x61
    "fcnvt.i64.64": "1100001",  # 0x61
    "fcnvt.i32.32": "1100001",  # 0x61
    "fcnvt.64.32":  "1100001",  # 0x61
    "fcnvt.64.b16": "1100001",  # 0x61
    "fcnvt.32.64":  "1100001",  # 0x61
    "fcnvt.32.b16": "1100001",  # 0x61
    "fcnvt.b16.64": "1100001",  # 0x61
    "fcnvt.b16.32": "1100001",  # 0x61

    "vmadd.32":  "1100010",  # 0x62
    "vadd.32":   "1100010",  # 0x62
    "vsub.32":   "1100010",  # 0x62
    "vmul.32":   "1100010",  # 0x62
    "vdiv.32":   "1100010",  # 0x62
    "vsqrt.32":  "1100010",  # 0x62
    "vexp.32":   "1100010",  # 0x62
    "vmadd.b16": "1100010",  # 0x62
    "vadd.b16":  "1100010",  # 0x62
    "vsub.b16":  "1100010",  # 0x62
    "vmul.b16":  "1100010",  # 0x62
    "vdiv.b16":  "1100010",  # 0x62
    "vsqrt.b16": "1100010",  # 0x62
    "vexp.b16":  "1100010",  # 0x62
    "vmadd.i32": "1100010",  # 0x62
    "vadd.i32":  "1100010",  # 0x62
    "vsub.i32":  "1100010",  # 0x62
    "vmul.i32":  "1100010",  # 0x62
    "vdiv.i32":  "1100010",  # 0x62
    "vsqrt.i32": "1100010",  # 0x62
    "vexp.i32":  "1100010",  # 0x62

    "vgt.32":  "1100011",  # 0x63
    "vgt.b16": "1100011",  # 0x63
    "vgt.i32": "1100011",  # 0x63
}

B_opcode_enc = {
    "bne":   "1000100",  # 0x44
    "beq":   "1000100",  # 0x44
    "bgt":   "1000100",  # 0x44
    "ble":   "1000100",  # 0x44
    "bneu":  "1001000",  # 0x48
    "bequ":  "1001000",  # 0x48
    "bgtu":  "1001000",  # 0x48
    "bleu":  "1001000",  # 0x48
    "bnei":  "1000011",  # 0x43
    "beqi":  "1000011",  # 0x43
    "bgti":  "1000011",  # 0x43
    "blei":  "1000011",  # 0x43
    "blti":  "1000011",  # 0x43
    "bgei":  "1000011",  # 0x43
    "bneiu": "1000101",  # 0x45
    "beqiu": "1000101",  # 0x45
    "bgtiu": "1000101",  # 0x45
    "bleiu": "1000101",  # 0x45
    "bltiu": "1000101",  # 0x45
    "bgeiu": "1000101",  # 0x45
}

J_opcode_enc = {
    "jmp": "1000110",  # 0x46
}

M1_opcode_enc = {
    "send":  "0010000",  # 0x10
    "sendb": "0010101",  # 0x15
}

M2_opcode_enc = {
    "sendm":  "0010001",  # 0x11
    "sendmb": "0010010",  # 0x12
    "instrans": "0011010",  # 0x1A
}

M3_opcode_enc = {
    "sendr":   "0010011",  # 0x13
    "sendr3":  "0010111",  # 0x17
    "sendmr":  "0010100",  # 0x14
    "sendmr2": "0011001",  # 0x19
}

M4_opcode_enc = {
    "sendops":  "0010110",  # 0x16
    "sendmops": "0011000",  # 0x18
}

E_opcode_enc = {
    "evi":  "1000000",  # 0x40
    "evii": "1000001",  # 0x41
}

R4_opcode_enc = {
    "ev":   "1110000",  # 0x70
    "cswp": "1110001",  # 0x71
}

VF_opcode_enc = {
    "vfill.32":  "1100100",  # 0x64
    "vfill.i32": "1100100",  # 0x64
    "vfill.b16": "1100100",  # 0x64
}

P_opcode_enc = {
    "print":     "1111111",  # 0x7F
    "perflog":   "1111111",  # 0x7F
}

all_opcode_enc = {
    **I_opcode_enc,
    **LI_opcode_enc,
    **P_opcode_enc,
    **S_opcode_enc,
    **R_opcode_enc,
    **B_opcode_enc,
    **J_opcode_enc,
    **M1_opcode_enc,
    **M2_opcode_enc,
    **M3_opcode_enc,
    **M4_opcode_enc,
    **E_opcode_enc,
    **R4_opcode_enc,
    **VF_opcode_enc,
}

"""
<instruction_name>: [(<bits>, <type>, <field_name>, <pos_in_disasm>), ...]
<type> is one of:
    "op": opcode
    "fc": function code
    "r5": 5-bit register
    "r4": 4-bit register
    "si": signed immediate
    "ui": unsigned immediate
    "b16": bfloat16 immediate
    "na": not applicable / unused
    "ty" : transition type
<pos_in_disasm>:
    0: not appearing in disassembly
    1~n: position in disassembly
"""
I_bitfields = {
    "ITYPE":    [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "ui",  "imm16", 3)],
    "addi":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "subi":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "muli":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "divi":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "modi":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "clti":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "cgti":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "ceqi":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "si",    "imm", 3)],
    "andi":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "ui",    "imm", 3)],
    "ori":      [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "ui",    "imm", 3)],
    "xori":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "ui",    "imm", 3)],
    "movil2":   [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "na", "NA", 0), (16, "ui",    "imm", 2)],
    "movil1":   [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "na", "NA", 0), ( 8, "ui",    "imm", 2), ( 8, "na", "NA", 0)],
    "yield":    [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "na", "NA", 0), (16, "na",     "NA", 0)],
    "yieldt":   [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "na", "NA", 0), (16, "na",     "NA", 0)],
    "lastact":  [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "na", "NA", 0), (16, "na",     "NA", 0)],
    "sli":      [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), ( 6, "ui",  "shift", 3), (10, "na", "NA", 0)],
    "sri":      [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), ( 6, "ui",  "shift", 3), (10, "na", "NA", 0)],
    "slori":    [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), ( 6, "ui",  "shift", 3), (10, "na", "NA", 0)],
    "srori":    [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), ( 6, "ui",  "shift", 3), (10, "na", "NA", 0)],
    "slandi":   [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), ( 6, "ui",  "shift", 3), (10, "na", "NA", 0)],
    "srandi":   [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), ( 6, "ui",  "shift", 3), (10, "na", "NA", 0)],
    "sari":     [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), ( 6, "ui",  "shift", 3), (10, "na", "NA", 0)],
    "hashsb32": [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "r4", "Xd", 1), (16, "ui", "htbase", 2)],
    "hashsb64": [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "na",     "NA", 0)],
    "hashl64":  [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "na",     "NA", 0)],
    "hash":     [(7, "op", "opcode", 0), (5, "r5",     "Xe", 1), (4, "r4", "Xd", 2), (16, "na",     "NA", 0)],
    "hashl":    [(7, "op", "opcode", 0), (5, "r5",     "Xe", 1), (4, "r4", "Xd", 2), ( 3, "ui",   "lenw", 3), (13, "na", "NA", 0)],
    "bcpylli":  [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "r4", "Xd", 2), (16, "ui",    "len", 3)],
    "movsbr":   [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "r4", "Xd", 1), (16, "na",     "NA", 0)],
    "movipr":   [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "r4", "Xd", 1), (16, "na",     "NA", 0)],
    "movlsb":   [(7, "op", "opcode", 0), (5, "r5",     "Xs", 1), (4, "na", "NA", 0), (16, "na",     "NA", 0)],
    "siw":      [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "na", "NA", 0), ( 4, "ui",  "width", 1)],
    "refill":   [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "na", "NA", 0), (16, "ui",    "imm", 1)],
    "ssprop":   [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "na", "NA", 0), ( 4, "ui",   "type", 1), (12, "ui", "value", 2)],
    #"movir":    [(7, "op", "opcode", 0), (5, "na",     "NA", 0), (4, "r4", "Xd", 1), (16, "si",    "imm", 2)],
}

LI_bitfields = {
    "LITYPE":   [(7, "op", "opcode", 0), (4, "r4", "Xd", 1), (21, "ui",   "imm", 2)],
    "movir":    [(7, "op", "opcode", 0), (4, "r4", "Xd", 1), (21, "si",   "imm", 2)],
    "evlb":     [(7, "op", "opcode", 0), (4, "r4", "Xd", 1), (21, "ui", "label", 2)],
}

P_bitfields = {
    "PTYPE":    [(7, "op", "opcode", 0), (19, "na",     "NA", 1), (3, "fc",   "func", 2), (3, "na",  "NA", 3)],
    "print":    [(7, "op", "opcode", 0), (19, "ui", "offset", 1), (3, "fc",   "func", 2), (3, "na",  "NA", 3)],
    "perflog":  [(7, "op", "opcode", 0), (19, "ui", "offset", 1), (3, "fc",   "func", 2), (3, "na",  "NA", 3)],
}

S_bitfields = {
    "STYPE":    [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui",  "imm4", 3), (12, "ui",      "imm12", 4)],
    "sladdii":  [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "slsubii":  [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "sraddii":  [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "srsubii":  [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "slorii":   [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "srorii":   [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "slandii":  [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "srandii":  [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "shift", 3), (12, "ui",        "imm", 4)],
    "movbil":   [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "na", "NA", 0), (3, "ui",  "lenb", 2), ( 1, "na",         "NA", 0), ( 8, "ui", "bits", 3), (4, "na", "NA", 0)],
    "movblr":   [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (3, "ui",  "lenb", 3), ( 1, "na",         "NA", 0), (12, "na",   "NA", 0)],
    "fstate":   [(7, "op", "opcode", 0), (5, "na",  "NA", 0), (4, "na", "NA", 0), (4, "ui",  "prop", 1), (12, "na", "stateident", 2)],
    "cswpi":    [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (4, "r4", "X2", 2), (4, "si",  "imm1", 3), ( 4, "si",       "imm2", 4), ( 8, "na",   "NA", 0)],
    "movlr":    [(7, "op", "opcode", 0), (5, "r5",  "Xs", 2), (4, "r4", "Xd", 3), (3, "ui",  "lenb", 5), ( 1, "ui",        "inc", 4), (12, "si",  "imm", 1)],
    "movrl":    [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 3), (3, "ui",  "lenb", 5), ( 1, "ui",        "inc", 4), (12, "si",  "imm", 2)],
    "swiz":     [(7, "op", "opcode", 0), (5, "r5",  "Xs", 1), (4, "r4", "Xd", 2), (4, "na",    "NA", 0), (12, "na",         "NA", 0)],
    "bcpyoli":  [(7, "op", "opcode", 0), (5, "r5", "Xop", 1), (4, "r4", "Xd", 2), (4, "ui",  "lenw", 3), (12, "na",         "NA", 0)],
}

R_bitfields = {
    "RTYPE":        [(7, "op", "opcode", 0), (5, "r5",  "Xs1", 1), (5, "r5", "Xd", 3), (5, "r5",   "Xs2", 2), (4, "ui",  "imm4", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "add":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "sub":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "mul":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "div":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "mod":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "and":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "or":           [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "xor":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "clt":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "cgt":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "ceq":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "cstr":         [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "sr":           [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "sl":           [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "sar":          [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "na",        "NA", 0)],
    "bcpyll":       [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "na",   "NA", 0), (3, "na",        "NA", 0)],
    "movrr":        [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "na",    "NA", 0), (4, "na",    "NA", 0), (3, "na",   "NA", 0), (3, "na",        "NA", 0)],  # FIXME: remove this instruction?
    "movwlr":       [(7, "op", "opcode", 0), (5, "r5",   "Xs", 2), (5, "r5", "Xd", 5), (5, "r5",    "Xb", 1), (3, "ui", "scale", 4), (1, "ui",  "inc", 3), (3, "na",        "NA", 0), (3, "na", "NA", 0)],
    "movwrl":       [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xb", 2), (3, "ui", "scale", 5), (1, "ui",  "inc", 4), (3, "na",        "NA", 0), (3, "na", "NA", 0)],
    "bcpyol":       [(7, "op", "opcode", 0), (5, "r5",  "Xop", 1), (5, "r5", "Xd", 2), (5, "r5", "Xlenw", 3), (4, "na",    "NA", 0), (3, "na",   "NA", 0), (3, "na",        "NA", 0)],

    "fmadd.64":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fadd.64":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fsub.64":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fmul.64":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fdiv.64":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fsqrt.64":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fexp.64":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fmadd.32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fadd.32":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fsub.32":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fmul.32":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fdiv.32":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fsqrt.32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fexp.32":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fmadd.b16":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fadd.b16":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fsub.b16":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fmul.b16":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fdiv.b16":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fsqrt.b16":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fexp.b16":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.64.i64": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.32.i32": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.i64.64": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.i32.32": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.64.32":  [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.64.b16": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.32.64":  [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.32.b16": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.b16.64": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
    "fcnvt.b16.32": [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (9, "na",    "NA", 0), (3, "fc", "func", 0), (3, "ui", "precision", 0)],

     "vmadd.32":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vadd.32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vsub.32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vmul.32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vdiv.32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vsqrt.32":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vexp.32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vmadd.b16":   [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vadd.b16":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vsub.b16":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vmul.b16":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vdiv.b16":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vsqrt.b16":   [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vexp.b16":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vmadd.i32":   [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vadd.i32":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vsub.i32":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vmul.i32":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vdiv.i32":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vsqrt.i32":   [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],
     "vexp.i32":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "fc", "func", 0), (3, "ui", "precision", 0)],

     "vgt.32":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "na",   "NA", 0), (3, "ui", "precision", 0)],
     "vgt.b16":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "na",   "NA", 0), (3, "ui", "precision", 0)],
     "vgt.i32":     [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (5, "r5", "Xd", 3), (5, "r5",    "Xt", 2), (4, "ui",  "mask", 4), (3, "na",   "NA", 0), (3, "ui", "precision", 0)],
}

B_bitfields = {
    "BTYPE":    [(7, "op", "opcode", 0), (5, "r5", "Xs1", 1), (5, "r5", "Xs2", 2), (9, "ui",  "imm12a", 3), (3, "fc", "func", 0), (3, "si",  "imm12b", 4)],
    "bne":      [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "beq":      [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bgt":      [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "ble":      [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bneu":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bequ":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bgtu":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bleu":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "r5",  "X2", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bnei":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "si", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "beqi":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "si", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bgti":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "si", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "blei":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "si", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "blti":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "si", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bgei":     [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "si", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bneiu":    [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "ui", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "beqiu":    [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "ui", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bgtiu":    [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "ui", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bleiu":    [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "ui", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bltiu":    [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "ui", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
    "bgeiu":    [(7, "op", "opcode", 0), (5, "r5",  "X1", 1), (5, "ui", "imm", 2), (9, "ui", "targeta", 3), (3, "fc", "func", 0), (3, "si", "targetb", 4)],
}

J_bitfields = {
    "JTYPE":    [(7, "op", "opcode", 0), (25, "si", "imm25", 1)],
    "jmp":      [(7, "op", "opcode", 0), (25, "si",   "imm", 1)],
}

M1_bitfields = {
    "M1TYPE":   [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 2), (5, "r5", "Xptr", 3), (3, "ui", "imm3", 4), (1, "na", "NA", 0), (1, "ui", "imm1", 5), (5, "na", "NA", 0)],
    "send":     [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 2), (5, "r5", "Xptr", 3), (3, "ui", "lenw", 4), (1, "na", "NA", 0), (1, "ui", "mode", 5), (5, "na", "NA", 0)],
    "sendb":    [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 2), (5, "r5", "Xptr", 3), (3, "ui", "lenw", 4), (1, "na", "NA", 0), (1, "ui", "mode", 5), (5, "na", "NA", 0)],
}

M2_bitfields = {
    "M2TYPE":   [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 3), (5, "r5", "Xptr", 4), (3, "ui", "imm3", 5), (2, "ui", "imm2", 6), (5, "r5", "Xd", 2)],
    "sendm":    [(7, "op", "opcode", 0), (5, "na", "NA", 0), (5, "r5", "Xc", 2), (5, "r5", "Xptr", 3), (3, "ui", "lenw", 4), (2, "ui", "mode", 5), (5, "r5", "Xd", 1)],
    "sendmb":   [(7, "op", "opcode", 0), (5, "na", "NA", 0), (5, "r5", "Xc", 2), (5, "r5", "Xptr", 3), (3, "ui", "lenw", 4), (2, "ui", "mode", 5), (5, "r5", "Xd", 1)],
    "instrans": [(7, "op", "opcode", 0), (5, "r5", "X1", 1), (5, "r5", "X2", 3), (5, "r5", "X3"  , 4), (3, "ui", "perm", 5), (2, "ui", "mode", 6), (5, "r5", "X4", 2)],
}

M3_bitfields = {
    "M3TYPE":   [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 3), (5, "r5", "X1", 4), (5, "r5", "X2", 5), (5, "r5", "Xd", 2)],
    "sendr":    [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 2), (5, "r5", "X1", 3), (5, "r5", "X2", 4), (5, "na", "NA", 0)],
    "sendr3":   [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 2), (5, "r5", "X1", 3), (5, "r5", "X2", 4), (5, "r5", "X3", 5)],
    "sendmr":   [(7, "op", "opcode", 0), (5, "na", "NA", 0), (5, "r5", "Xc", 2), (5, "r5", "X1", 3), (5, "na", "NA", 0), (5, "r5", "Xd", 1)],
    "sendmr2":  [(7, "op", "opcode", 0), (5, "na", "NA", 0), (5, "r5", "Xc", 2), (5, "r5", "X1", 3), (5, "r5", "X2", 4), (5, "r5", "Xd", 1)],
}

M4_bitfields = {
    "M4TYPE":   [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 3), (5, "r5", "Xop", 4), (3, "ui", "imm3", 5), (1, "na", "NA", 0), (1, "ui", "imm1", 6), (5, "r5", "Xd", 2)],
    "sendops":  [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 3), (5, "r5", "Xop", 4), (3, "ui", "lenw", 5), (1, "na", "NA", 0), (1, "ui", "mode", 6), (5, "na", "NA", 0)],
    "sendmops": [(7, "op", "opcode", 0), (5, "r5", "Xe", 1), (5, "r5", "Xc", 3), (5, "r5", "Xop", 4), (3, "ui", "lenw", 5), (1, "na", "NA", 0), (1, "ui", "mode", 6), (5, "r5", "Xd", 2)],
}

E_bitfields = {
    "ETYPE":    [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "sel", 4), (12, "ui", "imm12", 3)],
    "evi":      [(7, "op", "opcode", 0), (5, "r5",   "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "sel", 4), (12, "ui",   "imm", 3)],
    "evii":     [(7, "op", "opcode", 0), (5, "ui", "imm1", 2), (4, "r4", "Xd", 1), (4, "ui", "sel", 4), (12, "ui",  "imm2", 3)],
}

R4_bitfields = {
    "R4TYPE":   [(7, "op", "opcode", 0), (5, "r5", "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "sel", 5), (5, "r5", "Xop1", 3), (5, "r5", "Xop2", 4), (2, "na", "NA", 0)],
    "ev":       [(7, "op", "opcode", 0), (5, "r5", "Xs", 1), (4, "r4", "Xd", 2), (4, "ui", "sel", 5), (5, "r5", "Xop1", 3), (5, "r5", "Xop2", 4), (2, "na", "NA", 0)],
    "cswp":     [(7, "op", "opcode", 0), (5, "r5", "X1", 1), (4, "r4", "X2", 2), (4, "na",  "NA", 0), (5, "r5",   "X3", 3), (5, "r5",   "X4", 4), (2, "na", "NA", 0)],
}

VF_bitfields = {
    "VFTYPE":    [(7, "op", "opcode", 0), (4, "ui", "imma", 1), (1, "na", "NA", 0), (4, "r4", "Xd", 2), (1, "na", "NA", 0), (12, "ui", "immb", 5), (3, "ui", "precision", 0)],
    "vfill.32":  [(7, "op", "opcode", 0), (4, "ui", "imma", 1), (1, "na", "NA", 0), (4, "r4", "Xd", 2), (1, "na", "NA", 0), (12, "ui", "immb", 5), (3, "ui", "precision", 0)],
    "vfill.i32": [(7, "op", "opcode", 0), (4, "si", "imma", 1), (1, "na", "NA", 0), (4, "r4", "Xd", 2), (1, "na", "NA", 0), (12, "ui", "immb", 5), (3, "ui", "precision", 0)],
    "vfill.b16": [(7, "op", "opcode", 0), (4, "ui", "imma", 1), (1, "na", "NA", 0), (4, "r4", "Xd", 2), (1, "na", "NA", 0), (12, "ui", "immb", 5), (3, "ui", "precision", 0)],
}

EventTr_bitfields = {
    "EventTr":   [(8, "si", "attach", 2), (4, "ty", "type", 1), (20, "si", "target", 3)],
    "eventTX":   [(8, "si", "attach", 2), (4, "ty", "type", 1), (20, "si", "target", 3)],
}

EFATr_bitfields = {
    "EFATr":       [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
    "basicTX":     [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
    "majorityTX":  [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
    "defaultTX":   [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
    "epsilonTX":   [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
    "commonTX":    [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
    "flaggedTX":   [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
    "refillTX":    [(8, "si", "attach", 1), (4, "ty", "type", 0), (12, "si", "target", 2), (8, "ui", "signature", 3)],
}
# fmt: on

all_bitfields = {
    **I_bitfields,
    **LI_bitfields,
    **P_bitfields,
    **S_bitfields,
    **R_bitfields,
    **B_bitfields,
    **J_bitfields,
    **M1_bitfields,
    **M2_bitfields,
    **M3_bitfields,
    **M4_bitfields,
    **E_bitfields,
    **R4_bitfields,
    **VF_bitfields,
}


all_trans_bitfields = {
    **EventTr_bitfields,
    **EFATr_bitfields,
}
