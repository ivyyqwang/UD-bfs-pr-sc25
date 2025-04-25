import sys
import inspect
import os

DEBUG_LEVEL = 0

def debugMsg(level: int, text: str):
    if level <= DEBUG_LEVEL:
        print(text)


def errorMsg(text: str):
    call_path = ""
    frame = inspect.currentframe().f_back
    while frame is not None:
        filename = inspect.getframeinfo(frame).filename
        lineno = inspect.getframeinfo(frame).lineno
        basename = os.path.basename(filename)
        call_path = basename + ":" + str(lineno) + " -> " + call_path
        frame = frame.f_back

    if call_path == "":
        call_path = "unknown"
    elif call_path[-4:] == " -> ":
        call_path = call_path[:-4]

    print(f"ERROR [{call_path}]: {text}\n")
    exit(1)


def warningMsg(text: str):
    # Print to stderr
    print("WARNING!! - " + str(text), file=sys.stderr)
