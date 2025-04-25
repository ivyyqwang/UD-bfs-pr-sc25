from frontend.ASTweave import *
from Weave.WeaveIR import *
from backend.registerAllocator import WeaveRegisterAllocator
import Weave.optimizer as optimizer
import Weave.debug as debug


class WeavePythonCodeGen:
    """Class to generate ISAv2.3 Python code with LinkableModules"""

    INDENT_INC = 2

    class ArithOpsTypes(WIRinst.Enum):
        REG_IMM = 0
        REG_REG = 1
        UNKNOWN = 1000

    def __init__(
            self,
            program: WeaveIRmodule,
            regAlloc: WeaveRegisterAllocator,
            inlineCode: bool = False,
    ):
        self.program = program
        self.regAlloc = regAlloc
        self.out = ["from linker.EFAProgram import efaProgram\n"]
        self.curIndent = 0
        self._inlineCode = inlineCode
        self._transactionName = ""

    def add_header(self):
        """This function adds the EFA function header.
        This is always the same text for now
        """
        self.add_line(f"efa.code_level = 'machine'")
        self.add_line(f'state0 = efa.State("udweave_init") #Only one state code ')
        self.add_line(f"efa.add_initId(state0.state_id)")

    def add_footer(self):
        pass

    def add_transition(self, eventName: str) -> str:
        """Create a new transition instruction

        Args:
            eventName (str): Name of the event in the UDWeave program
        """
        tranName = eventName.replace(":", "_").replace(".", "_")
        self.add_line(f"tran{tranName} = efa.writeEvent('{eventName}')")
        return tranName

    def add_action(self, tranName: str, action: str, comment=""):
        """Create a new action into the output

        Args:
            comment (str): Comments to be added to the action
            tranName (str): Name of the transaction in the python assembly
            action (str): The assembly code to be written into the action
        """
        if comment:
            comment = f" # {comment}"
        self.add_line(f'tran{tranName}.writeAction(f"{action}") {comment}')

    def add_line(self, text: str):
        """Adds a new output line with the current indentation
        TODO: new lines within the line is not supported. It is an easy replace
        Args:
            text (str): Line to be added
        """
        self.out.append(" " * self.curIndent + text)

    def next_indent(self):
        """Add a new indent level. Indent is prepended per line"""
        self.curIndent += self.INDENT_INC

    def prev_indent(self):
        """Remove an indent level"""
        self.curIndent -= self.INDENT_INC
        if self.curIndent < 0:
            self.curIndent = 0

    def create_inst_format(self, opCode: str, ops: list):
        """Helper function for building a multiops instruction

        Args:
            opCode (str): Instruction Operation
            ops (list): String list with each operand

        Returns:
            str: Formatted instruction
        """
        operands = " ".join(str(op) for op in ops)
        return f"{opCode} {operands}"

    def _add_comment(self, comment: WeaveIRcomment):
        comm = comment.getValue().lstrip("/")
        self.add_line(f"##{comm}")

    def _add_inlineasm_action(self, evNum: str, lines: list, res: str = ""):
        for line in lines:
            self.add_action(evNum, res + line)
            res = ""

    def _add_inlineasm_python(self, lines: list, res: str = ""):
        # get first line indent
        indent = len(lines[0]) - len(lines[0].lstrip())
        for line in lines:
            # remove first line indent
            self.add_line(res + line[indent:])
            res = ""

    def get_ops_binaryInst(self, inst: WeaveIRbinaryOps):
        """Determine if reg to reg or reg to imm
        return the corresponding order of operands.
        Most operations in ISAv2 are:
        REG_SRC, REG_SRC, REG_DST, or
        REG_SRC, REG_DST, IMM
        This helper function determines this and returns
        the right order.

        Args:
            inst (WeaveIRarith): Arithmetic operation
        """
        ops = []
        if isinstance(inst.left, WeaveIRimmediate) and isinstance(
                inst.right, WeaveIRimmediate
        ):
            errorMsg(
                "Both operands are immediate values. No translation possible",
                inst.getFileLocation(),
            )
        elif isinstance(inst.left, WeaveIRimmediate) or isinstance(inst.left, WeaveIRsymPtr):
            ops.append(inst.right.getAllocation())
            if inst.getReturnReg():
                ops.append(inst.getReturnReg().getAllocation())
            ops.append(inst.left.name)
            return ops, self.ArithOpsTypes.REG_IMM
        if isinstance(inst.right, WeaveIRimmediate) or isinstance(inst.right, WeaveIRsymPtr):
            ops.append(inst.left.getAllocation())
            if inst.getReturnReg():
                ops.append(inst.getReturnReg().getAllocation())
            ops.append(inst.right.name)
            return ops, self.ArithOpsTypes.REG_IMM

        ops.append(inst.left.getAllocation())
        if inst.right:
            ops.append(inst.right.getAllocation())
        if inst.getReturnReg():
            ops.append(inst.getReturnReg().getAllocation())
        return ops, self.ArithOpsTypes.REG_REG

    def registerAllocator(self, th: WeaveIRthread):
        # TODO: Create a register allocator here It is per event.
        # This allocator must use the registers in ALL_REGISTERS. In case
        # The user changes these registers from the outside, this will prevent
        # the allocator to use registers that are needed for components
        # outside of UDweave
        pass

    def globalConstantsTranslate(self):
        self.add_line(f"## Global constants")
        for s in self.program.getSections():
            if isinstance(s, WeaveIRGlobalDecl):
                self.add_line(f"#constexp {s.fullName} = {s.value}")
        self.add_line("")

    def programTranslate(self):
        """Upper level function that translates all the program"""
        self.add_line(f"@efaProgram")
        self.add_line(f"def EFA_{self.program.name}(efa):")
        self.next_indent()
        self.add_header()

        self.staticDeclsTranslate()

        # Iterate over the scopes to allocate registers
        for s in self.program.sections:
            if isinstance(s, WeaveIRscope):
                self.allocateRegistersInScope(s)

         # We might have deleted instructions and end up with empty BBs, which is not allowed.
        optsToApply = ['EmptyBasicBlockMerging']
        for opt in optsToApply:
            toApply = optimizer.WeaveIRopt.getOpt(opt)
            if len(toApply) > 0:
                toApply[0].apply(self.program)
            else:
                debug.warningMsg(f"Optimization {opt} not found")

        # Iterate over program sections
        for s in self.program.sections:
            if isinstance(s, WeaveIRcomment):
                self._add_comment(s)
            elif isinstance(s, WeaveIRassembly):
                s.applyOperands()
                self._add_inlineasm_python(s.getLines())
            elif isinstance(s, WeaveIRscope):
                self.scopeTranslate(s)

        self.add_footer()
        self.prev_indent()

    def _thread_header_comment(self, th: WeaveIRthread):
        self.add_line("")
        if th.isAnonymous:
            self.add_line(f"###############################################")
            self.add_line(f"###### Writing code for anonymous thread ######")
            self.add_line(f"###############################################")
        else:
            self.add_line(f"######################################{'#' * len(th.name)}")
            self.add_line(f"###### Writing code for thread {th.name} ######")
            self.add_line(f"######################################{'#' * len(th.name)}")

    def staticDeclsTranslate(self):
        self.add_line(f"## Static declarations")
        for s in self.program.getSections():
            if isinstance(s, WeaveIRDecl) and s.isStatic:
                self.add_line(f'efa.addStaticData("{s.fullName}", {s.size})')
            elif isinstance(s, WeaveIRthread):
                for d in s.getSections():
                    if isinstance(d, WeaveIRDecl) and d.isStatic:
                        self.add_line(f'efa.addStaticData("{d.fullName}", {d.size})')
                    elif isinstance(d, WeaveIRscope):
                        for decl in d.getDeclarations():
                            if decl.isStatic:
                                self.add_line(f'efa.addStaticData("{decl.fullName}", {decl.size})')

    def threadTranslate(self, th: WeaveIRthread):

        self._thread_header_comment(th)

        for s in th.getSections():
            if isinstance(s, WeaveIRevent):
                self.eventTranslate(s)
            elif isinstance(s, WeaveIRcomment):
                self._add_comment(s)
            elif isinstance(s, WeaveIRassembly):
                s.applyOperands()
                self._add_inlineasm_python(s.getLines())
            elif isinstance(s, WeaveIRscope):
                self.scopeTranslate(s)

    def eventTranslate(self, ev: WeaveIRevent):
        self.add_line(f"# Writing code for event {ev.fullName}")
        self._transactionName = self.add_transition(ev.fullName)

        for b in ev.basic_blocks:
            self.basicBlockTranslate(self._transactionName, b)
        self.add_line("")

    def scopeTranslate(self, scope: WeaveIRscope):
        for s in scope.getBodies():
            if isinstance(s, WeaveIRthread):
                self.threadTranslate(s)
            elif isinstance(s, WeaveIRcomment):
                self._add_comment(s)
            elif isinstance(s, WeaveIRassembly):
                s.applyOperands()
                self._add_inlineasm_python(s.getLines())
            elif isinstance(s, WeaveIRscope):
                self.scopeTranslate(s)
            elif isinstance(s, WeaveIRbasicBlock):
                self.basicBlockTranslate(self._transactionName, s)
            elif isinstance(s, WeaveIRinstruction):
                self.instructionTranslate(self._transactionName, s)

    def basicBlockTranslate(self, transName: str, bb: WeaveIRbasicBlock):
        if len(bb.getInstructions()) == 0:
            errorMsg(
                f"Basic block {bb.name} is empty. This is not supported yet"
                " because dangling labels in the assembler is not allowed",
                bb.getFileLocation(),
            )
        label = bb.name
        label_used = False
        previousFileLocation = None
        for i, inst in enumerate(bb.getInstructions()):
            if (
                    inst.getFileLocation() is not None
                    and not inst.getFileLocation().sameLine(previousFileLocation)
            ):
                previousFileLocation = inst.getFileLocation()
                if self._inlineCode:
                    self.add_line("## " + inst.getFileLocation().getLine())
                debugMsg(
                    6, f"Generating code for line {inst.getFileLocation().getLine()}"
                )
            if i != 0 and label_used:
                label = None
            label_used = self.instructionTranslate(transName, inst, label)

    def _gatherOperandsPrintPerflog(self, inst, string: str, ops: list):
        regex = re.compile(r"%[0 #+-]?[0-9*]*\.?\d*([hl]{0,2}|[jztL])?[diuoxXeEfgGaAcpsSn%]")

        # Find all format specifiers in the string
        formatSpecifiers = []
        positions = []
        lengths = []
        pos = 0  # where to start searching for next time
        while True:
            match = regex.search(string, pos)
            if match is None:
                break
            formatSpecifiers.append(match.group(0))
            positions.append(match.start())
            lengths.append(match.end() - match.start())
            pos = match.end()

        # If the instruction has no operands, we can directly return the string
        if len(formatSpecifiers) == 0:
            return [string] + []

        params = []
        for op in ops:
            # If an operand is an immediate, we already know its value. Hence, we just replace the formater ('%ld', ...)
            # with the actual value and remove the parameter from the list of operands.
            # Doing so allows us to save registers for the immediate values and to support strings ('%s').
            if isinstance(op, WeaveIRimmediate):
                params.append(op)
            elif isinstance(op, WeaveIRregister):
                params.append(op.getAllocation())
            else:
                errorMsg(
                    f"UNREACHABLE: This instruction only supports immediate and register operands",
                    inst.getFileLocation(),
                )

        # Walk through the first operand that contains the string and the format specifiers
        # (such as "%ld: %ld"). Replace the specifier with the actual string and remove the parameter
        # from the list of operands.
        newString = ""
        startIndex = 0
        for index, pos in enumerate(positions):
            if isinstance(params[index], WeaveIRimmediate):
                newString += string[startIndex:pos] + params[index].name
                startIndex = pos + lengths[index]
                params[index] = None
        newString += string[startIndex:]
        params = [param for param in params if param is not None]

        return [newString] + params

    def instructionTranslate(
            self, transName: str, inst: WeaveIRinstruction, label: str = None
    ) -> bool:
        """Contains the actual mapping to assembly code of each instruction type in WeaveIR
            Label is needed because the emulator does not support an action that only
            contains a label

        Args:
            transName (str): transactionName of the event in the python code
            inst (WeaveIRinstruction): _description_
            label (str, optional): Label of the section. If not none it gets added to the instruction output.

        Returns:
            bool: True if the instruction consumed the label (e.g. comments and assembly code do not consume the label).
        """

        res = f"{label}: " if label else ""
        if isinstance(inst, WeaveIRmemory):

            def computeAddress():
                """ Compute the address and offset, when accessing local memory"""
                # in case we have to load from/store to a pointer that is a struct.
                if isinstance(inst.dataType, WeaveIRstructDecl):
                    if helper.isPowerOfTwo(inst.dataType.getSize(inst.getFileLocation())):
                        compScale = helper.log2(inst.dataType.getSize(inst.getFileLocation()))
                    else:
                        compScale = -1
                    field = inst.getFieldDecl()
                    compSize = field.dataType.getSize(inst.getFileLocation())

                    if isinstance(offset, WeaveIRimmediate):
                        compFieldOffset = (offset.getValue() * inst.dataType.getSize(inst.getFileLocation()) +
                                           inst.dataType.getFieldOffset(field))
                        offset.setValue(compFieldOffset)
                    else:
                        compFieldOffset = inst.dataType.getFieldOffset(field)
                elif isinstance(inst.dataType, WeaveIRunionDecl):
                    if helper.isPowerOfTwo(inst.dataType.getSize(inst.getFileLocation())):
                        compScale = helper.log2(inst.dataType.getSize(inst.getFileLocation()))
                    else:
                        compScale = -1
                    compSize = inst.dataType.getSize(inst.getFileLocation())
                    if isinstance(offset, WeaveIRimmediate):
                        compFieldOffset = offset.getValue() * inst.dataType.getSize(inst.getFileLocation())
                        offset.setValue(compFieldOffset)
                    else:
                        compFieldOffset = 0
                else:
                    compSize = inst.dataType.getSize(inst.getFileLocation())
                    compScale = inst.dataType.getScale()
                    if isinstance(offset, WeaveIRimmediate):
                        compFieldOffset = offset.getValue() << compScale
                    else:
                        compFieldOffset = 0
                return compScale, compSize, compFieldOffset

            # Register to register
            if inst.instType == WIRinst.WeaveIRmemoryTypes.LOAD:
                if (
                        isinstance(inst.getValueToStore(), WeaveIRsymPtr) or
                        isinstance(inst.getValueToStore(), WeaveIRsymConst) or
                        isinstance(inst.getValueToStore(), WeaveIRimmediate)
                ):
                    res += f"movir {inst.getReturnReg().getAllocation()} {inst.getValueToStore().name}"
                    self.add_action(transName, res)
                else:
                    res += f"addi {inst.getValueToStore().getAllocation()} {inst.getReturnReg().getAllocation()} 0"
                    self.add_action(transName, res)

            # Store to Scratchpad
            elif inst.instType == WIRinst.WeaveIRmemoryTypes.STORELOCAL:
                offset = inst.getOffsetDecl()

                if isinstance(offset, WeaveIRimmediate) and not -2048 <= offset.getOriginalValue() <= 2047:
                    errorMsg(f"Offset index ({offset.getOriginalValue()}) is out of range for store instruction. "
                             "It has to be in range -2048 <= offset <= 2047", inst.getFileLocation())

                scale, size, fieldOffset = computeAddress()
                valueToBeStored = inst.getValueToStore().getAllocation()
                if valueToBeStored is None:
                    valueToBeStored = self.regAlloc.getTempReg(0, inst.ctx_event).name

                if isinstance(offset, WeaveIRimmediate):
                    addressReg = inst.getPointerReg().getAllocation()

                    # The movrl instruction has only 4 bits for the address register. Hence, only the upper 16 registers
                    # (X16-X31) can be used as address registers. If the address register is not in this range (e.g.,
                    # the register is an operand buffer), we have to load the address into a temporary register first.
                    if inst.getPointerReg().isOBuff:
                        addressReg = self.regAlloc.getTempReg(1, inst.ctx_event).name
                        res += f"addi {inst.getPointerReg().getAllocation()} {addressReg} 0"
                        self.add_action(transName, res)
                        res = ''

                    res += f"movrl {valueToBeStored} {fieldOffset}({addressReg}) 0 {size}"
                    self.add_action(transName, res)
                else:
                    # For word size = 8, the movw instruction is used (see below)
                    # If the word size is != we have to build the address using a temporary register
                    # This is also the case, if the scale is -1, which means that the access is a field in a struct
                    # This field might not be aligned to 8 bytes required by the movw instruction. That is because,
                    # the $scale parameter is always shifted left by 3. Hence, only words with are aligned to 8 bytes
                    # can be used for this purpose.
                    offsetReg = inst.getOffsetReg().getAllocation()
                    if size != WIRinst.WeaveIRtypes.i64.getSize() or scale == -1:
                        # There is no register offset for sub word access
                        # build the address using a temporary register
                        temp1 = self.regAlloc.getTempReg(1, inst.ctx_event).name

                        # apply the scale.
                        # scale == -1, if it is a struct, so there is a chance, that we cannot use sli instruction
                        if scale == -1:
                            res += f"muli {offsetReg} {temp1} {inst.dataType.getSize(inst.getFileLocation())}"
                        else:
                            # Shift the value by scale and then add to temp register
                            res += f"sli {offsetReg} {temp1} {scale}"

                        self.add_action(transName, res)
                        res = f"add {temp1} {inst.getPointerReg().getAllocation()} {temp1}"
                        self.add_action(transName, res)
                        res = f"movrl {valueToBeStored} {fieldOffset}({temp1}) 0 {size}"
                        self.add_action(transName, res)
                    else:
                        #  Note: The scale is incremented by 3 by the instruction. Hence, it only works for 8 byte
                        #  values.
                        #        movwrl    Xs                         Xb                            Xd    inc, scale
                        res += f"movwrl {valueToBeStored} {inst.getPointerReg().getAllocation()}({offsetReg},0,0)"
                        self.add_action(transName, res)

            # Load from Scratchpad
            elif inst.instType == WIRinst.WeaveIRmemoryTypes.LOADLOCAL:
                ret = inst.getReturnReg()
                offset = inst.getOffsetDecl()
                if isinstance(offset, WeaveIRimmediate) and not -2048 <= offset.getOriginalValue() <= 2047:
                    errorMsg(f"Offset index ({offset.getOriginalValue()}) is out of range for load instruction. "
                             "It has to be in range -2048 <= offset <= 2047", inst.getFileLocation())

                scale, size, fieldOffset = computeAddress()

                if isinstance(offset, WeaveIRimmediate):
                    addressReg = inst.getPointerReg().getAllocation()

                    # The movlr instruction has only 4 bits for the address register. Hence, only the upper 16 registers
                    # (X16-X31) can be used as address registers. If the address register is not in this range (e.g.,
                    # the register is an operand buffer), we have to load the address into a temporary register first.
                    if inst.getPointerReg().isOBuff:
                        addressReg = self.regAlloc.getTempReg(0, inst.ctx_event).name
                        res += f"addi {inst.getPointerReg().getAllocation()} {addressReg} 0"
                        self.add_action(transName, res)
                        res = ''
                    res += f"movlr {fieldOffset}({addressReg}) {ret.getAllocation()} 0 {size}"
                    self.add_action(transName, res)
                else:
                    # For word size = 8, the movw instruction is used (see below)
                    # If the word size is != we have to build the address using a temporary register
                    # This is also the case, if the scale is -1, which means that the access is a field in a struct
                    # This field might not be aligned to 8 bytes required by the movw instruction. That is because,
                    # the $scale parameter is always shifted left by 3. Hence only words with are aligned to 8 bytes
                    # can be used for this purpose.
                    offsetReg = inst.getOffsetReg().getAllocation()
                    if size != WIRinst.WeaveIRtypes.i64.getSize() or scale == -1:
                        # There is no register offset for sub word access
                        # build the address using a temporary register
                        temp1 = self.regAlloc.getTempReg(0, inst.ctx_event).name

                        # apply the scale.
                        # scale == -1, if it is a struct, so there is a chance, that we cannot use sli instruction
                        if scale == -1:
                            res += f"muli {offsetReg} {temp1} {inst.dataType.getSize(inst.getFileLocation())}"
                        else:
                            # Shift the value by scale and then add to temp register
                            res += f"sli {offsetReg} {temp1} {scale}"

                        self.add_action(transName, res)
                        res = f"add {temp1} {inst.getPointerReg().getAllocation()} {temp1}"
                        self.add_action(transName, res)
                        res = f"movlr {fieldOffset}({temp1}) {ret.getAllocation()} 0 {size}"
                        self.add_action(transName, res)
                    else:
                        #  Note: The scale is incremented by 3 by the instruction. Hence, it only works for 8 byte
                        #  values.
                        #        movwlr                    Xb                      Xs    inc, scale      Xd
                        res += f"movwlr {inst.getPointerReg().getAllocation()}({offsetReg},0,0) {ret.getAllocation()}"
                        self.add_action(transName, res)

                # If a signed sub word is copied from the scratchpad, the value has to be sign extended
                if size != WIRinst.WeaveIRtypes.i64.getSize() and inst.getReturnReg().isSigned():
                    shifts = 64 - size * 8
                    self.add_action(transName, f"sli {ret.getAllocation()} {ret.getAllocation()} {shifts}",
                                    "sign extension for signed sub word load")
                    self.add_action(transName, f"sari {ret.getAllocation()} {ret.getAllocation()} {shifts}",
                                    "sign extension for signed sub word load")
        elif isinstance(inst, WeaveIRarith):
            opCode = ""
            typ = self.ArithOpsTypes.UNKNOWN
            ops, typ = self.get_ops_binaryInst(inst)
            if inst.instType == WIRinst.WeaveIRarithTypes.IADDITION:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "addi"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "add"
            elif inst.instType == WIRinst.WeaveIRarithTypes.ISUBTRACTION:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "subi"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "sub"
            elif inst.instType == WIRinst.WeaveIRarithTypes.IMULT:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "muli"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "mul"
            elif inst.instType == WIRinst.WeaveIRarithTypes.IDIVIDE:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "divi"
                else:
                    opCode = "div"
            elif inst.instType == WIRinst.WeaveIRarithTypes.MODULO:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "modi"
                else:
                    opCode = "mod"

            elif inst.instType == WIRinst.WeaveIRarithTypes.FADDITION:
                if typ == self.ArithOpsTypes.REG_IMM:
                    # TODO: This should be software emulated
                    # Load the value into a register that represents the FP
                    # value
                    errorMsg(
                        "Floating point division with imm value not supported yet ",
                        inst.getFileLocation(),
                    )
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "fadd"
            elif inst.instType == WIRinst.WeaveIRarithTypes.FSUBTRACTION:
                if typ == self.ArithOpsTypes.REG_IMM:
                    # TODO: This should be software emulated
                    # Load the value into a register that represents the FP
                    # value
                    errorMsg(
                        "Floating point division with imm value not supported yet ",
                        inst.getFileLocation(),
                    )
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "fsub"
            elif inst.instType == WIRinst.WeaveIRarithTypes.FMULT:
                if typ == self.ArithOpsTypes.REG_IMM:
                    # TODO: This should be software emulated
                    # Load the value into a register that represents the FP
                    # value
                    errorMsg(
                        "Floating point division with imm value not supported yet ",
                        inst.getFileLocation(),
                    )
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "fmul"
            elif inst.instType == WIRinst.WeaveIRarithTypes.FDIVIDE:
                if typ == self.ArithOpsTypes.REG_IMM:
                    # TODO: This should be software emulated
                    # Load the value into a register that represents the FP
                    # value
                    errorMsg(
                        "Floating point division with imm value not supported yet ",
                        inst.getFileLocation(),
                    )
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "fdiv"
            elif inst.instType == WIRinst.WeaveIRarithTypes.FMULTADD:
                if typ == self.ArithOpsTypes.REG_IMM:
                    # TODO: This should be software emulated
                    # Load the value into a register that represents the FP
                    # value
                    errorMsg(
                        "Floating point multiply-add with imm value not supported yet ",
                        inst.getFileLocation(),
                    )
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "fmadd"
            elif inst.instType == WIRinst.WeaveIRarithTypes.FSQRT:
                if typ == self.ArithOpsTypes.REG_IMM:
                    # TODO: This should be software emulated
                    # Load the value into a register that represents the FP
                    # value
                    errorMsg(
                        "Floating point square root with imm value not supported yet ",
                        inst.getFileLocation(),
                    )
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "fsqrt"
            elif inst.instType == WIRinst.WeaveIRarithTypes.FEXP:
                if typ == self.ArithOpsTypes.REG_IMM:
                    # TODO: This should be software emulated
                    # Load the value into a register that represents the FP
                    # value
                    errorMsg(
                        "Floating point exp with imm value not supported yet ",
                        inst.getFileLocation(),
                    )
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "fexp"
            else:
                errorMsg(
                    f"Unsupported Arithmetic Instruction {inst.instType}",
                    inst.getFileLocation(),
                )

            if inst.instType.isFP():
                opCode += f".{inst.dtype.mapToInstrName()}"

            res += self.create_inst_format(opCode, ops)
            self.add_action(transName, res)
        elif isinstance(inst, WeaveIRbitwise):
            opCode = ""
            ops, typ = self.get_ops_binaryInst(inst)

            if inst.instType == WIRinst.WeaveIRbitwiseTypes.SHFTLFT:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "sli"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "sl"
            elif inst.instType == WIRinst.WeaveIRbitwiseTypes.LSHFTRGT:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "sri"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "sr"
            elif inst.instType == WIRinst.WeaveIRbitwiseTypes.ASHFTRGT:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "sari"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "sar"
            elif inst.instType == WIRinst.WeaveIRbitwiseTypes.BWOR:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "ori"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "or"
            elif inst.instType == WIRinst.WeaveIRbitwiseTypes.BWAND:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "andi"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "and"
            elif inst.instType == WIRinst.WeaveIRbitwiseTypes.BWXOR:
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "xori"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "xor"
            else:
                errorMsg(
                    f"UNREACHABLE: Unknown bitwise operation {inst.instType}",
                    inst.getFileLocation(),
                )
            res += self.create_inst_format(opCode, ops)
            self.add_action(transName, res)
        elif isinstance(inst, WeaveIRShiftArith):
            opCode = ""
            if inst.shift_inst.instType == WIRinst.WeaveIRbitwiseTypes.SHFTLFT:
                opCode = "sl"
            elif inst.shift_inst.instType == WIRinst.WeaveIRbitwiseTypes.LSHFTRGT:
                opCode = "sr"
            else:
                errorMsg(
                    f"UNREACHABLE: SLBW: Unknown shift operation {inst.shift_inst.instType}",
                    inst.getFileLocation(),
                )
            if inst.arith_inst.instType == WIRinst.WeaveIRbitwiseTypes.BWOR:
                opCode += "ori"
                if isinstance(inst.arith_inst.right, WeaveIRimmediate):
                    opCode += "i"
            elif inst.arith_inst.instType == WIRinst.WeaveIRbitwiseTypes.BWAND:
                opCode += "andi"
                if isinstance(inst.arith_inst.right, WeaveIRimmediate):
                    opCode += "i"
            elif inst.arith_inst.instType == WIRinst.WeaveIRarithTypes.IADDITION:
                opCode += "addii"
            elif inst.arith_inst.instType == WIRinst.WeaveIRarithTypes.ISUBTRACTION:
                opCode += "subii"
            else:
                errorMsg(
                    f"UNREACHABLE: SLBW: Unknown bitwise operation {inst.arith_inst.instType}",
                    inst.getFileLocation(),
                )

            ops = []
            for op in inst.getInOps():
                if isinstance(op, WeaveIRimmediate):
                    ops.append(op.name)
                else:
                    ops.append(op.getAllocation())

            ops.insert(1, inst.getReturnReg().getAllocation())
            res += self.create_inst_format(opCode, ops)
            self.add_action(transName, res)
        elif isinstance(inst, WeaveIRbranch):
            opCode = ""
            if inst.instType == WIRinst.WeaveIRBranchTypes.UNCONDITIONAL:
                opCode = "jmp"
                ops = [inst.label]
            else:
                # The comparison operates on integers only. However, for the bit representation of the float
                # reinterpreted as an integer, the operation still returns the correct result. The reason is that
                # in case of e.g. float1 < float2, the mantissa of the larger float is also larger or the exponent of
                # the larger float is larger, when the mantissa is the same.
                # The only case, where this holds not true is when the sign bit is different and the size of the
                # floating point differs. For instance, for a negative 32-bit float all bits from the MSB at
                # position 63 down to position 30 are set to 1. This is not true for a negative double. Therefore,
                # we exclude this case.
                if (
                        inst.left.dtype == WIRinst.WeaveIRtypes.float and
                        inst.right.dtype == WIRinst.WeaveIRtypes.double or
                        inst.left.dtype == WIRinst.WeaveIRtypes.double and
                        inst.right.dtype == WIRinst.WeaveIRtypes.float
                ):
                    errorMsg(
                        "Floating point values of different sizes cannot be compared",
                        inst.getFileLocation(),
                    )
                ops, typ = self.get_ops_binaryInst(inst)
                if inst.instType == WIRinst.WeaveIRBranchTypes.CONDITIONALEQ:
                    if typ == self.ArithOpsTypes.REG_IMM:
                        opCode = "beqi"
                    elif typ == self.ArithOpsTypes.REG_REG:
                        opCode = "beq"
                elif inst.instType == WIRinst.WeaveIRBranchTypes.CONDITIONALNEQ:
                    if typ == self.ArithOpsTypes.REG_IMM:
                        opCode = "bnei"
                    elif typ == self.ArithOpsTypes.REG_REG:
                        opCode = "bne"
                elif inst.instType == WIRinst.WeaveIRBranchTypes.CONDITIONALLT:
                    if typ == self.ArithOpsTypes.REG_IMM:
                        opCode = "blti"
                    elif typ == self.ArithOpsTypes.REG_REG:
                        opCode = "bgt"
                        # swap the operands
                        ops = [ops[1], ops[0]]
                elif inst.instType == WIRinst.WeaveIRBranchTypes.CONDITIONALGT:
                    if typ == self.ArithOpsTypes.REG_IMM:
                        opCode = "bgti"
                    elif typ == self.ArithOpsTypes.REG_REG:
                        opCode = "bgt"
                elif inst.instType == WIRinst.WeaveIRBranchTypes.CONDITIONALGE:
                    if typ == self.ArithOpsTypes.REG_IMM:
                        opCode = "bgei"
                    elif typ == self.ArithOpsTypes.REG_REG:
                        opCode = "ble"
                        # swap the operands
                        ops = [ops[1], ops[0]]
                elif inst.instType == WIRinst.WeaveIRBranchTypes.CONDITIONALLE:
                    if typ == self.ArithOpsTypes.REG_IMM:
                        opCode = "blei"
                    elif typ == self.ArithOpsTypes.REG_REG:
                        opCode = "ble"
                else:
                    errorMsg(
                        "UNREACHABLE: Unknown instruction type for WeaveIRBranch translation",
                        inst.getFileLocation(),
                    )
                ops.append(inst.label)

                if not inst.isSigned():
                    opCode += "u"

            res += self.create_inst_format(opCode, ops)
            self.add_action(transName, res)
        elif isinstance(inst, WeaveIRcompare):
            opCode = ""
            ops, typ = self.get_ops_binaryInst(inst)
            # Check if types are integers
            if not (
                    (inst.left.dtype.isInteger and inst.right.dtype.isInteger)
                    or (inst.left.dtype.isPointer and inst.right.dtype.isPointer)
            ):
                errorMsg(
                    "Only integer comparison instructions are supported."
                    f" Comparing {inst.left.dtype.name} to {inst.right.dtype.name}",
                    inst.getFileLocation(),
                )

            if (inst.instType == WIRinst.WeaveIRcompareTypes.EQUAL or
                    inst.instType == WIRinst.WeaveIRcompareTypes.NOTEQUAL):
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "ceqi"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "ceq"
            elif (inst.instType == WIRinst.WeaveIRcompareTypes.UGREAT or
                  inst.instType == WIRinst.WeaveIRcompareTypes.ULESSEQ):
                warningMsg("There is no support for unsigned greater than in ISAv2. Assuming signed")
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "cgti"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "cgt"
            elif (inst.instType == WIRinst.WeaveIRcompareTypes.SGREAT or
                  inst.instType == WIRinst.WeaveIRcompareTypes.SLESSEQ):
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "cgti"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "cgt"
            elif (inst.instType == WIRinst.WeaveIRcompareTypes.ULESS or
                  inst.instType == WIRinst.WeaveIRcompareTypes.UGREATEQ):
                warningMsg("There is no support for an unsigned less-than instruction in the ISA. Assuming signed" +
                           str(inst.getFileLocation()))
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "clti"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "clt"
            elif (inst.instType == WIRinst.WeaveIRcompareTypes.SLESS or
                  inst.instType == WIRinst.WeaveIRcompareTypes.SGREATEQ):
                if typ == self.ArithOpsTypes.REG_IMM:
                    opCode = "clti"
                elif typ == self.ArithOpsTypes.REG_REG:
                    opCode = "clt"

            res += self.create_inst_format(opCode, ops)
            self.add_action(transName, res)

            # Negating the result of the comparison for instructions that we do not have.
            # E.g. a >= 5 is translated into a < 5 and here this result is negated.
            if (
                    inst.instType == WIRinst.WeaveIRcompareTypes.UGREATEQ
                    or inst.instType == WIRinst.WeaveIRcompareTypes.ULESSEQ
                    or inst.instType == WIRinst.WeaveIRcompareTypes.SGREATEQ
                    or inst.instType == WIRinst.WeaveIRcompareTypes.SLESSEQ
                    or inst.instType == WIRinst.WeaveIRcompareTypes.NOTEQUAL
            ):
                self.add_action(transName, f"xori {inst.getReturnReg().getAllocation()} "
                                           f"{inst.getReturnReg().getAllocation()} 1")
        elif isinstance(inst, WeaveIRsend):
            ops = []
            for op in inst.getInOps():
                if isinstance(op, WeaveIRimmediate) or isinstance(op, WeaveIRsymPtr):
                    ops.append(op.name)
                # elif isinstance(op, WeaveIRsymPtr):
                #     # Send instructions take registers, not immediate values as operand
                #     # when referring to event IDs. Therefore, we need to load the EventID
                #     # immediate value into a register before sending the event.
                #     temp1 = self.regAlloc.getTempReg(0).name
                #     res += f"movir {temp1} {op.name}"
                #     self.add_action(evNum, res)
                #     res = ""
                #     ops.append(temp1)
                else:
                    ops.append(op.getAllocation())

            res += self.create_inst_format(inst.instType.value, ops)
            self.add_action(transName, res)
        elif isinstance(inst, WeaveIRcast):

            def getFPPrecision() -> str:
                srcPrecision = inReg.dtype.mapToInstrName()
                dstPrecision = outReg.dtype.mapToInstrName()
                return f"{srcPrecision}.{dstPrecision}"

            inReg = inst.getInOps()[0]
            outReg = inst.getReturnReg()
            if (
                    (inReg.dtype.isInteger and outReg.dtype.isInteger)
                    or (inReg.dtype.isPointer and outReg.dtype.isInteger)
                    or (inReg.dtype.isInteger and outReg.dtype.isPointer)
            ):
                # TODO: This can be optimized out, but we don't know how sub word sizes will be managed in the future
                res += f"addi {inst.getInOps()[0].getAllocation()} {inst.getReturnReg().getAllocation()} 0"
            elif inReg.dtype.isFloatingPoint and outReg.dtype.isFloatingPoint:
                res += f"fcnvt.{getFPPrecision()} {inReg.getAllocation()} {outReg.getAllocation()}"
            elif (inReg.dtype.isFloatingPoint and outReg.dtype.isInteger or
                  inReg.dtype.isInteger and outReg.dtype.isFloatingPoint):
                precision = getFPPrecision()
                possibleConversions = ["64.i64", "64.32", "64.b16", "32.i32", "32.b16", "32.64", "b16.32", "b16.64",
                                       "i32.32", "i64.64"]

                if precision in possibleConversions:
                    res += f"fcnvt.{precision} {inReg.getAllocation()} {outReg.getAllocation()}"
                else:
                    if inReg.dtype.isInteger and outReg.dtype.isFloatingPoint:
                        # first we convert the integer to the same size as the float
                        res += f"addi {inReg.getAllocation()} {outReg.getAllocation()} 0"
                        self.add_action(transName, res, f"casting i{inReg.dtype.getSize() * 8}."
                                                        f"i{outReg.dtype.getSize() * 8}")
                        # and then we convert the integer to float
                        res = (
                            f"fcnvt.i{outReg.dtype.getSize() * 8}.{outReg.dtype.mapToInstrName()} {outReg.getAllocation()} "
                            f"{outReg.getAllocation()}")
                    else:
                        # first we convert the float into the same size as the integer
                        res += (
                            f"fcnvt.{inReg.dtype.mapToInstrName()}.i{inReg.dtype.getSize() * 8} {inReg.getAllocation()} "
                            f"{outReg.getAllocation()}")
                        self.add_action(transName, res, f"casting {inReg.dtype.getSize() * 8}."
                                                        f"i{inReg.dtype.getSize() * 8}")
                        # and then convert the integer to float
                        res = f"addi {outReg.getAllocation()} {outReg.getAllocation()} 0"
            else:
                errorMsg(
                    f"Unsupported cast from {inReg.dtype.name} to {outReg.dtype.name}",
                    inst.getFileLocation(),
                )

            self.add_action(transName, res, "This is for casting. May be used later on")
        elif isinstance(inst, WeaveIRupdate):
            update_ops = inst.getInOps()
            op_num = 1
            if not isinstance(update_ops[-1], WeaveIRimmediate):
                errorMsg(
                    "Last operand of update instruction must be an immediate value",
                    inst.getFileLocation(),
                )
            mask = update_ops[-1].getValue()
            result_reg = inst.getReturnReg()
            original_evw = update_ops[0]
            # The event word should be in a register. If it is
            # an immediate value, we need to load it into a register
            if isinstance(original_evw, WeaveIRimmediate):
                # Initialize result register to original_evw
                res += f"movir {result_reg.getAllocation()} {original_evw.getValue()}"
                self.add_action(transName, res)
                res = ""
                original_evw = result_reg

            # Check if we can use evlb instruction
            if mask & 0b1 and result_reg == original_evw:
                event_label = update_ops[op_num]
                if isinstance(event_label, WeaveIRregister):
                    errorMsg(
                        "Event label must be an immediate value or a label",
                    )
                res += f"evlb {result_reg.getAllocation()} {event_label.name}"
                self.add_action(transName, res)
                res = ""
                mask = mask & 0b1110
                op_num += 1

            def getNextOpSameType(
                    begin: int,
                    op_num: int,
                    other_op: Union[WeaveIRimmediate, WeaveIRregister, WeaveIRsymPtr],
                    res_reg: WeaveIRregister,
            ):
                # Iterate over the rest of the bits in the bitmask
                for i in range(begin, 4):
                    # get class and compare
                    if mask & (1 << i):
                        if isinstance(
                                update_ops[op_num], WeaveIRregister
                        ) and isinstance(other_op, WeaveIRregister):
                            return i, update_ops[op_num]
                        elif (
                                (
                                        isinstance(update_ops[op_num], WeaveIRimmediate)
                                        or isinstance(update_ops[op_num], WeaveIRsymPtr)
                                )
                                and (
                                        isinstance(other_op, WeaveIRimmediate)
                                        or isinstance(other_op, WeaveIRsymPtr)
                                )
                                and (
                                        res_reg.isControl
                                        and res_reg.number == WIRinst.WeaveIRcontrolRegs.CEVNT
                                )
                        ):
                            # This complex condition is because evii will modify the current event word only.
                            return i, update_ops[op_num]
                    op_num += 1
                return None, None

            origin = original_evw.getAllocation()
            for i in range(0, 4):
                if mask & (1 << i):
                    op = update_ops[op_num]
                    next_op_idx, next_op = getNextOpSameType(i + 1, op_num + 1, op, result_reg)
                    if next_op_idx is None:
                        if isinstance(op, WeaveIRimmediate) or isinstance(op, WeaveIRsymPtr):
                            res += f"evi {origin} {result_reg.getAllocation()} {op.name} {1 << i}"
                        else:
                            res += f"ev {origin} {result_reg.getAllocation()} {op.getAllocation()} {op.getAllocation()} {1 << i}"
                    else:
                        if (
                                isinstance(op, WeaveIRimmediate)
                                or isinstance(op, WeaveIRsymPtr)
                                and result_reg
                        ):
                            res += (
                                    f"evii {original_evw.getAllocation()} "
                                    + f"{op.name} {next_op.name} {(1 << i) | (1 << next_op_idx)}"
                            )
                        else:
                            res += (
                                    f"evr {original_evw.getAllocation()} {result_reg.getAllocation()} "
                                    + f"{op.getAllocation()} {next_op.getAllocation()} {(1 << i) | (1 << next_op_idx)}"
                            )
                    # Clear the already used bits
                    mask = mask & ~(1 << i)
                    if next_op_idx is not None:
                        mask = mask & ~(1 << next_op_idx)
                    op_num += 1
                    self.add_action(transName, res)
                    res = ""
                    # Change the origin to the result register for the upcoming instructions
                    origin = result_reg.getAllocation()

        elif isinstance(inst, WeaveIRcopyOperands):
            ops = inst.getInOps()
            copy_inst = "bcpyoli"
            if isinstance(ops[2], WeaveIRregister):
                copy_inst = "bcpyol"
            ops = [
                op.getAllocation() if isinstance(op, WeaveIRregister) else op.name
                for op in ops
            ]

            res += self.create_inst_format(copy_inst, ops)
            self.add_action(transName, res)
        elif isinstance(inst, WeaveIRyield):
            if inst.instType == WIRinst.WeaveIRyieldTypes.YIELD:
                res += "yield"
                self.add_action(transName, res)
            elif inst.instType == WIRinst.WeaveIRyieldTypes.YIELD_TERMINATE:
                res += "yield_terminate"
                self.add_action(transName, res)
            else:
                errorMsg(
                    "UNREACHABLE: Incorrect yield instruction type. "
                    f"{inst.instType.name} Not supported",
                    inst.getFileLocation(),
                )
        elif isinstance(inst, WeaveIRcomment):
            self._add_comment(inst)
            return False
        elif isinstance(inst, WeaveIRassembly):
            inst.applyOperands()

            # apply operands to label, has to be an "i" or "l" operand, cannot be a register
            if label is not None and len(res) > 0:
                for op in inst.getInOps():
                    if WIRinst.WeaveIRasmConstraints.REGISTER in op.constraints:
                        continue
                    label = op.applyOperand(label)
                res = f"{label}: " if label else ""

            if inst.isNativeInline:
                self._add_inlineasm_python(inst.getLines(), res)
            else:
                self._add_inlineasm_action(transName, inst.getLines(), res)
        elif isinstance(inst, WeaveIRprint):
            ops = self._gatherOperandsPrintPerflog(inst, f"'{inst.getInOps()[0].name}'",
                                                   inst.getInOps()[1:])
            res += self.create_inst_format("print", ops)
            self.add_action(transName, res)

        elif isinstance(inst, WeaveIRperflog):
            ops = self._gatherOperandsPrintPerflog(inst, f"'{inst.getInOps()[1].name}'",
                                                   inst.getInOps()[2:])
            ops.insert(0, inst.getInOps()[0].name)
            res += self.create_inst_format(f"perflog 1", ops)
            self.add_action(transName, res)

        elif isinstance(inst, WeaveIRhash):
            op = inst.getInOps()[0].getAllocation()
            if inst.hashType == WIRinst.WeaveIRhashTypes.HASHVALUE:
                nWords = ''
            else:
                nWords = f" {inst.getInOps()[1].name}"

            res += f"{inst.hashType.value} {op} {inst.getReturnReg().getAllocation()}{nWords}"
            self.add_action(transName, res)
        elif isinstance(inst, WeaveIRphi):
            errorMsg(f"Instruction {type(inst)} should have been removed before lowering. Something went wrong! {inst}")
            return False
        else:
            warningMsg(f"Instruction {type(inst)} not supported for lowering yet")
            return False
        return True

    def allocateRegistersInScope(self, scope: WeaveIRscope):
        self.regAlloc.allocate(scope)

        for d in scope.getDeclarations():
            if not d.isStatic and not d.isStruct and not d.isConstant and not d.isUnion:
                if isinstance(d, WeaveIRParamDecl):
                    self.add_line(
                        f"## Param \"{d.name}\" uses Register {d.getRegs[0].allocated}, scope ({scope.name})"
                    )
                else:
                    self.add_line(
                        f"## Scoped Variable \"{d.name}\" uses Register {d.getRegs[0].allocated}"
                        f", scope ({scope.name})"
                    )
            elif not d.isStatic and not d.isConstant:

                def addComments(ty: WeaveIRstructDecl, name: str):
                    for field in ty.getFields():
                        if isinstance(field, WeaveIRstructDecl):
                            addComments(field, name + "." + field.name)
                        elif not isinstance(field, WeaveIRpadding):
                            self.add_line(
                                f"## Scoped variable \"{name}.{field.name}\" uses Register "
                                f"{field.getAsOperand().getAllocation()}, scope {scope.name}"
                            )

                addComments(d.dataType, d.name)

    def traverse(self):
        debugMsg(5, "Starting PythonCodeGen")
        self.globalConstantsTranslate()
        self.programTranslate()
        return "\n".join(self.out)
