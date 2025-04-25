from linker.EFAsections.Section import Section

from enum import Enum
from typing import Union

from common.debug import *


class SymbolType(Enum):
    STATE = "state"
    TRANSITION = "transition"
    SHARED_BLOCK = "shared_block"
    STATIC_DATA = "static_data"
    BRANCH_LABEL = "branch_label"
    UNKNOWN = "unknown"


class Symbol(object):
    def __init__(
        self, name: str, symbol_type: SymbolType, section: Union[Section, None] = None
    ) -> None:
        """Object that represents a symbol in an UpDown program.

        Args:
            id (int): ID of the symbol.
            name (str, optional): Name of the symbol. Defaults to None.
        """
        self._type = symbol_type
        self._name = name
        self._section = section
        self._is_init_null_state = False

        self._id = -1
        self._size = 0
        section.setSymbol(self) if section is not None else None

        debugMsg(10, f"Creating Symbol object {self._name} of type {self._type.name}")

        ## Private symbols are expected to be states, transitions
        ## that are not events, and branch_labels
        self._private = False

        self._used_in = []

    ###########################
    ### Getters and setters ###
    ###########################
    @property
    def name(self) -> str:
        """Get the name of the symbol.

        Returns:
            str: Name of the symbol.
        """
        return self._name

    @property
    def isNullState(self) -> bool:
        """Returns if the symbol is an initID (for states)"""
        return self._is_init_null_state

    @property
    def isPrivate(self) -> bool:
        """Returns if the symbol is private.

        Returns:
            bool: True if the symbol is private, False otherwise.
        """
        return self._private

    @property
    def id(self) -> int:
        """Get the ID of the symbol.

        Returns:
            int: ID of the symbol.
        """
        return self._id

    @property
    def isDefined(self) -> bool:
        """Returns if the symbol is defined.

        Returns:
            bool: True if the symbol is defined, False otherwise.
        """
        isDef = self._section is not None and self.symbolType != SymbolType.UNKNOWN
        debugMsg(
            15,
            f"Checking if symbol {self.symbolType.name} - {self._name} returns {isDef}",
        )
        return isDef

    @property
    def symbolType(self) -> SymbolType:
        """Get the type of the symbol.

        Returns:
            SymbolType: Type of the symbol.
        """
        return self._type

    @property
    def section(self) -> Union[Section, None]:
        """Get the section of the symbol.

        Returns:
            Section: Section of the symbol.
        """
        assert self.isDefined, "Attempting to access a section of an undefined symbol."
        return self._section

    @property
    def size(self) -> int:
        """Get the size of the symbol.

        Returns:
            int: Size of the symbol.
        """
        return self._size

    def setIsNullState(self, is_init_null_state: bool) -> None:
        """Set if the symbol is an initID null state (for states)

        Args:
            is_init (bool): True if the symbol is an initID, False otherwise.
        """
        self._is_init_null_state = is_init_null_state

    def setID(self, id: int) -> None:
        """Set the ID of the symbol.

        Args:
            id (int): New ID of the symbol.
        """
        self._id = id

    def setName(self, name: str) -> None:
        """Set the name of the symbol.

        Args:
            name (str): _description_
        """
        old_name = self._name
        self._name = name
        if self._section is not None:
            self._section.setLabelName(name)

        for section in self._used_in:
            section.renameSymbol(old_name, name)

    def setPrivate(self, external: bool) -> None:
        """Set if the symbol is external.

        Args:
            external (bool): True if the symbol is external, False otherwise.
        """
        self._private = external

    def setSection(self, section: Section) -> None:
        """Set the section of the symbol.

        Args:
            section (Section): New section of the symbol.
        """
        self._section = section

    def setSize(self, size: int) -> None:
        """Set the size of the symbol.

        This is useful for Data symbols.

        Args:
            size (int): New size of the symbol.
        """
        self._size = size

    @property
    def isState(self) -> bool:
        """Returns if the symbol is a state.

        Returns:
            bool: True if the symbol is a state, False otherwise.
        """
        return self._type == SymbolType.STATE

    @property
    def isTransition(self) -> bool:
        """Returns if the symbol is a transition.

        Returns:
            bool: True if the symbol is a transition, False otherwise.
        """
        return self._type == SymbolType.TRANSITION

    @property
    def isSharedBlock(self) -> bool:
        """Returns if the symbol is a shared block.

        Returns:
            bool: True if the symbol is a shared block, False otherwise.
        """
        return self._type == SymbolType.SHARED_BLOCK

    @property
    def isStaticData(self) -> bool:
        """Returns if the symbol is static data.

        Returns:
            bool: True if the symbol is static data, False otherwise.
        """
        return self._type == SymbolType.STATIC_DATA

    def addUsedIn(self, section: "ActionSection") -> None:
        """Add a section to the list of Action Sections that use this symbol.

        Args:
            section (ActionSection): ActionSection that uses this symbol.
        """
        self._used_in.append(section)

    @property
    def isBranchLabel(self) -> bool:
        """Returns if the symbol is a branch label.

        Returns:
            bool: True if the symbol is a branch label, False otherwise.
        """
        return self._type == SymbolType.BRANCH_LABEL

    def __str__(self) -> str:
        """String representation of a symbol.

        Returns:
            str: String representation of a symbol.
        """
        return f"{self.symbolType.value} [{self.id}] - {self.name}"

    def __hash__(self):
        return hash((self._type, self._id, self._name))

    def __eq__(self, other: Union[str, "Symbol"]) -> bool:
        if isinstance(other, str):
            return self._name == other
        elif isinstance(other, Symbol):
            return (
                self._name == other.name
                and self._type == other.symbolType
                and self._id == other.id
            )
        else:
            return False
