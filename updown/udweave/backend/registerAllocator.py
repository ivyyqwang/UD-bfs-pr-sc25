from Weave.WeaveIRenums import *
from Weave.WeaveIR import *

# required to run the code prior to Pythin version 3.9
from typing import Optional, Tuple


class AllocRegTypes(Enum):
    GPR_ISAV1 = {"prefix": "UDPR_", "min": 0, "max": 15}  # UD registers
    GPR_ISAV2 = {"prefix": "X", "min": 16, "max": 31}  # user registers
    OB_ISAV1 = {"prefix": "OB_", "min": 0, "max": 8}  # operand buffer
    OB_ISAV2 = {"prefix": "X", "min": 8, "max": 15}
    CONTROL_ISAV2_NETID = {"prefix": "X", "val": 0}
    CONTROL_ISAV2_CCONT = {"prefix": "X", "val": 1}
    CONTROL_ISAV2_CEVNT = {"prefix": "X", "val": 2}
    CONTROL_ISAV2_LMBASE = {"prefix": "X", "val": 7}


class AllocRegister:
    def __init__(self, ty: AllocRegTypes, number: int = None):
        self.type = ty
        self.number = number
        self._lastUsedInstr = None

    @property
    def name(self) -> str:
        return self.type.value["prefix"] + str(self.number)

    @property
    def prefix(self) -> str:
        return self.type.value["prefix"]

    @property
    def asNumber(self) -> int:
        return self.number

    def setNumberFromStr(self, strName: str) -> None:
        self.number = int(strName.split(AllocRegTypes.GPR_ISAV2.name)[-1])

    def __eq__(self, other) -> bool:
        return self.name == other.name

    def __str__(self) -> str:
        return self.name

    def setLastUsedInstr(self, instr: Optional[WeaveIRinstruction]) -> None:
        self._lastUsedInstr = instr

    def getLastUsedInstr(self) -> WeaveIRinstruction:
        return self._lastUsedInstr


class WeaveRegisterAllocator(ABC):
    """Interface to allow multiple implementations of register allocators
    Abstract class, do not implement
    """

    def __init__(self):
        self.all_regs = [
            AllocRegister(AllocRegTypes.GPR_ISAV2, i)
            for i in range(
                AllocRegTypes.GPR_ISAV2.value["min"],
                AllocRegTypes.GPR_ISAV2.value["max"] + 1,
            )
        ]
        self.all_op_regs = [
            AllocRegister(AllocRegTypes.OB_ISAV2, i)
            for i in range(
                AllocRegTypes.OB_ISAV2.value["min"],
                AllocRegTypes.OB_ISAV2.value["max"] + 1,
            )
        ]
        # There is a special register (X3) that can be used for a 9th operand
        self.all_op_regs.append(AllocRegister(AllocRegTypes.OB_ISAV2, 3))
        self.notUsed = self.all_regs.copy()

    def regExists(self, name: str) -> bool:
        return len(list(filter(lambda a: a.name == name, self.all_regs))) != 0

    def markUsed(self, reg: AllocRegister) -> None:
        try:
            self.notUsed.remove(reg)
        except ValueError:
            pass

    def markUnused(self, reg: AllocRegister) -> None:
        self.notUsed.append(reg)

    def getTempReg(self, num: int, event: Optional[WeaveIRevent]) -> AllocRegister:
        if num < len(self.notUsed):
            return self.notUsed[num]
        errorMsg("Not enough registers available to lower to python")

    def changeAvailableRegisters(self, newSet: list) -> None:
        """In case the user wants to restrict the available registers

        Args:
            newSet (list): List of str containing register names
        """
        self.all_regs = newSet

    def getControlReg(self, reg: WeaveIRregister) -> AllocRegister:
        if not reg.isControl:
            errorMsg(
                "Trying to get a control register on a register "
                f"that is of type {reg.regType}"
            )
        if reg.number == WeaveIRcontrolRegs.CCONT:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_CCONT,
                AllocRegTypes.CONTROL_ISAV2_CCONT.value["val"],
            )
        if reg.number == WeaveIRcontrolRegs.CEVNT:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_CEVNT,
                AllocRegTypes.CONTROL_ISAV2_CEVNT.value["val"],
            )
        if reg.number == WeaveIRcontrolRegs.NETID:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_NETID,
                AllocRegTypes.CONTROL_ISAV2_NETID.value["val"],
            )
        if reg.number == WeaveIRcontrolRegs.LMBASE:
            return AllocRegister(
                AllocRegTypes.CONTROL_ISAV2_LMBASE,
                AllocRegTypes.CONTROL_ISAV2_LMBASE.value["val"],
            )
        errorMsg(f"UNREACHABLE: Unknown control register type {reg.number}")

    @abstractmethod
    def allocate(self, th: WeaveIRscope) -> None:
        """
            This is the main function of the register allocator.
        """


class WeaveSimpleRegAlloc(WeaveRegisterAllocator):
    """A simple dumb register allocator for nonSSA form"""

    def __init__(self):
        debugMsg(6, "Creating simple register allocator")
        super().__init__()

    def recursiveTypeReg(self, ty: AllocRegTypes, thread: bool) -> None:
        for field in ty.getFields():
            if isinstance(field, WeaveIRstructDecl):
                self.recursiveTypeReg(field, thread)
            elif not isinstance(field, WeaveIRpadding):
                val = self.getReg(field.getRegs[0])
                field.getRegs[0].allocate(val.name)
                self.markUsed(val)
                debugMsg(
                    6, f"Allocating {'thread' if thread else 'local'} {val.name} for {field.getRegs[0].name}"
                )

    def getReg(self, reg: WeaveIRregister, inst: WeaveIRinstruction = None) -> AllocRegister:
        if reg.isControl:
            return self.getControlReg(reg)
        if reg.isOBuff:
            return self.getParamReg(reg)
        if reg.number >= len(self.all_regs):
            if inst:
                errorMsg(
                    f"Not enough registers to allocate register {reg.number} for {inst.to_string(0)}",
                    inst.getFileLocation()
                )
            else:
                errorMsg(f"Not enough registers to allocate register {reg.number}")
        return self.all_regs[reg.number]

    def getParamReg(self, reg: WeaveIRregister) -> AllocRegister:
        if reg.isControl:
            return self.getControlReg(reg)
        if reg.number >= len(self.all_op_regs):
            errorMsg(f"Not enough registers to allocate register {reg.number} for parameter")
        return self.all_op_regs[reg.number]

    def allocate(self, scope: WeaveIRscope) -> None:
        # This assumes nonSSA form. It just uses the same
        # register number, however, it fails if there are no more registers.
        # Register allocation occurs during code gen.

        # Thread local variables are kept across events
        # single allocation and propagate to all instructions
        for decl in scope.getDeclarations():
            if decl.isStatic or decl.isConstant:
                continue
            if decl.isStruct or decl.isUnion:
                self.recursiveTypeReg(decl.dataType, scope.depth == 1)
            elif isinstance(decl, WeaveIRParamDecl):
                val = self.getParamReg(decl.getRegs[0])
                decl.getRegs[0].allocate(val.name)
                self.markUsed(val)
                debugMsg(
                    6, f"Allocating register {val.name} for parameter {decl.name} in scope {scope.name}"
                )
            else:
                val = self.getReg(decl.getRegs[0])
                decl.getRegs[0].allocate(val.name)
                self.markUsed(val)
                debugMsg(
                    6, f"Allocating register {val.name} for {decl.name} in scope {scope.name}"
                )
        self.allocateReturnRegs(scope)

    def allocateReturnRegs(self, scope: WeaveIRscope) -> None:
        for s in scope.getBodies():
            if isinstance(s, WeaveIRthread):
                for section in s.sections:
                    if isinstance(section, WeaveIRscope):
                        self.allocateReturnRegs(section)
                    elif isinstance(section, WeaveIRevent):
                        self.allocateRegsForEvents(section)
            if isinstance(s, WeaveIRevent):
                self.allocateRegsForEvents(s)

    def allocateRegsForEvents(self, event: WeaveIRevent):
        for bb in event.basic_blocks:
            for inst in bb.instructions:
                if isinstance(inst, WeaveIRinstruction):
                    if (
                            inst.getReturnReg()
                            and not inst.getReturnReg().alreadyAllocated
                    ):
                        val = self.getReg(inst.getReturnReg(), inst)
                        inst.getReturnReg().allocate(val.name)

                        debugMsg(
                            6,
                            f"Allocating {val.name} for {inst.getReturnReg().name}",
                        )
                    readOps = inst.getInOps()
                    for op in readOps:
                        if (
                                isinstance(op, WeaveIRregister)
                                and not op.alreadyAllocated
                        ):
                            val = self.getReg(op, inst)
                            op.allocate(val.name)
                            debugMsg(6, f"Allocating {val.name} for {op.name}")


class WeaveLifetimeRegAlloc(WeaveRegisterAllocator):

    def __init__(self):
        debugMsg(6, "Creating life time register allocator")
        super().__init__()
        self._used = []
        self._regsUnUsedInEvent = {}

    def getGPR(self, inst, event: Optional[WeaveIRevent]) -> AllocRegister:
        if len(self.notUsed) == 0 and inst is not None:
            errorMsg(f"Not enough registers available to allocate {inst.to_string(0)} {inst.getFileLocation()}")
        reg = self.notUsed.pop(0)
        self._used.append(reg)

        # keep track of the unused registers per event
        if event is not None:
            self._regsUnUsedInEvent[event] = self.notUsed.copy()
        return reg

    def putGPR(self, reg: AllocRegister) -> None:
        # We return the register to the beginning of the list. The purpose is to easily determine the maximum
        # used register in the final EFA Python file by searching the file for X31, X30, ....
        self.notUsed.insert(0, reg)
        self._used.remove(reg)

    def getTempReg(self, num: int, event: WeaveIRevent) -> AllocRegister:
        if event in self._regsUnUsedInEvent:
            if num >= len(self._regsUnUsedInEvent[event]):
                errorMsg("Not enough registers available to lower to python")
            return self._regsUnUsedInEvent[event][num]
        errorMsg(f"Event {event} not found in the register allocator")

    def allocate(self, scope: WeaveIRscope) -> None:
        """
        @TODO ensure that this is called for the scope that has the thread inside
        @TODO after that, the self.used etc attributes need to be reset.
        """
        # This assumes SSA form. The allocation fails if there are no more registers.
        # Thread local variables are kept across events
        # Single allocation and propagate to all instructions

        # get the declarations in the current scope
        decls = scope.getDeclarations()

        #  reset the used registers
        self._used = []
        self.notUsed = self.all_regs.copy()

        # Iterate through the declarations searching for thread and global declarations.
        # These declarations are assigned a register immediately
        for decl in decls:
            if (isinstance(decl, WeaveIRthreadDecl) or isinstance(decl, WeaveIRGlobalDecl)) and not decl.isAllocated:
                # since it is a thread or global declaration, we remove the register from the pool, so that
                # it is never reassigned.
                reg = self.notUsed.pop(0)
                decl.updateVirtualRegs(decl.getRegs, reg)
                debugMsg(6, f"Allocating register {reg.name} for {decl.name} in scope {scope.name}")

        # Iterate through the instructions in the scope's body
        # Search in the operands for the declarations. If the declaration is not yet allocated, pop a free register
        # from the pool of GPRs and assign it to the declaration. Then, search from the instructions from the bottom
        # up to find, when the declaration is used last. Store this instruction with the just allocated register.
        # Before moving on to the next instruction, check, if the current instruction equals any of the
        # lastUsedInstruction in the usedRegisters array. If there is a positive match, deallocate the register.
        for s in scope.getBodies():
            if isinstance(s, WeaveIRthread):
                for section in s.sections:
                    if isinstance(section, WeaveIRscope):
                        self.allocate(section)
                    elif isinstance(section, WeaveIRevent):
                        self.allocateEventRegisters(section)
            if isinstance(s, WeaveIRevent):
                self.allocateEventRegisters(s)

        # release all registers
        self._used.clear()
        self.notUsed = self.all_regs.copy()

    def allocateEventRegisters(self, event: WeaveIRevent) -> None:
        self._regsUnUsedInEvent[event] = self.notUsed.copy()
        self.allocateRegsForParams(event)
        self.allocateRegsForEvent(event)
        self.searchUnallocatedOperands(event)
        self.deadCodeRemoval(event)
        self.removePhiNodes(event)
        self.releaseEventRegisters(event)

    def releaseEventRegisters(self, event: WeaveIRevent) -> None:
        """ Release the registers used in the event. Leave the thread registers untouched."""
        for reg in self._used:
            self.putGPR(reg)

    def allocateRegsForParams(self, event: WeaveIRevent):
        decls = event.getParams()
        usedRegs = []
        for decl in decls:
            if not decl.isAllocated:
                if len(self.all_op_regs) == 0:
                    errorMsg("Not enough registers available to allocate " + decl.name)

                reg = self.all_op_regs.pop(0)
                usedRegs.append(reg)
                decl.updateVirtualRegs(decl.getRegs, reg)
                debugMsg(6, f"Allocating register {reg.name} for {decl.name} in scope {event.name}")

        # after we finished assignment of the parameters, return the registers to the pool
        self.all_op_regs = usedRegs + self.all_op_regs

    def allocateRegsForEvent(self, event: WeaveIRevent):
        decls = event.ctx_scope.getAllNestedDeclarations()
        insts = self.flattenBB(event)
        for inst in insts:
            if isinstance(inst, WeaveIRassembly):
                for op in inst.getInOps():
                    decl = op.varName
                    if (
                            WIRinst.WeaveIRasmConstraints.REGISTER in op.constraints or
                            WIRinst.WeaveIRasmConstraints.OUTPUT in op.constraints) and not decl.isAllocated:
                        lastInstruction, lastInstructionWrite = self.lastInstruction(event, decl, inst, insts[-1], True)
                        virtualRegs = self.getVirtualRegistersForRange(event, decl, inst, lastInstruction)
                        reg = self.getGPR(inst, event)
                        reg.setLastUsedInstr(lastInstruction)
                        decl.updateVirtualRegs(virtualRegs, reg)
                        debugMsg(6, f"Instruction: {inst}, last read: {lastInstruction}, "
                                    f"allocating {reg.name} (event: {event.name}")
                self.releaseUsedRegisters(event, inst, decls)

            elif isinstance(inst, WeaveIRinstruction):
                if inst.getReturnReg():
                    if not inst.getReturnReg().alreadyAllocated:
                        # find the associated declaration
                        decl = inst.getReturnReg().getDecl()
                        if decl and not decl.isAllocated:

                            # from the current instruction that writes a value to the to-be-assigned register, go down
                            # in the flattened list of the instructions to find the last instruction where the register
                            # is read from before either the declaration is written again or the event ends.
                            lastInstruction, lastInstructionWrite = self.lastInstruction(event, decl, inst, insts[-1],
                                                                                         False)
                            if lastInstruction is None or lastInstructionWrite:
                                warningMsg(f"Unused variable {decl.name} in event {event.name}" +
                                           str(inst.getFileLocation()))
                                continue

                            # assign the register to the declaration for instructions between inst and lastInstruction
                            virtualRegs = self.getVirtualRegistersForRange(event, decl, inst, lastInstruction)
                            reg = self.getGPR(inst, event)
                            reg.setLastUsedInstr(lastInstruction)
                            decl.updateVirtualRegs(virtualRegs, reg)
                            debugMsg(6, f"Instruction: {inst}, last read: {lastInstruction}, "
                                        f"allocating {reg.name} (event: {event.name}")

                # inst might be an intrinsic function or a store to memory. Both do not return anything
                else:
                    for op in inst.getInOps():
                        # For intrinsic functions, the operand must have been initialized earlier.
                        # However, an exception is to be made, if event labels are used as operands. In this case, a
                        # temporary register is to be assigned and it is normal, that it is not initialized.
                        # If not, echo a warning and assign a register temporary, which is essentially freed immediately
                        # after the instruction.
                        if isinstance(op, WeaveIRregister) and not op.alreadyAllocated:
                            if op.toBeInitialized:
                                warningMsg(f"Operand {op.name} in instruction \"{inst.to_string(0)}\" has not been "
                                       f"initialized. " + str(inst.getFileLocation()))
                            decl = op.getDecl()
                            reg = self.getGPR(inst, event)
                            reg.setLastUsedInstr(inst)
                            decl.updateVirtualRegs({op}, reg)

                self.releaseUsedRegisters(event, inst, decls)

    def releaseUsedRegisters(self, event: WeaveIRevent, inst: WeaveIRinstruction, decls: list) -> None:
        for reg in reversed(self._used):
            if reg.getLastUsedInstr() is None or reg.getLastUsedInstr() == inst:
                self.putGPR(reg)
                for decl in decls:
                    if decl.getPhysicalReg() is not None and decl.getPhysicalReg() == reg:
                        decl.setPhysicalReg(None)
                        debugMsg(6,
                                 f"Deallocating {reg.name} from {decl.name} in scope {event.name}")
                        break

    def lastInstruction(self, event: WeaveIRevent, currentDecl: WeaveIRDecl,
                        upperBoundInstr: WeaveIRinstruction, lowerBoundInstr: WeaveIRinstruction, includeStart: bool) \
            -> Tuple[Optional[WeaveIRinstruction], bool]:
        """ Searches from the upper bound to find the last instruction where the declaration is used in the operand
        list. """

        insts = self.getInstrRange(event, upperBoundInstr, lowerBoundInstr, False, includeStart)

        lastInstruction = None
        lastInstructionWrite = None

        for inst in insts:
            if isinstance(inst, WeaveIRinstruction):
                hasBeenRead = False

                # not found
                if inst == lowerBoundInstr:
                    return lastInstruction, lastInstructionWrite

                # check, if the instruction is a phi node
                # We found that the next instruction that uses this declaration writes to it. However, it might
                # not be true. Consider the following situation
                #   if(condition) {
                #       tmp = 1; //<--
                #   } else {
                #       tmp = 2;
                #   }
                #   print("%d", tmp);
                # Consider that we are currently looking at the instruction marked with //<--. The next
                # instruction that uses the declaration tmp is the print statement. However, the print statement
                # in a flat array holding the instruction, the next instruction that handles tmp is `tmp = 2`.
                # Hence, we have to check, if there is a phi node later, that reads tmp to avoid this
                # situation.
                if isinstance(inst, WeaveIRphi) and inst.getDeclaration() == currentDecl:
                    lastInstruction = inst
                    lastInstructionWrite = False
                    continue

                for op in inst.getInOps():
                    if isinstance(op, WeaveIRregister):
                        readDecl = op.getDecl()
                        if readDecl and readDecl == currentDecl:
                            lastInstruction = inst
                            lastInstructionWrite = False

                            # The instruction might also write to the current declaration
                            # for instance, in `j = j + 1`
                            hasBeenRead = True
                            break

                    elif isinstance(op, WeaveIRbinaryOps):
                        returnReg: WeaveIRregister = op.getReturnReg()
                        if returnReg:
                            readDecl = returnReg.getDecl()
                            if readDecl and readDecl == currentDecl:
                                lastInstruction = inst
                                lastInstructionWrite = False
                                hasBeenRead = True
                                break

                    elif isinstance(op, WeaveIRDecl) and op == currentDecl:
                        lastInstruction = inst
                        lastInstructionWrite = False
                        hasBeenRead = True
                        break

                    elif isinstance(op, WeaveIRasmOperand) and op.varName == currentDecl:
                        if WIRinst.WeaveIRasmConstraints.REGISTER in op.constraints:
                            lastInstruction = inst
                            lastInstructionWrite = False
                            hasBeenRead = True
                        elif WIRinst.WeaveIRasmConstraints.OUTPUT in op.constraints:
                            lastInstruction = inst
                            if lastInstructionWrite is None:
                                lastInstructionWrite = True
                            hasBeenRead = True

                # check, if the instruction is writing to the current declaration
                if not hasBeenRead and inst.getReturnReg() is not None:
                    decl = inst.getReturnReg().getDecl()
                    if decl and decl == currentDecl:
                        lastInstruction = inst
                        lastInstructionWrite = True

        return lastInstruction, lastInstructionWrite

    def getInstrRange(self, event: WeaveIRevent, upperBoundInstr: WeaveIRinstruction,
                      lowerBoundInstr: WeaveIRinstruction, reverse: bool, includeStart: bool) -> list:
        insts = self.flattenBB(event)
        result = []
        searchActive = False
        if reverse:
            insts = reversed(insts)
            startBound = lowerBoundInstr
            endBound = upperBoundInstr
        else:
            startBound = upperBoundInstr
            endBound = lowerBoundInstr

        for inst in insts:
            if inst == startBound:
                searchActive = True
                if not includeStart:
                    continue  # skip the just found instruction
            if searchActive:
                result.append(inst)
                if inst == endBound:
                    return result
        return result

    def getVirtualRegistersForRange(self, event: WeaveIRevent, decl: WeaveIRDecl, upperBoundInstr: WeaveIRinstruction,
                                    lowerBoundInstr: WeaveIRinstruction) -> set:
        """ Returns a sub list of the registers for a declaration between the start and end instruction. """
        virtualRegs = set()
        insts = self.getInstrRange(event, upperBoundInstr, lowerBoundInstr, False, True)

        for inst in insts:
            if isinstance(inst, WeaveIRinstruction):
                reg = inst.getReturnReg()
                if reg is not None and reg in decl.getRegs:
                    virtualRegs.add(inst.getReturnReg())
                for op in inst.getInOps():
                    if isinstance(op, WeaveIRregister) and op in decl.getRegs:
                        virtualRegs.add(op)
                    elif isinstance(op, WeaveIRbinaryOps) and op.getReturnReg() in decl.getRegs:
                        virtualRegs.add(op.getReturnReg())
                    elif isinstance(op, WeaveIRDecl) and op == decl:
                        virtualRegs.add(op.getAsOperand())
                    elif (isinstance(op, WeaveIRasmOperand) and op.varName == decl) and (
                            WIRinst.WeaveIRasmConstraints.REGISTER in op.constraints or
                            WIRinst.WeaveIRasmConstraints.OUTPUT in op.constraints):
                        virtualRegs.update(op.varName.getRegs)
        return virtualRegs

    def searchUnallocatedOperands(self, event: WeaveIRevent) -> None:
        """ Searches for unallocated operands in the instruction. This might happen, if the developer
        implemented
        ```
            event e() {
                long temp0, temp1;
                temp0 = 1024*temp1;
            }
        ```
        The variable temp1 has not been allocated a register, because it has not been assigned a value yet.
        Considering, 2 options:
            1. Assign a register that is free.
            2. Replace the variable by a constant.
                In this case, we have to check, if we can fold the instruction again, since 2 immediates are not allowed
                in the same instruction.
        We take option 1 and use the return register of the current instruction.
        ```"""
        for bb in event.basic_blocks:
            for inst in bb.instructions:
                if not isinstance(inst, WeaveIRinstruction):
                    continue

                # We do not care about the Phi instruction and potentially uninitialized registers
                if isinstance(inst, WeaveIRphi):
                    continue

                for index, op in enumerate(inst.getInOps()):
                    if isinstance(op, WeaveIRregister) and not op.alreadyAllocated:
                        if op.isControl:
                            val = self.getControlReg(op)
                            op.allocate(val.name)
                        elif op.isGPR:
                            if not isinstance(inst, WeaveIRphi):
                                warningMsg(f"Operand {op.name} in instruction \"{inst.to_string(0)}\" has not been "
                                           f"initialized. " + str(inst.getFileLocation()))
                            # option 1
                            if inst.getReturnReg() is not None:
                                reg = self.getTempReg(0, event)
                                reg.setLastUsedInstr(None)
                                op.allocate(reg)
                            else:
                                tempDecl = op.ctx.ctx_scope.getTempDeclaration(op.dataType, op.quals, False)
                                physReg = self.getTempReg(0, event)
                                tempDecl.curReg.allocate(physReg)
                                inst.getInOps()[index] = tempDecl.curReg
                            # option 2
                            # inst.getInOps()[index] = WeaveIRimmediate(op.ctx, 0, op.dataType)

            # release the resources
            for reg in reversed(self._used):
                self.putGPR(reg)

    def deadCodeRemoval(self, event: WeaveIRevent) -> None:
        """ There might be instructions left that have not been assigned a physical register. This can happen, if the
        developer wrote an instruction that does not have any side effects. For instance,
            unsigned long k;
            k = 3;
        And the variable k is never used. In this case, the instruction `k = 3;` is removed.
        """

        for bb in reversed(event.basic_blocks):
            for inst in reversed(bb.instructions):
                if (isinstance(inst, WeaveIRinstruction) and inst.getReturnReg() is not None and
                        not inst.getReturnReg().alreadyAllocated):
                    bb.instructions.remove(inst)

    def removePhiNodes(self, event: WeaveIRevent) -> None:
        """ After the event has been processed, remove the phi node as they do not have a instruction representation
        when lowering to the instructions. This might create empty basic blocks, which are not allowed. They are
        removed, when the pythonLowering executes the optimizer. """
        for bb in event.basic_blocks:
            for inst in reversed(bb.getInstructions()):
                if isinstance(inst, WeaveIRphi):
                    bb.instructions.remove(inst)

    def flattenBB(self, event: WeaveIRevent) -> list:
        """ Convert the instructions in the BB for an event into a flat list """
        return [instruction for bb in event.basic_blocks for instruction in bb.instructions]
