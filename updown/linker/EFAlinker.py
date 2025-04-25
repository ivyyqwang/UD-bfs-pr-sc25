#! /usr/bin/env python
## EFA Linker
## This represents the linker of multiple Linkable Modules into a single Linkable Module.
## Remember that the EFAprogram is a linkable module with an interface that is compatible
## with the EFA emulator.

from linker.LinkableModule import LinkableModule
from linker.EFAsections.StaticDataSection import staticDataType

from typing import List, Tuple
import argparse

from common.debug import *
import common.debug as debug
from common.pythonLoader import pythonLoader
from common.helper import *
import re
import pathlib


def interpretAddress(address: str) -> dict:
    """Interpret an address string and return the type and the address

    Args:
        address (str): Address string

    Returns:
        Tuple[staticDataType, int]: Type and address
    """
    res = {
        "lane_private": 0x0,
        "updown_private": 0x0,
        "dram_shared": 0x0,
    }

    def getIntNum(addr):
        isNum, num = isNumericLiteral(addr)
        if isNum and not isinstance(num, int):
            errorMsg(f"Numeric value of address {addr} [{num}] is not a number")
        return isNum, num

    for addr in address.split(","):
        isNum, num = getIntNum(addr)

        if isNum:
            res["lane_private"] = num
        elif addr.startswith("lane_private"):
            isNum, num = getIntNum(addr.split(":")[1])
            res["lane_private"] = num
        elif addr.startswith("updown_private"):
            isNum, num = getIntNum(addr.split(":")[1])
            res["updown_private"] = num
        elif addr.startswith("dram_shared"):
            isNum, num = getIntNum(addr.split(":")[1])
            res["dram_shared"] = num
        else:
            errorMsg(f"Unknown address type {addr} in {address}")

    return res


class EFAlinker:
    def __init__(self, outputName: str, base_address: int = 0):
        self._linkableModules: List[LinkableModule] = []
        self._resultLinkableModule: LinkableModule = LinkableModule(outputName)
        self._base_address = base_address
        self._outputName = outputName

    def getLinkableModules(self) -> List[LinkableModule]:
        """Get the list of linkable modules

        Returns:
            List[LinkableModule]: List of linkable modules
        """
        return self._linkableModules

    def link(self, must_resolve = True) -> LinkableModule:
        """Link all the linkable modules into a single linkable module

        This is the function that performs the final
        symbol resolution. It is still possible to get
        unresolved symbols here, if there are symbols that are
        not resolved after all the linkable modules have been
        linked.

        Returns:
            LinkableModule: The resulting linkable module
        """

        for lm in self._linkableModules:
            debugMsg(5, f"Linking {lm.name}")
            self._resultLinkableModule.addLinkableModule(lm)

        debugMsg(5, f"Resolving symbols")
        self._resultLinkableModule.resolveSymbols(True, must_resolve)

        ## Create a unified list of symbols by combining all the symbols
        ## from all the linkable modules

        ## execute the symbol solver for all the unresolved symbols
        return self._resultLinkableModule

    def loadConstants(self, filepaths: List[str], additionalPaths: List[str] = []) -> None:
        """ Load the constants from all the linkable modules
        
        This function searches for symbols that are used in the libraries, but
        but not defined here. Instead, those symbols are defined in the program.
        Since, the values of those symbols are used to define classes from templates,
        this method needs to be executed, before the linker extracts other symbols.
        In the program, this method searches for #define and inserts those as
        variables in the respected libraries.

        To target library use `#define libraryName.VARIABLE_NAME = VALUE`

        """

        constants = {}
        constExp = re.compile(r'^#constexp ([^\s]+)\s*=\s*(\d)+', re.MULTILINE)
        for file in filepaths:
            if not os.path.exists(file):
                errorMsg(f"File {file} does not exist")
            content = pathlib.Path(file).read_text()
            findConstants = re.findall(constExp, content)
            for constant in findConstants:
                if constant[0] in constants:
                    errorMsg(f"Constant {constant[0]} already defined!")
                constants[constant[0]] = constant[1]
            
        #print(constants)
        #print(additionalPaths)
        return constants


    def loadSymbols(self) -> list:
        """Load the symbols from all the linkable modules

        This function checks for all the classes that have been
        loaded as part of the input files, and extracts the
        different EFA functions, executes them such that the
        linkableModule gets all the symbols (defined and undefined)

        Since all the symbols are loaded into a single final
        Linkable module, there is some partial symbol resolution
        in this step.

        Returns:
            list: List of linkable modules that have been loaded
        """
        classes = LinkableModule.getEFAclasses()

        for classObject in classes:
            linkableModule = classObject(classObject.__name__)
            programs = classObject.getEFAPrograms()
            for program in programs:
                debugMsg(5, f"Executing {program} from {linkableModule.name}")
                method = getattr(linkableModule, program)
                method()
            ## Resolve all the symbols
            linkableModule.resolveSymbols()
            linkableModule.cleanSymbols()
            self.addLinkableModule(linkableModule)

        return self._linkableModules

    def addLinkableModule(self, linkableModule: LinkableModule) -> None:
        """Add a linkable module to the list of linkable modules

        Arguments:
            linkableModule {LinkableModule} -- The linkable module to be added

        Returns:
            None
        """
        self._linkableModules.append(linkableModule)

    def loadFiles(
        self, filepaths: List[str], additionalPaths: List[str]
    ) -> List[LinkableModule]:
        """Load the files into the linker

        For each file path, we add the path to the import path
        of this python program, we then use that to access the module
        defined by the python file. We then extract the EFA functions
        from the modules using loadSymbols

        Arguments:
            filepaths {List[str]} -- List of filepaths to be loaded

        Returns:
            List[LinkableModule] -- List of linkable modules that have been loaded
        """
        constants = self.loadConstants(filepaths, additionalPaths)
        pythonLoader(filepaths, additionalPaths, constants)
        self.loadSymbols()

        return self._linkableModules

    def dumpPython(
        self, base_path: str = "./", base_name: str = "a.out", finalize: bool = False
    ) -> None:
        """Dump the python code for the EFA program

        This function dumps the python code for the EFA program
        that is a compatible Linkable Module. This is not an executable
        python code. Use the Loader to obtain the executable python code.
        """
        if finalize:
            self._resultLinkableModule.allocateStaticMemory(self._base_address)
            self._resultLinkableModule.assignIDs()
        self._resultLinkableModule.dumpPython(base_path, base_name, finalize)

    def dumpHeader(self, base_path: str = "./", base_name: str = "a.out") -> None:
        """Dump the header file for the EFA program

        This function dumps the header file for the EFA program
        that is a compatible Linkable Module. This is not an executable
        python code. Use the Loader to obtain the executable python code.
        """
        self._resultLinkableModule.dumpHeader(base_path, base_name)

    def dumpRaw(self):
        ## Dump the result linkable module to a raw file
        self._resultLinkableModule.dump()


def nameCleanUp(full_path: str) -> Tuple[str, str, str]:
    """Given a file name, separate path and base name.
    Return a version of the basename that is compatible with
    class names in python. This is, remove all the special characters"""
    base_path, base_name = os.path.split(full_path)
    if base_path == "":
        base_path = "./"
    base_name = os.path.splitext(base_name)[0]
    special_characters = ["-", ".", ":", " ", ",", ";"]
    clean_name = base_name
    for c in special_characters:
        clean_name = clean_name.replace(c, "_")
    return base_path, base_name, clean_name


def linkerMain():
    ## Define program arguments: List of input files. If output should be a python file
    parser = argparse.ArgumentParser(description="EFA Linker")

    parser.add_argument(
        "inputFiles",
        metavar="inputFiles",
        type=str,
        nargs="+",
        help="List of input files to link",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="output",
        type=str,
        nargs=1,
        help="Output file name",
        default=["output"],
    )

    parser.add_argument(
        "-f",
        "--format",
        metavar="format",
        type=str,
        choices=["raw", "linkable-module", "efa"],
        nargs=1,
        help="Output format: raw, linkable-module, efa",
        default=["efa"],
    )

    parser.add_argument(
        "-d",
        "--debug-level",
        dest="deb_level",
        action="store",
        help="Set debug level",
        default=0,
    )

    parser.add_argument(
        "-L",
        "--library-path",
        dest="lib_path",
        type=str,
        action="append",
        help="Add a path where other libraries/python modules are to be searched for",
        default=[],
    )

    parser.add_argument(
        "--no-header",
        dest="no_header",
        action="store_true",
        help="Do not generate the header file",
        default=False,
    )

    parser.add_argument(
        "--base-address",
        dest="base_address",
        action="store",
        type=str,
        help="Base address for static data. Format is <address> or [type]:<address>, "
        "[[type]:<address> ...]]]. type can be lane_private, updown_private, or dram_shared",
        default="0x0",
    )

    args = parser.parse_args()

    if args.deb_level:
        debug.DEBUG_LEVEL = int(args.deb_level)

    debugMsg(5, f"Running linker with arguments: {args}")

    base_addr = interpretAddress(args.base_address)

    base_path, base_name, clean_name = nameCleanUp(args.output[0])
    
    format = [i.lower() for i in args.format]

    linker = EFAlinker(clean_name, base_addr)
    
    debugMsg(5, f"Loading Files {args.inputFiles}")
    linker.loadFiles(args.inputFiles, args.lib_path)
    if debug.DEBUG_LEVEL >= 8:
        for lm in linker.getLinkableModules():
            lm.dump()
    debugMsg(8, f"Linking")
    must_resolve = "efa" in format
    linker.link(must_resolve)
    if debug.DEBUG_LEVEL >= 8:
        linker._resultLinkableModule.dump()
    if "linkable-module" in format:
        debugMsg(8, f"Dumping Linkable Module")
        linker.dumpPython(base_path, base_name)
    elif "efa" in format:
        debugMsg(8, f"Dumping EFA")
        linker.dumpPython(base_path, base_name, finalize=True)
        if not args.no_header:
            linker.dumpHeader(base_path, base_name)
    elif "raw" in format:
        debugMsg(8, f"Dumping Raw")
        linker.dumpRaw()


if __name__ == "__main__":
    linkerMain()
