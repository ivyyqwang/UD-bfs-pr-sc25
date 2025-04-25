from abc import ABC, abstractmethod
from enum import Enum

from linker.Symbol.Symbol import Symbol, SymbolType
from linker.EFAsections.Section import Section
from linker.EFAsections.StaticDataSection import staticDataType
from typing import Union

from common.debug import *

from collections import OrderedDict
from copy import copy

import re

INDENT = " " * 4

NULL_STATE_NAME = "init_null_state"


class LinkableModule(ABC):
    efa_methods = []

    @classmethod
    def getEFAclasses(cls):
        return cls.efa_methods

    @classmethod
    def registerEFAclass(cls, efa_class):
        cls.efa_methods.append(efa_class)

    def assignIDs(self):
        """Iterate over all the symbols and assign unique IDs"""
        stateID = 0
        transitionID = 0
        # sharedBlockSymbolID = 0

        for symbol in self._symbols.values():
            if symbol.symbolType == SymbolType.STATE:
                debugMsg(15, f"Assigning ID {stateID} to state {symbol.name}")
                symbol.setID(stateID)
                stateID += 1
            elif symbol.symbolType == SymbolType.TRANSITION:
                debugMsg(15, f"Assigning ID {transitionID} to transition {symbol.name}")
                ## Only event transitions need an ID defined by the linker
                ## Non event transitions must respect their original labels
                if symbol.section.isEventTransition:
                    symbol.setID(transitionID)
                    transitionID += 1
                else:
                    symbol.setID(symbol.section.labelName)
            elif symbol.symbolType == SymbolType.SHARED_BLOCK:
                symbol.setID(symbol.name)
            elif symbol.symbolType == SymbolType.STATIC_DATA:
                ## This should have been done with allocateStaticMemory
                pass
            elif symbol.symbolType == SymbolType.BRANCH_LABEL:
                ## We do not modify branch labels
                symbol.setID(symbol.name)

    def setNullState(self, sym: Symbol):
        """
        Set the initial null state to the module.
        All event transitions start from a Null state.
        """
        debugMsg(15, f"Setting null state to {sym.name}")
        if self._null_state is None:
            self._null_state = []
        self._null_state.append(sym)
        sym.setPrivate(False)
        sym.setIsNullState(True)
        self._symbols[NULL_STATE_NAME] = sym
        old_name = sym.name
        if old_name != NULL_STATE_NAME:
            sym.setName(NULL_STATE_NAME)
            del self._symbols[old_name]

    @property
    def nullState(self) -> Union[Symbol, None]:
        """Get the null state of the module.

        Returns:
            Symbol: Null state of the module.
        """

        return self._null_state[-1] if self._null_state is not None else None

    def allocateStaticMemory(self, baseAddr: dict):
        """Iterate over all the symbols and assign unique IDs"""
        lane_private_addr = baseAddr["lane_private"]
        updown_private_addr = baseAddr["updown_private"]
        dram_shared_addr = baseAddr["dram_shared"]

        for symbol in self._symbols.values():
            if symbol.symbolType == SymbolType.STATIC_DATA:
                ## IDs for static data symbols are the addresses where they are allocated
                if symbol.section.type == staticDataType.LANE_PRIVATE:
                    debugMsg(
                        4,
                        f"Allocating {symbol.symbolType.name} {symbol.name} {symbol.section.type.name} at {lane_private_addr}",
                    )
                    symbol.setID(lane_private_addr)
                    lane_private_addr += symbol.size
                elif symbol.section.type == staticDataType.UPDOWN_PRIVATE:
                    debugMsg(
                        4,
                        f"Allocating {symbol.symbolType.name} {symbol.name} {symbol.section.type.name} at {updown_private_addr}",
                    )
                    symbol.setID(updown_private_addr)
                    updown_private_addr += symbol.size
                elif symbol.section.type == staticDataType.DRAM_SHARED:
                    debugMsg(
                        4,
                        f"Allocating {symbol.symbolType.name} {symbol.name} {symbol.section.type.name} at {dram_shared_addr}",
                    )
                    symbol.setID(dram_shared_addr)
                    dram_shared_addr += symbol.size
                else:
                    errorMsg(f"Unknown static data type {symbol.type}")

    def __init__(self, name: Union[str, None] = None):
        """Section that represents a partial or complete UpDown program.

        Args:
            name (str, optional): Name of the module. Defaults to None.
        """
        self._name = name

        debugMsg(1, f"Creating module {self._name}")

        ## Create the table of symbols. A dictionary of symbol -> Section
        self._symbols = OrderedDict()
        self._null_state = None

    def _checkEventType(self, type: str) -> bool:
        return type in ["eventCarry"]

    def _collapseNullStates(self):
        """If multiple null states are defined, they are pushed to a
        list. We need to call the combineSection on all of them and collapse it
        into the last null state of the list"""
        if self._null_state is None:
            errorMsg("Null state not set")
        if self._null_state is not None and len(self._null_state) > 1:
            debugMsg(15, f"Collapsing null states {self._null_state}")
            for nullState in self._null_state[:-1]:
                self.nullState.section.combineSection(nullState.section)

    def addSymbol(self, symbol: Symbol) -> None:
        """Add a symbol to the list of symbols defined in the module.

        Args:
            symbol (Symbol): Symbol to be added.
        """
        self._symbols[symbol.name] = symbol
        debugMsg(
            1,
            f"Adding symbol {symbol.symbolType.name} {symbol.name} to module {self._name}",
        )

    def removeSymbol(self, symbol: Symbol) -> None:
        """ Remove the symbol from the list of symbols """

        del self._symbols[symbol.name]

    ###########################
    ### Getters and setters ###
    ###########################
    @property
    def symbols(self) -> OrderedDict:
        """Get the list of symbols defined in the module.

        Returns:
            list: List of symbols defined in the module.
        """
        return self._symbols

    def getSymbol(self, name: str) -> Union[Symbol, None]:
        """Get the symbol with the given name.

        Args:
            name (str): Name of the symbol to get.

        Returns:
            Symbol: Symbol with the given name.
        """
        if name in self._symbols:
            return self._symbols[name]
        return None

    def getStateSymbol(self, name: str) -> Union[Symbol, None]:
        """Get the state symbol with the given name.

        Args:
            name (str): Name of the state symbol to get.

        Returns:
            Symbol: State symbol with the given name.
        """
        sym = self.getSymbol(name)
        return sym if sym and sym.isState else None

    def getTransitionSymbol(self, name: str) -> Union[Symbol, None]:
        """Get the transition symbol with the given name.

        Args:
            name (str): Name of the transition symbol to get.

        Returns:
            Symbol: Transition symbol with the given name.
        """
        sym = self.getSymbol(name)
        return sym if sym and sym.isTransition else None

    def getSharedBlockSymbol(self, name: str) -> Union[Symbol, None]:
        """Get the shared block symbol with the given name.

        Args:
            name (str): Name of the shared block symbol to get.

        Returns:
            Symbol: Shared block symbol with the given name.
        """
        sym = self.getSymbol(name)
        return sym if sym and sym.isSharedBlock else None

    def getStaticDataSymbol(self, name: str) -> Union[Symbol, None]:
        """Get the static data symbol with the given name.

        Args:
            name (str): Name of the static data symbol to get.

        Returns:
            Symbol: Static data symbol with the given name.
        """
        sym = self.getSymbol(name)
        return sym if sym and sym.isStaticData else None

    def getStateSection(self, name: str) -> Union[Section, None]:
        """Get the state section with the given name.

        Args:
            name (str): Name of the state section to get.

        Returns:
            Section: State section with the given name.
        """
        sym = self.getStateSymbol(name)
        return sym.section if sym else None

    def getTransitionSection(self, name: str) -> Union[Section, None]:
        """Get the transition section with the given name.

        Args:
            name (str): Name of the transition section to get.

        Returns:
            Section: Transition section with the given name.
        """
        sym = self.getTransitionSymbol(name)
        return sym.section if sym else None

    def getSharedBlockSection(self, name: str) -> Union[Section, None]:
        """Get the shared block section with the given name.

        Args:
            name (str): Name of the shared block section to get.

        Returns:
            Section: Shared block section with the given name.
        """
        sym = self.getSharedBlockSymbol(name)
        return sym.section if sym else None

    def getStaticDataSection(self, name: str) -> Union[Section, None]:
        """Get the static data section with the given name.

        Args:
            name (str): Name of the static data section to get.

        Returns:
            Section: Static data section with the given name.
        """
        sym = self.getStaticDataSymbol(name)
        return sym.section if sym else None

    def addLinkableModule(self, module: "LinkableModule") -> None:
        """Add the symbols of another module to this module.
            Creates a single list of symbols with references to all the other linkable modules.
        Args:
            module (LinkableModule): Module whose symbols are to be added.
        """

        debugMsg(1, f"Adding module {module.name} to module {self.name}")

        if self.nullState is None:
            if module.nullState is not None:
                self.setNullState(module.nullState)
            else:
                errorMsg(
                    "Trying to add a module without a defined null state (initial state)"
                )
        else:
            if module.nullState is not None and module.nullState.section is not None:
                self.nullState.section.combineSection(module.nullState.section)  # type: ignore
            else:
                errorMsg(
                    "Trying to add a module without a defined null state (initial state)"
                )

        newSymbols = module.symbols
        for sym in newSymbols.values():
            if sym == module.nullState:
                continue
            debugMsg(
                10,
                f"Attempting to add symbol {sym.symbolType.name} {sym.name} from {module.name} to module {self.name}",
            )
            ## Perform name mangling to avoid name collision on private symbols.
            ## The only externable symbols are transitions of type event,
            ## shared blocks and static data
            name = sym.name
            if sym.isPrivate and f"{module.name}_" not in name:
                ## Private symbols must be defined
                assert (
                    sym.isDefined
                ), f"Undefined private symbol {sym.name} in module {module.name}"
                ## Name mangling for privatization of symbols
                name = f"{module.name}_{name}"
                debugMsg(
                    10,
                    f"Performing name mangling on symbol {sym.name} to {name} in module {self.name}",
                )
                sym.setName(name)

            if sym.isDefined:
                debugMsg(10, f"Adding defined symbol {sym.name}")
                ## We omit undefined symbols from the list of symbols when adding new symbols
                ## We expect the defined version to be added in other linkable modules.
                ## At the end, any undefined symbol should be catched by the linker
                self._symbols[name] = sym
                sym.section.setLinkableModule(self)

    def cleanSymbols(self) -> None:
        """Remove replace all the illegal characters with an _.
        Illegal characters are those not supported by python variable names.
        """
        for sym in self.symbols.values():
            newName = re.sub(r"\W", "_", sym.name)
            debugMsg(10, f"Cleaning symbol {sym.name} to {newName}")
            sym.setName(newName)

    @property
    def undefinedSymbols(self) -> list:
        """Get the list of undefined symbols in the module.

        Returns:
            list: List of undefined symbols in the module.
        """
        return [sym[1] for sym in self.symbols.items() if not sym[1].isDefined]

    @property
    def stateSymbols(self) -> list:
        """Get the list of states defined in the module.

        Returns:
            list: List of states defined in the module.
        """
        return [symbol for _, symbol in self.symbols.items() if symbol.isState]

    @property
    def transitionSymbols(self) -> list:
        """Get the list of transitions defined in the module.

        Returns:
            list: List of transitions defined in the module.
        """
        return [symbol for _, symbol in self.symbols.items() if symbol.isTransition]

    @property
    def eventTransitionSymbols(self) -> list:
        """Get the list of event transitions defined in the module.

        Returns:
            list: List of event transitions defined in the module.
        """
        return [
            symbol
            for _, symbol in self.symbols.items()
            if symbol.isTransition and symbol.section.isEventTransition
        ]

    @property
    def sharedBlockSymbols(self) -> list:
        """Get the list of shared blocks defined in the module.

        Returns:
            list: List of shared blocks defined in the module.
        """
        return [symbol for _, symbol in self.symbols.items() if symbol.isSharedBlock]

    @property
    def staticDataSymbols(self) -> list:
        """Get the list of static data defined in the module.

        Returns:
            list: List of static data defined in the module.
        """
        return [symbol for _, symbol in self.symbols.items() if symbol.isStaticData]

    def symbolExists(self, symbolName: str) -> bool:
        """Check if a symbol exists in the module.

        Args:
            symbolName (str): Name of the symbol.

        Returns:
            bool: True if the symbol exists, False otherwise.
        """
        return self.getSymbol(symbolName) is not None

    def stateSymbolExists(self, stateName: str) -> bool:
        """Check if a state exists in the module.

        Args:
            stateName (str): Name of the state.

        Returns:
            bool: True if the state exists, False otherwise.
        """
        return self.getStateSymbol(stateName) is not None

    def transitionSymbolExists(self, transitionName: str) -> bool:
        """Check if a transition exists in the module.

        Args:
            transitionName (str): Name of the transition.

        Returns:
            bool: True if the transition exists, False otherwise.
        """
        return self.getTransitionSymbol(transitionName) is not None

    def shareBlockSymbolExists(self, blockName: str) -> bool:
        """Check if a shared block exists in the module.

        Args:
            blockName (str): Name of the shared block.

        Returns:
            bool: True if the shared block exists, False otherwise.
        """
        return self.getSharedBlockSymbol(blockName) is not None

    def staticDataSymbolExists(self, dataName: str) -> bool:
        """Check if a static data exists in the module.

        Args:
            dataName (str): Name of the static data.

        Returns:
            bool: True if the static data exists, False otherwise.
        """
        return self.getStaticDataSymbol(dataName) is not None

    def stateSectionExists(self, stateName: str) -> bool:
        """Check if a state exists in the EFA program.

        Args:
            stateName (str): Name of the state.

        Returns:
            bool: True if the state exists, False otherwise.
        """
        return self.getStateSection(stateName) is not None

    def transitionSectionExists(self, transitionName: str) -> bool:
        """Check if a transition exists in the module.

        Args:
            transitionName (str): Name of the transition.

        Returns:
            bool: True if the transition exists, False otherwise.
        """
        return self.getTransitionSection(transitionName) is not None

    def shareBlockSectionExists(self, blockName: str) -> bool:
        """Check if a shared block exists in the module.

        Args:
            blockName (str): Name of the shared block.

        Returns:
            bool: True if the shared block exists, False otherwise.
        """
        return self.getSharedBlockSection(blockName) is not None

    def staticDataSectionExists(self, dataName: str) -> bool:
        """Check if a static data exists in the module.

        Args:
            dataName (str): Name of the static data.

        Returns:
            bool: True if the static data exists, False otherwise.
        """
        return self.getStaticDataSection(dataName) is not None

    def setName(self, name: str) -> None:
        """Set the name of the module.

        Args:
            name (str): New name of the module.
        """
        self._name = name

    def resolveSymbols(self, unresolved: bool = False, must_resolve=True) -> None:
        """Resolve the symbols in the module.

            Iterate over all the actions in the transitions and
            basic blocks. Search for symbols in the operands
            and see if the symbol exists. If not, create a new
            symbol that is undefined, and add it.
        Args:
            unresolved (bool, optional): If True, only resolve unresolved symbols.
                Defaults to False.
        """

        ## TODO: Right now it is not possible to tell what kind of symbol
        ## it is. This means that if there are multiple symbols with the same
        ## name, this will create a conflict that will result in undefined
        ## behavior. This needs to be fixed by using information about the instructions
        ## and what type of symbol they expect. I tried to do this, but the
        ## logic for the instruction is not complete, and there are still
        ## design choices in the ISA to be made

        self._collapseNullStates()

        originalSymbols = copy(self.symbols)
        for _, symb in originalSymbols.items():
            if (
                symb.symbolType == SymbolType.TRANSITION
                or symb.symbolType == SymbolType.SHARED_BLOCK
            ):
                debugMsg(
                    15, f"Resolving symbols in {symb.symbolType.name} - {symb.name}"
                )
                symb.section.assignSymbols(unresolved, must_resolve)

    @property
    def name(self) -> str:
        """Get the name of the module.

        Returns:
            str: Name of the module.
        """
        return self._name

    def __indent(self, str, indent=4):
        return "\n".join([" " * indent + line for line in str.split("\n")])

    def __print_indent(self, str, indent=0):
        print(self.__indent(str, indent))

    def dump(self):
        """Dump the module to stdout."""

        def printSections(symbols):
            for symbol in symbols:
                self.__print_indent(f"{symbol.section}", 4)

        self.__print_indent("Module: %s" % self.name, 0)
        self.__print_indent("State Symbols:", 2)
        printSections(self.stateSymbols)
        self.__print_indent("Transition Symbols:", 2)
        printSections(self.transitionSymbols)
        self.__print_indent("Shared Block Symbols:", 2)
        printSections(self.sharedBlockSymbols)
        self.__print_indent("  Static Data Symbols:")
        printSections(self.staticDataSymbols)

    def dumpPython(
        self, base_path: str = "./", filename: str = "a.out", finalize: bool = False
    ) -> None:
        """Dump the python code for the EFA program

        This function dumps the python code for the EFA program
        that is a compatible Linkable Module. This is not an executable
        python code. Use the Loader to obtain the executable python code.
        """



        if finalize:
            template = (
                "from EFA_v2 import EFA, State, Transition\n\n"
                "def efaProgram_{modname}(efa):\n\n"
                "{efaProgram}\n"
            )
        else:
            template = (
                "from linker.EFAProgram import efaProgram\n"
                "from linker.EFAsections.StaticDataSection import staticDataType\n\n"
                "@efaProgram\n"
                "def efaProgram_{modname}(efa):\n\n"
                "{efaProgram}\n"
            )

        pythonEFA = ""
        for state in self.stateSymbols:
            if finalize:
                pythonEFA += f"{INDENT}## {state.name} with ID {state.id}\n"
                pythonEFA += (
                    f"{INDENT}{state.name}_{state.id} = State()\n"
                    f"{INDENT}efa.add_state({state.name}_{state.id})\n"
                )
                if len(state.section.alphabet) > 0:
                    pythonEFA += f"{INDENT}{state.name}_{state.id}.alphabet = {state.section.alphabet}\n"
                if state.isNullState:
                    pythonEFA += (
                        f"{INDENT}efa.add_initId({state.name}_{state.id}.state_id)\n"
                    )
            else:
                pythonEFA += (
                    f"{INDENT}## {state.name}\n"
                    f'{INDENT}{state.name} = efa.State("{state.name}")\n'
                    f"{INDENT}efa.add_state({state.name})\n"
                )
                if len(state.section.alphabet) > 0:
                    pythonEFA += (
                        f"{INDENT}{state.name}.alphabet = {state.section.alphabet}\n"
                    )
                if state.isNullState:
                    pythonEFA += f"{INDENT}efa.add_initId({state.name}.state_id)\n"
        pythonEFA += "\n"

        for statData in self.staticDataSymbols:
            if not finalize:
                statDataSec = statData.section
                pythonEFA += (
                    f"{INDENT}## {statDataSec.name} of size {statDataSec.size}\n"
                    f"{INDENT}efa.addStaticData('{statDataSec.name}', {statDataSec.size}, {statDataSec.type})\n"
                )

        pythonEFA += f"{INDENT}## Add event ids and names:\n"
        for tran in self.transitionSymbols:
            if finalize and tran.section.type == 'eventCarry':
                pythonEFA += f"{INDENT}efa.add_name({tran.id}, '{tran.name}')\n"
        pythonEFA += "\n"
        
        for tran in self.transitionSymbols:
            if finalize:
                pythonEFA += f"{INDENT}## {tran.name} with ID {tran.id}\n"
            else:
                pythonEFA += f"{INDENT}## {tran.name}\n"
            tranSect = tran.section
            fromState = tranSect.origin.symbol
            toState = tranSect.destination.symbol
            if finalize and not tranSect.isEventTransition: 
                '''
                For non-event transitions, if the ID was not an integer, it represents a transition
                from a state with def/maj/flagdef/flagmaj property. Assign it a string for assembler to understand.
                '''
                if isinstance(tran.id, int) or tran.id.isdigit():
                    pythonEFA += (
                        f"{INDENT}{tran.name}_{tran.id} = "
                        f'{fromState.name}_{fromState.id}.writeTransition("{tranSect.type}", '
                        f"{fromState.name}_{fromState.id}, "
                        f"{toState.name}_{toState.id}, "
                        f"{tran.id})\n"
                    )
                else:
                    pythonEFA += (
                        f"{INDENT}{tran.name}_{tran.id} = "
                        f'{fromState.name}_{fromState.id}.writeTransition("{tranSect.type}", '
                        f"{fromState.name}_{fromState.id}, "
                        f"{toState.name}_{toState.id}, "
                        f"'{tran.id}')\n"
                    )
            elif finalize:
                pythonEFA += (
                    f"{INDENT}{tran.name}_{tran.id} = "
                    f'{fromState.name}_{fromState.id}.writeTransition("{tranSect.type}", '
                    f"{fromState.name}_{fromState.id}, "
                    f"{toState.name}_{toState.id}, "
                    f"{tran.id})\n"
                )
            else:
                pythonEFA += (
                    f"{INDENT}{tran.name} = "
                    f'{fromState.name}.writeTransition("{tranSect.type}", '
                    f"{fromState.name}, "
                    f"{toState.name}, "
                    f'"{tranSect.label}")\n'
                )
            for action in tranSect.actions:
                if finalize:
                    actStr = action.finalize()
                    pythonEFA += (
                        f'{INDENT}{tran.name}_{tran.id}.writeAction("{actStr}")\n'
                    )
                else:
                    pythonEFA += f'{INDENT}{tran.name}.writeAction("{action.action}")\n'
            pythonEFA += "\n"

        for block in self.sharedBlockSymbols:
            blockSect = block.section
            pythonEFA += f"{INDENT}## {block.name}\n"
            for action in blockSect.actions:
                if finalize:
                    actStr = action.finalize()
                    pythonEFA += (
                        f'{INDENT}efa.appendBlockAction("{block.name}", "{actStr}")\n'
                    )
                else:
                    pythonEFA += f'{INDENT}efa.appendBlockAction("{block.name}", "{action.action}")\n'

            for linkedState in blockSect.linkedStates:
                if finalize:
                    pythonEFA += f'{INDENT}efa.linkBlocktoState("{block.name}", {linkedState.symbol.name}_{linkedState.symbol.id})\n'
                else:
                    pythonEFA += f'{INDENT}efa.linkBlocktoState("{block.name}", {linkedState.symbol.name})\n'

        pythonEFA += "\n\n"
        if finalize:
            pythonEFA += f"def main():\n"
            pythonEFA += f"{INDENT}efa = EFA([])\n"
            pythonEFA += f"{INDENT}efa.code_level = 'machine'\n"
            pythonEFA += f"{INDENT}efaProgram_{self.name}(efa)\n"
            pythonEFA += f"{INDENT}return efa\n"

        with open(base_path + "/" + filename + ".py", "w") as f:
            f.write(
                template.format(
                    filename=filename,
                    modname=self.name,
                    INDENT=INDENT,
                    efaProgram=pythonEFA,
                ).strip()
            )

    def dumpHeader(self, base_path: str = "./", filename: str = "a") -> None:
        """Dump a C++ header file that contains the definitions of the
        event symbols such that they can be used in the UpDown runtime"""

        template = (
            "#ifndef __{modname}_H__\n"
            "#define __{modname}_H__\n\n"
            "namespace {modname} {{\n\n"
            f"{INDENT}typedef unsigned int EventSymbol;\n\n"
            "{eventSymbols}"
        )

        eventSymbols = ""

        for tran in self.eventTransitionSymbols:
            eventSymbols += f"{INDENT}constexpr EventSymbol {tran.name} = {tran.id};\n"

        eventSymbols += "\n} // namespace\n"
        eventSymbols += "\n#endif\n"

        with open(base_path + "/" + filename + ".hpp", "w") as f:
            f.write(
                template.format(
                    filename=filename,
                    modname=self.name,
                    INDENT=INDENT,
                    eventSymbols=eventSymbols,
                ).strip()
            )
