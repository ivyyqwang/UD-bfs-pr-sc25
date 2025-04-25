from __future__ import annotations
import isa_encodings as enc
import os
from collections import OrderedDict

inst_categories = [
    (
        "int_arith",
        [
            "addi",
            "subi",
            "muli",
            "divi",
            "modi",
            "add",
            "sub",
            "mul",
            "div",
            "mod",
            "sladdii",
            "slsubii",
            "sraddii",
            "srsubii",
        ],
    ),
    (
        "int_cmp",
        [
            "clti",
            "cgti",
            "ceqi",
            "clt",
            "cgt",
            "ceq",
            "cstr",
        ],
    ),
    (
        "bitwise",
        [
            "sli",
            "sri",
            "slori",
            "srori",
            "slandi",
            "srandi",
            "slorii",
            "srorii",
            "slandii",
            "srandii",
            "sari",
            "sl",
            "sr",
            "sar",
            "andi",
            "and",
            "ori",
            "or",
            "xori",
            "xor",
            "swiz",
        ],
    ),
    (
        "ctrl_flow",
        [
            "bne",
            "beq",
            "bgt",
            "ble",
            "bneu",
            "bequ",
            "bgtu",
            "bleu",
            "bnei",
            "beqi",
            "bgti",
            "blei",
            "blti",
            "bgei",
            "bneiu",
            "beqiu",
            "bgtiu",
            "bleiu",
            "bltiu",
            "bgeiu",
            "jmp",
        ],
    ),
    (
        "msg",
        [
            "send",
            "sendb",
            "sendm",
            "sendmb",
            "sendr",
            "sendr3",
            "sendmr",
            "sendmr2",
            "sendops",
            "sendmops",
            "instrans",
        ],
    ),
    (
        "dat_mov",
        [
            "movil2",
            "movil1",
            "movbil",
            "movblr",
            "bcpyll",
            "bcpylli",
            "movsbr",
            "movrr",
            "movir",
            "movipr",
            "movlsb",
            "movlr",
            "movrl",
            "movwlr",
            "movwrl",
            "bcpyoli",
            "bcpyol",
        ],
    ),
    (
        "tran_ctrl",
        [
            "lastact",
            "ssprop",
            "fstate",
            "siw",
            "refill",
        ],
    ),
    (
        "thread_ctrl",
        [
            "yield",
            "yieldt",
        ],
    ),
    (
        "fp_arith",
        [
            "fmadd.64",
            "fadd.64",
            "fsub.64",
            "fmul.64",
            "fdiv.64",
            "fsqrt.64",
            "fexp.64",
            "fmadd.32",
            "fadd.32",
            "fsub.32",
            "fmul.32",
            "fdiv.32",
            "fsqrt.32",
            "fexp.32",
            "fmadd.b16",
            "fadd.b16",
            "fsub.b16",
            "fmul.b16",
            "fdiv.b16",
            "fsqrt.b16",
            "fexp.b16",
            "fcnvt.64.i64",
            "fcnvt.32.i32",
            "fcnvt.i64.64",
            "fcnvt.i32.32",
            "fcnvt.64.32",
            "fcnvt.64.b16",
            "fcnvt.32.64",
            "fcnvt.32.b16",
            "fcnvt.b16.64",
            "fcnvt.b16.32",
        ],
    ),
    (
        "vec",
        [
            "vmadd.32",
            "vadd.32",
            "vsub.32",
            "vmul.32",
            "vdiv.32",
            "vsqrt.32",
            "vexp.32",
            "vmadd.b16",
            "vadd.b16",
            "vsub.b16",
            "vmul.b16",
            "vdiv.b16",
            "vsqrt.b16",
            "vexp.b16",
            "vmadd.i32",
            "vadd.i32",
            "vsub.i32",
            "vmul.i32",
            "vdiv.i32",
            "vsqrt.i32",
            "vexp.i32",
            "vgt.32",
            "vgt.b16",
            "vgt.i32",
            "vfill.32",
            "vfill.i32",
            "vfill.b16",
        ],
    ),
    (
        "hash",
        [
            "hashsb32",
            "hashsb64",
            "hashl64",
            "hash",
            "hashl",
        ],
    ),
    (
        "ev",
        [
            "evi",
            "evii",
            "ev",
            "evlb",
        ],
    ),
    (
        "atomic",
        [
            "cswp",
            "cswpi",
        ],
    ),
    (
        "debug",
        [
            "print",
            "perflog",
        ],
    ),
]

transitions = [
    "basicTX",
    "majorityTX",
    "defaultTX",
    "epsilonTX",
    "commonTX",
    "flaggedTX",
    "refillTX",
    "eventTX",
]


class EncGen:
    @classmethod
    def gen_bitfields_const(cls, file, bitfields: dict, annotation: str):
        file.write(f"/* {annotation} */\n")
        for inst_name, fields in bitfields.items():
            cur_bit = 0
            for num_bits, field_type, field_name, pos in fields:
                if field_type == "na" or field_type == "op":
                    cur_bit += num_bits
                    continue
                file.write(f"const uint8_t BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT = {cur_bit};\n")
                file.write(f"const uint8_t BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_NBITS = {num_bits};\n")
                file.write(f"const uint32_t BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_MASK = {hex((1 << num_bits) - 1)};\n")
                if field_type == "fc" or field_type == "ui":
                    # unsigned
                    file.write(f"const bool BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SIGNED = {'false'};\n")
                    # file.write(f"inline uint64_t extrInst{inst_name.capitalize()}{field_name.capitalize()}(EncInst inst) {{ return static_cast<uint64_t>(inst) >> BF_{inst_name.upper()}_{field_name.upper()}_SHIFT & BF_{inst_name.upper()}_{field_name.upper()}_MASK; }}\n")
                    file.write(
                        f"inline constexpr uint64_t extrInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst inst) {{ return extrUnsignedImm(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_NBITS); }}\n"
                    )
                    file.write(
                        f"inline constexpr void embdInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst& inst, uint64_t imm) {{ embdUnsignedImm(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_MASK, imm); }}\n"
                    )
                elif field_type == "r5":
                    file.write(f"const bool BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SIGNED = {'false'};\n")
                    file.write(
                        f"inline constexpr RegId extrInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst inst) {{ return extrReg5(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT); }}\n"
                    )
                    file.write(
                        f"inline constexpr void embdInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst& inst, RegId reg) {{ embdReg5(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT, reg); }}\n"
                    )
                elif field_type == "r4":
                    file.write(f"const bool BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SIGNED = {'false'};\n")
                    file.write(
                        f"inline constexpr RegId extrInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst inst) {{ return extrReg4(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT); }}\n"
                    )
                    file.write(
                        f"inline constexpr void embdInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst& inst, RegId reg) {{ embdReg4(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT, reg); }}\n"
                    )
                elif field_type == "si":
                    # signed
                    file.write(f"const bool BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SIGNED = {'true'};\n")
                    # file.write(f"inline int64_t extrInst{inst_name.capitalize()}{field_name.capitalize()}(EncInst inst) {{ return static_cast<int64_t>(inst) << (64 - BF_{inst_name.upper()}_{field_name.upper()}_SHIFT - BF_{inst_name.upper()}_{field_name.upper()}_NBITS) >> (64 - BF_{inst_name.upper()}_{field_name.upper()}_NBITS); }}\n")
                    file.write(
                        f"inline constexpr int64_t extrInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst inst) {{ return extrSignedImm(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_NBITS); }}\n"
                    )
                    file.write(
                        f"inline constexpr void embdInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(EncInst& inst, int64_t imm) {{ embdSignedImm(inst, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_SHIFT, BF_{inst_name.upper().replace('.', '_')}_{field_name.upper()}_MASK, imm); }}\n"
                    )
                file.write("\n")
                cur_bit += num_bits

    # @classmethod
    # def gen_opcodes_const(cls, file opcodes: dict, annotation: str):
    #     file.write(f"/* {annotation} */\n")
    #     for inst_name, opcode_bin_str in opcodes.items():
    #         file.write(f"const uint8_t OP_{inst_name.upper()} = {hex(int(opcode_bin_str, 2))};\n")
    #     file.write("\n")

    @classmethod
    def gen_registers_enum(cls, file, registers: dict, annotation: str = "Register Encodings Enum"):
        file.write(f"/* {annotation} */\n")
        file.write("enum class RegId : uint8_t {\n")
        for reg_name, reg_enc_bin_str in registers.items():
            file.write(f"  {reg_name.upper()} = {int(reg_enc_bin_str, 2)},\n")
        file.write("};\n")
        file.write("\n")
        file.write("inline const char *REG_NAMES[] = {\n")
        for i in range(enc.NUM_REGISTERS):
            file.write(f"  \"{enc.register_enc_rev[i]}\",\n")
        file.write("};\n")
        file.write("\n")

    # @classmethod
    # def gen_registers_map(cls, file, registers: dict, annotation: str = "Register Encodings Map"):
    #     file.write(f"#ifndef __REG_NAMES_MAP__\n#define __REG_NAMES_MAP__\n")
    #     file.write(f"/* {annotation} */\n")
    #     # file.write("#include <unordered_map>\n")
    #     file.write("std::unordered_map<std::string, RegId> REG_NAMES_MAP = {\n")
    #     for reg_name, reg_enc_bin_str in registers.items():
    #         file.write(f"  {{\"{reg_name.upper()}\", RegId::{reg_name.upper()}}},\n")
    #     file.write("};\n#endif // __REG_NAMES_MAP__\n\n")

    @classmethod
    def gen_opcodes_enum(cls, file, opcodes_list: list[dict], annotation_list: list[str]):
        file.write("/* Opcodes Enum */\n")
        file.write("enum class Opcode : uint8_t {\n")
        for opcodes, annotation in zip(opcodes_list, annotation_list):
            file.write(f"  // {annotation}\n")
            for inst_name, inst_enc_bin_str in opcodes.items():
                file.write(f"  {inst_name.upper().replace('.', '_')} = {hex(int(inst_enc_bin_str, 2))},\n")
        file.write("};\n")
        file.write("\n")

    @classmethod
    def gen_state_property_enum(cls, file, state_properties: dict, annotation: str = "State Properties Enum"):
        file.write(f"/* {annotation} */\n")
        file.write("enum class StateProperty : uint8_t {\n")
        for prop_name, prop_num in state_properties.items():
            file.write(f"  {prop_name.upper()} = {prop_num},\n")
        file.write("};\n")
        file.write("\n")
        file.write("inline const char *STATE_PROPERTY_NAMES[] = {\n")
        for i in range(enc.NUM_STATE_PROPERTIES):
            file.write(f"  \"{enc.state_property_enc_rev[i]}\",\n")
        file.write("};\n")
        file.write("\n")

    @classmethod
    def gen_transition_type_enum(cls, file, transition_types: dict, annotation: str = "Transition Types Enum"):
        file.write(f"/* {annotation} */\n")
        file.write("enum class TransitionType : uint8_t {\n")
        for type_name, type_enc_bin_str in transition_types.items():
            file.write(f"  {type_name.upper()} = {int(type_enc_bin_str, 2)},\n")
        file.write("};\n")
        file.write("\n")
        file.write("inline const char *TRANSITION_TYPE_NAMES[] = {\n")
        for i in range(enc.NUM_TRANSITION_TYPES):
            file.write(f"  \"{enc.transition_type_enc_rev[i]}\",\n")
        file.write("};\n")
        file.write("\n")

    @staticmethod
    def reverse_dict(d: dict):
        out = dict()
        for k, v in d.items():
            if v not in out:
                out[v] = [k]
            else:
                out[v].append(k)
        return out

    @classmethod
    def write_prototypes(cls, folderpath: str = "./"):
        all_inst_opcode_rev_dict = cls.reverse_dict(enc.all_opcode_enc)

        for cat, insts in inst_categories:
            with open(os.path.join(folderpath, f"{cat}_inst.hh"), "w") as file:
                file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")
                file.write("#pragma once\n")
                file.write("#include <cstdint>\n")
                file.write("#include <string>\n")
                file.write('#include "encodings.hh"\n')
                file.write("\n")
                file.write("namespace basim {\n\n")
                file.write("struct ArchState; // forward declaration\n")
                file.write("class Cycles; // forward declaration\n")
                file.write("\n")
                for inst_name in insts:
                    opcode = enc.all_opcode_enc[inst_name]
                    if opcode not in all_inst_opcode_rev_dict:
                        continue
                    same_opcode_inst_names = all_inst_opcode_rev_dict[opcode]
                    del all_inst_opcode_rev_dict[opcode]
                    fused_inst_name = "".join(list(OrderedDict.fromkeys([inst.split(".")[0].capitalize() for inst in same_opcode_inst_names])))
                    file.write(f"/* {', '.join(same_opcode_inst_names)} Instruction */\n")
                    file.write(f"Cycles exeInst{fused_inst_name}(ArchState& ast, EncInst inst);\n")
                    file.write(f"std::string disasmInst{fused_inst_name}(EncInst inst);\n")
                    file.write(f"EncInst constrInst{fused_inst_name}(")
                    param_written = 0
                    for (num_bits, field_type, field_name, pos) in sorted(enc.all_bitfields[inst_name], key=lambda tup: tup[3]):
                        if field_type != "op" and field_type != "na":
                            if param_written > 0:
                                file.write(", ")
                        if field_type == "ui" or field_type == "fc":
                            file.write(f"uint64_t {field_name}")
                            param_written += 1
                        elif field_type == "si":
                            file.write(f"int64_t {field_name}")
                            param_written += 1
                        elif field_type == "r5" or field_type == "r4":
                            file.write(f"RegId {field_name}")
                            param_written += 1
                    file.write(");\n")
                    file.write("\n")
                file.write("}; // namespace basim\n")
                file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")

        # Generate dummy_inst for not encoded instructions
        with open(os.path.join(folderpath, "dummy_inst.hh"), "w") as file:
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")
            file.write("#pragma once\n")
            file.write("#include <cstdint>\n")
            file.write("#include <string>\n")
            file.write('#include "encodings.hh"\n')
            file.write('#include "debug.hh"\n')
            file.write("\n")
            file.write("namespace basim {\n\n")
            file.write("struct ArchState; // forward declaration\n")
            file.write("class Cycles; // forward declaration\n")
            file.write("\n")
            file.write("/* dummy Instruction */\n")
            file.write("Cycles exeInstDummy(ArchState& ast, EncInst inst);\n")
            file.write("std::string disasmInstDummy(EncInst inst);\n")
            file.write("EncInst constrInstDummy();\n")
            file.write("\n}; // namespace basim\n")
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")

        with open(os.path.join(folderpath, "dummy_inst.cpp"), "w") as file:
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")
            file.write(f'#include "{cat}_inst.hh"\n')
            file.write('#include "archstate.hh"\n')
            file.write('#include "lanetypes.hh"\n')
            file.write('#include "debug.hh"\n')
            file.write("\n")
            file.write("namespace basim {\n\n")
            file.write("/* dummy Instruction */\n")
            file.write("Cycles exeInstDummy(ArchState& ast, EncInst inst) {\n")
            file.write("  BASIM_WARNING(\"INSTRUCTION EXE NOT IMPLEMENTED, ENCODED INSTRUCTION = 0x%08x\", inst);\n")
            file.write("  return Cycles(0);\n")
            file.write("}\n")
            file.write("\n")
            file.write("std::string disasmInstDummy(EncInst inst) {\n")
            file.write("  std::string disasm_str = \"DUMMY\";\n")
            file.write("  char buffer[16];\n")
            file.write("  snprintf(buffer, sizeof(buffer), \"0x%08x\", inst);\n")
            file.write("  disasm_str += \" \" + std::string(buffer);\n")
            file.write("  return disasm_str;\n")
            file.write("}\n")
            file.write("\n")
            file.write("EncInst constrInstDummy() {\n")
            file.write("  BASIM_WARNING(\"INSTRUCTION CONSTR NOT IMPLEMENTED\");\n")
            file.write("  return static_cast<EncInst>(0);\n")
            file.write("}\n")
            file.write("\n}; // namespace basim\n")
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")

    @classmethod
    def write_boilerplates(cls, folderpath: str = "./"):
        all_inst_opcode_rev_dict = cls.reverse_dict(enc.all_opcode_enc)

        for cat, insts in inst_categories:
            with open(os.path.join(folderpath, f"{cat}_inst.cpp"), "w") as file:
                file.write(f'#include "{cat}_inst.hh"\n')
                file.write('#include "archstate.hh"\n')
                file.write('#include "lanetypes.hh"\n')
                file.write('#include "debug.hh"\n')
                file.write("\n")
                file.write("namespace basim {\n\n")
                for inst_name in insts:
                    opcode = enc.all_opcode_enc[inst_name]
                    if opcode not in all_inst_opcode_rev_dict:
                        continue
                    same_opcode_inst_names = all_inst_opcode_rev_dict[opcode]
                    del all_inst_opcode_rev_dict[opcode]  # remove opcode from dict to avoid duplicates
                    fused_inst_name = "".join(list(OrderedDict.fromkeys([inst.split(".")[0].capitalize() for inst in same_opcode_inst_names])))
                    file.write(f"/* {', '.join(same_opcode_inst_names)} Instruction */\n")

                    # exeInst
                    file.write(f"Cycles exeInst{fused_inst_name}(ArchState& ast, EncInst inst) {{\n")
                    file.write(f"  BASIM_WARNING(\"INSTRUCTION {', '.join(same_opcode_inst_names)} EXE NOT IMPLEMENTED\");\n")
                    file.write("  return Cycles(0);\n")
                    file.write("}\n")
                    file.write("\n")

                    # disasmInst
                    file.write(f"std::string disasmInst{fused_inst_name}(EncInst inst) {{\n")
                    file.write("  std::string disasm_str;\n")
                    for (num_bits, field_type, field_name, pos) in sorted(enc.all_bitfields[inst_name], key=lambda tup: tup[3]):
                        if field_type == "na":
                            continue
                        elif field_type == "op":
                            file.write(f"  disasm_str += \"{fused_inst_name.upper()}\";\n")
                        elif field_type == "r5" or field_type == "r4":
                            file.write(f"  disasm_str += std::string(\" \") + REG_NAMES[static_cast<uint8_t>(extrInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(inst))];\n")
                        elif field_type == "ty":
                            file.write(f"  disasm_str += std::string(\" \") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(inst))];\n")
                        else:
                            file.write(f"  disasm_str += std::string(\" \") + std::to_string(extrInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(inst));\n")
                    file.write("  return disasm_str;\n")
                    file.write("}\n")
                    file.write("\n")

                    # constrInst
                    file.write(f"EncInst constrInst{fused_inst_name}(")
                    param_written = 0
                    for (num_bits, field_type, field_name, pos) in sorted(enc.all_bitfields[inst_name], key=lambda tup: tup[3]):
                        if field_type != "op" and field_type != "na":
                            if param_written > 0:
                                file.write(", ")
                        if field_type == "ui" or field_type == "fc":
                            file.write(f"uint64_t {field_name}")
                            param_written += 1
                        elif field_type == "si":
                            file.write(f"int64_t {field_name}")
                            param_written += 1
                        elif field_type == "r5" or field_type == "r4":
                            file.write(f"RegId {field_name}")
                            param_written += 1
                    file.write(") {\n")
                    file.write("  EncInst inst;\n")
                    for (num_bits, field_type, field_name, pos) in sorted(enc.all_bitfields[inst_name], key=lambda tup: tup[3]):
                        if field_type == "na":
                            continue
                        elif field_type == "op":
                            file.write(f"  embdInstOpcode(inst, Opcode::{inst_name.upper().replace('.', '_')});\n")
                        else:
                            file.write(f"  embdInst{inst_name.capitalize().replace('.', '_')}{field_name.capitalize()}(inst, {field_name});\n")
                    file.write("  return inst;\n")
                    file.write("}\n")

                    file.write("\n\n")
                file.write("}; // namespace basim\n")

    @classmethod
    def write_inst_decode(cls, filepath: str = "inst_decode.hh"):
        all_inst_opcode_rev_dict = cls.reverse_dict(enc.all_opcode_enc)
        all_inst_int_opcode_rev_dict = dict()
        for opcode, inst_names in all_inst_opcode_rev_dict.items():
            all_inst_int_opcode_rev_dict[int(opcode, 2)] = inst_names
        all_inst_int_opcode_rev_dict = dict(sorted(all_inst_int_opcode_rev_dict.items()))

        with open(filepath, "w") as file:
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")
            file.write("#pragma once\n")
            file.write('#include "encodings.hh"\n')
            for cat, insts in inst_categories:
                file.write(f'#include "{cat}_inst.hh"\n')
            file.write('#include "transition.hh"\n')
            file.write('#include "dummy_inst.hh"\n')
            file.write('#include "debug.hh"\n')
            file.write("\n")
            file.write("namespace basim {\n\n")

            file.write("struct InstHandle {\n")
            file.write("  Cycles (*exe)(ArchState &, EncInst);\n")
            file.write("  std::string (*disasm)(EncInst);\n")
            file.write("};\n")
            file.write("\n")

            # file.write("struct TransHandle {\n")
            # file.write("  Cycles (*exe)(ArchState &, EncInst);\n")
            # file.write("  std::string (*disasm)(EncInst);\n")
            # file.write("};\n")
            # file.write("\n")

            file.write("inline constexpr InstHandle instHandleTable[128] = {\n")
            for i in range(0, 128):
                if i in all_inst_int_opcode_rev_dict:
                    fused_inst_name = "".join(list(OrderedDict.fromkeys([inst.split(".")[0].capitalize() for inst in all_inst_int_opcode_rev_dict[i]])))
                    file.write(f"  {{ // 0x{i:02x}\n")
                    file.write(f"    exeInst{fused_inst_name},\n")
                    file.write(f"    disasmInst{fused_inst_name},\n")
                    # file.write(f"    constrInst{fused_inst_name},\n")
                    file.write("  },\n")
                else:
                    file.write(f"  {{ // 0x{i:02x}, not encoded\n")
                    file.write(f"    exeInst{'Dummy'},\n")
                    file.write(f"    disasmInst{'Dummy'},\n")
                    # file.write(f"    constrInst{'Dummy'},\n")
                    file.write("  },\n")
            file.write("}; // instHandleTable\n")
            file.write("\n")

            # file.write("inline constexpr TransHandle tranHandleTable[16] = {\n")
            # for i in range(0, 16):
            #     if i in enc.transition_type_enc_rev:
            #         trans_name = enc.transition_type_enc_rev[i]
            #         file.write(f"  {{ // 0x{i:02x}\n")
            #         file.write(f"    exeTrans{trans_name},\n")
            #         file.write(f"    disasmTrans{trans_name},\n")
            #         file.write("  },\n")
            #     else:
            #         file.write(f"  {{ // 0x{i:02x}, not encoded\n")
            #         file.write(f"    exeInst{'Dummy'},\n")
            #         file.write(f"    disasmInst{'Dummy'},\n")
            #         file.write("  },\n")
            # file.write("}; // transHandleTable\n")
            # file.write("\n")

            file.write("inline constexpr InstHandle decodeInst(EncInst inst) { return instHandleTable[static_cast<uint8_t>(extrInstOpcode(inst))]; }\n")
            file.write("\n")
            # file.write("inline constexpr TransHandle decodeTrans(EncInst inst) { return transHandleTable[static_cast<uint8_t>(extrInstOpcode(inst))]; }\n")
            # file.write("\n")
            file.write("}; // namespace basim\n")
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")

    @classmethod
    def write_enc(cls, filepath: str = "encodings.hh"):
        with open(filepath, "w") as file:
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")
            file.write("#pragma once\n")
            file.write("#include <cstdint>\n")
            # file.write("#include <unordered_map>\n")
            # file.write("#include <string>\n")
            file.write("\n")
            file.write("namespace basim {\n\n")
            cls.gen_registers_enum(file, enc.register_enc)
            # cls.gen_registers_map(file, enc.register_enc)
            cls.gen_state_property_enum(file, enc.state_property_enc)
            cls.gen_transition_type_enum(file, enc.transition_type_enc)
            cls.gen_opcodes_enum(
                file,
                [
                    enc.I_opcode_enc,
                    enc.LI_opcode_enc,
                    enc.P_opcode_enc,
                    enc.S_opcode_enc,
                    enc.R_opcode_enc,
                    enc.B_opcode_enc,
                    enc.J_opcode_enc,
                    enc.M1_opcode_enc,
                    enc.M2_opcode_enc,
                    enc.M3_opcode_enc,
                    enc.M4_opcode_enc,
                    enc.E_opcode_enc,
                    enc.R4_opcode_enc,
                    enc.VF_opcode_enc,
                ],
                ["I-Type", "LI-Type", "P-Type", "S-Type", "R-Type", "B-Type", "J-Type", "M1-Type", "M2-Type", "M3-Type", "M4-Type", "E-Type", "R4-Type", "VF-Type"],
            )

            file.write("/* Utils */\n")
            file.write("typedef uint32_t EncInst;\n")
            file.write("\n")
            file.write(
                "inline constexpr uint64_t extrUnsignedImm(EncInst inst, uint8_t shift, uint8_t nbits) { return static_cast<uint64_t>((inst >> shift) & ((EncInst(1) << nbits) - 1)); }\n"
            )
            file.write(
                "inline constexpr int64_t extrSignedImm(EncInst inst, uint8_t shift, uint8_t nbits) { return static_cast<int64_t>(int32_t(inst) << (32 - shift - nbits) >> (32 - nbits)); }\n"
            )
            file.write(
                "inline constexpr RegId extrReg5(EncInst inst, uint8_t shift) { return static_cast<RegId>(extrUnsignedImm(inst, shift, 5)); }\n"
            )
            file.write(
                "inline constexpr RegId extrReg4(EncInst inst, uint8_t shift) { return static_cast<RegId>(extrUnsignedImm(inst, shift, 4) + 16); }\n"
            )
            file.write("\n")
            file.write(
                "inline constexpr void embdUnsignedImm(EncInst& inst, uint8_t shift, uint32_t mask, uint64_t imm) { inst = ((static_cast<EncInst>(imm) & static_cast<EncInst>(mask)) << shift) | (inst & ~(static_cast<EncInst>(mask) << shift)); }\n"
            )
            file.write(
                "inline constexpr void embdSignedImm(EncInst& inst, uint8_t shift, uint32_t mask, int64_t imm) { inst = ((static_cast<EncInst>(imm) & static_cast<EncInst>(mask)) << shift) | (inst & ~(static_cast<EncInst>(mask) << shift)); }\n"
            )
            file.write(
                "inline constexpr void embdReg5(EncInst& inst, uint8_t shift, RegId reg) { embdUnsignedImm(inst, shift, 0x1F, static_cast<uint64_t>(reg)); }\n"
            )
            file.write(
                "inline constexpr void embdReg4(EncInst& inst, uint8_t shift, RegId reg) { embdUnsignedImm(inst, shift, 0xF, static_cast<uint64_t>(reg) - 16); }\n"
            )
            file.write("\n")

            file.write("/* Instruction Opcode Bitfield */\n")
            file.write(f"const uint8_t BF_INST_OPCODE_SHIFT = {0};\n")
            file.write(f"const uint8_t BF_INST_OPCODE_NBITS = {7};\n")
            file.write(f"const uint32_t BF_INST_OPCODE_MASK = {hex((1 << 7) - 1)};\n")
            file.write(f"const bool BF_INST_OPCODE_SIGNED = {'false'};\n")
            file.write(
                "inline constexpr Opcode extrInstOpcode(EncInst inst) { return static_cast<Opcode>(extrUnsignedImm(inst, BF_INST_OPCODE_SHIFT, BF_INST_OPCODE_NBITS)); }\n"
            )
            file.write(
                "inline constexpr void embdInstOpcode(EncInst& inst, Opcode opc) { embdUnsignedImm(inst, BF_INST_OPCODE_SHIFT, BF_INST_OPCODE_MASK, static_cast<uint64_t>(opc)); }\n"
            )
            file.write("\n")

            file.write("/* Transition Type Bitfield */\n")
            file.write(f"const uint8_t BF_TRNAS_TYPE_SHIFT = {8};\n")
            file.write(f"const uint8_t BF_TRNAS_TYPE_NBITS = {4};\n")
            file.write(f"const uint32_t BF_TRNAS_TYPE_MASK = {hex((1 << 4) - 1)};\n")
            file.write(f"const bool BF_TRNAS_TYPE_SIGNED = {'false'};\n")
            file.write(
                "inline constexpr TransitionType extrTransType(EncInst inst) { return static_cast<TransitionType>(extrUnsignedImm(inst, BF_TRNAS_TYPE_SHIFT, BF_TRNAS_TYPE_NBITS)); }\n"
            )
            file.write(
                "inline constexpr void embdTransType(EncInst& inst, TransitionType type) { embdUnsignedImm(inst, BF_TRNAS_TYPE_SHIFT, BF_TRNAS_TYPE_MASK, static_cast<uint64_t>(type)); }\n"
            )
            file.write("\n")

            # TODO: add string names

            cls.gen_bitfields_const(file, enc.I_bitfields, "I-Type Bitfields")
            cls.gen_bitfields_const(file, enc.LI_bitfields, "LI-Type Bitfields")
            cls.gen_bitfields_const(file, enc.P_bitfields, "P-Type Bitfields")
            cls.gen_bitfields_const(file, enc.S_bitfields, "S-Type Bitfields")
            cls.gen_bitfields_const(file, enc.R_bitfields, "R-Type Bitfields")
            cls.gen_bitfields_const(file, enc.B_bitfields, "B-Type Bitfields")
            cls.gen_bitfields_const(file, enc.J_bitfields, "J-Type Bitfields")
            cls.gen_bitfields_const(file, enc.M1_bitfields, "M1-Type Bitfields")
            cls.gen_bitfields_const(file, enc.M2_bitfields, "M2-Type Bitfields")
            cls.gen_bitfields_const(file, enc.M3_bitfields, "M3-Type Bitfields")
            cls.gen_bitfields_const(file, enc.M4_bitfields, "M4-Type Bitfields")
            cls.gen_bitfields_const(file, enc.E_bitfields, "E-Type Bitfields")
            cls.gen_bitfields_const(file, enc.R4_bitfields, "R4-Type Bitfields")
            cls.gen_bitfields_const(file, enc.VF_bitfields, "VF-Type Bitfields")
            cls.gen_bitfields_const(file, enc.EventTr_bitfields, "Event-Transition Bitfields")
            cls.gen_bitfields_const(file, enc.EFATr_bitfields, "EFA-Transition Bitfields")
            file.write("}; // namespace basim\n")
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")
            file.close()

    @classmethod
    def write_trans_prototypes(cls, folderpath: str = "./"):
        trans_rev_dict = cls.reverse_dict(enc.transition_type_enc)

        with open(os.path.join(folderpath, f"transition.hh"), "w") as file:
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")
            file.write("#pragma once\n")
            file.write("#include <cstdint>\n")
            file.write("#include <string>\n")
            file.write('#include "encodings.hh"\n')
            file.write("\n")
            file.write("namespace basim {\n\n")
            file.write("struct ArchState; // forward declaration\n")
            file.write("class Cycles; // forward declaration\n")
            file.write("\n")
            for trans in transitions:
                file.write(f"/* {trans} Transition */\n")
                file.write(f"Cycles exeTrans{trans}(ArchState& ast, EncInst inst);\n")
                file.write(f"std::string disasmTrans{trans}(EncInst inst);\n")
                file.write(f"EncInst constrTrans{trans}(")
                param_written = 0
                for (num_bits, field_type, field_name, pos) in sorted(enc.all_trans_bitfields[trans], key=lambda tup: tup[3]):
                    if field_type != "op" and field_type != "na":
                        if param_written > 0:
                            file.write(", ")
                    if field_type == "ui":
                        file.write(f"uint64_t {field_name}")
                        param_written += 1
                    elif field_type == "si":
                        file.write(f"int64_t {field_name}")
                        param_written += 1
                    elif field_type == "ty":
                        file.write(f"TransitionType {field_name}")
                        param_written += 1
                file.write(");\n")
                file.write("\n")
            file.write("\n")
            file.write("}; // namespace basim\n")
            file.write("/* AUTOGENERATED FILE - DO NOT MODIFY */\n")

    @classmethod
    def write_trans_boilerplates(cls, folderpath: str = "./"):
        trans_rev_dict = cls.reverse_dict(enc.transition_type_enc)

        with open(os.path.join(folderpath, f"transition.cpp"), "w") as file:
            file.write(f'#include "transition.hh"\n')
            file.write('#include "archstate.hh"\n')
            file.write('#include "lanetypes.hh"\n')
            file.write('#include "debug.hh"\n')
            file.write("\n")
            file.write("namespace basim {\n\n")
            for trans in transitions:
                file.write(f"/* {trans} Transition */\n")
                # exeTrans
                file.write(f"Cycles exeTrans{trans}(ArchState& ast, EncInst inst) {{\n")
                file.write(f"  BASIM_WARNING(\"TRANSITION {trans} EXE NOT IMPLEMENTED\");\n")
                file.write("  return Cycles(0);\n")
                file.write("}\n")
                file.write("\n")

                # disasmTrans
                file.write(f"std::string disasmTrans{trans}(EncInst inst) {{\n")
                file.write("  std::string disasm_str;\n")
                for (num_bits, field_type, field_name, pos) in sorted(enc.all_trans_bitfields[trans], key=lambda tup: tup[3]):
                    if field_type == "na":
                        continue
                    elif field_type == "ty":
                        file.write("  disasm_str += \"TRANS\";\n")
                        file.write(f"  disasm_str += std::string(\" \") + TRANSITION_TYPE_NAMES[static_cast<uint8_t>(extrTransType(inst))];\n")
                    elif field_type == "op":
                        file.write(f"  disasm_str += \"{trans.upper()}\";\n")
                    elif field_type == "r5" or field_type == "r4":
                        file.write(f"  disasm_str += std::string(\" \") + REG_NAMES[static_cast<uint8_t>(extrInst{trans.capitalize().replace('.', '_')}{field_name.capitalize()}(inst))];\n")
                    else:
                        file.write(f"  disasm_str += std::string(\" \") + std::to_string(extrInst{trans.capitalize().replace('.', '_')}{field_name.capitalize()}(inst));\n")
                file.write("  return disasm_str;\n")
                file.write("}\n")
                file.write("\n")

                # constrInst
                file.write(f"EncInst constrTrans{trans}(")
                param_written = 0
                for (num_bits, field_type, field_name, pos) in sorted(enc.all_trans_bitfields[trans], key=lambda tup: tup[3]):
                    if field_type != "op" and field_type != "na":
                        if param_written > 0:
                            file.write(", ")
                    if field_type == "ui":
                        file.write(f"uint64_t {field_name}")
                        param_written += 1
                    elif field_type == "si":
                        file.write(f"int64_t {field_name}")
                        param_written += 1
                    elif field_type == "ty":
                        file.write(f"TransitionType {field_name}")
                        param_written += 1
                file.write(") {\n")
                file.write("  EncInst inst;\n")
                for (num_bits, field_type, field_name, pos) in sorted(enc.all_trans_bitfields[trans], key=lambda tup: tup[3]):
                    if field_type == "na":
                        continue
                    elif field_type == "op":
                        file.write(f"  embdInstOpcode(inst, Opcode::{trans.upper().replace('.', '_')});\n")
                    elif field_type == "ty":
                        file.write(f"  embdTransType(inst, {field_name});\n")
                    else:
                        file.write(f"  embdInst{trans.capitalize()}{field_name.capitalize()}(inst, {field_name});\n")
                file.write("  return inst;\n")
                file.write("}\n")
                file.write("\n")

            file.write("\n")
            file.write("}; // namespace basim\n")


if __name__ == "__main__":
    EncGen.write_enc()
    EncGen.write_prototypes()
    EncGen.write_boilerplates()
    EncGen.write_inst_decode()
    EncGen.write_trans_prototypes()
    EncGen.write_trans_boilerplates()
