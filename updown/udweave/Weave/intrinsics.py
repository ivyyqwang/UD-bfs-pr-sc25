from Weave.WeaveIRenums import *
from Weave.WeaveIR import *
from backend.registerAllocator import AllocRegTypes, AllocRegister



class WeaveIntrinsicVar(ABC):
    """Base class for intrinsic variables

    This class contains the basic information for Intrinsic variables that are
    automatically translated into WeaveIR. This includes code generation functionality for
    WeaveIR. Contrary to intrinsic functions, intrinsic variables are resolved during code generation
    """

    def __init__(self):
        pass

    @classmethod
    @abstractmethod
    def getName(cls):
        """Returns a string containing the intrinsic's name"""
        pass

    @abstractmethod
    def generateWeaveIR(self, ctx):
        """Method to generate WeaveIR.
        Used during Intrinsic function lowering"""
        pass

    @classmethod
    def allIntrinsics(cls):
        return list(cls.__subclasses__())

    @classmethod
    def getIntrinsics(cls, name):
        return list(filter(lambda i: i.getName() == name, cls.allIntrinsics()))

    def __eq__(self, other):
        return self.getName() == other.getName()

    @classmethod
    def genConstant(cls, ctx, val: int, dtype: WeaveIRtypes) -> WeaveIRimmediate:
        return WeaveIRimmediate(ctx=ctx, val=val, dataType=dtype, quals=[WeaveIRqualifiers.unsigned])

    @classmethod
    def genReg(cls, ctx, reg: WeaveIRcontrolRegs, dtype: WeaveIRtypes, allocRegType: AllocRegTypes):
        retDecl = WeaveIRDecl(ctx=ctx, var_name=cls.getName(), typ=dtype, quals=[WeaveIRqualifiers.unsigned])

        reg = WeaveIRregister(
            ctx=ctx,
            decl=None,
            num=reg,
            ty=WeaveIRregTypes.control,
            dtype=dtype,
            quals=[WeaveIRqualifiers.unsigned]
        )
        allocRegister = AllocRegister(allocRegType, allocRegType.value["val"])
        reg.allocate(allocRegister.name)
        retDecl.addReg(reg)
        return retDecl


class THREADNAME(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "__THREADNAME__"

    @classmethod
    def generateWeaveIR(cls, ctx):
        if ctx.ctx_thread:
            return WeaveIRimmediate(ctx, ctx.ctx_thread.name)
        else:
            return WeaveIRimmediate(ctx, "")


class EVENTNAME(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "__EVENTNAME__"

    @classmethod
    def generateWeaveIR(cls, ctx):
        if ctx.ctx_event:
            return WeaveIRimmediate(ctx, ctx.ctx_event.fullName)
        else:
            return WeaveIRimmediate(ctx, "")


class TID(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "TID"

    @classmethod
    def generateWeaveIR(cls, ctx):
        newCEVNT = WeaveIRregister(
            ctx,
            None,
            WeaveIRcontrolRegs.CEVNT,
            WeaveIRregTypes.control,
            WeaveIRtypes.i32,
            [WeaveIRqualifiers.unsigned],
        )
        tempDecl = ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32, [WeaveIRqualifiers.unsigned])
        cur_bb = ctx.ctx_event.curBB
        shftrght_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.LSHFTRGT,
            left=newCEVNT,
            right=WeaveIRimmediate(ctx, 24, WeaveIRtypes.i32),
        )
        shftrght_inst.setRetOp(tempDecl.curReg)
        cur_bb.addInstruction(shftrght_inst)

        and_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.BWAND,
            left=tempDecl.curReg,
            right=WeaveIRimmediate(ctx, 0xFF, WeaveIRtypes.i32),
        )
        and_inst.setRetOp(tempDecl.curReg)
        cur_bb.addInstruction(and_inst)
        return and_inst


class LID(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "LID"

    @classmethod
    def generateWeaveIR(cls, ctx):
        netId = WeaveIRregister(
            ctx, None, WeaveIRcontrolRegs.NETID, WeaveIRregTypes.control, WeaveIRtypes.i32
        )
        cur_bb = ctx.ctx_event.curBB
        and_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.BWAND,
            left=netId,
            right=WeaveIRimmediate(ctx, 0x3F, WeaveIRtypes.i32),
        )
        and_inst.setRetOp(ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32).curReg)
        cur_bb.addInstruction(and_inst)

        return and_inst


class UDID(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "UDID"

    @classmethod
    def generateWeaveIR(cls, ctx):
        netId = WeaveIRregister(
            ctx, None, WeaveIRcontrolRegs.NETID, WeaveIRregTypes.control, WeaveIRtypes.i32
        )
        tempDecl = ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32, [WeaveIRqualifiers.unsigned])
        cur_bb = ctx.ctx_event.curBB
        shftrght_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.LSHFTRGT,
            left=netId,
            right=WeaveIRimmediate(ctx, 6, WeaveIRtypes.i32),
        )
        shftrght_inst.setRetOp(tempDecl.curReg)
        cur_bb.addInstruction(shftrght_inst)

        and_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.BWAND,
            left=tempDecl.curReg,
            right=WeaveIRimmediate(ctx, 0x3, WeaveIRtypes.i32),
        )
        and_inst.setRetOp(tempDecl.curReg)
        cur_bb.addInstruction(and_inst)
        return and_inst


class CLID(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "CLID"

    @classmethod
    def generateWeaveIR(cls, ctx):
        netId = WeaveIRregister(
            ctx, None, WeaveIRcontrolRegs.NETID, WeaveIRregTypes.control, WeaveIRtypes.i32
        )
        tempDecl = ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32, [WeaveIRqualifiers.unsigned])
        cur_bb = ctx.ctx_event.curBB
        shftrght_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.LSHFTRGT,
            left=netId,
            right=WeaveIRimmediate(ctx, 8, WeaveIRtypes.i32),
        )
        shftrght_inst.setRetOp(tempDecl.curReg)
        cur_bb.addInstruction(shftrght_inst)

        and_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.BWAND,
            left=tempDecl.curReg,
            right=WeaveIRimmediate(ctx, 0x7, WeaveIRtypes.i32),
        )
        and_inst.setRetOp(tempDecl.curReg)
        cur_bb.addInstruction(and_inst)
        return and_inst


class NID(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "NID"

    @classmethod
    def generateWeaveIR(cls, ctx):
        netId = WeaveIRregister(
            ctx, None, WeaveIRcontrolRegs.NETID, WeaveIRregTypes.control, WeaveIRtypes.i32
        )
        tempDecl = ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32, [WeaveIRqualifiers.unsigned])
        cur_bb = ctx.ctx_event.curBB
        shftrght_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.LSHFTRGT,
            left=netId,
            right=WeaveIRimmediate(ctx, 11, WeaveIRtypes.i32),
        )
        shftrght_inst.setRetOp(tempDecl.curReg)
        cur_bb.addInstruction(shftrght_inst)

        and_inst = WeaveIRbitwise(
            ctx=cur_bb,
            dataType=WeaveIRtypes.i32,
            opType=WeaveIRbitwiseTypes.BWAND,
            left=tempDecl.curReg,
            right=WeaveIRimmediate(ctx, 0xFFFF, WeaveIRtypes.i32),
        )
        returnReg = ctx.ctx_scope.getTempRegister(tempDecl)
        and_inst.setRetOp(returnReg)
        cur_bb.addInstruction(and_inst)
        return and_inst


class NETID(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "NETID"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genReg(ctx, WeaveIRcontrolRegs.NETID, WeaveIRtypes.i32, AllocRegTypes.CONTROL_ISAV2_NETID)


class CEVNT(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "CEVNT"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genReg(ctx, WeaveIRcontrolRegs.CEVNT, WeaveIRtypes.i64, AllocRegTypes.CONTROL_ISAV2_CEVNT)


class CCONT(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "CCONT"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genReg(ctx, WeaveIRcontrolRegs.CCONT, WeaveIRtypes.i64, AllocRegTypes.CONTROL_ISAV2_CCONT)


class NEWTH(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "NEWTH"

    @classmethod
    def generateWeaveIR(cls, ctx) -> WeaveIRimmediate:
        return cls.genConstant(ctx, 0xFF, WeaveIRtypes.c8)


class SP_NEAR_ADDRESS(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_NEAR_ADDRESS"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.NEAR_ADDRESS.value, WeaveIRtypes.c8)


class SP_DIRECT(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_DIRECT"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.DIRECT.value, WeaveIRtypes.c8)


class SP_SHORTEST(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_SHORTEST"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.SHORTEST_64.value, WeaveIRtypes.c8)


class SP_SHORTEST_LOW(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_SHORTEST_LOW"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.SHORTEST_32_LOW.value, WeaveIRtypes.c8)


class SP_SHORTEST_HIGH(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_SHORTEST_HIGH"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.SHORTEST_32_HIGH.value, WeaveIRtypes.c8)


class SP_LONGEST(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_LONGEST"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.LONGEST_64.value, WeaveIRtypes.c8)


class SP_LONGEST_LOW(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_LONGEST_LOW"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.SHORTEST_32_LOW.value, WeaveIRtypes.c8)


class SP_LONGEST_HIGH(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "SP_LONGEST_HIGH"

    @classmethod
    def generateWeaveIR(cls, ctx):
        return cls.genConstant(ctx, WeaveIRsendPolicy.LONGEST_32_HIGH.value, WeaveIRtypes.c8)


class BaseLM(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "LMBASE"

    @classmethod
    def generateWeaveIR(cls, ctx):
        retDecl = WeaveIRDecl(
            ctx,
            cls.getName(),
            WeaveIRtypes.ptr,
            WeaveIRtypes.void,
            [WeaveIRqualifiers.spmem, WeaveIRqualifiers.unsigned],
        )
        reg = WeaveIRregister(
            ctx=ctx,
            decl=None,
            num=WeaveIRcontrolRegs.LMBASE,
            ty=WeaveIRregTypes.control,
            dtype=WeaveIRtypes.ptr,
            quals=[WeaveIRqualifiers.spmem, WeaveIRqualifiers.unsigned]
        )

        allocRegister = AllocRegister(AllocRegTypes.CONTROL_ISAV2_LMBASE,
                                      AllocRegTypes.CONTROL_ISAV2_LMBASE.value["val"])
        reg.allocate(allocRegister.name)
        retDecl.addReg(reg)
        return retDecl


class IgnoreContinuation(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "IGNRCONT"

    @classmethod
    def generateWeaveIR(cls, ctx) -> WeaveIRimmediate:
        return cls.genConstant(ctx, 0x7FFFFFFFFFFFFFFF, WeaveIRtypes.c64)


class YIELD(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "yield"

    @classmethod
    def generateWeaveIR(cls, ctx):
        cur_bb = ctx.ctx_event.curBB
        yil = WeaveIRyield(ctx, WeaveIRyieldTypes.YIELD)
        cur_bb.addInstruction(yil)
        return yil


class YIELDterminate(WeaveIntrinsicVar):
    def __init__(self):
        super().__init__()

    @classmethod
    def getName(cls):
        return "yield_terminate"

    @classmethod
    def generateWeaveIR(cls, ctx):
        cur_bb = ctx.ctx_event.curBB
        yil = WeaveIRyield(ctx, WeaveIRyieldTypes.YIELD_TERMINATE)
        cur_bb.addInstruction(yil)
        return yil


########################################################################
############## INTRINSIC FUNCTIONS BELOW THIS POINT ####################
########################################################################


class WeaveIntrinsicFunc(ABC):
    """Base class for intrinsic functions

    This class contains the basic information for Intrinsic functions that are
    automatically translated into WeaveIR. This includes details about
    number of parameters, parameters data types, code generation functionality for
    WeaveIR, and others.
    """

    inputTypes = None
    returnType = None

    def __init__(self, ctx):
        self.ctx = ctx
        self.selectedInputTypes = None
        pass

    class __metaclass__(type):  # Python 2 syntax for metaclasses
        pass

    @classmethod
    @abstractmethod
    def getName(cls):
        """Returns a string containing the intrinsic's name"""
        pass

    @classmethod
    @abstractmethod
    def getReturnType(cls):
        """Return a WeaveIRtype for the return type of the intrinsic"""
        pass

    @classmethod
    @abstractmethod
    def getInputTypes(cls):
        """Returns a list of WeaveIRtypes for the input type of the intrinsic's parameters"""
        pass

    @abstractmethod
    def generateWeaveIR(self):
        """Method to generate WeaveIR.

        Used during Intrinsic function lowering"""
        pass

    def setSelectedInputTypes(self, selectedInputTypes: list):
        self.selectedInputTypes = selectedInputTypes

    def getNumOps(self):
        return len(self.selectedInputTypes)

    @classmethod
    def allIntrinsics(cls):
        return list(cls.__subclasses__())

    @classmethod
    def getIntrinsics(cls, name):
        return list(filter(lambda i: i.getName() == name, cls.allIntrinsics()))

    def __eq__(self, other):
        return (
                self.getName() == other.getName()
                and self.inputTypes == other.inputTypes
                and self.returnType == other.returnType
        )

    @classmethod
    def earlyInline(cls):
        """Determine if this intrinsic should be inlined early
        during the AST generation phase."""
        return False

    @classmethod
    def variadicArguments(cls):
        """Determine if this intrinsic has variadic arguments"""
        return False

    def convertImmToReg(self, inputTypes: list, convertImm2Reg: list = None) -> tuple:
        """
        Converts an immediate to a register with the same value as the immediate.
        Some intrinsics require that the immediate be a register.
        If convertImm2Reg is not None, it is a list of booleans that indicate, if an operand should be converted to a
        register value, if the operand is an immediate.
        @param inputTypes: Current input types
        @type inputTypes: list[list[WeaveIRtypes]]
        @param convertImm2Reg: Which of the entry in inputTypes should be converted to a register
        @type convertImm2Reg: list[bool]
        @return: Converted input types and the WeaveIR instructions to convert the immediates to registers
        @rtype: tuple[list, list]
        """

        if convertImm2Reg is None:
            convertImm2Reg = [True] * self.getNumOps()

        res = []
        final_ops = []
        tempDecl = None

        for op, ty, cI2R in zip(self.ctx.getInOps(), self.selectedInputTypes, convertImm2Reg):
            if isinstance(op, WeaveIRimmediate) and cI2R:
                ty = op.dtype if ty == WeaveIRtypes.void else ty

                # Temporary register to hold the value of the immediate
                tempDecl = self.ctx.ctx_scope.getTempDeclaration(ty, [WeaveIRqualifiers.unsigned])

                # Initialize temp to second operand
                res.append(
                    WeaveIRmemory(
                        ctx=self.ctx,
                        dataType=ty,
                        opType=WeaveIRmemoryTypes.LOAD,
                        ops=[op],
                    )
                )
                res[-1].setRetOp(tempDecl.curReg)
                final_ops.append(tempDecl.curReg)
            else:
                final_ops.append(op)
        return final_ops, res, tempDecl

    def checkNetIDImmediate(self, ops) -> tuple:
        res = []
        tempDecl = None

        # Check, if we are crossing the 12 bit field limitations.
        # TODO: Note: We do not do this check in the optimizer, as this instruction generates multiple instructions in
        # in assembly. Maintaining registers will be difficult without breaking something. It is probably a good idea,
        # to revisit this and to move it into the optimizer (to be all together), once the register allocator has been
        # rewritten.
        if isinstance(ops, WeaveIRimmediate):
            if ops.getOriginalValue() >= (1 << 12):
                tempDecl = self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32)
                res.append(
                    WeaveIRmemory(
                        ctx=self.ctx,
                        dataType=WeaveIRtypes.i32,
                        opType=WeaveIRmemoryTypes.LOAD,
                        ops=[ops],
                    )
                )
                res[-1].setRetOp(tempDecl.curReg)
                res[-1].setFileLocation(ops.getFileLocation())
                ops = tempDecl.curReg
        return res, ops, tempDecl

    def checkGlobalAddress(self, addr: WeaveIRbase):
        if not isinstance(addr, WeaveIRregister):
            errorMsg(
                "The global address should be a register",
                self.ctx.getFileLocation(),
            )
        if WeaveIRqualifiers.spmem in addr.quals:
            errorMsg(
                "The given address is in the scratchpad memory",
                self.ctx.getFileLocation(),
            )
        if addr.dtype != WeaveIRtypes.ptr:
            errorMsg(
                "The given address is not a pointer",
                self.ctx.getFileLocation(),
            )

    def checkSendPolicy(self, ops: list, res: list) -> WeaveIRsendPolicy:
        try:
            sendPolicy = WeaveIRsendPolicy(ops[-1].getOriginalValue())
            if sendPolicy == WeaveIRsendPolicy.DIRECT:
                return sendPolicy

            tempDecl = self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i64)
            res.append(
                WeaveIRmemory(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i64,
                    opType=WeaveIRmemoryTypes.LOAD,
                    ops=[ops[-1]],
                )
            )
            res[-1].setRetOp(tempDecl.curReg)
            res[-1].setFileLocation(self.ctx.getFileLocation())
            res.append(
                WeaveIRbitwise(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i64,
                    opType=WeaveIRbitwiseTypes.SHFTLFT,
                    left=tempDecl.curReg,
                    right=WeaveIRimmediate(self.ctx, 59, WeaveIRtypes.i32),
                )
            )
            res[-1].setRetOp(tempDecl.curReg)
            res[-1].setFileLocation(self.ctx.getFileLocation())
            res.append(
                WeaveIRbitwise(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i64,
                    opType=WeaveIRbitwiseTypes.BWOR,
                    left=tempDecl.curReg,
                    right=ops[0],
                )
            )
            res[-1].setRetOp(tempDecl.curReg)
            res[-1].setFileLocation(self.ctx.getFileLocation())
            ops[0] = tempDecl.curReg
            return sendPolicy

        except ValueError:
            errorMsg(
                "UpDown send instruction only supports immediate values for the sendPolicy parameter.",
                self.ctx.getFileLocation(),
            )
        return WeaveIRsendPolicy.DIRECT


class sendEvWordToNIDCont(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the continuation
    send_event(unsigned long evWord,
        <type>* local data,
        unsigned int size,
        unsigned long contWord,
        [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # data
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.i64,  # contWord
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # data
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.i64,  # contWord
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # data
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.c64,  # IGNRCONT
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # data
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.c64,  # IGNRCONT
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [False, False, False, True])
        if not isinstance(ops[2], WeaveIRimmediate):
            errorMsg(
                "UpDown send instruction only supports immediate values for the size parameter.",
                self.ctx.getFileLocation(),
            )
        elif not 2 <= ops[2].getOriginalValue() <= 9:
            errorMsg(
                "The size is out of range. It has to be between 2 and 9.",
                self.ctx.getFileLocation(),
            )
            
        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 5:
            sendPolicy = self.checkSendPolicy(ops, res)
            
        ops = [
            ops[0],  # Xe Destination Event Word
            ops[3],  # Xc Continuation Word
            ops[1],  # Xptr Pointer to SPmem
            ops[2],  # $len Size of transfer in words
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SEND_WCONT, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord0NIDCont(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the continuation
    send_event(unsigned long evWord,
        unsigned long contWord,
        [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.i64,  # contWord
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.i64,  # contWord
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.c64,  # IGNRCONT
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.c64,  # IGNRCONT
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [True, True, False])
        
        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 3:
            sendPolicy = self.checkSendPolicy(ops, res)
            
        ops = [
            ops[0],  # Xe Destination Event Word
            ops[1],  # Xc Continuation Word
            ops[0],  # X1 Data Word
            ops[0],  # X2 Data Word (Dup'ed to have all operands)
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_WCONT, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord1NIDCont(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the continuation
    send_event(unsigned long evWord,
        <type> data,
        unsigned long contWord,
        [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data
            WeaveIRtypes.i64,  # contWord
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data
            WeaveIRtypes.i64,  # contWord
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data
            WeaveIRtypes.c64,  # IGNRCONT
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data
            WeaveIRtypes.c64,  # IGNRCONT
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [True, True, True, False])
        
        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 4:
            sendPolicy = self.checkSendPolicy(ops, res)
        
        ops = [
            ops[0],  # Xe Destination Event Word
            ops[2],  # Xc Continuation Word
            ops[1],  # X1 Data Word
            ops[1],  # X2 Data Word (Dup'ed to have all operands)
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_WCONT, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord2NIDCont(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the continuation
    send_event(unsigned long evWord,
        <type> data1,
        <type> data2,
        unsigned long contWord,
        [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.i64,  # contWord
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.i64,  # contWord
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.c64,  # IGNRCONT
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.c64,  # IGNRCONT
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [True, True, True, True, False])
        
        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 5:
            sendPolicy = self.checkSendPolicy(ops, res)
            
        ops = [
            ops[0],  # Xe Destination Event Word
            ops[3],  # Xc Continuation Word
            ops[1],  # X1 Data Word
            ops[2],  # X2 Data Word
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_WCONT, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord3NIDCont(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the continuation
    send_event(unsigned long evWord,
        <type> data1,
        <type> data2,
        <type> data3,
        unsigned long contWord,
        [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.void,  # data3
            WeaveIRtypes.i64,  # contWord
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.void,  # data3
            WeaveIRtypes.i64,  # contWord
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.void,  # data3
            WeaveIRtypes.c64,  # IGNRCONT
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.void,  # data3
            WeaveIRtypes.c64,  # IGNRCONT
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(),
                                                  [True, True, True, True, True, False])

        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 6:
            sendPolicy = self.checkSendPolicy(ops, res)

        ops = [
            ops[0],  # Xe Destination Event Word
            ops[4],  # Xc Continuation Word
            ops[1],  # X1 Data Word
            ops[2],  # X2 Data Word
            ops[3],  # X3 Data Word
        ]
        
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR3_WCONT, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendOpsCont(WeaveIntrinsicFunc):
    """ Send data in the operand buffer to a specific network ID specifying the continuation
    send_ops(unsigned long evWord,
        <type> startOpRegisterVariable,
        unsigned int numRegisters,
        unsigned long contWord,
        [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_ops"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i32,  # number of registers to send
            WeaveIRtypes.i64,  # continuation word
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i32,  # number of registers to send
            WeaveIRtypes.i64,  # continuation word
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i32,  # number of registers to send
            WeaveIRtypes.c64,  # IGNRCONT
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i32,  # number of registers to send
            WeaveIRtypes.c64,  # IGNRCONT
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i64,  # number of registers to send
            WeaveIRtypes.i64,  # continuation word
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i64,  # number of registers to send
            WeaveIRtypes.i64,  # continuation word
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i64,  # number of registers to send
            WeaveIRtypes.c64,  # IGNRCONT
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i64,  # number of registers to send
            WeaveIRtypes.c64,  # IGNRCONT
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        if not isinstance(ops[2], WeaveIRimmediate) or not 2 <= ops[2].getOriginalValue() <= 9:
            errorMsg(
                "UpDown sendops instruction only supports immediate values between 2 and 9 as length",
                self.ctx.getFileLocation(),
            )
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [False, False, False, True])
        
        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 5:
            sendPolicy = self.checkSendPolicy(ops, res)

        ops = [
            ops[0],  # Xe  Destination Event Word
            ops[3],  # Xc  continuation word
            ops[1],  # Xop Start operand register number
            ops[2],  # $imm number of registers to send
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDOPS_WCONT, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendEvWordToNIDEvLabel(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the event label as the continuation
    send_event(unsigned long evWord,
                <type>* local data,
                unsigned int size,
                eventLabel,
                [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # data
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.ptr,  # eventLabel
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # data
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.ptr,  # eventLabel
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops = self.ctx.getInOps()
        res = []
        if not isinstance(ops[2], WeaveIRimmediate):
            errorMsg(
                "UpDown send instruction only supports immediate values",
                self.ctx.getFileLocation(),
            )
        elif not 2 <= ops[2].getOriginalValue() <= 9:
            errorMsg(
                "The size is out of range. It has to be between 2 and 9.",
                self.ctx.getFileLocation(),
            )

        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 5:
            sendPolicy = self.checkSendPolicy(ops, res)

        ops = [
            ops[0],  # Xe Destination Event Word
            ops[3],  # Xc Event label
            ops[1],  # Xptr Pointer to SPmem
            ops[2],  # $len Size of transfer in words
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]

        res = [WeaveIRsend(self.ctx, WeaveIRsendTypes.SEND_WRET, ops, sendPolicy)]
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord0NIDEvLabel(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the event label as the continuation
    send_event(unsigned long evWord,
                eventLabel,
                [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # eventLabel
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.ptr,  # eventLabel
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [True, False, False])

        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 3:
            sendPolicy = self.checkSendPolicy(ops, res)

        ops = [
            ops[0],  # Xe Destination Event Word
            ops[1],  # Xc Event label
            ops[0],  # X1 Data Word
            ops[0],  # X2 Data Word (Dup'ed to have all operands)
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_WRET, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord1NIDEvLabel(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the event label as the continuation
    send_event(unsigned long evWord,
                <type> data1,
                eventLabel,
                [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data
            WeaveIRtypes.ptr,  # eventLabel
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data
            WeaveIRtypes.ptr,  # eventLabel
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [True, True, False, False])

        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 4:
            sendPolicy = self.checkSendPolicy(ops, res)

        ops = [
            ops[0],  # Xe Destination Event Word
            ops[2],  # Xc Event label
            ops[1],  # X1 Data Word
            ops[1],  # X2 Data Word (Dup'ed to have all operands)
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_WRET, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord2NIDEvLabel(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the event label as the continuation
    send_event(unsigned long evWord,
                <type> data1,
                <type> data2,
                unsigned int size,
                eventLabel,
                [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.ptr,  # eventLabel
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.ptr,  # eventLabel
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [True, True, True, False, False])

        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 5:
            sendPolicy = self.checkSendPolicy(ops, res)

        ops = [
            ops[0],  # Xe Destination Event Word
            ops[3],  # Xc Event label
            ops[1],  # X1 Data Word
            ops[2],  # X2 Data Word
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_WRET, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendrEvWord3NIDEvLabel(WeaveIntrinsicFunc):
    """Send an event word to a specific network ID,
    specifying the event label as the continuation
    send_event(unsigned long evWord,
                <type> data1,
                <type> data2,
                <type> data3,
                unsigned int size,
                eventLabel,
                [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.void,  # data3
            WeaveIRtypes.ptr,  # eventLabel
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # data1
            WeaveIRtypes.void,  # data2
            WeaveIRtypes.void,  # data3
            WeaveIRtypes.ptr,  # eventLabel
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(),
                                                  [True, True, True, True, False, False])

        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 6:
            sendPolicy = self.checkSendPolicy(ops, res)

        ops = [
            ops[0],  # Xe Destination Event Word
            ops[4],  # Xc Event label
            ops[1],  # X1 Data Word
            ops[2],  # X2 Data Word
            ops[3],  # X3 Data Word
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR3_WRET, ops, sendPolicy))
        self.ctx.ctx_scope.endScope()
        return res


class sendOpsEvLabel(WeaveIntrinsicFunc):
    """ Send data in the operand buffer to a specific network ID specifying the event label
    send_ops(unsigned long evWord,
        <type>> startOpRegisterVariable,
        unsigned int numRegisters,
        eventLabel,
        [unsigned int sendPolicy])
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_ops"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i32,  # number of registers to send (2-9)
            WeaveIRtypes.ptr,  # eventLabel
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i32,  # number of registers to send (2-9)
            WeaveIRtypes.ptr,  # eventLabel
            WeaveIRtypes.c8,  # sendPolicy
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i64,  # number of registers to send (2-9)
            WeaveIRtypes.ptr,  # eventLabel
        ], [
            WeaveIRtypes.i64,  # evWord
            WeaveIRtypes.void,  # operand variable indicating the first operand register to send
            WeaveIRtypes.i64,  # number of registers to send (2-9)
            WeaveIRtypes.ptr,  # eventLabel
            WeaveIRtypes.c8,  # sendPolicy
        ]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        res = []
        if not isinstance(ops[2], WeaveIRimmediate) or not 1 <= ops[2].getOriginalValue() <= 9:
            errorMsg(
                "UpDown sendops instruction only supports immediate values between 1 and 9 as length",
                self.ctx.getFileLocation(),
            )
        if ops[2].getOriginalValue() == 1:
            ops[2].setValue(2)
        
        sendPolicy = WeaveIRsendPolicy.DIRECT
        if len(ops) == 5:
            sendPolicy = self.checkSendPolicy(ops, res)

        self.ctx.ctx_scope.startScope()
        ops = [
            ops[0],  # Xe  Destination Event Word
            ops[3],  # Xc  Event label
            ops[1],  # Xop Start operand register number
            ops[2],  # $imm number of registers to send
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        self.ctx.ctx_scope.endScope()
        return [WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDOPS_WRET, ops, sendPolicy)]


class sendRdDRAMCont(WeaveIntrinsicFunc):
    """Send a read request to the DRAM, specify the continuation word
    send_dram_read(<type>* globalAddress,
                    unsigned int size,
                    unsigned long contWord)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_read"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.i64,  # contWord
        ]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        if not isinstance(ops[1], WeaveIRimmediate):
            errorMsg(
                "UpDown send instruction only supports immediate values",
                self.ctx.getFileLocation(),
            )
        self.checkGlobalAddress(ops[0])

        ops = [
            ops[0],  # Global Address
            ops[2],  # Continuation Word
            ops[1],  # Size
        ]
        return [WeaveIRsend(self.ctx, WeaveIRsendTypes.SEND_DMLM_LD, ops)]


class sendRdDRAMEvLabel(WeaveIntrinsicFunc):
    """Send a read request to the DRAM, specify the continuation as an event label
    send_dram_read(<type>* globalAddress,
               unsigned int size,
               eventLabel)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_read"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.i32,  # size
            WeaveIRtypes.ptr,  # eventLabel
        ]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops = self.ctx.getInOps()
        if not isinstance(ops[1], WeaveIRimmediate):
            errorMsg(
                "UpDown send instruction only supports immediate values",
                self.ctx.getFileLocation(),
            )
        self.checkGlobalAddress(ops[0])

        ops = [
            ops[0],  # Global Address
            ops[2],  # Event Label
            ops[1],  # Size
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res = [
            WeaveIRsend(self.ctx, WeaveIRsendTypes.SEND_DMLM_LD_WRET, ops)
        ]
        self.ctx.ctx_scope.endScope()
        return res


class sendWrDRAMCont(WeaveIntrinsicFunc):
    """Send a write request to DRAM, data comes from scratchpad pointer,
    specify the continuation word
    send_dram_write(<type>* globalAddress,
                <type>* local data,
                unsigned int size,
                unsigned long contWord)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.ptr,  # Pointer to local data to write
            WeaveIRtypes.i32,  # size in words
            WeaveIRtypes.i64,  # contWord
        ]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        if not isinstance(ops[2], WeaveIRimmediate):
            errorMsg(
                "UpDown send instruction only supports immediate values",
                self.ctx.getFileLocation(),
            )
        ops = [
            ops[0],  # Global Address
            ops[3],  # Continuation Word
            ops[1],  # Xptr Pointer to local data
            ops[2],  # $len Size in words
        ]
        return [WeaveIRsend(self.ctx, WeaveIRsendTypes.SEND_DMLM, ops)]


class sendr1WrDRAMCont(WeaveIntrinsicFunc):
    """Send a write request to DRAM, data comes from a register,
    specify the continuation word
    send_dram_write(<type>* globalAddress,
                <type> data,
                unsigned long contWord)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.void,  # Data
            WeaveIRtypes.i64,  # contWord
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes())
        self.checkGlobalAddress(ops[0])
        ops = [
            ops[0],  # Global Address
            ops[2],  # Continuation Word
            ops[1],  # X1 data to write
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_DMLM, ops))
        self.ctx.ctx_scope.endScope()
        return res


class sendr2WrDRAMCont(WeaveIntrinsicFunc):
    """Send a write to DRAM, data comes from 2 registers,
    specify the continuation word
    send_dram_write(<type>* globalAddress,
                <type> data1,
                <type> data2,
                unsigned long contWord)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.void,  # Data1
            WeaveIRtypes.void,  # Data2
            WeaveIRtypes.i64,  # contWord
        ]]

    def generateWeaveIR(self):
        # convertImmToReg might assign a temp register
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes())
        self.checkGlobalAddress(ops[0])
        ops = [
            ops[0],  # Global Address
            ops[3],  # Continuation Word
            ops[1],  # X1 data to write
            ops[2],  # X2 data to write
        ]
        res.append(WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR2_DMLM, ops))
        self.ctx.ctx_scope.endScope()
        return res


class sendOpsWrDRAMCont(WeaveIntrinsicFunc):
    """ Send a write request to DRAM, the data comes from the operand registers and the continuation word is an event
    label.
    send_dram_write_ops(<type>* globalAddress,
                <type> firstOpRegisterVariable,
                i32 length,
                unsigned long contWord)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write_ops"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.void,  # the operand variable indicating the first operand register to send
            WeaveIRtypes.i32,  # length
            WeaveIRtypes.i64,  # continuation word
        ]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        self.checkGlobalAddress(ops[0])
        if not isinstance(ops[2], WeaveIRimmediate) or not 1 <= ops[2].getOriginalValue() <= 8:
            errorMsg(
                "UpDown sendmops instruction only supports immediate values between 1 and 8 as length",
                self.ctx.getFileLocation(),
            )

        ops = [
            ops[0],  # Xd Global Address
            ops[3],  # Xc continuation word
            ops[1],  # Xop Start operand register number
            ops[2],  # $imm number of registers to send
            WeaveIRimmediate(ctx=self.ctx, val=0)  # mode
        ]
        return [WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDMOPS, ops)]


class sendWrDRAMEvLabel(WeaveIntrinsicFunc):
    """Send a write request to DRAM, data comes from scratchpad pointer,
    specify the continuation as an event label
    send_dram_write(<type>* globalAddress,
                <type>* local data,
                unsigned int size,
                eventLabel)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.ptr,  # Pointer to local data to write
            WeaveIRtypes.i32,  # size in words
            WeaveIRtypes.ptr,  # Event Label
        ]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops = self.ctx.getInOps()
        if not isinstance(ops[2], WeaveIRimmediate):
            errorMsg(
                "UpDown send instruction only supports immediate values",
                self.ctx.getFileLocation(),
            )
        ops = [
            ops[0],  # Global Address
            ops[3],  # Event Label
            ops[1],  # Xptr Pointer to local data
            ops[2],  # $len Size in words
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res = [WeaveIRsend(self.ctx, WeaveIRsendTypes.SEND_DMLM_WRET, ops)]
        self.ctx.ctx_scope.endScope()
        return res


class sendr1WrDRAMEvLabel(WeaveIntrinsicFunc):
    """Send a write request to DRAM, data comes from a register,
    specify the continuation as an event label
    send_dram_write(<type>* globalAddress,
                <type> data,
                eventLabel)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.void,  # Data
            WeaveIRtypes.ptr,  # Event Label
        ]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes())
        ops = [
            ops[0],  # Global Address
            ops[2],  # Event Label
            ops[1],  # X1 data to write
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res.append(
            WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR_DMLM_WRET, ops)
        )
        self.ctx.ctx_scope.endScope()
        return res


class sendr2WrDRAMEvLabel(WeaveIntrinsicFunc):
    """Send a write request to DRAM, data comes from 2 registers,
    specify the continuation as an event label
    send_dram_write(<type>* globalAddress,
                <type> data1,
                <type> data2,
                eventLabel)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.void,  # Data1
            WeaveIRtypes.void,  # Data2
            WeaveIRtypes.ptr,  # Event Label
        ]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes())
        self.checkGlobalAddress(ops[0])

        ops = [
            ops[0],  # Global Address
            ops[3],  # Event Label
            ops[1],  # X1 data to write
            ops[2],  # X2 data to write
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        res.append(
            WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDR2_DMLM_WRET, ops)
        )
        self.ctx.ctx_scope.endScope()
        return res


class sendOpsWrDRAMEvLabel(WeaveIntrinsicFunc):
    """ Send a write request to DRAM, the data comes from the operand registers and the continuation word is an event
    label.
    send_dram_write_ops(<type>* globalAddress,
                <type> firstOpRegisterVariable,
                i32 length,
                eventLabel)
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "send_dram_write_ops"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[
            WeaveIRtypes.ptr,  # globalAddress
            WeaveIRtypes.void,  # the first operand register variable of the operand buffer to send
            WeaveIRtypes.i32,  # length
            WeaveIRtypes.ptr,  # Event Label
        ]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        if not isinstance(ops[2], WeaveIRimmediate) or not 1 <= ops[2].getOriginalValue() <= 8:
            errorMsg(
                "UpDown sendmops instruction only supports immediate values between 1 and 8 as length",
                self.ctx.getFileLocation(),
            )

        self.ctx.ctx_scope.startScope()
        self.checkGlobalAddress(ops[0])
        ops = [
            ops[0],  # Xd  Global Address
            ops[3],  # Xc  event label
            ops[1],  # Xop Start operand register number
            ops[2],  # $imm number of registers to send
            self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr, toBeInitialized=False).curReg,
        ]
        self.ctx.ctx_scope.endScope()
        return [WeaveIRsend(self.ctx, WeaveIRsendTypes.SENDOPS_DMLM_WRET, ops)]


class EWnew(WeaveIntrinsicFunc):
    """Create a new Event Word from scratch. Use event label
    Assign a newThread to the event word
    evw_new(unsigned int NetID,
            EventLabel)
    Return => unsigned long newEvWord
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "evw_new"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i64

    @classmethod
    def getInputTypes(cls):
        return [
            [WeaveIRtypes.i32, WeaveIRtypes.ptr, WeaveIRtypes.i32],
            [WeaveIRtypes.i64, WeaveIRtypes.ptr, WeaveIRtypes.i32],
            [WeaveIRtypes.i32, WeaveIRtypes.ptr, WeaveIRtypes.i64],
            [WeaveIRtypes.i64, WeaveIRtypes.ptr, WeaveIRtypes.i64],
            [WeaveIRtypes.i32, WeaveIRtypes.ptr],
            [WeaveIRtypes.i64, WeaveIRtypes.ptr],
        ]

    def generateWeaveIR(self):
        resultReg = self.ctx.getAsOperand()
        ops = self.ctx.getInOps()
        res, ops[0], tempDecl = self.checkNetIDImmediate(ops[0])

        # Initialize the event word to 0
        res.append(
            WeaveIRmemory(
                self.ctx,
                WeaveIRtypes.i64,
                WeaveIRmemoryTypes.LOAD,
                [WeaveIRimmediate(self.ctx, 0, WeaveIRtypes.i64)],
            )
        )
        res[-1].setRetOp(resultReg)

        if len(ops) == 3:
            warningMsg(f"DEPRECATED! The number of operands for evw_new {self.ctx.getFileLocation()} "
                       "is not required anymore. It is ignored and will be removed in the future.")

        # new thread
        imm_newThr = WeaveIRimmediate(self.ctx, 0xFF, WeaveIRtypes.i32)
        res.append(
            WeaveIRupdate(
                self.ctx,
                [
                    resultReg,  # Empty Event Word
                    ops[1],  # Event Label
                    imm_newThr,  # ThreadID = New Thread ID = 0xFF
                    ops[0],  # NetID
                    WeaveIRimmediate(self.ctx, 0b1101, WeaveIRtypes.i32),  # Mask
                ],
            )
        )
        res[-1].setRetOp(resultReg)
        return res


class EWupdateNetID(WeaveIntrinsicFunc):
    """Modify the NetworkID of an already existing Event Word
    evw_update_netid(unsigned long evWord,
                 unsigned int netId)
    Return => unsigned long newEvWord
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "evw_update_netid"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i64

    @classmethod
    def getInputTypes(cls):
        return [
            [WeaveIRtypes.i64, WeaveIRtypes.i32],
            [WeaveIRtypes.i64, WeaveIRtypes.i64]
        ]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        res, ops[1], tempDecl = self.checkNetIDImmediate(ops[1])
        ops = [
            ops[0],  # Current Event Word
            ops[1],  # NetId
            WeaveIRimmediate(self.ctx, 0x8, WeaveIRtypes.i32),
        ]
        res.append(WeaveIRupdate(self.ctx, ops))
        res[-1].setRetOp(self.ctx.getAsOperand())
        return res


class EWupdateEvent(WeaveIntrinsicFunc):
    """Modify the Event of an already existing Event Word
    evw_update_event(unsigned long evWord,
                 EventLabel)
    Return => unsigned long newEvWord
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "evw_update_event"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i64

    @classmethod
    def getInputTypes(cls):
        return [
            [WeaveIRtypes.i64, WeaveIRtypes.ptr, WeaveIRtypes.i32],
            [WeaveIRtypes.i64, WeaveIRtypes.ptr, WeaveIRtypes.i64],
            [WeaveIRtypes.i64, WeaveIRtypes.ptr]]

    def generateWeaveIR(self):
        res = []
        ops = self.ctx.getInOps()

        if len(ops) == 3:
            warningMsg(f"DEPRECATED! The number of operands for evw_update_event {self.ctx.getFileLocation()} "
                       "is not required anymore. It is ignored and will be removed in the future.")

        ops = [
            ops[0],  # Current Event Word
            ops[1],  # Event Label
            WeaveIRimmediate(self.ctx, 0b0001, WeaveIRtypes.i32),
        ]
        res.append(WeaveIRupdate(self.ctx, ops))
        res[-1].setRetOp(self.ctx.getAsOperand())
        return res


class EWupdateThreadWmode(WeaveIntrinsicFunc):
    """Modify the ThreadID and Thread Mode of
    an already existing Event Word
    evw_update_thread(unsigned long evWord,
                  unsigned int thrId,
                  unsigned int thrMode)
    Return => unsigned long newEvWord
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "evw_update_thread"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i64

    @classmethod
    def getInputTypes(cls):
        return [
            [WeaveIRtypes.i64, WeaveIRtypes.i32, WeaveIRtypes.i32],
            [WeaveIRtypes.i64, WeaveIRtypes.i32, WeaveIRtypes.i64],
            [WeaveIRtypes.i64, WeaveIRtypes.c8, WeaveIRtypes.i32],
            [WeaveIRtypes.i64, WeaveIRtypes.c8, WeaveIRtypes.i64],
        ]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        opsUpdate = [
            ops[0],  # Current Event Word
            ops[1],  # new thread ID or NEWTH
            WeaveIRimmediate(self.ctx, 0x4, WeaveIRtypes.i32),
        ]
        res = [WeaveIRupdate(self.ctx, opsUpdate)]

        tempDecl = self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i64)
        res[-1].setRetOp(tempDecl.curReg)
        res[-1].setFileLocation(self.ctx.getFileLocation())

        if ops[2].getValue() == 0:
            res.append(
                WeaveIRbitwise(
                    self.ctx,
                    WeaveIRtypes.i64,
                    WeaveIRbitwiseTypes.BWAND,
                    res[-1].getAsOperand(),
                    WeaveIRimmediate(self.ctx, 0xFFFF_FFFF_FF7F_FFFF, WeaveIRtypes.i64),
                )
            )
        else:
            res.append(
                WeaveIRbitwise(
                    self.ctx,
                    WeaveIRtypes.i64,
                    WeaveIRbitwiseTypes.BWOR,
                    res[-1].getAsOperand(),
                    WeaveIRimmediate(self.ctx, 0x0000_0000_0080_0000, WeaveIRtypes.i64),
                )
            )
        res[-1].setRetOp(self.ctx.getAsOperand())
        res[-1].setFileLocation(self.ctx.getFileLocation())
        return res


class EWupdateThread(WeaveIntrinsicFunc):
    """Modify the ThreadID of
    an already existing Event Word
    evw_update_thread(unsigned long evWord,
                  unsigned int thrId)
    Return => unsigned long newEvWord
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "evw_update_thread"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i64

    @classmethod
    def getInputTypes(cls):
        return [
            [WeaveIRtypes.i64, WeaveIRtypes.c8],
            [WeaveIRtypes.i64, WeaveIRtypes.i32],
            [WeaveIRtypes.i64, WeaveIRtypes.i64],
        ]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        ops = [
            ops[0],  # Current Event Word
            ops[1],  # value to be used for update
            WeaveIRimmediate(self.ctx, 0x4, WeaveIRtypes.i32),
        ]
        update = WeaveIRupdate(self.ctx, ops)
        update.setRetOp(self.ctx.getAsOperand())
        return [update]


class newNetID(WeaveIntrinsicFunc):
    """Create a network ID
        netid_new(unsigned int lid,
            unsigned int udid,
            unsigned int cid,
            unsigned int nid)
    Return => unsigned int newNetId"""

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "netid_new"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i32

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.i32, WeaveIRtypes.i32, WeaveIRtypes.i32, WeaveIRtypes.i32]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        reg = self.ctx.getAsOperand()
        res = []

        tempDecl = self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32)

        # Initialize result to nid
        res.append(
            WeaveIRmemory(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRmemoryTypes.LOAD,
                ops=[ops[3]],
            )
        )
        res[-1].setRetOp(tempDecl.curReg)
        # Chunk value to 16 bits
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.BWAND,
                left=reg,
                right=WeaveIRimmediate(self.ctx, 0xFFFF, WeaveIRtypes.i32),
            )
        )

        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
        if isinstance(ops[2], WeaveIRregister):
            # Chunk the value in cid to 3 bits
            res.append(
                WeaveIRbitwise(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i32,
                    opType=WeaveIRbitwiseTypes.BWAND,
                    left=ops[2],
                    right=WeaveIRimmediate(self.ctx, 0x7, WeaveIRtypes.i32),
                )
            )
            res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
            newOp = tempDecl.curReg
        else:
            # Chunk the immediate value in cid to 3 bits
            if ops[2].getValue() > 0x7:
                warningMsg("Trunking operand cid for netid_new() to be 3 bits")
                ops[2].setValue(ops[2].getValue() & 0x7)
            newOp = ops[2]

        # Make space for the cid
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.SHFTLFT,
                left=reg,
                right=WeaveIRimmediate(self.ctx, 3, WeaveIRtypes.i32),
            )
        )
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
        # Add the cid to the new word
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.BWOR,
                left=reg,
                right=newOp,
            )
        )
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
        if isinstance(ops[2], WeaveIRregister):
            # Chunk the value in udid to 2 bits
            res.append(
                WeaveIRbitwise(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i32,
                    opType=WeaveIRbitwiseTypes.BWAND,
                    left=ops[1],
                    right=WeaveIRimmediate(self.ctx, 0x3, WeaveIRtypes.i32),
                )
            )
            res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
            newop = tempDecl.curReg
        else:
            # Chunk the immediate value in udid to 2 bits
            if ops[1].getValue() > 0x3:
                warningMsg("Trunking operand cid for netid_new() to be 3 bits")
                ops[1].setValue(ops[1].getValue() & 0x3)
            newop = ops[1]

        # Make space for the cid
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.SHFTLFT,
                left=reg,
                right=WeaveIRimmediate(self.ctx, 2, WeaveIRtypes.i32),
            )
        )
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
        # Add the cid to the new word
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.BWOR,
                left=reg,
                right=newop,
            )
        )
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
        if isinstance(ops[2], WeaveIRregister):
            # Chunk the value in laneID to 6 bits
            res.append(
                WeaveIRbitwise(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i32,
                    opType=WeaveIRbitwiseTypes.BWAND,
                    left=ops[0],
                    right=WeaveIRimmediate(self.ctx, 0x3F, WeaveIRtypes.i32),
                )
            )
            res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
            newop = tempDecl.curReg
        else:
            # Chunk the immediate value in laneID to 6 bits
            if ops[0].getValue() > 0x3F:
                warningMsg("Trunking operand cid for netid_new() to be 3 bits")
                ops[0].setValue(ops[0].getValue() & 0x3F)
            newop = ops[0]
        # Make space for the cid
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.SHFTLFT,
                left=reg,
                right=WeaveIRimmediate(self.ctx, 6, WeaveIRtypes.i32),
            )
        )
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))
        # Add the cid to the new word
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.BWOR,
                left=reg,
                right=newop,
            )
        )
        res[-1].setRetOp(reg)
        return res


class updateNetID(WeaveIntrinsicFunc, ABC):
    """A parent class for all netid_update_XXX methods.
    netid_update_XXX(unsigned int netID,
             unsigned int XXX)
    Return => unsigned int updatedNetId
    """

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i32

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.i32, WeaveIRtypes.i32]]

    def generateInstructions(self, warningMsgString: str, maskValue: int, position: int):
        ops = self.ctx.getInOps()
        reg = self.ctx.getAsOperand()

        # Temporary declaration to hold the value of the mask and (later) second operand
        tempDecl = self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.i32)

        # Clear out the bits
        #   1a) Create the mask
        res = [
            WeaveIRmemory(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRmemoryTypes.LOAD,
                ops=[WeaveIRimmediate(self.ctx, maskValue, WeaveIRtypes.i32)],
            )
        ]
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))

        #   1b) Shift the mask to the right position
        if position != 0:
            res.append(
                WeaveIRbitwise(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i32,
                    opType=WeaveIRbitwiseTypes.SHFTLFT,
                    left=tempDecl.curReg,
                    right=WeaveIRimmediate(self.ctx, position, WeaveIRtypes.i32),
                )
            )
            res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))

        #   1c) BW NOT the mask
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.BWXOR,
                left=tempDecl.curReg,
                right=WeaveIRimmediate(self.ctx, -1, WeaveIRtypes.i32),
            )
        )
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))

        #   2) BWAND the first operand with the mask
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.BWAND,
                left=ops[0],
                right=tempDecl.curReg,
            )
        )
        res[-1].setRetOp(reg)

        # If the second operand is an immediate do transformations at compile time
        if isinstance(ops[1], WeaveIRimmediate):
            val = ops[1].getValue()
            if val > maskValue:
                warningMsg(warningMsgString)
            val = (val & maskValue) << position
            newVal = WeaveIRimmediate(self.ctx, val, WeaveIRtypes.i32)
            res.append(
                WeaveIRarith(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i32,
                    opType=WeaveIRarithTypes.IADDITION,
                    left=reg,
                    right=newVal,
                )
            )
            res[-1].setRetOp(reg)
            return res

        # load and BWAND the second operand
        res.append(
            WeaveIRbitwise(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRbitwiseTypes.BWAND,
                left=ops[1],
                right=WeaveIRimmediate(self.ctx, maskValue, WeaveIRtypes.i32),
            )
        )
        res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))

        if position != 0:
            res.append(
                WeaveIRbitwise(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.i32,
                    opType=WeaveIRbitwiseTypes.SHFTLFT,
                    left=tempDecl.curReg,
                    right=WeaveIRimmediate(self.ctx, position, WeaveIRtypes.i32),
                )
            )
            res[-1].setRetOp(self.ctx.ctx_scope.getTempRegister(tempDecl))

        res.append(
            WeaveIRarith(
                ctx=self.ctx,
                dataType=WeaveIRtypes.i32,
                opType=WeaveIRarithTypes.IADDITION,
                left=reg,
                right=tempDecl.curReg,
            )
        )
        res[-1].setRetOp(reg)

        return res


class updateNetIDlid(updateNetID, WeaveIntrinsicFunc):
    """Create a network ID
    netid_update_lid(unsigned int netID,
             unsigned int lid)
    Return => unsigned int updatedNetId
    """

    @classmethod
    def getName(cls):
        return "netid_update_lid"

    def generateWeaveIR(self):
        return self.generateInstructions(
            "Trunking operand LID for netid_update_lid() to be 6 bits",
            0x3F,
            0,
        )


class updateNetIDudid(updateNetID, WeaveIntrinsicFunc):
    """Create a network ID updating an existing one with a new udid
    netid_update_udid(unsigned int netID,
             unsigned int udid)
    Return => unsigned int updatedNetId
    """

    @classmethod
    def getName(cls):
        return "netid_update_udid"

    def generateWeaveIR(self):
        return self.generateInstructions(
            "Trunking operand UD ID for netid_update_udid() to be 2 bits", 0x3, 6
        )


class updateNetIDcid(updateNetID, WeaveIntrinsicFunc):
    """Create a network ID updating an existing one with a new cid
    netid_update_cid(unsigned int netID,
             unsigned int cid)
    Return => unsigned int updatedNetId
    """

    @classmethod
    def getName(cls):
        return "netid_update_cid"

    def generateWeaveIR(self):
        return self.generateInstructions(
            "Trunking CID for netid_update_cid() to be 3 bits",
            0x7,
            6 + 2,  # (6 bits of lid and 2 bits of udid)
        )


class updateNetIDnid(updateNetID, WeaveIntrinsicFunc):
    """Create a network ID updating an existing one with a new nid
    netid_update_nid(unsigned int netID,
             unsigned int nid)
    Return => unsigned int updatedNetId
    """

    @classmethod
    def getName(cls):
        return "netid_update_nid"

    def generateWeaveIR(self):
        return self.generateInstructions(
            "Trunking NID for netid_update_cid() to be 16 bits",
            0xFFFF,
            6 + 2 + 3,  # (6 bits of lid, 2 bits of udid and 3 bits of cid)
        )


class updateNetIDsp(updateNetID, WeaveIntrinsicFunc):
    """Create a network ID updating an existing one with a new send policy
    netid_update_sp(unsigned int netID,
             unsigned int sp)
    Return => unsigned int updatedNetId
    """

    @classmethod
    def getName(cls):
        return "netid_update_sp"

    def generateWeaveIR(self):
        return self.generateInstructions(
            "Trunking SP for netid_update_sp() to be 3 bits",
            0x7,
            6 + 2 + 3 + 16,  # (6 bits of lid, 2 bits of udid, 3 bits of cid and 16 bits of nid)
        )


class copyOperandsImm(WeaveIntrinsicFunc):
    """Copy the operands from the operand buffer to
    local memory
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "copyOperands"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.void, WeaveIRtypes.ptr, WeaveIRtypes.i32],
                [WeaveIRtypes.void, WeaveIRtypes.ptr, WeaveIRtypes.i64]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        res = []

        if not isinstance(ops[0], WeaveIRregister):
            errorMsg(
                "The first operand of copyOperands() must be a register",
                self.ctx.getFileLocation(),
            )

        if not ops[0].isOBuff:
            errorMsg(
                "The second operand of copyOperands() must be an argument of the event",
                self.ctx.getFileLocation(),
            )

        address_reg = ops[1]
        if isinstance(ops[1], WeaveIRimmediate):
            # Move to register
            tempDecl = self.ctx.ctx_scope.getTempDeclaration(WeaveIRtypes.ptr)
            res.append(
                WeaveIRmemory(
                    ctx=self.ctx,
                    dataType=WeaveIRtypes.ptr,
                    opType=WeaveIRmemoryTypes.LOAD,
                    ops=[ops[1]],
                )
            )
            res[-1].setRetOp(tempDecl.curReg)

        ops = [
            ops[0],  # First Operand
            address_reg,  # Address of the buffer
            ops[2],  # Number of Operands
        ]
        res.append(WeaveIRcopyOperands(self.ctx, ops))
        return res


class sizeof(WeaveIntrinsicFunc):
    """Get the size of a data type"""

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "sizeof"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i32

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.void]]

    @classmethod
    def earlyInline(cls):
        return True

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        return WeaveIRimmediate(
            self.ctx,
            ops[0].dtype.getSize(self.ctx.getFileLocation()),
            WeaveIRtypes.i32
        )


class printIntrinsic(WeaveIntrinsicFunc):
    """Print a value"""

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "print"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.void]]

    @classmethod
    def earlyInline(cls):
        return False

    @classmethod
    def variadicArguments(cls):
        return True

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        # Check first operand is an immediate string
        if (
                not isinstance(ops[0], WeaveIRimmediate)
                and ops[0].dtype != WeaveIRtypes.void
        ):
            errorMsg(
                "First operand of print() must be a string",
                self.ctx.getFileLocation(),
            )
        val = ops[0].getValue()
        if not isinstance(val, str):
            val = str(val)

        # Count '%'s in string
        numArgs = val.count("%") - 2 * val.count("%%")
        if numArgs != len(ops) - 1:
            errorMsg(
                "Number of arguments does not match number of %s in string",
                self.ctx.getFileLocation(),
            )

        res = [WeaveIRprint(self.ctx, ops)]
        return res


class hashValue(WeaveIntrinsicFunc):
    """
        Hash a register value
        hash(long data)
        Return => long hashValue
        The issue with that intrinsic is that the return register is also an input.
        It breaks comon C syntax and is not recommended to use.
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "hash"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i64

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.i64], [WeaveIRtypes.i32]]

    def generateWeaveIR(self):
        self.ctx.ctx_scope.startScope()
        ops, res, tempDecl = self.convertImmToReg(self.getInputTypes())

        # The hash function is special. The destination register is the input operand at the same time.
        ops.append(self.ctx.getAsOperand())

        res.append(WeaveIRhash(self.ctx, ops, WeaveIRhashTypes.HASHVALUE))
        res[-1].setRetOp(self.ctx.getAsOperand())
        res[-1].setFileLocation(self.ctx.getFileLocation())
        self.ctx.ctx_scope.endScope()
        return res


# class hashValueV2(WeaveIntrinsicFunc):
#     """
#         Hash a register value
#         hash(long data, long* inputAndOutput)
#         Return void
#     """
#
#     def __init__(self, ctx):
#         super().__init__(ctx)
#
#     @classmethod
#     def getName(cls):
#         return "hash"
#
#     @classmethod
#     def getReturnType(cls):
#         return WeaveIRtypes.void
#
#     @classmethod
#     def getInputTypes(cls):
#         return [[WeaveIRtypes.i64, WeaveIRtypes.ptr], [WeaveIRtypes.i32, WeaveIRtypes.ptr]]
#
#     def generateWeaveIR(self):
#         self.ctx.ctx_scope.startScope()
#         ops, res, tempDecl = self.convertImmToReg(self.getInputTypes(), [True, False])
#         res.append(WeaveIRhash(self.ctx, ops[0], WeaveIRhashTypes.HASHVALUE))
#         res[-1].setRetOp(ops[1])
#         res[-1].setFileLocation(self.ctx.getFileLocation())
#         self.ctx.ctx_scope.endScope()
#         return res

class hashLM(WeaveIntrinsicFunc):
    """
        Hash multiple entries in the LM
        hash(void* ptr, unsigned int numEntries)
        Return => long hashValue
    """

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "hash"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.i64

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.ptr, WeaveIRtypes.i64], [WeaveIRtypes.ptr, WeaveIRtypes.i32]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        if not isinstance(ops[1], WeaveIRimmediate):
            errorMsg(
                "Second operand of hash() must be an immediate value",
                self.ctx.getFileLocation(),
            )
        if ops[1].getOriginalValue() < 0 or ops[1].getOriginalValue() > 8:
            errorMsg(
                "Second operand of hash() must be a value between 1 and 8",
                self.ctx.getFileLocation(),
            )

        # The hash function is special. The destination register is the input operand at the same time.
        ops.append(self.ctx.getAsOperand())

        res = WeaveIRhash(self.ctx, ops, WeaveIRhashTypes.HASHLM)
        res.setRetOp(self.ctx.getAsOperand())
        res.setFileLocation(self.ctx.getFileLocation())
        return [res]


class perflogIntrinsic(WeaveIntrinsicFunc):
    """Perflog for debugging"""

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "perflog"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.void

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.i32, WeaveIRtypes.void], [WeaveIRtypes.i64, WeaveIRtypes.void]]

    @classmethod
    def earlyInline(cls):
        return False

    @classmethod
    def variadicArguments(cls):
        return True

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        # Check, if the ID of the event to be logged is an immediate value
        if not isinstance(ops[0], WeaveIRimmediate) or ops[0].dtype not in [WeaveIRtypes.i32, WeaveIRtypes.i64]:
            errorMsg(
                "First operand of perflog() must be an immediate integer value. It is an arbitrary ID to find the "
                "particular event in the log file.",
                self.ctx.getFileLocation(),
            )
        # Check second operand is an immediate string
        if not isinstance(ops[1], WeaveIRimmediate) and ops[1].dtype != WeaveIRtypes.void:
            errorMsg(
                "Second operand of perflog() must be a string",
                self.ctx.getFileLocation(),
            )

        val = ops[1].getValue()
        if not isinstance(val, str):
            val = str(val)

        # Count '%'s in string
        numArgs = val.count("%") - 2 * val.count("%%")
        if numArgs != len(ops) - 2:
            errorMsg(
                "Number of arguments does not match number of %s in string",
                self.ctx.getFileLocation(),
            )

        return [WeaveIRperflog(self.ctx, ops)]


class sqrt(WeaveIntrinsicFunc):
    """Square root of an FP value"""

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "sqrt"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.double

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.float], [WeaveIRtypes.double]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        res = WeaveIRarith(self.ctx, ops[0].dtype, WeaveIRarithTypes.FSQRT, ops[0], None)
        res.setRetOp(self.ctx.getAsOperand())
        return [res]


class exp(WeaveIntrinsicFunc):
    """Exponent of an FP value"""

    def __init__(self, ctx):
        super().__init__(ctx)

    @classmethod
    def getName(cls):
        return "exp"

    @classmethod
    def getReturnType(cls):
        return WeaveIRtypes.double

    @classmethod
    def getInputTypes(cls):
        return [[WeaveIRtypes.float], [WeaveIRtypes.double]]

    def generateWeaveIR(self):
        ops = self.ctx.getInOps()
        res = WeaveIRarith(self.ctx, ops[0].dtype, WeaveIRarithTypes.FEXP, ops[0], None)
        res.setRetOp(self.ctx.getAsOperand())
        return [res]
