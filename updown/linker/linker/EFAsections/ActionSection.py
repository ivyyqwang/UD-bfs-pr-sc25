from linker.EFAsections.Section import Section
from linker.Symbol.Symbol import Symbol, SymbolType

from common.helper import *
from common.debug import *

from typing import Union


class ActionSection(Section):
    """Container for actions inside a Program

    An action is an instruction that is executed when certain transitions are taken.

    This allows to keep track of symbols that have not been resolved yet and that will
    later on be resolved during linking

    If an action is not associated to a transition, it should be associated to a state

    """

    def __init__(
        self,
        action: str,
        linkableModule: "LinkableModule",
    ):
        """Create an Action

        Args:
            action (str): String containing the instruction
            transition (TransitionInfo): Transition parent of this action
        """
        super().__init__(linkableModule, "")
        self._action = action
        ## Symbols that are referenced in the action, including undefined symbols
        self._referenceSymbols = []
        self._parentSection = None
        self._opcode = getActionOpCode(action)
        ## TODO: Actions should be compared vs the real instruction based on the ISA
        # if self._opcode is not None:
        #     self._instruction = UpDownInstructions[self._opcode]
        # else:
        #     self._instruction = None

    @property
    def action(self) -> str:
        """Get the action

        Returns:
            str: _description_
        """
        return self._action

    @property
    def isUnresolved(self) -> bool:
        """Returns if any of the symbols in the action are unresolved

        Returns:
            bool: Unresolved flag
        """
        return not all([symbol.isDefined for symbol in self._referenceSymbols])

    @property
    def inTransition(self) -> bool:
        """Returns if the action is inside a transition

        Returns:
            bool: In transition flag
        """
        return self._parentSection is not None and isinstance(
            self._parentSection, "TransitionSection"
        )

    @property
    def inSharedBlock(self) -> bool:
        """Returns if the action is inside a shared block

        Returns:
            bool: In shared block flag
        """
        return self._parentSection is not None and isinstance(
            self._parentSection, "SharedBlockSection"
        )

    def getUnresolvedSymbols(self) -> list:
        """Get the unresolved symbols of the action

        Returns:
            list: List of unresolved symbols
        """
        return [symbol for symbol in self._referenceSymbols if not symbol.isDefined]

    def assignSymbols(self, unresolved: bool = False, must_resolve=True) -> None:
        """Assign the symbols of the action

        Iterate over all the actions, and get the possible symbols in
        string form, then use these to either pass the symbol to the Action
        already assigned, or create an unresolved symbol in the action.

        Args:
            unresolved (bool, optional): If the symbols are unresolved. Defaults to False.

        """
        debugMsg(
            15, f"Assigning symbols to action {self._action} with flag {unresolved}"
        )
        symbols_str = self._detectSymbols()
        if not unresolved:
            for symstr in symbols_str:
                symbol = self._linkableModule.getSymbol(symstr)
                if symbol is not None:
                    self.addReferenceSymbol(symbol)
                    debugMsg(
                        15,
                        f"Adding action {self._action} to already existing symbol {symstr} type {symbol.symbolType.name}",
                    )
                    symbol.addUsedIn(self)
                else:
                    ## TODO: This should be able to determine the type of symbol that is
                    ## expected. Also to be able to see if the symbol is exportable or not
                    newSym = Symbol(symstr, SymbolType.UNKNOWN, self)
                    self.addReferenceSymbol(newSym)
                    debugMsg(15, f"Adding action {self._action} to new symbol {symstr}")
                    newSym.addUsedIn(self)
                    ## Since it is undefined external, it must not be a private symbol
                    newSym.setPrivate(False)
                    self._linkableModule.addSymbol(newSym)
        else:
            for sym in self.getUnresolvedSymbols():
                debugMsg(15, f"Resolving symbol {sym.name} in action {self._action}")
                symstr = sym.name
                symbol = self._linkableModule.getSymbol(symstr)
                if symbol is not None:
                    debugMsg(
                        15,
                        f"Adding action {self._action} to already existing symbol {symstr} type {symbol.symbolType.name}",
                    )
                    self.replaceReferenceSymbol(symbol)
                    symbol.addUsedIn(self)
                else:
                    if must_resolve:
                        errorMsg(f"Unresolved symbol {symstr} in action {self._action}")

    def finalize(self) -> str:
        """Finalize the action

        Convert all symbols into actual IDs

        Returns:
            str: Resolved action
        """
        if self.isUnresolved:
            raise Exception(f"In action {self._action} there are unresolved symbols")
        else:
            resolvedAction = self._action
            for symbol in self._referenceSymbols:
                resolvedAction = resolvedAction.replace(symbol.name, str(symbol.id), 1)

            return resolvedAction

    def _detectSymbols(self) -> list:
        """Detects the symbols in the action"""
        ops = getActionOperands(self._action)
        symbols = []
        for op in ops:
            if (
                not isRegister(op)
                and not isNumericLiteral(op)[0]
                and not isReservedWord(op)
                and not isStringLiteral(op)
            ):
                symbols.append(op)

        label = getTargetLabel(self._action)
        if label is not None:
            symbols.append(label)

        debugMsg(25, f"Symbols found in action: {symbols}")
        return symbols

    def setTransition(self, transition: "TransitionSection") -> None:
        """Set the transition of the action"""
        self._parentSection = transition

    def setSharedBlock(self, sharedBlock: "SharedBlockSection") -> None:
        """Set the shared block of the action"""
        self._parentSection = sharedBlock

    def renameSymbol(self, oldName: str, newName: str) -> None:
        """Rename a symbol in the action

        Args:
            oldName (str): Old name of the symbol
            newName (str): New name of the symbol
        """
        pattern = r"\b" + re.escape(oldName) + r"\b"
        new_act = re.sub(pattern, newName, self._action)
        debugMsg(
            10,
            f"Renaming symbol {oldName} to {newName} in action {self._action} to {new_act}",
        )
        self._action = new_act

    @property
    def referenceSymbols(self) -> list:
        return self._referenceSymbols

    @property
    def transition(self):
        assert self.inTransition
        return self._parentSection

    @property
    def sharedBlock(self):
        assert self.inSharedBlock
        return self._parentSection

    def addReferenceSymbol(self, symbol: Symbol):
        self._referenceSymbols.append(symbol)

    def replaceReferenceSymbol(self, newSymbol: Symbol):
        self._referenceSymbols = [
            newSymbol if s.name == newSymbol.name else s for s in self._referenceSymbols
        ]

    def __str__(self) -> str:
        res = f"{self._action}\n"
        syms = [f"{s.symbolType.name} - {s.name}" for s in self._referenceSymbols]
        res = res + f"  Referenced symbols: {syms}\n"
        return res

    def combineSection(self, other: Section) -> None:
        super().combineSection(other)
        errorMsg("Cannot combine action with other section")
