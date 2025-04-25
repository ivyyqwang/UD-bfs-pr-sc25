from enum import Enum
import frontend.ASTweave as ASTweave
from Weave.WeaveIR import *
from Weave.debug import debugMsg, errorMsg, warningMsg
from Weave.fileLocation import FileLocation
from Weave.helper import log2


class WeaveIRconfiguration(Enum):
    ALLIGN = 8


class WeaveIRregTypes(Enum):
    """WeaveIR register types:
    * General purpose register
    * Operand Buffer
    * Control registers

    Args:
        Enum (int): Enum
    """

    gpr = 0
    opbuff = 1
    control = 2
    unknown = 1000


class WeaveIRcontrolRegs(Enum):
    NETID = 0
    CCONT = 1
    CEVNT = 2
    LMBASE = 3


class WeaveIRtypes(Enum):
    """WeaveIR data types
    * Integers with 8, 16, 32, 64 bit length
    * floating point for 16, 32 and 64 bit lengths
    * pointers
    """

    # integers
    i8 = 0
    i16 = 1
    i32 = 2
    i64 = 3
    # floats
    bf16 = 4
    float = 5
    double = 6
    # pointers
    ptr = 7
    void = 8
    # structures
    struct = 9
    union = 10
    # constants
    c8 = 11
    c16 = 12
    c32 = 13
    c64 = 14

    unknown = 1000

    @property
    def isInteger(self):
        return self in [self.i8, self.i16, self.i32, self.i64]

    @property
    def isFloatingPoint(self):
        return self in [self.bf16, self.float, self.double]

    @property
    def isPointer(self):
        return self == self.ptr

    @property
    def isStruct(self):
        return self == self.struct

    @property
    def isUnion(self):
        return self == self.union

    def getSize(self, Loc: FileLocation = None) -> int:
        """Get the size of the data type in bytes

        Returns:
            int: size of the data type in bytes
        """

        type_sizes = {
            WeaveIRtypes.i8: 1,
            WeaveIRtypes.i16: 2,
            WeaveIRtypes.i32: 4,
            WeaveIRtypes.i64: 8,
            WeaveIRtypes.bf16: 2,
            WeaveIRtypes.float: 4,
            WeaveIRtypes.double: 8,
            WeaveIRtypes.ptr: 8,
            WeaveIRtypes.struct: 0,
            WeaveIRtypes.union: 0,
            WeaveIRtypes.c8: 1,
            WeaveIRtypes.c16: 2,
            WeaveIRtypes.c32: 4,
            WeaveIRtypes.c64: 8,
        }

        if self not in type_sizes:
            errorMsg(f"Unknown data type {self}, cannot get size", Loc)
        return type_sizes[self]

    def getScale(self) -> int:
        """The number of bytes^2 to shift by to get the next
        element in the array

        Returns:
            int: scale value
        """
        type_scales = {
            WeaveIRtypes.i8: 0,
            WeaveIRtypes.i16: 1,
            WeaveIRtypes.i32: 2,
            WeaveIRtypes.i64: 3,
            WeaveIRtypes.bf16: 2,
            WeaveIRtypes.float: 2,
            WeaveIRtypes.double: 3,
            WeaveIRtypes.ptr: 3,
            WeaveIRtypes.struct: 0,
            WeaveIRtypes.union: 0,
            WeaveIRtypes.c8: 0,
            WeaveIRtypes.c16: 1,
            WeaveIRtypes.c32: 2,
            WeaveIRtypes.c64: 3,
        }

        if self not in type_scales:
            errorMsg(f"Unknown data type {self}, cannot get scale")
        return type_scales[self]

    def mapToInstrName(self) -> str:
        mapValues = {
            WeaveIRtypes.i64: "i64", WeaveIRtypes.i32: "i32", WeaveIRtypes.i16: "i16", WeaveIRtypes.i8: "i8",
            WeaveIRtypes.double: "64", WeaveIRtypes.float: "32", WeaveIRtypes.bf16: "b16",
            WeaveIRtypes.c64: "i64", WeaveIRtypes.c32: "i32", WeaveIRtypes.c16: "i16", WeaveIRtypes.c8: "i8",
        }
        if self not in mapValues:
            return ""
        return mapValues[self]


class WeaveIRuserDefinedType:
    """ This is a class with state, apart from the type, it stores the size of the struct """

    def __init__(self, size: int, typeIn: WeaveIRtypes):
        self.size = size
        self.type = typeIn

    def getSize(self, Loc: FileLocation = None) -> int:
        return self.size

    def setSize(self, size: int):
        self.size = size

    @property
    def name(self):
        return self.type.name


class WeaveIRqualifiers(Enum):
    """Type qualifiers that modify the WeaveIR type
    * Constant value
    * unsigned value
    * signed value
    * scratchpad memory - Used with pointers
    """

    unsigned = 0
    signed = 1
    const = 2
    spmem = 3
    static = 4
    private = 5
    constexp = 6
    unknown = 1000


class WeaveIRarithTypes(Enum):
    """Arithmetic operations for WeaveIR
    Contains all the arithmetic operations in both
    formats: integer or floating point. The instruction
    may contain additional qualifiers to differentiate
    between sign and unsigned
    """

    IADDITION = "add"
    FADDITION = "fadd"
    ISUBTRACTION = "sub"
    FSUBTRACTION = "fsub"
    IMULT = "mul"
    FMULT = "fmul"
    IDIVIDE = "div"
    FDIVIDE = "fdiv"
    FSQRT = "fsqrt"
    FEXP = "fexp"
    FMULTADD = "fmadd"
    MODULO = "mod"
    UNKNOWN = 1000

    def isCommutative(self) -> bool:
        return self in [
            WeaveIRarithTypes.IADDITION,
            WeaveIRarithTypes.FADDITION,
            WeaveIRarithTypes.IMULT,
            WeaveIRarithTypes.FMULT,
        ]

    def isFP(self) -> bool:
        return self in [self.FADDITION, self.FSUBTRACTION, self.FMULT, self.FDIVIDE, self.FEXP, self.FSQRT,
                        self.FMULTADD]


class WeaveIRbitwiseTypes(Enum):
    """Bitwise operations
    This includes shift left and right, and bitwise logic operations
    This differentiates between shift rights that are logical (zero filled)
    and arithmetic (sign extended) operations.

    Args:
        Enum (_type_): _description_
    """

    SHFTLFT = "shl"
    LSHFTRGT = "lshr"
    ASHFTRGT = "ashr"
    BWOR = "or"
    BWAND = "and"
    BWXOR = "xor"
    UNKNOWN = 1000

    def isCommutative(self) -> bool:
        return self in [
            WeaveIRbitwiseTypes.BWOR,
            WeaveIRbitwiseTypes.BWAND,
            WeaveIRbitwiseTypes.BWXOR,
        ]


class WeaveIRcompareTypes(Enum):
    EQUAL = "eq"
    NOTEQUAL = "ne"
    UGREAT = "ugt"
    UGREATEQ = "uge"
    ULESS = "ult"
    ULESSEQ = "ule"
    SGREAT = "sgt"
    SGREATEQ = "sge"
    SLESS = "slt"
    SLESSEQ = "sle"
    UNKNOWN = 1000

    def isCommutative(self) -> bool:
        return self in [
            WeaveIRcompareTypes.EQUAL,
            WeaveIRcompareTypes.NOTEQUAL,
        ]


class WeaveIRBranchTypes(Enum):
    UNCONDITIONAL = "jmp"
    CONDITIONALNEQ = "bne"
    CONDITIONALEQ = "beq"
    CONDITIONALGT = "bgt"
    CONDITIONALLT = "blt"
    CONDITIONALGE = "bge"
    CONDITIONALLE = "ble"
    UNKNOWN = 1000

    def negateCondition(self):
        if self == self.UNCONDITIONAL:
            return errorMsg("Cannot negate an unconditional branch")

        mappingCondition = {
            self.CONDITIONALNEQ: self.CONDITIONALEQ,
            self.CONDITIONALEQ: self.CONDITIONALNEQ,
            self.CONDITIONALGT: self.CONDITIONALLE,
            self.CONDITIONALLT: self.CONDITIONALGE,
            self.CONDITIONALGE: self.CONDITIONALLT,
            self.CONDITIONALLE: self.CONDITIONALGT
        }
        return mappingCondition[self]


class WeaveIRmemoryTypes(Enum):
    LOAD = "load"
    LOADLOCAL = "local_load"
    STORELOCAL = "local_store"
    UNKNOWN = 1000

    @property
    def isLocal(self):
        return self in [self.LOADLOCAL, self.STORELOCAL]


class WeaveIRsendPolicy(Enum):
    """ Send policy for the send instructions
    Refer to https://docs.google.com/document/d/1zLna4Ud4ssfploZHDs9niQKfR3W6dcwK/edit#heading=h.s2udj4pmbag9
    """
    DIRECT = 0  # Target refers to exact lane network ID
    SHORTEST_64 = 1  # Send to the shortest queue among the 64 lanes within a UD
    SHORTEST_32_LOW = 2  # Send to the shortest queue among the 32 lower order lanes within a UD (LID:0-31)
    SHORTEST_32_HIGH = 3  # Send to the shortest queue among the 32 higher order lanes within a UD (LID:32-63)
    LONGEST_32_LOW = 4  # Send to the longest queue among the 32 lower order lanes within a UD (LID:0-31)
    LONGEST_32_HIGH = 5  # Send to the longest queue among the 32 higher order lanes within a UD (LID:32-63)
    LONGEST_64 = 6  # Send to the longest queue among the 64 lanes within a UD

    # Send to an UpDown who is on the same node as the destination address (specified in the first
    # data of the message). Note that the specific updown and lane to be sent to is undefined.
    NEAR_ADDRESS = 7

    UNKNOWN = 1000


class WeaveIRsendTypes(Enum):
    SEND = "send"
    SENDR = "sendr"
    SENDR3 = "sendr3"
    SENDOPS = "sendops"

    # Pseudo instructions for send instructions
    # All pseudo instructions ending with "_wret" need an additional register to temporarily store their computation
    # from a label to a word.
    SEND_WCONT = "send_wcont"
    SENDR_WCONT = "sendr_wcont"
    SENDR3_WCONT = "sendr3_wcont"
    SENDOPS_WCONT = "sendops_wcont"
    SEND_WRET = "send_wret"
    SENDR_WRET = "sendr_wret"
    SENDR3_WRET = "sendr3_wret"
    SENDOPS_WRET = "sendops_wret"

    # DRAM access
    SENDM = "sendm"
    SENDMR = "sendmr"
    SENDMR2 = "sendmr2"
    SENDMOPS = "sendmops"

    # Pseudo instructions for DRAM access
    # All pseudo instructions ending with "_wret" need an additional register to temporarily store their computation
    # from a label to a word.

    # Send read requests to DRAM
    SEND_DMLM_LD = "send_dmlm_ld"
    SEND_DMLM_LD_WRET = "send_dmlm_ld_wret"

    # Send write requests to DRAM
    #    Local Memory
    SEND_DMLM = "send_dmlm"
    SEND_DMLM_WRET = "send_dmlm_wret"
    #    1 register
    SENDR_DMLM = "sendr_dmlm"
    SENDR_DMLM_WRET = "sendr_dmlm_wret"
    #    2 registers
    SENDR2_DMLM = "sendr2_dmlm"
    SENDR2_DMLM_WRET = "sendr2_dmlm_wret"

    # operand registers of an event
    SENDOPS_DMLM_WRET = "sendops_dmlm_wret"


class WeaveIRyieldTypes(Enum):
    YIELD = "yield"
    YIELD_TERMINATE = "yield_terminate"


class WeaveIRasmConstraints(Enum):
    REGISTER = "r"
    LABEL = "l"
    LITERAL = "i"
    OUTPUT = "="

    @classmethod
    def getList(cls):
        return [e.value for e in cls]


class WeaveIRhashTypes(Enum):
    HASHVALUE = "hash"
    HASHLM = "hashl"


def convertASTtype(dataType):
    """Function to convert AST data types to WeaveIR types

    Args:
        dataType (ASTweave.WeaveDataTypes): The AST data type

    Returns:
        WeaveIRtypes: The WeaveIR data type
    """
    map_ast_t = {
        ASTweave.WeaveDataTypesPrimitives.Char: WeaveIRtypes.i8,
        ASTweave.WeaveDataTypesPrimitives.Short: WeaveIRtypes.i16,
        ASTweave.WeaveDataTypesPrimitives.Integer: WeaveIRtypes.i32,
        ASTweave.WeaveDataTypesPrimitives.Long: WeaveIRtypes.i64,
        ASTweave.WeaveDataTypesPrimitives.BF16: WeaveIRtypes.bf16,
        ASTweave.WeaveDataTypesPrimitives.Float: WeaveIRtypes.float,
        ASTweave.WeaveDataTypesPrimitives.Double: WeaveIRtypes.double,
        ASTweave.WeaveDataTypesPrimitives.String: WeaveIRtypes.void,
        ASTweave.WeaveDataTypesPrimitives.UserDefined: WeaveIRtypes.unknown,
        ASTweave.WeaveDataTypesPrimitives.Undefined: WeaveIRtypes.unknown,
    }
    return map_ast_t[dataType.type]


def convertASTqual(qual):
    """Convert qualifiers from AST to WeaveIR

    Args:
        qual (ASTweave.WeaveTypeQualifier): Qualifier in AST

    Returns:
        WeaveIRqualifiers: The equivalent WeaveIR qualifier
    """
    map_ast_q = {
        ASTweave.WeaveTypeQualifier.Constant: WeaveIRqualifiers.const,
        ASTweave.WeaveTypeQualifier.GlobalConstant: WeaveIRqualifiers.const,
        ASTweave.WeaveTypeQualifier.Unsigned: WeaveIRqualifiers.unsigned,
        ASTweave.WeaveTypeQualifier.Signed: WeaveIRqualifiers.signed,
        ASTweave.WeaveTypeQualifier.Static: WeaveIRqualifiers.static,
        ASTweave.WeaveTypeQualifier.Private: WeaveIRqualifiers.private,
        ASTweave.WeaveTypeQualifier.Pointer: None,
        ASTweave.WeaveTypeQualifier.LocalPointer: None,
    }
    try:
        return map_ast_q[qual]
    except TypeError as e:
        debugMsg(1, f"Error when trying to convert the qualifier {qual}")
        raise


def convertASTarithOp(op, type):
    """Convert AST arithmetic operations to WeaveIR depending on the data types

    The data type determines floating point vs integer operations.

    Args:
        op (ASTweave.WeaveBinaryOps): The operation to be translated from AST to WeaveIR
        type (STweave.WeaveIRtypes): Data type in WeaveIR format

    Returns:
        WeaveIRarithTypes: The converted operation in WeaveIR format
    """
    map_ast_q = {}
    if type.isInteger:
        map_ast_q = {
            ASTweave.WeaveBinaryOps.PLUS: WeaveIRarithTypes.IADDITION,
            ASTweave.WeaveBinaryOps.MINUS: WeaveIRarithTypes.ISUBTRACTION,
            ASTweave.WeaveBinaryOps.TIMES: WeaveIRarithTypes.IMULT,
            ASTweave.WeaveBinaryOps.DIVIDE: WeaveIRarithTypes.IDIVIDE,
            ASTweave.WeaveBinaryOps.MODULO: WeaveIRarithTypes.MODULO,
        }
    elif type.isFloatingPoint:
        map_ast_q = {
            ASTweave.WeaveBinaryOps.PLUS: WeaveIRarithTypes.FADDITION,
            ASTweave.WeaveBinaryOps.MINUS: WeaveIRarithTypes.FSUBTRACTION,
            ASTweave.WeaveBinaryOps.TIMES: WeaveIRarithTypes.FMULT,
            ASTweave.WeaveBinaryOps.DIVIDE: WeaveIRarithTypes.FDIVIDE,
            ASTweave.WeaveBinaryOps.MODULO: WeaveIRarithTypes.MODULO,
        }
    elif type.isPointer:
        map_ast_q = {
            ASTweave.WeaveBinaryOps.PLUS: WeaveIRarithTypes.IADDITION,
            ASTweave.WeaveBinaryOps.MINUS: WeaveIRarithTypes.ISUBTRACTION,
        }
    return map_ast_q[op] if op in map_ast_q else WeaveIRarithTypes.UNKNOWN


def convertASTbitwiseOp(op, quals):
    """Convert AST bitwise operations to WeaveIR bitwise operations

    Args:
        op (ASTweave.WeaveBinaryOps): The operation to be translated from AST to WeaveIR
        quals (STweave.WeaveDataTypes): List of AST quals

    Returns:
        WeaveIRbitwiseTypes: The converted operation in WeaveIR format
    """

    map_ast_q = {
        ASTweave.WeaveBinaryOps.SHFTLFT: WeaveIRbitwiseTypes.SHFTLFT,
        ASTweave.WeaveBinaryOps.BWOR: WeaveIRbitwiseTypes.BWOR,
        ASTweave.WeaveBinaryOps.OR: WeaveIRbitwiseTypes.BWOR,
        ASTweave.WeaveBinaryOps.BWAND: WeaveIRbitwiseTypes.BWAND,
        ASTweave.WeaveBinaryOps.AND: WeaveIRbitwiseTypes.BWAND,
        ASTweave.WeaveBinaryOps.BWXOR: WeaveIRbitwiseTypes.BWXOR,
        ASTweave.WeaveBinaryOps.SHFTRGT: (
            WeaveIRbitwiseTypes.ASHFTRGT
            if WeaveIRqualifiers.signed in quals
            else WeaveIRbitwiseTypes.LSHFTRGT
        )
    }

    return map_ast_q[op] if op in map_ast_q else WeaveIRbitwiseTypes.UNKNOWN


def convertASTcompareOp(op, quals):
    """Convert AST Comparison operations to WeaveIR comparison operations

    Args:
        op (ASTweave.WeaveBinaryOps): The operation to be translated from AST to WeaveIR
        qual (STweave.WeaveIRqualifiers): WeaveIR Qualifier for sign vs unsigned

    Returns:
        WeaveIRcompareTypes: The converted operation in WeaveIR for comparison
    """

    map_ast_q = {
        ASTweave.WeaveBinaryOps.EQUAL: WeaveIRcompareTypes.EQUAL,
        ASTweave.WeaveBinaryOps.DIFFERENT: WeaveIRcompareTypes.NOTEQUAL,
    }

    if WeaveIRqualifiers.signed in quals:
        map_ast_q.update(
            {
                ASTweave.WeaveBinaryOps.GREATERTHAN: WeaveIRcompareTypes.SGREAT,
                ASTweave.WeaveBinaryOps.GREATEREQTO: WeaveIRcompareTypes.SGREATEQ,
                ASTweave.WeaveBinaryOps.LESSTHAN: WeaveIRcompareTypes.SLESS,
                ASTweave.WeaveBinaryOps.LESSEQTO: WeaveIRcompareTypes.SLESSEQ,
            }
        )
    else:
        map_ast_q.update(
            {
                ASTweave.WeaveBinaryOps.GREATERTHAN: WeaveIRcompareTypes.UGREAT,
                ASTweave.WeaveBinaryOps.GREATEREQTO: WeaveIRcompareTypes.UGREATEQ,
                ASTweave.WeaveBinaryOps.LESSTHAN: WeaveIRcompareTypes.ULESS,
                ASTweave.WeaveBinaryOps.LESSEQTO: WeaveIRcompareTypes.ULESSEQ,
            }
        )

    return map_ast_q[op] if op in map_ast_q else WeaveIRcompareTypes.UNKNOWN
