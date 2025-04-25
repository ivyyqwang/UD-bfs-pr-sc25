# UpDown Weave Compiler
This repository contains the compiler infrastructure for UDweave programs. UpDown is an architecture being proposed at the University of Chicago as part of the AGILE project.

Read the [Reference Manual](https://docs.google.com/document/d/1WYa5l5XEd5rVfUJWUtLs7thHzFKgV2eW0F-52sx1rUQ/edit#) for more information

## Project Organization
This project is organized as follows:

* Using PLY, there is a front end implementation that is in charge of generating an AST. The treelib Python library is used to help keep track of the tree, although we should consider removing this. The extra indirection (e.g. `.data.`) seems unnecessary.
* In the frontend folder. The files `lexer.py` and `parser.py` are the AST generation. The files in `tests_parser` are to test these two files, but they may contain code that is not syntactically correct (e.g. using variables that have not been previously defined)
* In the frontend folder. The file `ASTweave.py` is for code generation into WeaveIR. WeaveIR is an intermediate representation of UDweave programs that contains additional information about context (e.g. thread local and local variables, events, threads, and control flow graph information)
* The Weave folder contains infrastructure related files. The file `WeaveIR.py` contains the definition of the WeaveIR, including how to print the WeaveIR in human readable format.
* The backend folder is intended to contain different lowering possibilities. The `PythonGen` file contains lowering to Python representation of UpDown programs. 

## Current status
With this version it is possible to lower programs that contain a single basic block with no branches. Arithmetic operations are supported, as long as there is an equivalent ISA instruction. Things like integer division has not yet been implemented. 

## How to run
Make sure that you have ply and treelib in python. Using pip install.

List of current options 

| Flag                  | Description | 
| :---                  |    :----    |
| --input               | Input file to be compiled. If not provided, direct text can be input. It is not recommended to omit this. |
| -dp,  --debug-parser  | Activate Parsing debug information from PLY |
| -dl, --debug-lexer    | Activate Lexer debug information from PLY |
| -d, --debug-level     | Activate debug level messages from UDweave |
| --ast-dump            | Dump the AST |
| --weave-ir            | Dump the WeaveIR |

To run a parser front end example use 

```Bash
python3 UDweave.py --input tests_parser/operations.udw --ast-dump
```

To run the CodeGen example:

```Bash
python3 UDweave.py --input tests_codegen/event.udw --weave-ir
```


## Testing infrastructure

This project uses LLVM's lit and fileCheck testing infrastructures. A Makefile is provided to be able to run the tests. 

To run the tests, use the following command:

```Bash
make test
```

Note: Currently the use of this infrastructure is under development. A lot of the tests do not use this infrastructure yet. This is work in progress