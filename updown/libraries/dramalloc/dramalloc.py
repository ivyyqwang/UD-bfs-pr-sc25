import logging
from EFA_v2 import *

class RegFile:
    def __init__(self, registers=None, prefix="UDPR_"):
        self.available = registers
        if self.available is None:
            self.available = list(range(16))
        self.reg_mapping = {}
        self.name_prefix = prefix

    def __getitem__(self, name):
        if name not in self.reg_mapping:
            self.reg_mapping[name] = self.available.pop()
            reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
            logging.info(f"Allocated {reg_name} for {name}")
        reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
        return reg_name

    def assign(self, name, i):
        self.reg_mapping[name] = i
        self.available.remove(i)
        reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
        logging.info(f"Explicit allocation of {reg_name} for {name}")
        return reg_name

    def free(self, name):
        reg_name = f"{self.name_prefix}{self.reg_mapping[name]}"
        register = self.reg_mapping[name]
        del self.reg_mapping[name]
        self.available.append(register)
        logging.info(f"Freed {reg_name} for {name}")

class TranslationEntryInstaller:
    def __init__(self, nr_nodes, nr_clusters, nr_uds, enable_debug=False):
        self.enable_debug = enable_debug
        self.nr_nodes = nr_nodes
        self.nr_clusters = nr_clusters
        self.nr_uds = nr_uds

        self.registers = RegFile()

        self.count = self.registers["count"]
        self.nwid = self.registers["nwid"]
        self.event_word = self.registers["event_word"]

    def _debug_log(self, tran, msg):
        if self.enable_debug:
            tran.writeAction(f"print {msg}")


    def implement_installer_request_sender(self, tran):
        addr = self.registers["addr"]
        evw_temp0 = self.registers["evw_temp0"]
        evw_temp1 = self.registers["evw_temp1"]
        lm_base = self.registers["lm_base"]

        # wenyi: base address compat
        # tran.writeAction("print 'installer_request_sender: Installing on: %ld' NWID")
        self._debug_log(tran, f"'installer_request_sender: Start installing translation entry, sender nwid = %ld' NWID")
        self._debug_log(tran, f"'Translation entry: vbase = %ld(0x%lx) pbase = %ld(0x%lx) size = %ld(0x%lx) swizzle_mask = %ld' X8 X8 X11 X11 X9 X9 X10")
        tran.writeAction(f"movir {addr} 2") # 2 words away
        
        tran.writeAction(f"mov_imm2reg {self.count} 0")
        tran.writeAction(f"mov_imm2reg {self.nwid} 0")

        tran.writeAction(f"ev_update_2 {self.event_word} {501} 255 5")
        

        for idx in range(5):
            # tran.writeAction(f"mov_reg2lm X{8 + idx} {addr} 8")
            # tran.writeAction(f"addi {addr} {addr} 8")
            tran.writeAction(f"movwrl X{8 + idx} {'X7'}({addr},1,0)")
        # reset addr
        # tran.writeAction(f"addi X7 {addr} 16")

        for node in range(self.nr_nodes):
            for cluster in range(self.nr_clusters):
                for ud in range(self.nr_uds):
                    current_nwid = 0 | node << 11 | cluster << 8 | ud << 6
                    # print(f"current_nwid: {current_nwid}")
                    tran.writeAction(
                        f"evi {self.event_word} {self.event_word} {current_nwid} 8")
                    # self._debug_log(tran, f"'installer_request_sender: Send install request to nwid = {current_nwid}'")
                    tran.writeAction(f"sendops_wret {self.event_word} 502 {'X8'} {5} {evw_temp0}")
                    tran.writeAction(f"addi {self.count} {self.count} 1")

        self._debug_log(tran, f"'installer_request_sender: Send %ld install requests, wait for returns' {self.count}")
        tran.writeAction("yield")

        self.registers.free("addr")
        self.registers.free("evw_temp0")
        self.registers.free("evw_temp1")
        self.registers.free("lm_base")

    def implement_termination_event(self, tran):
        temp_val = self.registers["temp_val"]
        temp_addr = self.registers["temp_addr"]
        lm_base = self.registers["lm_base"]
        tran.writeAction(f"subi {self.count} {self.count} 1")
        tran.writeAction(f"bnec {self.count} 0 wait_for_more_returns")

        tran.writeAction(f"mov_imm2reg {temp_val} -1")
        tran.writeAction(f"mov_imm2reg {temp_addr} 0")
        # wenyi: base address compat
        # tran.writeAction(f"addi X7 {lm_base} 0")
        # tran.writeAction(f"mov_reg2lm {temp_val} {temp_addr} 8")
        self._debug_log(tran, f"'install_termination_event: translation entry installation finished, return value = %ld' {temp_val}")
        tran.writeAction(f"movwrl {temp_val} {'X7'}({temp_addr},0,0)")
        

        tran.writeAction(f"yield_terminate")

        tran.writeAction("wait_for_more_returns: yield")

        self.registers.free("temp_val")
        self.registers.free("temp_addr")
        self.registers.free("lm_base")

    def implement_installer_event(self, tran):
        # tran.writeAction("print 'installer_event: install on: %ld' NWID")
        self._debug_log(tran, f"'installer_event: install on: %ld' NWID")
        tran.writeAction(f"blei X{8 + 4} 1 local_segment")
        tran.writeAction(f"instrans X8 X11 X9 X10 1 {0b11}")
        tran.writeAction("jmp finish")
        tran.writeAction(f"local_segment: instrans X8 X11 X9 X10 0 {0b11}")
        tran.writeAction(f"finish: addi NWID X16 0")
        tran.writeAction(f"sendr_reply X1 X16 X20")
        tran.writeAction("yield_terminate")

    def implement_argument_ptr_getter_event(self, tran):
        arg_addr = self.registers["arg_addr"]
        lm_base = self.registers["lm_base"]
        lm_ptr = self.registers["lm_ptr"]

        # tran.writeAction("print 'Getting from nwid: %ld' NWID")
        self._debug_log(tran, f"'Getting from nwid: %ld' NWID")
        #wenyi: base address compat, third value is the address
        # tran.writeAction(f"mov_imm2reg {arg_addr} 0")
        # tran.writeAction(f"addi X7 {arg_addr} 16")
        # tran.writeAction(f"mov_lm2reg {arg_addr} {arg_addr} 8")
        # tran.writeAction(f"addi X7 {lm_base} 0")
        tran.writeAction(f"movir {lm_ptr} 2")
        tran.writeAction(f"movwlr {'X7'}({lm_ptr},0,0) {arg_addr}")
        # tran.writeAction(f"print 'address gotten: %ld' {arg_addr}")
        self._debug_log(tran, f"'address gotten: %ld' {arg_addr}")
        tran.writeAction(f"sendr_reply {arg_addr} {arg_addr} X20")
        tran.writeAction("yield_terminate")
        self.registers.free("arg_addr")
        self.registers.free("lm_base")
        self.registers.free("lm_ptr")
