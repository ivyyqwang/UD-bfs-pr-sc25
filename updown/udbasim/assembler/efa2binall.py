import os, sys
import importlib
import argparse

sys.path.append(f"{os.getcwd()}/efas/")
# import efas
from efas import *
from efa2bin import *
from pathlib import Path
from EFA_v2 import *
from UpDown_Assembler import *


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


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
    parser.add_argument("--efa", help="Input EFA to convert", required=False)
    parser.add_argument("--outpath", help="path of the outputfile", required=False)
    parser.add_argument(
        "--debug-messages",
        help="use switch to debug assembler",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--toplinker",
        help="use switch to binary with resolved event symbols",
        required=False,
        action="store_true",
        default=True,
    )
    args = parser.parse_args()
    print("Are we here?")
    skipfile = open("skipfile.txt", "r")
    skiplist = skipfile.read().splitlines()
    print(
        bcolors.WARNING
        + "Will skip these tests from assembling"
        + " ".join(str(x) for x in skiplist)
    )
    print(bcolors.RESET)
    do_print = args.debug_messages
    # link_top_bin=args.toplinker
    link_top_bin = True
    assemble_failed = []
    module_not_found = []
    if not args.efa:
        print(bcolors.WARNING + "No EFA specified will assemble ALL programs now")
        for path in Path("../testprogs/efas/").rglob("*.py"):
            path = path.resolve()
            print(bcolors.OKBLUE + f"Assembling {path}") if do_print else None
            print(bcolors.RESET) if do_print else None
            directory, filename = extract_directory_and_filename(path)
            if (
                filename == "__init__.py"
                or filename == "test_helpers.py"
                or filename in skiplist
            ):
                continue
            func_name = filename.replace(".py", "")
            cwdpath = os.path.abspath(os.getcwd())
            outdir = "../testprogs/binaries"
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            outfile = outdir + "/" + func_name + ".bin"
            sys.path.append(f"{directory}")
            globalprog()
            try:
                module = import_module_from_file(func_name)
            except:
                module_not_found.append(path)
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                efa = func()
            elif hasattr(module, "main"):
                func = getattr(module, "main")
                efa = func()
            else:
                print(
                    bcolors.FAIL
                    + f"Function 'main' or '{func_name}' not found in module {func_name} ({func_name}.py file)"
                )
                print(bcolors.RESET)
                sys.exit()
            try:
                assemble_program(efa, outfile, do_print, link_top_bin)
            except:
                assemble_failed.append(path)

        print(
            bcolors.FAIL
            + "Following programs were not assembled due to issues, pleae check"
        )
        for efa in assemble_failed:
            print(efa)
        print(bcolors.RESET)

        print(
            bcolors.FAIL
            + "Following programs were not assembled since module names are different from efa"
        )
        for func in module_not_found:
            print(func)
        print(bcolors.RESET)
    else:
        directory, filename = extract_directory_and_filename(args.efa)
        func_name = filename.replace(".py", "")
        path = os.path.abspath(os.getcwd())
        if not args.outpath:
            print(bcolors.FAIL + "Outpath to be specified for EFA")
            sys.exit(1)
        outdir = args.outpath
        outfile = outdir + "/" + func_name + ".bin"
        print(
            f"func_name: {func_name}, directory: {directory} outdir:{outdir}"
        ) if do_print else None
        print(outfile) if do_print else None
        sys.path.append(f"{directory}")
        globalprog()
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
        assemble_program(efa, outfile, do_print, link_top_bin)
