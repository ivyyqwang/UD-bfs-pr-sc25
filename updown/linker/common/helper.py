from typing import Union, Tuple
from common.instructions import UpDownInstFormat
import re

import os

module_dir = os.path.dirname(__file__)
instructions_file = os.path.join(module_dir, "instructions.txt")

UpDownInstructions = UpDownInstFormat.readInstructions(instructions_file)

from common.debug import *
from typing import List

LABEL_REGEX = r"[a-zA-Z_][a-zA-Z0-9_\-.]*"


def isRegister(arg: str) -> bool:
    """Checks if the argument is a register name

    Args:
        arg (str): The name that needs to be checked

    Returns:
        bool: The name corresponds to a register name
    """
    ## ISA V2 Registers
    registersList = [f"X{index}" for index in range(32)]
    ## ISA V1 Registers
    registersList += [f"UDPR_{index}" for index in range(32)]
    ## ISA V1 Special Registers
    registersList += [
        "SBP",
        "NWID",
        "LID",
        "SBPB",
        "EQT",
        "TS",
        "TID",
        "SBCR",
        "SBP",
        "SBPB",
        "SBCR",
    ]
    ## ISA V1 operand buffers
    registersList += [f"OB{index}" for index in range(10)]
    return arg in registersList


def isReservedWord(arg: str) -> bool:
    """Checks if the argument is a reserved word

    Args:
        arg (str): The name that needs to be checked

    Returns:
        bool: The name corresponds to a reserved word
    """
    reservedWords = []
    return arg in reservedWords


def isSymbol(arg: str) -> bool:
    """Checks if a given string is a label

    A label is a string that:
    1. Is not a reserved word (e.g. an ISA instruction name)
    2. does not start with a number
    3. Contains only alphanumeric characters and underscores

    Args:
        arg (str): The string that needs to be checked

    Returns:
        bool: True if the string is a label, False otherwise
    """
    if arg in UpDownInstructions:
        return False
    if arg[0].isnumeric():
        return False
    if re.match(f"^{LABEL_REGEX}$", arg) is None:
        return False
    return True

def isStringLiteral(arg: str) -> bool:
    """Checks if the argument is a string literal

    Args:
        arg (str): The name that needs to be checked

    Returns:
        bool: The name corresponds to a string literal
    """
    if arg[0] == "'" and arg[-1] == "'":
        return True
    if arg[0] == '"' and arg[-1] == '"':
        return True
    return False

def isNumericLiteral(arg: str) -> Tuple[bool, Union[int, float, None]]:
    """Checks if the argument is a literal

    Args:
        arg (str): The name that needs to be checked

    Returns:
        bool: The name corresponds to a literal
    """
    try:
        int(arg)
        return True, int(arg)
    except ValueError:
        try:
            int(arg, 16)
            return True, int(arg, 16)
        except ValueError:
            try:
                int(arg, 2)
                return True, int(arg, 2)
            except ValueError:
                try:
                    float(arg)
                    return True, float(arg)
                except ValueError:
                    return False, None



def hasTargetLabel(action: str) -> bool:
    """Check if the action starts with a target label

    Labels use the format LABEL_REGEX + ":" + action

    Args:
        action (str): The action to check

    Returns:
        bool: True if the action starts with a label, False otherwise
    """
    return re.match(f"^{LABEL_REGEX}:", action) is not None


def getActionOpCode(action: str) -> Union[str, None]:
    """Get the opcode of the action

    Args:
        action (str): The action to check

    Returns:
        Union[str, None]: The opcode if it exists, None otherwise
    """
    if hasTargetLabel(action):
        action = action.split(":")[1].strip().split(" ")[0]
    ## TODO: OpCodes should be compared and used here vs the ISA. For now we return the first element
    # if action in UpDownInstructions:
    #     return action
    return action.split()[0]


def getActionOperands(action) -> List[str]:
    """Get a list of operands from the action

    Given an action get the operands. Remove possible labels and opcode

    """
    opcode = getActionOpCode(action)
    ## Operands may have parenthesis, comas or spaces
    if hasTargetLabel(action):
        ## Remove the label
        operands = ':'.join(action.split(":")[1:]).strip()
    else:
        operands = action

    ## Remove pseudo instructions that have strings
    if opcode == "print" or opcode == "perflog":
        operands = re.sub(r'".*"', "", operands)
        operands = re.sub(r"'.*'", "", operands)

    ## Remove the opcode by replacing first occurrence of it
    operands = operands.replace(opcode, "", 1)
    operands = operands.replace("(", " ")
    operands = operands.replace(")", " ")
    operands = operands.replace(",", " ")

    operands = operands.strip()
    debugMsg(20, f"stripped operands: {operands}")
    operands = operands.split()

    return operands


def getTargetLabel(action: str) -> Union[str, None]:
    """Get the target label of the action

    Args:
        action (str): The action to check

    Returns:
        Union[str, None]: The target label if it exists, None otherwise
    """
    if hasTargetLabel(action):
        return action.split(":")[0].strip()
    return None


def randomString(length: int) -> str:
    """Generate a random string of fixed length

    Args:
        length (int): The length of the string

    Returns:
        str: The random string
    """
    import random
    import string

    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))
