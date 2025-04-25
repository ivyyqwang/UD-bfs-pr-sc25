""" This file contains all the types used in the AST
    and the parser. It also allows support for user defined types
"""
from enum import Enum


class WeaveTypeQualifier(Enum):
    """To avoid representing all combination of
    types and qualifiers, we separate qualifiers from
    data types.
    """

    Constant = 0
    Unsigned = 1
    Signed = 2
    Pointer = 3
    LocalPointer = 4
    Static = 5
    Private = 6  # Creates one copy per lane
    GlobalConstant = 7


class WeaveDeclTypes(Enum):
    """Check declaration context type: thread, param, event local"""

    Thread = 0
    Param = 1
    Event = 2
    Global = 3
    Extern = 4  # Implies global
    Struct = 5
    Union = 6
    Scope = 7


class WeaveDataTypesPrimitives(Enum):
    """Notice that these data types are different to
    those supported by weaveIR
    """
    Char = "char"
    Short = "short"
    Integer = "int"
    Long = "long"
    BF16 = "bf16"
    Float = "float"
    Double = "double"
    String = "string"
    UserDefined = "userDefined"
    Undefined = 6


class WeaveDataTypes:
    def __init__(self, ty: WeaveDataTypesPrimitives = WeaveDataTypesPrimitives.UserDefined, name: str = None):
        self.type = ty
        self.name = name

        if ty == WeaveDataTypesPrimitives.UserDefined and name is None:
            raise ValueError("User defined type must have a name")

    def setName(self, name: str):
        """Used for structs
        Args:
            name (str): name of the struct
        """
        self.name = name

    def getName(self) -> str:
        """Used for structs
        Returns:
            str: name of the struct
        """
        if self.type == WeaveDataTypesPrimitives.UserDefined:
            return self.name
        else:
            return self.type.name

    def isFP(self):
        return self.type in [WeaveDataTypesPrimitives.BF16, WeaveDataTypesPrimitives.Float,
                             WeaveDataTypesPrimitives.Double]


class WeaveASTTypes(Enum):
    """Different types of AST Nodes"""

    Root = 0
    BinaryOperator = 1
    UnaryOperator = 2
    Literal = 3
    Identifier = 4
    IfStatement = 5
    WhileStatement = 6
    ForStatement = 7
    AssignStatement = 8
    DeclarationStatement = 9
    CastOperation = 10
    Thread = 11
    Event = 12
    Assembly = 13
    Call = 14
    Comment = 15
    Empty = 16
    AssemblyOperand = 17
    Struct = 18
    Union = 19
    Scope = 20
    Break = 21
    Continue = 22
    Unkown = 1000


class WeaveBinaryOps(Enum):
    """Supported operations that take 2 operands
    usually in the form "a OP b", but also for a[b]
    """

    PLUS = 0
    MINUS = 1
    TIMES = 2
    DIVIDE = 3
    MODULO = 4
    SHFTLFT = 5
    SHFTRGT = 6
    LESSTHAN = 7
    LESSEQTO = 8
    GREATERTHAN = 9
    GREATEREQTO = 10
    AND = 11
    OR = 12
    BWOR = 13
    BWAND = 14
    BWXOR = 15
    EQUAL = 16
    DIFFERENT = 17
    MEMORY_DERREF = 18
    STRUCT_ELEMENT_ACCESS = 19

    def isCommutative(self) -> bool:
        return self in [
            WeaveBinaryOps.PLUS,
            WeaveBinaryOps.TIMES,
            WeaveBinaryOps.AND,
            WeaveBinaryOps.OR,
            WeaveBinaryOps.BWAND,
            WeaveBinaryOps.BWOR,
            WeaveBinaryOps.BWXOR,
            WeaveBinaryOps.EQUAL,
            WeaveBinaryOps.DIFFERENT,
        ]


class WeaveTemplateParamTypes(Enum):
    """Supported template parameter types"""

    TYPENAME = 0
    EVENTNAME = 1
    UNKNOWN = 1000


class WeaveUnaryOps(Enum):
    NOT = 0
    BWNOT = 1
    NEGATE = 2
    DERREF = 3
