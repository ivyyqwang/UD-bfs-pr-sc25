from enum import Enum

from linker.EFAsections.Section import Section
from linker.EFAsections.TransitionSection import TransitionSection


from common.debug import *


class staticDataType(Enum):
    """Enum that represents the type of static data.
    This allows to understand different address regions to be used
    """

    LANE_PRIVATE = 0
    UPDOWN_PRIVATE = 1
    DRAM_SHARED = 2


class StaticDataSection(Section):
    def __init__(
        self,
        dataName: str,
        size: int,
        type: staticDataType,
        linkableModule: "LinkableModule",
    ):
        """Wrapper object of an EFA state to keep information during linking

        Args:
            state (EFA.State): State
        """
        super().__init__(linkableModule, dataName)
        self._size = size
        self._type = type

    @property
    def size(self) -> int:
        """Get the size of the section.

        Returns:
            int: Size of the section.
        """
        return self._size

    def setSize(self, size: int) -> None:
        """Set the size of the section.

        This is useful for Data Section

        Args:
            size (int): New size of the Section.
        """
        self._size = size

    @property
    def type(self) -> staticDataType:
        """Get the type of the section.

        Returns:
            staticDataType: Type of the section.
        """
        return self._type

    def setType(self, type: staticDataType) -> None:
        """Set the type of the section.

        This is useful for Data Section

        Args:
            type (staticDataType): New type of the Section.
        """
        self._type = type

    @property
    def name(self) -> str:
        """Get the name of the state"""
        return self.labelName

    def __str__(self) -> str:
        """Get the string representation of the state

        Returns:
            str: String representation of the state
        """

        return f"Static Data: {self.labelName} of size {self.size}"

    def combineSection(self, other: Section) -> None:
        super().combineSection(other)
        errorMsg("Static Data Sections cannot be combined")
