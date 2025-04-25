#!/usr/bin/env python3
import frontend.lexer as lex
import frontend.parser as par
import frontend.codeGen as codeGen
import frontend.preprocessor
import Weave.debug as debug
from backend import pythonGen
from backend.registerAllocator import WeaveLifetimeRegAlloc
from Weave.optimizer import *
import sys

import os
import argparse

WEAVE_VERSION = 0.1

__INIT_FILE = True


def outputManager(result, outFile):
    global __INIT_FILE
    if outFile and len(outFile) > 0:
        try:
            with open(outFile, "w" if __INIT_FILE else "+a") as f:
                f.write(result)
            __INIT_FILE = False
        except Exception as e:
            print(f"Error trying to write output file: {str(e)}")
    else:
        print(result)


def main():
    # check version
    if not (sys.version_info.major >= 3 and sys.version_info.minor >= 8):
        errorMsg("UpDown Weave requires Python 3.8 or higher.")

    parser = argparse.ArgumentParser(description="UpDown Weave compiler")
    parser.add_argument(
        "--input", "-i", dest="input", action="store", type=str, help="input file"
    )
    parser.add_argument(
        "-dp",
        "--debug-parser",
        dest="deb_parser",
        action="store_true",
        help="Enable debug parser",
    )
    parser.add_argument(
        "-dl",
        "--debug-lexer",
        dest="deb_lexer",
        action="store_true",
        help="Enable debug parser",
    )

    parser.add_argument(
        "-d", "--debug-level", dest="deb_level", action="store", help="Set debug level"
    )

    parser.add_argument(
        "--ast-dump",
        dest="ast_dump",
        action="store_true",
        help="Dump Abstract Syntax Tree and stop",
    )

    parser.add_argument(
        "--weave-ir",
        dest="weave_ir",
        action="store_true",
        help="Generate Weave IR and stop",
    )

    parser.add_argument(
        "--opts",
        dest="opts",
        action="store",
        help="Define Optimization Passes",
    )

    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        action="store",
        type=str,
        help="Output file",
    )

    parser.add_argument(
        "--preprocessor",
        "-E",
        dest="preprocessor",
        action="store_true",
        help="Run preprocessor only",
    )

    parser.add_argument(
        "--cpp-preprocessor-path",
        dest="cpp_preprocessor_path",
        action="store",
        type=str,
        help="Path to cpp preprocessor",
        default="cpp",
    )

    parser.add_argument(
        "--preprocessor-args",
        dest="preprocessor_args",
        action="append",
        type=str,
        nargs='*',
        help="extra arguments for the proprocessor",
        default=[]
    )

    parser.add_argument(
        "--include-path",
        "-I",
        dest="include_path",
        action="append",
        type=str,
        help="set the Include path directory used by the preprocessor for #include directives",
    )

    parser.add_argument(
        "--inline-code-in-backend",
        dest="inline_code_in_backend",
        action="store_true",
        help="Inline code in the generated backend as comments",
    )

    parser.add_argument(
        "-O",
        dest="opt_level",
        action="store",
        type=int,
        help="Optimization levels: 0, 2",
        default=0,
    )

    parser.add_argument(
        "-w",
        dest="warningActive",
        action="store_false",
        help="Disable warning messages",
        default=True
    )
    args = parser.parse_args()
    inFile = args.input
    outFile = args.output
    deb_parser = args.deb_parser
    deb_lexer = args.deb_lexer
    # flatten list of lists
    preprocessor_args = [arg[0] for arg in args.preprocessor_args]
    if args.deb_level:
        debug.DEBUG_LEVEL = int(args.deb_level)

    debug.WARNING_ACTIVE = args.warningActive

    lexer = lex.WeaveLexer()
    lexer.build(debug=deb_lexer)
    p = par.WeaveParser(lexer.lexer)
    p.build(debug=deb_parser)

    cg = codeGen.WeaveCodeGen(inline_code=args.inline_code_in_backend)

    applyOpts = str(args.opts).split(",") if args.opts else []
    if args.opt_level >= 2:
        applyOpts.append("RemoveUnusedVariables")
    applyOpts.append("InlineIntrinsic")
    # if args.opt_level >= 2:
    #     applyOpts.append("UnusedInstrRemoval")
    applyOpts.append("IfCmpBranchMerging")
    applyOpts.append("FaddFmulMerging")
    applyOpts.append("OperandSubstitution")
    applyOpts.append("SplitImmediates")
    if args.opt_level >= 2:
        applyOpts.append("BranchJumpMerging")
    applyOpts.append("EmptyBasicBlockMerging")

    if inFile:
        try:
            if not os.path.isfile(inFile):
                errorMsg(f"File {inFile} not found")

            prep = frontend.preprocessor.WeavePreprocessor(
                path=args.cpp_preprocessor_path, input_file=inFile, args=preprocessor_args
            )

            if args.include_path:
                prep.setIncludePaths(args.include_path)

            contents = prep.preprocess()

            if args.preprocessor:
                outputManager(contents, outFile)
                sys.exit(0)

            # result = p.parser.parse(contents, lexer=l.lexer, debug=True, tracking=True)
            result = p.parse(
                contents, debug=deb_parser, fileName=inFile, fileContent=contents
            )
            if args.ast_dump:
                outputManager(str(p.getTree()), outFile)
                sys.exit(0)
            result = cg.traverse(result)
            if args.weave_ir:
                res = f"PreOPT:\n{result}"
                outputManager(res, outFile)
            for opt in applyOpts:
                toApply = WeaveIRopt.getOpt(opt)
                if len(toApply) > 0:
                    toApply[0].apply(result)
                else:
                    debug.warningMsg(f"Optimization {opt} not found")
            if args.weave_ir:
                res = f"\nPostOPT:\n{result}"
                outputManager(res, outFile)
                sys.exit(0)
            pygen = pythonGen.WeavePythonCodeGen(result, WeaveLifetimeRegAlloc(), args.inline_code_in_backend)
            result = pygen.traverse()
            outputManager(result, outFile)
        except Exception as e:
            print(f"UDWeave General Error -- Report a bug: {str(e)}\n\n")
            raise e

    else:
        print(f"UpDown Weave Compiler - Version {WEAVE_VERSION}")
        parser.print_usage()
        sys.exit(0)
        # TODO: How to support quick snippets for easy assembly generation? Implement below
        while True:
            try:
                s = input("Interactive Mode > ")
            except EOFError:
                break
            if not s:
                continue
            result = p.parse(s)
            print(result)


if __name__ == "__main__":
    main()
