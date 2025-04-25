WOVEN_ASSERT = False
DEBUG_LEVEL = 0
WARNING_ACTIVE = True

import sys

def debugMsg(level, text):
    if level <= DEBUG_LEVEL:
        print(text)


def errorMsg(text: str, position=None):
    if position:
        print(f"{str(position)}: {text}\n{position.getLineHighlighted()}")
    else:
        print(text)
    sys.exit(1)


def warningMsg(text):
    if WARNING_ACTIVE:
        print("WARNING!! - " + str(text))


def weaveAssert(condition, message):
    if WOVEN_ASSERT:
        assert condition, message
