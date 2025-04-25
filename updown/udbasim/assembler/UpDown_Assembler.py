# Assembler for UpDown ISA v2
import os, sys
#sys.path.append(f"{os.getcwd()}/efas/")
from EFA_v2 import *
from UpDown_Assembler_helper import *
from isa_encodings import *
import binascii

do_print = False

I_old_opcode_enc = {
    #old names
    "comp_lt":     "0000011",  # 0x03
    "comp_gt":     "0000100",  # 0x04
    "comp_eq":     "0000101",  # 0x05
    "put_2byte_imm":   "0001110",  # 0x0e
    "put_1byte_imm":   "0001111",  # 0x0f
    "yield_terminate":   "0000010",  # 0x02
    "lshift":      "1010000",  # 0x50
    "rshift":      "1010001",  # 0x51
    "lshift_or":    "1010010",  # 0x52
    "rshift_or":    "1010011",  # 0x53
    "lshift_and":   "1010100",  # 0x54
    "rshift_and":   "1010101",  # 0x55
    "arithrshift":     "1010110",  # 0x56
    "hash_sb32": "1010111",  # 0x57
    "hash_sb64": "1011000",  # 0x58
    "hash_lm64":  "1011001",  # 0x59
    "hash_lm":    "1011011",  # 0x5b
    "copy_imm":  "1011100",  # 0x5c
    "mov_sb2reg":   "1011101",  # 0x5d
    "mov_uip2reg":   "1011110",  # 0x5e
    "mov_lm2sb":   "1011111",  # 0x5f
    "set_issue_width":      "1111001",  # 0x79
    "set_state_property":   "1111000",  # 0x78
}
S_old_opcode_enc = {
    #old_names
    "lshift_add_imm": "0100010",  # 0x22
    "lshift_sub_imm": "0100011",  # 0x23
    "rshift_add_imm": "0101000",  # 0x28
    "rshift_sub_imm": "0101111",  # 0x2f
    "lshift_or_imm":  "0100101",  # 0x25
    "rshift_or_imm":  "0100110",  # 0x26
    "lshift_and_imm": "0100111",  # 0x27
    "rshift_and_imm": "0101001",  # 0x29
    "put_bits":  "0101010",  # 0x2a
    "get_bits":  "0101011",  # 0x2b
    "cmpswp_i":   "0101101",  # 0x2d
    "move":   "0100000",  # 0x20   #movlr
    #"move":   "0100001",  # 0x21   #movrl
    "swizzle":    "0101110",  # 0x2e
    "bcopy_opsi": "0100100",  # 0x24
    "mov_lm2reg":   "0100000",  # 0x20   #movlr
    "mov_reg2lm":   "0100001",  # 0x21   #movrl
}
R_old_opcode_enc = {
    #old names
    "andr":    "0110100",  # 0x34
    "orr":     "0110100",  # 0x34
    #"xorr":    "0110100",  # 0x34
    "compreg_lt":    "0110101",  # 0x35
    "compreg_gt":    "0110101",  # 0x35
    "compreg_eq":    "0110101",  # 0x35
    "compare_string":   "0110101",  # 0x35
    "rshift_t":     "0110110",  # 0x36
    "lshift_t":     "0110110",  # 0x36
    "arithrshift_t":    "0110110",  # 0x36
    "copy": "0110111",  # 0x37
    "move_word": "0110001",  # 0x31    #movwlr
    #"move_word": "0110010",  # 0x32    #movwrl
    "bcopy_ops": "0110000",  # 0x30
}
R_old_func_mapping = {
    #old names
    "andr":    "0",  # and
    "orr":     "1",  # or`
    "xorr":    "2",  # xor
    "compreg_lt":    "0",  # clt
    "compreg_gt":    "1",  # cgt
    "compreg_eq":    "2",  # ceq
    "compare_string":   "3",  # cstr
    "rshift_t":     "0",  # sr
    "lshift_t":     "1",  # sl
    "arithrshift_t":    "2",  # sar
    "copy": "0",  # bcpyll
    "move_word": "0",  # 0x31    #movwlr
    #"move_word": "0110010",  # 0x32    #movwrl
    "bcopy_ops": "0",  # bcpyol
}
E_old_opcode_enc = {
    #old names
    "ev_update_1":  "1000000",  # 0x40
    "ev_update_2": "1000001",  # 0x41
}
R4_old_opcode_enc = {
    #old names
    "ev_update_reg_2":   "1110000",  # 0x70
    "cmpswp": "1110001",  # 0x71
}

LI_old_opcode_enc = {
    #old names
    "mov_imm2reg":    "0001000",  # 0x08
}
B_old_opcode_enc = {
    "bnec":  "1000011",  # 0x43
    "beqc":  "1000011",  # 0x43
    "bgtc":  "1000011",  # 0x43
    "blec":  "1000011",  # 0x43
    "bltc":  "1000011",  # 0x43
    "bgec":  "1000011",  # 0x43
}
B_old_func_mapping = {
    "bnec":  "0",
    "beqc":  "1",
    "bgtc":  "2",
    "blec":  "3",
    "bltc":  "4",
    "bgec":  "5",
}
def inbinary2(val):
    if val < 0:
#        val = (val & 0b11) | 0b100
        sys.exit(f"incorrect negative number {val} detected!")
    str = f'{val:2b}'
    str2=str.replace(' ','0')
    if val & 0b11 != val:
        print ("Field's encoding exceeds 2 bits limit!")
        sys.exit()
    return str2
def inbinary3(val):
    if val < 0:
        val = (val & 0b11) | 0b100
    str = f'{val:3b}'
    str2=str.replace(' ','0')
    if val & 0b111 != val:
        print ("Field's encoding exceeds 3 bits limit!")
        sys.exit()
    return str2
def inbinary4(val):
    if val < 0:
        val = (val & 0b111) | 0b1000
    str = f'{val:4b}'
    str2=str.replace(' ','0')
#    print(f'binary of 4bits {val} is {str2}')
    if val & 0b1111 != val:
        print ("Field's encoding exceeds 4 bits limit!")
        sys.exit()
    return str2
def inbinary5(val):
    if val < 0:
        val = (val & 0b1111) | 0b10000
    str = f'{val:5b}'
    str2=str.replace(' ','0')
#    print(f'binary of 5bits {val} is {str2}')
    if val & 0b11111 != val:
        print ("Field's encoding exceeds 5 bits limit!")
        sys.exit()
    return str2
def inbinary8(val):
    if val < 0:
        val = (val & 0b1111111) | 0b10000000
    str = f'{val:8b}'
    str2=str.replace(' ','0')
    if val & 0b11111111 != val:
        print ("Field's encoding exceeds 8 bits limit!")
        sys.exit()
    return str2
def inbinary12(val):
    if val < 0:
        val = (val & 0b11111111111) | 0b100000000000
    str = f'{val:12b}'
    str2=str.replace(' ','0')
#    print(f'binary of 12bits {val} is {str2}')
    if val & 0b111111111111 != val:
        print (f"Field's encoding exceeds 12 bits limit (value: {val})!")
        sys.exit()
    return str2
def inbinary16(val):
    if val < 0:
        val = (val & 0b111111111111111) | 0b1000000000000000
    str = f'{val:16b}'
    str2=str.replace(' ','0')
#    print(f'binary of 16bits {val} is {str2}')
    if val & 0b1111111111111111 != val:
        print ("Field's encoding exceeds 16 bits limit!")
        sys.exit()
    return str2
def inbinary19(val):
    if val < 0:
        sys.exit(f"19 bit immidiate can not be negative")
    str = f'{val:19b}'
    str2=str.replace(' ','0')
    if val & 0b1111111111111111111 != val:
        print ("Field's encoding exceeds 19 bits limit!")
        sys.exit()
    return str2
def inbinary20(val):
    if val < 0:
        sys.exit(f"20 bit immidiate can not be negative")
    str = f'{val:20b}'
    str2=str.replace(' ','0')
    if val & 0b11111111111111111111 != val:
        print ("Field's encoding exceeds 20 bits limit!")
        sys.exit()
    return str2
def inbinary21(val):
    if val < 0:
        val = (val & 0b11111111111111111111) | 0b100000000000000000000
    str = f'{val:21b}'
    str2=str.replace(' ','0')
    if val & 0b111111111111111111111 != val:
        print ("Field's encoding exceeds 21 bits limit!")
        sys.exit()
    return str2
def inbinary25(val):
    if val < 0:
        val = (val & 0b111111111111111111111111) | 0b1000000000000000000000000
    str = f'{val:25b}'
    str2=str.replace(' ','0')
    if val & 0b1111111111111111111111111 != val:
        print ("Field's encoding exceeds 25 bits limit!")
        sys.exit()
    return str2

def encode_I_opcode(name):
    return I_opcode_enc[name]
def encode_LI_opcode(name):
    return LI_opcode_enc[name]
def encode_VF_opcode(name):
    return VF_opcode_enc[name]
def encode_S_opcode(name):
    return S_opcode_enc[name]
def encode_R_opcode(name):
    return R_opcode_enc[name]
def encode_B_opcode(name):
    return B_opcode_enc[name]
def encode_J_opcode(name):
    return J_opcode_enc[name]
def encode_M1_opcode(name):
    return M1_opcode_enc[name]
def encode_M2_opcode(name):
    return M2_opcode_enc[name]
def encode_M3_opcode(name):
    return M3_opcode_enc[name]
def encode_M4_opcode(name):
    return M4_opcode_enc[name]
def encode_E_opcode(name):
    return E_opcode_enc[name]
def encode_R4_opcode(name):
    return R4_opcode_enc[name]
def encode_P_opcode(name):
    return P_opcode_enc[name]


def encode_register(name):
    return register_enc[name]
def encode_transition_type(tr_type):
    return transition_type_enc[tr_type]

def encode_event_target(value):
    return inbinary20(value)

def encode_signature(value):
    return inbinary8(value)
def encode_EFA_tr_target(value):
    return inbinary12(value)
def encode_attach(value):
    return inbinary8(value)
def encode_attach_base(value):
    return inbinary3(value)
def encode_attach_scalar(value):
    return inbinary3(value)
def encode_attach_refill_base(value):
    return inbinary3(value)
def encode_attach_refill_scalar(value):
    return inbinary2(value)
def encode_attach_refill_refill(value):
    return inbinary3(value)
##
# check value ranges?
# handle weird special case for branch bits -- split 9, 3
def encode_immediate16(value):
    return inbinary16(value)
def encode_immediate12(value):
    return inbinary12(value)
def encode_immediate4(value):
    return inbinary4(value)
def encode_immediate5(value):
    return inbinary5(value)
def encode_immediate_LI(value):
    return inbinary21(value)
def encode_immediate_jump(value):
    return inbinary25(value)
def encode_func(name):
    return func_enc[name]
def encode_message_mode(value):
    return inbinary2(int(value))
def encode_len(value):
    return inbinary3(int(value) - 1)
def encode_send_len(value):
    return inbinary3(int(value) - 2)
def encode_perm(value):
    return inbinary3(int(value))
def encode_precision(name):
    return precision_enc[name]
def encode_mask(value):
    return inbinary4(int(value))
#def encode_message_numops(value):
#    return inbinary3(value)
#def encode_event_select(value):
#    return inbinary3(value)
def encode_P_offset(offset):
    return inbinary19(offset)

##
## reserved = {}  encoded as hardwired "0"s
##


#each of this rutines should retuern a string of the right length for each of the subparts, (leading 0's are the tricky parts)
def encode_I_format(python_inst):

    #prepare ssprop for encoding
    if(python_inst.opcode == "set_state_property" or python_inst.opcode == "ssprop"):
        dispatch_type = python_inst.imm
        value = 0
        if dispatch_type == "basic":
            type_name = "BASIC"
        elif dispatch_type == "common":
            type_name = "COMMON"
        elif dispatch_type == "epsilon":
            type_name = "EPSILON"
        elif dispatch_type == "default":
            type_name = "DEFAULT"
            value = int(python_inst.dst)
            python_inst.dst = "X16"      #set to default for encoding
        elif dispatch_type == "majority":
            type_name = "MAJORITY"
            value = int(python_inst.dst)
            python_inst.dst = "X16"      #set to default for encoding
        elif dispatch_type == "flag_default":
            type_name = "FLAG_DEFAULT"
            value = int(python_inst.dst)
            python_inst.dst = "X16"      #set to default for encoding
        elif dispatch_type == "flag_majority":
            type_name = "FLAG_MAJORITY"
            value = int(python_inst.dst)
            python_inst.dst = "X16"      #set to default for encoding
        elif dispatch_type == "flag":
            type_name = "FLAG"
        else:
            sys.exit(f" ssprop type {python_inst.imm} is not supported!")
        python_inst.imm = str( (( value  & 0b111111111111) << 4) | ( state_property_enc[type_name]  & 0b1111) )

    if python_inst.dst not in general_purpose_register_enc and python_inst.dst != UNUSED_reg and python_inst.dst != 'NWID':
        sys.exit(f"I type instruction only allow X16-X31 as the destination!. The destination is {python_inst.dst}!")


    if(python_inst.opcode == "move_lm2sb" or python_inst.opcode == "movlsb"):
        return ["0000000000000000",
                "0000",
                encode_register(python_inst.src),
                encode_I_opcode(python_inst.opcode)
               ]
    else:
        return [encode_immediate16(int(python_inst.imm)),
                encode_register(python_inst.dst)[1:],
                encode_register(python_inst.src),
                encode_I_opcode(python_inst.opcode)
               ]

def encode_LI_format(python_inst):
    return [encode_immediate_LI(int(python_inst.imm)),
            encode_register(python_inst.dst)[1:],
            encode_LI_opcode(python_inst.opcode)
            ]

def encode_VF_format(python_inst):
    precision =  (python_inst.opcode.split('.'))[1]
    if precision == "32" or precision == "b16":
        immidiate = float(python_inst.imm)
        s = struct.pack('<f', immidiate)
        immidiate = struct.unpack('<l', s)[0]
        #immidiate holds the integer form of the b16
        immidiate = (immidiate >> 16) & 0x000000000000FFFF  #>>16 to convert from fp32 to b16
    elif precision == "i32":
        immidiate = int(python_inst.imm)
    else:
        sys.exit("incorrect precision {precision} defined for {python_inst.opcode} instruction!")
    if python_inst.dst not in general_purpose_register_enc:
        sys.exit(f"VF type instruction only allow X16-X31 as the destination!")
    return [encode_precision(precision),
            encode_immediate16(immidiate)[:12],
            "0",
            encode_register(python_inst.dst)[1:],
            "0",
            encode_immediate16(immidiate)[-4:],
            encode_VF_opcode(python_inst.opcode)
           ]

def encode_R_format(python_inst):
    if (len(python_inst.opcode.split('.')) >1 ):
        return [
            encode_precision(python_inst.precision),
            encode_func(name_func_mapping[python_inst.opcode]),
            encode_immediate4(int(python_inst.mask)),
            encode_register(python_inst.rt),
            encode_register(python_inst.dst),
            encode_register(python_inst.src),
            encode_R_opcode(python_inst.opcode)
        ]
    elif (python_inst.opcode == "move_word" or python_inst.opcode == "movwlr" or python_inst.opcode == "movwrl"):
        if python_inst.lm_mode == 'ld' or python_inst.lm_mode == 'st' :
            inc_bit = "0"
            return [
                "000",
                encode_func(name_func_mapping[python_inst.opcode]),
                inc_bit,
                inbinary3((int(python_inst.imm))),
                encode_register(python_inst.rt),
                encode_register(python_inst.dst),
                encode_register(python_inst.src),
                encode_R_opcode(python_inst.opcode)
            ]
        elif python_inst.lm_mode == 'ld_inc' or python_inst.lm_mode == 'st_inc' :
            inc_bit = "1"
            return [
                "000",
                encode_func(name_func_mapping[python_inst.opcode]),
                inc_bit,
                inbinary3((int(python_inst.imm))),
                encode_register(python_inst.rt),
                encode_register(python_inst.dst),
                encode_register(python_inst.src),
                encode_R_opcode(python_inst.opcode)
            ]
    else:
        return [
            "000",
            encode_func(name_func_mapping[python_inst.opcode]),
            "0000",
            encode_register(python_inst.rt),
            encode_register(python_inst.dst),
            encode_register(python_inst.src),
            encode_R_opcode(python_inst.opcode)
        ]

def encode_S_format(python_inst):
    if python_inst.dst not in general_purpose_register_enc:
        sys.exit(f"dst is {python_inst.dst} S type instruction only allow X16-X31 as the destination!")
    if python_inst.opcode == "move" or python_inst.opcode == "movlr" or python_inst.opcode == "movrl":
        if len(python_inst.lm_mode) > 2 :
            inc_bit = "1"
        else:
            inc_bit = "0"
        return [encode_immediate12(int(python_inst.imm2)),
            inc_bit,
            inbinary3((int(python_inst.imm) - 1)),
            encode_register(python_inst.dst)[1:],
            encode_register(python_inst.src),
            encode_S_opcode(python_inst.opcode)
        ]
    elif python_inst.opcode == "cmpswp_i" or python_inst.opcode == "cswpi":
        #imm2 only occupies 4 bits but its signed
        return ["00000000",
            encode_immediate4(int(python_inst.imm2)),
            encode_immediate4(int(python_inst.imm)),
            encode_register(python_inst.dst)[1:],
            encode_register(python_inst.src),
            encode_S_opcode(python_inst.opcode)
        ]
    else:
        return [encode_immediate12(int(python_inst.imm2)),
            encode_immediate4(int(python_inst.imm)),
            encode_register(python_inst.dst)[1:],
            encode_register(python_inst.src),
            encode_S_opcode(python_inst.opcode)
        ]
def encode_B_format(python_inst, target_symbols, shared_blocks,seqnum):
    #TODO: account for shared blocks
    #if (python_inst.dst not in target_symbols) and (python_inst.dst not in shared_blocks):
    if (python_inst.dst not in target_symbols): #and (python_inst.dst not in shared_blocks):
        sys.exit(f"B instruction target {python_inst.dst} is not marked in the corresponding action block or is not a shared block!")
    if python_inst.dst in target_symbols:
        target = encode_immediate12((target_symbols[python_inst.dst] - seqnum)<<2)
    else:
        target = encode_immediate12(shared_blocks[python_inst.dst])     #TODO: make this an offset instead of the direct address and put it back in here
    main_opcode = python_inst.funct
    if main_opcode == "bne" or main_opcode == "beq" or main_opcode == "bgt" or main_opcode == "ble" or main_opcode == "bneu" or main_opcode == "bequ" or main_opcode == "bgtu" or main_opcode == "bleu":
        return [target[0:3],
            encode_func(name_func_mapping[main_opcode]),
            target[3:12],
            encode_register(python_inst.op2),
            encode_register(python_inst.op1),
            encode_B_opcode(main_opcode)
            ]
    else:
        return [target[0:3],
            encode_func(name_func_mapping[main_opcode]),
            target[3:12],
            encode_immediate5(int(python_inst.op2)),
            encode_register(python_inst.op1),
            encode_B_opcode(main_opcode)
           ]

def encode_J_format(python_inst, target_symbols,shared_blocks,seqnum):
    #TODO: account for shared blocks
    if python_inst.dst not in target_symbols:
        sys.exit(f"J instruction target {python_inst.dst} is not marked in the corresponding action block!")
    target = encode_immediate_jump((target_symbols[python_inst.dst] - seqnum)<<2)
    return [
        target,
        encode_J_opcode(python_inst.opcode)
    ]

def encode_M1_format(python_inst):
    if (python_inst.addr_mode != "1" and python_inst.addr_mode != "0"):
        sys.exit(f"incorrect mode {python_inst.addr_mode} detected for M1 instr!")
    return["00000", python_inst.addr_mode, "0",
           encode_send_len(python_inst.op2),
           #encode_len(python_inst.op2),
           encode_register(python_inst.op1),
           encode_register(python_inst.cont),
           encode_register(python_inst.event),
           encode_M1_opcode(python_inst.opcode)
    ]

def encode_M2_format(python_inst):
    if python_inst.opcode == "instrans":
        return[encode_register(python_inst.op4),
                encode_message_mode(python_inst.mode), 
                encode_perm(python_inst.size),
                encode_register(python_inst.op3),
                encode_register(python_inst.op2),
                encode_register(python_inst.op1),
                encode_M2_opcode(python_inst.opcode)
            ]
    else:
        return[encode_register(python_inst.dst),
                encode_message_mode(python_inst.addr_mode), 
                encode_len(python_inst.op2),
                encode_register(python_inst.op1),
                encode_register(python_inst.cont),
                "00000",
                encode_M2_opcode(python_inst.opcode)
            ]

def encode_M3_format(python_inst):
    # if python_inst.op2 not in general_purpose_register_enc:
    #     sys.exit(f"M3 type instruction only allow X16-X31 as the Xptr!")
    # if (python_inst.addr_mode != "1" and python_inst.addr_mode != "0"):
    #     sys.exit(f"incorrect mode {python_inst.addr_mode} detected for M3 instr!")
    if python_inst.opcode == "sendr":
        return["00000",
               encode_register(python_inst.op2),
               encode_register(python_inst.op1),
               encode_register(python_inst.cont),
               encode_register(python_inst.event),
               encode_M3_opcode(python_inst.opcode)  
        ]
    elif python_inst.opcode == "sendr3":
        return[encode_register(python_inst.op3),
               encode_register(python_inst.op2),
               encode_register(python_inst.op1),
               encode_register(python_inst.cont),
               encode_register(python_inst.event),
               encode_M3_opcode(python_inst.opcode)  
        ]
    elif python_inst.opcode == "sendmr":
        return[encode_register(python_inst.dst),
               "00000",
               encode_register(python_inst.op1),
               encode_register(python_inst.cont),
               "00000",
               encode_M3_opcode(python_inst.opcode)  
        ]
    elif python_inst.opcode == "sendmr2":
        return[encode_register(python_inst.dst),
               encode_register(python_inst.op2),
               encode_register(python_inst.op1),
               encode_register(python_inst.cont),
               "00000",
               encode_M3_opcode(python_inst.opcode)  
        ]
    else:
        sys.exit(f"incorrect opcode {python_inst.opcode} detected for M3 instr!")

def encode_M4_format(python_inst):
    if python_inst.opcode == "sendops":
        if (python_inst.addr_mode != "1" and python_inst.addr_mode != "0"):
            sys.exit(f"incorrect mode {python_inst.addr_mode} detected for M4(sendops) instr!")
        return["00000", python_inst.addr_mode, "0",
                encode_send_len(python_inst.op2),
                #encode_len(python_inst.op2),
                encode_register(python_inst.op1),
                encode_register(python_inst.cont),
                encode_register(python_inst.event),
                encode_M4_opcode(python_inst.opcode)
        ]
    elif python_inst.opcode == "sendmops":
        return[encode_register(python_inst.dst),
               python_inst.addr_mode,"0",
               encode_len(python_inst.op2),
               encode_register(python_inst.op1),
               encode_register(python_inst.cont),
               "00000",
               encode_M4_opcode(python_inst.opcode)
        ]
    else:
        sys.exit(f"incorrect M4 opcode {python_inst.opcode}!")


##
## unclear about the Xs/imm encoding; clarify and fix
##
def encode_E_format(python_inst):
    if python_inst.dst not in general_purpose_register_enc:
        sys.exit(f"E type instruction only allow X16-X31 as the destination!")
    if python_inst.opcode == "evi":
        return[encode_immediate12(int(python_inst.imm)),
                encode_mask(python_inst.imm2),
                encode_register(python_inst.dst)[1:],
                encode_register(python_inst.src),
                encode_E_opcode(python_inst.opcode)
            ]

def encode_R4_format(python_inst):
    if python_inst.dst not in general_purpose_register_enc:
        sys.exit(f"R4 type instruction only allow X16-X31 as the Xptr!")
    if python_inst.opcode == "cmpswp" or python_inst.opcode == "cswp":
        return ["00",
                encode_register(python_inst.op2),
                encode_register(python_inst.op1),
                "0000",
                encode_register(python_inst.dst)[1:],
                encode_register(python_inst.src),
                encode_R4_opcode(python_inst.opcode)
                ]
    elif python_inst.opcode == "ev" or python_inst.opcode == "ev_update_reg_2":
       # if (int(python_inst.imm) & 0b0001) == 1:
       #     sys.exit(f"linkable module input should have been used to resolve the event label!") #TODO:check the type of the input
        return ["00",
                encode_register(python_inst.op2),
                encode_register(python_inst.op1),
                encode_mask(python_inst.imm),
                encode_register(python_inst.dst)[1:],
                encode_register(python_inst.src),
                encode_R4_opcode(python_inst.opcode)
                ]
    else:
        sys.exit(f"incorrect R4 opcode {python_inst.opcode}!")

def encode_P_format(python_inst):
    return["000",
           encode_func(name_func_mapping[python_inst.opcode]), 
           encode_P_offset(python_inst.print_id),
           encode_P_opcode(python_inst.opcode)
    ]

def string_to_bin(input):
    hex_str = binascii.hexlify(input.encode())
    bin_str = bin(int(hex_str, 16))[2:].zfill(32 * ((len(hex_str) + 7) // 8))
    return str(bin_str)

def encode_P_content(python_inst):
    bin_fmtstr = ""
    bin_reglist = ""
    fmtstr = python_inst.fmtstr
    reglist = ""
    if len(fmtstr) != 0:
        bin_fmtstr = string_to_bin(fmtstr)

    if python_inst.opcode == "perflog":
        reglist += str(python_inst.mode)
        reglist += ";"
        reglist += str(python_inst.msg_id)
        reglist += ";"
        if python_inst.mode == 0 or python_inst.mode == 2 or python_inst == 0:
            for pp in python_inst.payload_list:
                reglist += pp
                reglist += ","
            if len(python_inst.payload_list) != 0:
                reglist = reglist[:-1]
            reglist += ";"
    for i, reg in enumerate(python_inst.reglist):
        if i > 0:
            reglist += ","
        reglist += reg
    if len(reglist) != 0:
        bin_reglist = string_to_bin(reglist)

    # print(fmtstr, len(bin_fmtstr) // 8, bin_fmtstr)
    # print(reglist, len(bin_reglist) // 8, bin_reglist)

    return [
            bin_reglist,
            bin_fmtstr,
            "{:032b}".format(len(bin_reglist) // 8),
            "{:032b}".format(len(bin_fmtstr) // 8),
    ]

def change2newISA(action, opcode_enc, old_opcode_enc):
    assigned_label = old_opcode_enc[action.opcode]
    for opcode in opcode_enc:
        if opcode_enc[opcode] == assigned_label:
            new_opcode = opcode
    if action.opcode == "move":
        if action.lm_mode[:2] == "st":
            new_opcode = "movrl"
        elif action.lm_mode[:2] == "ld":
            new_opcode = "movlr"
    #TODO: support floating point and vector inst differently
    action.opcode = new_opcode
    return action

def change2newISA_withfunc(action, opcode_enc, old_opcode_enc, old_func_mapping):
    assigned_label = old_opcode_enc[action.opcode]
    func_label = old_func_mapping[action.opcode]

    for opcode in opcode_enc:
        if opcode_enc[opcode] == assigned_label and name_func_mapping[opcode] == func_label:
            new_opcode = opcode
    if action.opcode == "move":
        if action.lm_mode[:2] == "st":
            new_opcode = "movrl"
        elif action.lm_mode[:2] == "ld":
            new_opcode = "movlr"
    #TODO: support floating point and vector inst differently
    action.opcode = new_opcode
    action.func = func_label
    return action

# Program memory image is a dictionary with a set of keys (start addresses), each of which 
# has a list of 32-bit words in binary format.  The regions indicated by each key are presumed
# to be non-overlapping
#

class program_memory_image:
    def __init__(self):
        self.prog = dict();
        self.symbols = dict();   # map for all event labels and transitions (partially resolved tables from the linker - arbitrary locations)
        self.data = [];      # map for all data labels

myprogram = program_memory_image()

def globalprog():
    global myprogram 
    myprogram = program_memory_image()
# ----------------------------------------------------------------- Assembler implementation  -----------------------------------------
def encode_action(action, target_symbols, shared_Blocks,seqnum, do_print = False):
    if (action.opcode in I_old_opcode_enc or action.opcode in S_old_opcode_enc or action.opcode in R_old_opcode_enc or 
            action.opcode in R4_old_opcode_enc or action.opcode in E_old_opcode_enc or action.opcode in LI_old_opcode_enc or action.opcode in B_old_opcode_enc):
        if (action.opcode in I_old_opcode_enc):
            action = change2newISA(action, I_opcode_enc, I_old_opcode_enc)
        elif  (action.opcode in S_old_opcode_enc):
            action = change2newISA(action, S_opcode_enc, S_old_opcode_enc)
        elif  (action.opcode in R_old_opcode_enc):
            #action = change2newISA(action, R_opcode_enc, R_old_opcode_enc)
            action = change2newISA_withfunc(action, R_opcode_enc, R_old_opcode_enc, R_old_func_mapping)
        elif  (action.opcode in R4_old_opcode_enc):
            action = change2newISA(action, R4_opcode_enc, R4_old_opcode_enc)
        elif  (action.opcode in E_old_opcode_enc):
            action = change2newISA(action, E_opcode_enc, E_old_opcode_enc)
        elif  (action.opcode in LI_old_opcode_enc):
            action = change2newISA(action, LI_opcode_enc, LI_old_opcode_enc)
        elif  (action.opcode in B_old_opcode_enc):
            #action = change2newISA(action, B_opcode_enc, B_old_opcode_enc)
            action = change2newISA_withfunc(action, B_opcode_enc, B_old_opcode_enc, B_old_func_mapping)
    if (action.opcode in I_opcode_enc):
        print (f"I OPCODE {action.opcode}")   if do_print else None
        return encode_I_format(action), None
    elif (action.opcode in LI_opcode_enc):
        print (f"LI OPCODE {action.opcode}")  if do_print else None
        return encode_LI_format(action), None
    elif (action.opcode in VF_opcode_enc):
        print (f"VF OPCODE {action.opcode}")  if do_print else None
        return encode_VF_format(action), None
    elif (action.opcode in S_opcode_enc):
        print (f"S OPCODE {action.opcode}")  if do_print else None
        return encode_S_format(action), None
    elif (action.opcode in R_opcode_enc):
        print (f"R OPCODE {action.opcode}")  if do_print else None
        return encode_R_format(action), None
    elif (action.opcode in M1_opcode_enc):
        print (f"M1 OPCODE {action.opcode}")  if do_print else None
        return encode_M1_format(action), None
    elif (action.opcode in M2_opcode_enc):
        print (f"M2 OPCODE {action.opcode}")  if do_print else None
        return encode_M2_format(action), None
    elif (action.opcode in M3_opcode_enc):
        print (f"M3 OPCODE {action.opcode}")  if do_print else None
        return encode_M3_format(action), None
    elif (action.opcode in M4_opcode_enc):
        print (f"M4 OPCODE {action.opcode}")  if do_print else None
        return encode_M4_format(action), None
    elif (action.opcode in R4_opcode_enc):
        print (f"R4 OPCODE {action.opcode}")  if do_print else None
        return encode_R4_format(action), None
    elif (action.opcode in E_opcode_enc):
        print (f"E OPCODE {action.opcode}")  if do_print else None
        return encode_E_format(action), None
    elif (action.opcode == "branch" and action.funct in B_opcode_enc):
        print (f"B OPCODE {action.funct}")  if do_print else None
        return encode_B_format(action, target_symbols, shared_Blocks,seqnum), None
    elif (action.opcode in J_opcode_enc):
        print (f"J OPCODE {action.opcode}")  if do_print else None
        return encode_J_format(action, target_symbols, shared_Blocks,seqnum), None
    elif (action.opcode in P_opcode_enc):
        print (f"P OPCODE {action.opcode}")  if do_print else None
        print (action.fmtstr) if do_print else None
        return encode_P_format(action), [action.print_id, encode_P_content(action)]
    #elif (action.opcode in P_opcode_enc):
    #    print ("PRINT")  if do_print else None
    else:
        if action.opcode == "branch":
            print (f"instruction {action.opcode} {action.funct} not implemented in assembler")
        else:
            sys.exit(f"instruction {action.opcode} not implemented in assembler")
    return None, None

def get_efa_base(efa_counter):
    efa_base = efa_counter << 14
    return efa_base

def get_next_inst_addr(address):
    address = address + 4
    return address

def resolve_event_label(tr, offset):
    if tr.label not in myprogram.symbols:
        myprogram.symbols[tr.label] = offset
    else:
        sys.exit(f"event label {tr.label} used multiple times!")
    return None

def get_event_label(label):
    #print(f"label is {label}")
    if label in myprogram.symbols:
        return myprogram.symbols[label]
    else:
        sys.exit(f"event label {label} is not resolved!")


#flagCarry_with_action
#commonCarry_with_action
#majority
#basic_with_action
def encode_event_instr(tr,allstates_symbols):
    if tr.anno_type == 'eventCarry' or tr.anno_type == 'eventCarry_with_action': 
        return["00000000000000000000",
        encode_transition_type(tr.anno_type),
        "00000001"] #attach: 1 since the actions start right after the event transition
    elif tr.anno_type == 'commonCarry' or tr.anno_type == 'commonCarry_with_action' \
            or tr.anno_type == 'basic' or tr.anno_type == 'basic_with_action' \
            or tr.anno_type == 'flagCarry' or tr.anno_type == 'flagCarry_with_action' \
            or tr.anno_type == 'majorityCarry' or tr.anno_type == 'defaultCarry' \
            or tr.anno_type == 'flagmajorityCarry' or tr.anno_type == 'flagdefaultCarry' \
            or tr.anno_type == 'refill' or tr.anno_type == 'refill_with_action' \
            or tr.anno_type == 'epsilonCarry' or tr.anno_type == 'epsilonCarry_with_action' \
            or tr.anno_type == 'event':    
        return[encode_event_target(allstates_symbols[tr.dst.state_id]),
        encode_transition_type(tr.anno_type),
        "00000001"]
    else:
        #TODO: write the encoding of rest of instructions
        sys.exit(f"Transition type {tr.anno_type} not supported yet!")
    return None


def resolve_branch_targets(actions):
    target_pointer = -1 #targets are relative to the beginning of action block
    target_symbols = dict();
    for action in actions:
        target_pointer = target_pointer + 1
        if (action.label is not None) and (action.label!= ""):
            if action.label not in target_symbols:
                target_symbols[action.label] = target_pointer
            else:
                sys.exit(f"duplicated label {action.label} within action block!")
    return target_symbols

def encode_event_tr(tr, address,allstates_symbols, do_print = False ):
    l = []
    l.append(pack(encode_event_instr(tr, allstates_symbols)))
    ####---------change the action block if evi/evlb replacement is necessary---------
    ####tr = update_event_labels(tr, myprogram)
    #---------encode the (possibly with additional) actions---------
    #store the targets of branch within the action block
    target_symbols = resolve_branch_targets(tr.actions)
    l = encode_action_block(tr.actions, l, do_print, None)
    myprogram.prog[address] = l
    return None

def encode_action_block(actions, l, do_print, shared_blocks):
    #store the targets of branch within the action block
    target_symbols = resolve_branch_targets(actions)
    #print(f"targets table: {target_symbols}")
    seqnum = -1
    for action in actions:
        seqnum += 1
        result, c = encode_action(action,target_symbols, shared_blocks, seqnum, do_print)
        if result is None:
            continue
        l.append(pack(result))    #this needs additional sharedB_target_symbols input for EFAs
        if c is not None:
            c[1] = pack_print(c[1])
            myprogram.data.append([len(c[1]) // 8, c[0], c[1]])
    return l

def createDir(outfile):
    outDir = os.path.dirname(outfile)
    if not os.path.exists(outDir):
        os.makedirs(outDir)

def generate_binaryfile(efa, outfile, link_top_bin):
    do_print_bin = False
    print_counter().reset_counter()

    myprogram.data = [(a, c) for a, _, c in sorted(myprogram.data, key=lambda x: x[1])]

    createDir(outfile)
    binary_file = open(outfile, "wb")
    # offset from the beginning of the file to the start of the event list
    offset0 = 5 * 8

    # offset from the beginning of the file to the start of the instructions
    offset1 = offset0
    if link_top_bin:
        offset1 += 4 + 4 * 2 * len(myprogram.symbols)

    # offset from the beginning of the file to the start of the strings
    offset2 = offset1
    for key in myprogram.prog:
        offset2 += 8 * 2 + 4 * len(myprogram.prog[key])

    # offset from the beginning of the file to the start of the event label list
    offset3 = offset2
    for lengthOfString, _ in myprogram.data:
        offset3 += 4 + lengthOfString

    # offset from the beginning of the file to the first free address after the event list
    offset4 = offset3 + 4
    for key, value in efa.names.items():
        offset4 += 4 + 4 + len(value)

    binary_file.write(offset0.to_bytes(8, 'little'))
    print(offset0, " + ", offset0.to_bytes(8, 'little')) if do_print_bin else None
    binary_file.write(offset1.to_bytes(8, 'little'))
    print(offset1, " + ", offset1.to_bytes(8, 'little')) if do_print_bin else None
    binary_file.write(offset2.to_bytes(8, 'little'))
    print(offset2, " + ", offset2.to_bytes(8, 'little')) if do_print_bin else None
    binary_file.write(offset3.to_bytes(8, 'little'))
    print(offset3, " + ", offset3.to_bytes(8, 'little')) if do_print_bin else None
    binary_file.write(offset4.to_bytes(8, 'little'))
    print(offset4, " + ", offset4.to_bytes(8, 'little')) if do_print_bin else None

    if link_top_bin:
        binary_file.write(len(myprogram.symbols).to_bytes(4, 'little'))  # number of event labels
        print(len(myprogram.symbols), " - ", len(myprogram.symbols).to_bytes(4, 'little')) if do_print_bin else None
        for key in myprogram.symbols:
            print(f"event label: {key} resolved: {myprogram.symbols[key]}") if do_print else None
            binary_file.write((key).to_bytes(4, 'little'))
            print(key, " -- ", (key).to_bytes(4, 'little')) if do_print_bin else None
            binary_file.write((myprogram.symbols[key]).to_bytes(4, 'little'))
            print(myprogram.symbols[key], " --- ", (myprogram.symbols[key]).to_bytes(4, 'little')) if do_print_bin else None

    for key in myprogram.prog:
        print(f"address: {key} and size: {len(myprogram.prog[key])}") if do_print else None
        binary_file.write((key).to_bytes(8, 'little'))  # address of the instructions block
        print(key, " = ", (key).to_bytes(8, 'little')) if do_print_bin else None
        binary_file.write(len(myprogram.prog[key]).to_bytes(8, 'little'))  # numnber of instructions
        print(len(myprogram.prog[key]), " == ", len(myprogram.prog[key]).to_bytes(8, 'little')) if do_print_bin else None
        # print(f"key {key}")
        counter = 0
        for instr in myprogram.prog[key]:
            counter += 1
            int_instr = int(instr, 2)
            print(f'hex rep: {int_instr:X} binary rep: {int_instr:b}') if do_print else None
            binary_file.write(int_instr.to_bytes(4, 'little'))
            print(int_instr, " === ", int_instr.to_bytes(4, 'little')) if do_print_bin else None

    # compute the addresses in the file for each of the strings and add them to the file
    counter = offset2 + 4 * len(myprogram.data)
    for lengthOfString, _ in myprogram.data:
        binary_file.write((counter).to_bytes(4, 'little'))
        print(counter, " ** ", counter.to_bytes(4, 'little')) if do_print_bin else None
        counter += lengthOfString

    # Adding strings
    for length, data in myprogram.data:
        int_data = int(data, 2)
        binary_file.write(int_data.to_bytes(length, 'little'))
        print(int_data, " *** ", int_data.to_bytes(length, 'little')) if do_print_bin else None

    # number of event labels
    binary_file.write(len(efa.names.items()).to_bytes(4, 'little'))
    print(len(efa.names.items()), " ... ", len(efa.names.items()).to_bytes(4, 'little')) if do_print_bin else None

    # Add label to ID map at the end of the file
    for key, value in efa.names.items():
        id = int(key)
        # Encode ID
        binary_file.write((myprogram.symbols[id]).to_bytes(4, 'little'))
        print((myprogram.symbols[id]), " = ", (myprogram.symbols[id]).to_bytes(4, 'little')) if do_print_bin else None
        # Encode offset equal to the event name string length (in bytes)
        binary_file.write(len(value).to_bytes(4, 'little'))
        print(len(value), " = ", (len(value)).to_bytes(4, 'little')) if do_print_bin else None
        # Encode event name
        enc_val = value.encode('ascii')
        binary_file.write(enc_val)
        print(value, " = ", enc_val) if do_print_bin else None
    binary_file.close()
    return None

def encode_EFAstate_trs(state, incomings, allstates_symbols, manager):
    state_type = identify_carried_dispatch_type(incomings[state.state_id][0])
    if state_type == "basic" or state_type == "flag" or state_type == "majority" or state_type == "flagmajority" or state_type == "default" or state_type == "flagdefault":
        base = get_baseINattach(state)
        base_tx_count = 2** (base+1)
        if (get_max_action_count(state,True) != 0):
            scalar = get_scalarINattach(state)
            scalar_action_count = 2**scalar
        else:
            scalar = 0
            scalar_action_count = 0
        print(f"{state_type} state{state.state_id}[addr:{allstates_symbols[state.state_id]}] ==>  base={base} base_tx_count={base_tx_count} scalar={scalar} scalar_action_count={scalar_action_count}")    if do_print else None
        # ---- encode tx block ------
        for label in range (base_tx_count):
            if len(state.get_tran_byLabel(label))>0 and (state.get_tran_byLabel(label))[0].name[:1] in {"9","8","7","6","5","4","3","2","1","0"}:
                print (f"TX ENCODING -------- tr [{label}]->(dst:{(state.get_tran_byLabel(label))[0].dst.state_id}) -------- addr:{allstates_symbols[state.state_id]+(label<<2)}") if do_print else None 
                manager.set_memory( (allstates_symbols[state.state_id]>>2) + label, pack(encode_EFA_transition_instr(state.get_tran_byLabel(label)[0], state_type, label, allstates_symbols, base, scalar)))
        if state_type == "majority" or state_type == "flagmajority" or state_type == "default" or state_type == "flagdefault":
            majdef_tr = get_majdef_tx(state)
            print(f"TX ENCODING -------- state {state.state_id} maj/def tx name {majdef_tr.name} label: {majdef_tr.label}, tx_addr = {allstates_symbols[state.state_id]+(majdef_tr.label<<2)}") if do_print else None
            manager.set_memory( (allstates_symbols[state.state_id]>>2) + (majdef_tr.label) , pack(encode_EFA_transition_instr( majdef_tr, state_type, 0, allstates_symbols, 0, 0)))


        
    elif state_type == "common" or state_type == "epsilon":
        manager.set_memory( (allstates_symbols[state.state_id]>>2),pack(encode_EFA_transition_instr(state.trans[0], state_type, 0, allstates_symbols, 0, 0)) )
        if len(state.trans) > 1:
            sys.exit(f"{state_type} state {state.state_id} has more than 1 transition!")
    else:
        sys.exit("state type {state_type} is not supported!")
    return

def encode_EFA_transition_instr(tr, state_type, label, allstates_symbols, base, scalar):
    if state_type == "basic" or state_type == "flag" or state_type == "majority" or state_type == "flagmajority" or state_type == "default" or state_type == "flagdefault":
        if (tr.name[:1] not in {"9","8","7","6","5","4","3","2","1","0"}):  #maj or default transiotion
            if tr.anno_type[:4] == "majority"[:4] or tr.anno_type[:4] == "default"[:4] or tr.anno_type[:5] == "flagdefault"[:5] or tr.anno_type[:5] == "flagmajority"[:5]:
                attach = encode_attach(get_majdef_tx(tr.dst).label) #these transition annotations should not have actions
            else:
                attach = "00000001"         #for simplicity we filled the majority actions right after the transition
            return["00000000",
                    encode_EFA_tr_target((allstates_symbols[tr.dst.state_id]>>2) & 0xFFF),
                    encode_transition_type(tr.anno_type),
                    attach] 
        elif tr.anno_type[:4] == "refill"[:4]:
            if len(tr.anno_type.split('_')) > 1:
                return[encode_signature(label),
                encode_EFA_tr_target((allstates_symbols[tr.dst.state_id]>>2) & 0xFFF),
                encode_transition_type(tr.anno_type),
                encode_attach_refill_refill(tr.refill_val), #refill
                encode_attach_refill_base(base),
                encode_attach_refill_scalar(scalar)]
            else: #no action
                return[encode_signature(label),
                encode_EFA_tr_target((allstates_symbols[tr.dst.state_id]>>2) & 0xFFF),
                encode_transition_type(tr.anno_type),
                encode_attach_refill_refill(tr.refill_val), #refill
                "00000"]
        else:
            if len(tr.anno_type.split('_')) > 1:
                return[encode_signature(label),
                encode_EFA_tr_target((allstates_symbols[tr.dst.state_id]>>2) & 0xFFF),
                encode_transition_type(tr.anno_type),
                "11", #mode
                encode_attach_base(base),
                encode_attach_scalar(scalar)]
            else: #no action
                if tr.anno_type[:4] == "majority"[:4] or tr.anno_type[:4] == "default"[:4] or tr.anno_type[:5] == "flagdefault"[:5] or tr.anno_type[:5] == "flagmajority"[:5]:
                    attach = encode_attach(get_majdef_tx(tr.dst).label)
                else:
                    attach = "00000000"
                return[encode_signature(label),
                encode_EFA_tr_target((allstates_symbols[tr.dst.state_id]>>2) & 0xFFF),
                encode_transition_type(tr.anno_type),
                attach]
    elif state_type == "common" or state_type == "epsilon":
        if len(tr.anno_type.split('_')) > 1:
            return["00000000",
            encode_EFA_tr_target((allstates_symbols[tr.dst.state_id]>>2) & 0xFFF),
            encode_transition_type(tr.anno_type),
            "00", #mode
            "000001"]
        else: #no action
            if tr.anno_type[:4] == "majority"[:4] or tr.anno_type[:4] == "default"[:4] or tr.anno_type[:5] == "flagdefault"[:5] or tr.anno_type[:5] == "flagmajority"[:5]:
                attach = encode_attach(get_majdef_tx(tr.dst).label)
            else:
                attach = "00000000"
            return["00000000",
            encode_EFA_tr_target((allstates_symbols[tr.dst.state_id]>>2) & 0xFFF),
            encode_transition_type(tr.anno_type),
            attach]
    else:
        sys.exit(f"state type not supported yet")


# TODO: pass a list of EFAs with an init state to this function
#Notes
# Naive method of dealing with large event_label in evii & evi => each of them are considered to take up to two addresses 
#
#
#
def assemble_program(efa, outfile, print_flag, link_top_bin, text_symbol_table_file = None):
    do_print = print_flag
    allstates_symbols = dict()      #used for encoding within EFAs and also by events to transition to EFA states

    #----------------------- resolve instructions
    #change maj/flagmaj/def/flagdef carry transitions with actions
    for tr in [tr for state in efa.states for tr in state.trans if (tr.anno_type[:5] in {"majorityCarry"[:5], "defaultCarry"[:5], "flagmajorityCarry"[:5], "flagdefaultCarry"[:5]})]:
        if(tr.actions):
            change_majoritydefault(tr)
        # NOTE: Next commented paragraph is only for checking feasability of majdef_offset
        # However, at this point measured majdef_offset could be incorrect due to unresolved addresses of other TX and actions (so its commented)
        # Its helpful to move this check to set_state_bitmap() function where the final majdef_offset's are calculated
        '''
        else:
            majdef_offset = calculate_defmaj_offset(tr.dst)
            if majdef_offset > 4095:
                sys.exit(f"Majority or default transition's offset of {tr.dst.state_id} do not fit the 12 bit value!")
            elif majdef_offset > 255:
                if (tr.name[:5] != 'default'[:5]) or (tr.name[:5] != 'flagdefault'[:5]):
                    change_majoritydefault(tr)
                else:
                    sys.exit(f"def/maj value of {tr.dst.state_id} exceed 8 bits! Default transition can not be augmented with ssprop! use epsilon TX after default TX to hold ssprop!")
        '''

    #change psudo and deprecated instructions of all transitions
    for tr in [tr for state in efa.states for tr in state.trans if tr.actions]:
        tr.actions = change_pseudo_instr(tr.actions)
    #change psudo and deprecated instructions of all shared blocks
    for label in efa.sharedBlock:
        efa.sharedBlock[label] = change_pseudo_instr(efa.sharedBlock[label])

    #----------------------- split the program across EFAs and event-driven section -----------------------
    #traverse the state machine and assign each EFA a different color (i.e.ID)
    efa_count = color_EFAs(efa)
    #create a dictionary to map EFA colors to EFA states
    efa_states = make_efa_states_dict(efa)
    #assign EFA color to its corresponding shared blocks 
    color_sharedblocks(efa)
    #check correctness of shared block coloring
    if len(efa.EFA_sharedblocks) != efa_count:
        sys.exit(f"len(efa.EFA_sharedblocks)={len(efa.EFA_sharedblocks)} while efa_count={efa_count} and all encoding programs should at least have one shared block associated to them") 
    #print(f"efa_count is {efa_count}\nefa_states length is {len(efa_states)}")
    print(f"len(efa.EFA_sharedblocks)={len(efa.EFA_sharedblocks)}, len(efa.sharedBlock_state_links)={len(efa.sharedBlock_state_links)}\n\n\n") if do_print else None

    #---------------------------- resolve event labels --------------------------
    incomings = ConstructIncoming(efa)

    #------ skip EFA instruction regions  ----
    if efa_count == 0:
        address = 0
    else:
        #skip EFA instruction region (each EFA has a 14 bit instruction space limit)
        #Note: only EFA states are bound to the 14 bit instruction limit, if a state needs larges that 14 bit address space it should be able to as ling as its stateID is in 14 bit limit
        #this part of assembler should be changed to allow encoding states that need more that 14 bit address restriction for their transitions and actions
        address = get_efa_base(efa_count)
    print(f"=================== resolving event labels starting address {address}=========================") if do_print else None
    #------ create the event label dictionary ----
    for state in efa.states:
        #print(f"---------------------------state {state.state_id}")
        for tr in state.trans:
            #print(f"tr.src.state_id: {tr.src.state_id}, tr.label: {tr.label} actions_size: {len(tr.actions)}")
            if tr.src.state_id == efa.init_state_id[0]: #only event transitions's source state = init state
                resolve_event_label(tr, address)
                action_list = tr.actions
                address += 4    #event transition
                address = allocate_actions_addresses(action_list , address, False)
                #address = assign_event_tr_addresses(tr, address)
    #myprogram.symbols: mapping of program event labels and resolved event labels (i.e. event transition addresses)
    print(f'symbols dictionary: \n {myprogram.symbols}')  if do_print else None
    if text_symbol_table_file != None:
        names = efa.get_name()
        with open(text_symbol_table_file, "w") as f:
            for key, value in myprogram.symbols.items():
                strname = names[key]
                f.write(f"{value} : {hex(value)} : {strname}\n")
    
    #make a dictionary for each EFA to store its shared blocks resolved addresses
    sharedB_symbols_ar = [dict() for _ in range(efa_count)]

    #-------changing the event labels in the actions of the program and shared blocks---- (called after event labels are resolved)
    for state in efa.states:
     #   print(f"---------------------------state {state.state_id}")
        for tr in state.trans:
     #       print(f"tr.src.state_id: {tr.src.state_id}, tr.label: {tr.label} actions_size: {len(tr.actions)}")
            tr.actions = update_event_labels(tr.actions, myprogram)
    #changing the event labels in shared blocks
    efa_counter = 0
    while efa_counter < efa_count:
      #  print(f"---- shared b efa{efa_counter}")
        sharedB_symbols = sharedB_symbols_ar[efa_counter]
        for label in efa.EFA_sharedblocks[efa_counter]:
            efa.sharedBlock[label] =  update_event_labels(efa.sharedBlock[label], myprogram)
        efa_counter += 1

    #----------------------------------------------EffClip implementation ------------------------------------
    #remove the lastact instructions of outgoing transitions of basic or flag states
    #lastact is removed in cases that the lastact dont fall within max_tx_action_count defined using the scalar filed in attach
    for state in [state for efa_id in range(efa_count) for state in efa_states[efa_id]]:
        remove_lastact(state, incomings)

    #bitmap helper data structure (each EFA has a bitmap that shows which instruction sloths are available in its instruction block)
    word_count = 2**12
    manager_ar = [MemoryManager(word_count) for _ in range(efa_count)]

    #-----------------------EFA memory address assignment ------------------------ 
    #for efa in efa_list:   
    #resolve shared blocks address, and update shared block instruction (actions) location in EFA's bitmap
    #for each state resolve it's address and update its instructions (transitions and actions) location in EFA's bitmap 
    efa_counter = 0
    address = 0
    while efa_counter < efa_count:
        print(f"=================== resolving state and shared block addresses of EFA{efa_counter} starting address {address}=========================") if do_print else None
        #----------- assign memory slot to shared blocks ----------
        sharedB_symbols = sharedB_symbols_ar[efa_counter]                #for resolved shared block symbols
        address = get_efa_base(efa_counter)
        print(f"\n------EFA #{efa_counter} base_addr: {address}---------") if do_print else None
        sharedB_symbols, address = assign_sharedblock_addr(efa, address, efa_counter, sharedB_symbols, manager_ar[efa_counter])
        print(f"sharedB_symbols: {sharedB_symbols}") if do_print else None
        address = get_efa_base(efa_counter)     #assigning the state address should be from the very beginning for flag and basic transitions benefit
        #----------- assign memory slot to states (trs and actions) ----------
        assign_efa_state_addr(efa_states[efa_counter], allstates_symbols, address,efa, manager_ar[efa_counter], do_print)
        print(f"allstates_symbols: {allstates_symbols}") if do_print else None

        efa_counter +=1


    #----------------------------------------------Instructions encoding ------------------------------------
    #----------- encode each EFAs ----------
    efa_counter = 0
    while efa_counter < efa_count:
        print(f"=================== encoding EFA {efa_counter}=========================") if do_print else None
        sharedB_symbols = sharedB_symbols_ar[efa_counter]
        manager = manager_ar[efa_counter]
        #------------changing the event labels in EFA and its shared block actions ----------------
        #if evi and evlb instructions are used (WARNING: assembler can not detect the event labels that are updated using movir)
        #for label in efa.EFA_sharedblocks[efa_counter]:
        #    efa.sharedBlock[label] =  update_event_labels(efa.sharedBlock[label], myprogram)
        #for state in efa_states[efa_counter]:
        #    for tr in state.trans:
        #        tr.actions = update_event_labels(tr.actions, myprogram)

        #----------- encode shared blocks ----------
        for label in efa.EFA_sharedblocks[efa_counter]:
            print (f"ENCODING -------- sharedB {label}  -------- addr:{sharedB_symbols[label]}")  if do_print else None
            l = []
            action_list = efa.sharedBlock[label]
            l = encode_action_block(action_list, l, do_print, None)
            sblock_addr = sharedB_symbols[label]
            #myprogram.prog[ sblock_addr ] = l
            for instr in l:
                manager.set_memory(sblock_addr>>2,instr)
                #print(instr)
                #print(sblock_addr)
                sblock_addr += 4

    
        #----------- encode states (trs and actions) ----------
        for state in efa_states[efa_counter]:
            #--------------- encode Transitions ---------------------------
            if len(state.trans) >0:
                print (f"ENCODING    ------------------------------ state {state.state_id}   ------------------------------ addr:{allstates_symbols[state.state_id]}")  if do_print else None
                encode_EFAstate_trs(state,incomings,allstates_symbols,manager)
                address = allstates_symbols[state.state_id]
                #myprogram.prog[address] = l
                #--------------- encode actions ---------------------------
                for tr in state.trans:
                    if len(tr.anno_type.split('_')) > 1:
                        address = get_action_address(state, tr, incomings,allstates_symbols[state.state_id])
                        print (f"ACTION ENCODING -------- action of tr [{tr.label}]->(dst:{tr.dst.state_id}) -------- addr:{address}")  if do_print else None
                        l = []
                        l = encode_action_block(tr.actions, l, do_print, sharedB_symbols)
                        #myprogram.prog[address] = l
                        action_addr = address
                        for instr in l:
                            manager.set_memory(action_addr>>2,instr)
                            #print(instr)
                            #print(action_addr)
                            action_addr += 4
                        #address += len(tr.actions)<<2            #necessary for marking of event placement
            else:
                print(f"state {state.state_id} has no transition to encode!!")   if do_print else None

        #----------- fill in myprogram.prog ----------
        EFA_address = get_efa_base(efa_counter)
        consecutive_blocks = manager.find_consecutive_inst()
        for start, length in consecutive_blocks:
            l=[]
            address = EFA_address + (start <<2)
            for i in range(length):
                l.append(manager.get_memory(start+i))
            myprogram.prog[address] = l

        efa_counter +=1
    print("\n\n\n") if do_print else None
    #-----------------------Events memory placement ------------------------
#naive event tx placement (after the last address used for all other EFAs)
#start traversing all states and txs (and EFAs) from the EFA0.init_state (should lead to accessing all EFAs)
    #states = get_all_states (EFA0.init_state)
    #print(f"efa.init_state_id[0]: {efa.init_state_id[0]}")  if do_print else None
    print(f"=================== encoding events =========================") if do_print else None
    '''
    #------ create the event label dictionary ----
    for state in efa.states:
        for tr in state.trans:
            #print(f"tr.src.state_id: {tr.src.state_id}, tr.label: {tr.label}")
            if tr.src.state_id == efa.init_state_id[0]:
                resolve_event_label(tr, address)
                action_list = tr.actions
                address += 4    #event transition
                address = allocate_actions_addresses(action_list , address)
                #address = assign_event_tr_addresses(tr, address)
    print(f'symbols dictionary: \n {myprogram.symbols}')  if do_print else None
    '''

    #------ event transition and its actions encoding ----
    for state in efa.states:
        for tr in state.trans:
            #print(f"tr.src.state_id: {tr.src.state_id}, tr.label: {tr.label}")
            if tr.src.state_id == efa.init_state_id[0]:
                address = get_event_label(tr.label)
                encode_event_tr(tr, address,allstates_symbols, do_print)
    print(f'instructions dictionary: \n {myprogram.prog}')   if do_print else None

    #-----------------------EFA memory encoding ------------------------ (with resolved event_labels)
    generate_binaryfile(efa, outfile, link_top_bin)
    return None

