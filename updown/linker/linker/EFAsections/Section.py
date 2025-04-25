from abc import ABC, abstractmethod


class Section(ABC):
    def __init__(self, linkableModule: "LinkableModule", labelName: str):
        """Abstract class for a section of an EFA program

        A section is effectively a part of the EFA program in the
        linkable module
        """
        self._linkableModule = linkableModule
        self._symbol = None
        self._labelName = labelName
        pass

    @property
    def symbol(self) -> "Symbol":
        """Get the symbol of the section

        Returns:
            Symbol: Symbol of the section
        """
        assert self._symbol is not None
        return self._symbol

    @property
    def labelName(self) -> str:
        """Get the label name of the section

        Returns:
            str: Label name of the section
        """
        return self._labelName

    @property
    def linkableModule(self) -> "LinkableModule":
        """Get the linkable module of the section

        Returns:
            LinkableModule: Linkable module of the section
        """
        return self._linkableModule

    def setSymbol(self, symbol: "Symbol") -> None:
        """Set the symbol of the section

        Args:
            symbol (Symbol): Symbol of the section
        """
        self._symbol = symbol

    def setLabelName(self, labelName: str) -> None:
        """Set the label name of the section

        Args:
            labelName (str): Label name of the section
        """
        self._labelName = labelName

    def setLinkableModule(self, linkableModule: "LinkableModule") -> None:
        """Set the linkable module of the section

        Args:
            linkableModule (LinkableModule): Linkable module of the section
        """
        self._linkableModule = linkableModule
        if (
            self._symbol is not None
            and self._symbol.isState
            and self._symbol.isNullState
        ):
            self._symbol = self._linkableModule.nullState

    @abstractmethod
    def combineSection(self, other: "Section") -> None:
        """
        Allows for creating a single section that combines both sections,
        Merge other into self"""
        pass

    @abstractmethod
    def __str__(self):
        pass
