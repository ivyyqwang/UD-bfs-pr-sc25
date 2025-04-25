import os, sys
import importlib
import argparse

sys.path.append(f"{os.getcwd()}/efas/")
# import efas
from efas import *
from pathlib import Path
from EFA_v2 import *
from UpDown_Assembler import *


def import_module_from_file(func_name):
    try:
        module = importlib.import_module(func_name)
        return module

    except ImportError:
        print(f"Error importing module from '{func_name}'.", file=sys.stderr)
        exit(1)


def extract_directory_and_filename(file_path):
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    return directory, filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--efa", help="Input EFA to convert", required=True)
    parser.add_argument("--outpath", help="path of the outputfile", required=True)
    parser.add_argument(
        "--debug-messages",
        help="use switch to debug assembler",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--text-symbol-table",
        help="write the symbol table to a text file",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--toplinker",
        help="use switch to binary with resolved event symbols",
        required=False,
        action="store_true",
    )
    # parser.add_argument("--debug_messages", help="should be ON or OFF", required=False)
    args = parser.parse_args()

    # link_top_bin=args.toplinker
    link_top_bin = True
    do_print = args.debug_messages
    # if args.debug_messages == "ON":
    #    do_print = True
    # elif args.debug_messages == "OFF":
    #    do_print = False
    directory, filename = extract_directory_and_filename(args.efa)
    func_name = filename.replace(".py", "")
    path = os.path.abspath(os.getcwd())
    outdir = args.outpath
    outfile = outdir + "/" + func_name + ".bin"
    text_symbol_table_file = None
    if args.text_symbol_table:
        text_symbol_table_file = outdir + "/" + func_name + ".symbol_table"
    print(
        f"func_name: {func_name}, directory: {directory} outdir:{outdir}"
    ) if do_print else None
    print(outfile) if do_print else None
    sys.path.append(f"{directory}")
    module = import_module_from_file(func_name)
    if hasattr(module, func_name):
        func = getattr(module, func_name)
        efa = func()
    elif hasattr(module, "main"):
        func = getattr(module, "main")
        efa = func()
    else:
        print(
            f"Function 'main' or '{func_name}' not found in module {func_name} ({func_name}.py file)"
        )
        sys.exit()
    assemble_program(efa, outfile, do_print, link_top_bin, text_symbol_table_file)
