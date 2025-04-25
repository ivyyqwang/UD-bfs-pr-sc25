
import os, sys
import importlib.util
import argparse
sys.path.append(f"{os.getcwd()}/efas/")
from efas import *
from pathlib import Path
from EFA_v2 import *
from UpDown_Assembler import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--efa_file", help="Input EFA to convert", required=True)
    parser.add_argument("--efa_func", help="Input EFA to convert", required=True)
    args = parser.parse_args()
    directory = os.path.abspath(os.getcwd())
    file_path = f"{directory}/{args.efa_file}.py"
    # Load the module from the specified file
    spec = importlib.util.spec_from_file_location(args.efa_file, file_path)
    my_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(my_module)
    # Get the function by name from the module
    function = getattr(my_module, args.efa_func)

    efa = function()

    outfile = directory + "/" +args.efa_func+ ".bin"
    #print(f"outfile: {outfile}")

    assemble_program(efa, outfile)
