from linker.EFAsections.Section import Section
from linker.EFAsections.ActionSection import ActionSection
from linker.EFAsections.StateSection import StateSection


from common.debug import *

from typing import Any


class TransitionSection(Section):
    def __init__(
        self,
        type: str,
        origin: StateSection,
        destination: StateSection,
        transitionLabel: Any,
        linkableModule: "LinkableModule",
    ):
        """Wrapper object of an EFA transition to keep information during linking

        Args:
            transition (EFA.Transition): Transition
        """
        super().__init__(linkableModule, transitionLabel)
        self._actions = []
        self._originState = origin
        self._destinationState = destination
        self._type = type
        origin.addOutTransition(self)
        destination.addInTransition(self)

    @property
    def actions(self) -> list:
        return self._actions

    def assignSymbols(self, unresolved: bool = False, must_resolve=True) -> None:
        """Assign the symbols of the actions of the transition
        Iterate over all the actions, and get the possible symbols in
        string form, then use these to either pass the symbol to the Action
        already assigned, or create an unresolved symbol in the action.

        Args:
            unresolved (bool, optional): If True, create unresolved symbols. Defaults to False.
        """
        for action in self._actions:
            action.assignSymbols(unresolved, must_resolve)

    def addAction(self, action: ActionSection) -> None:
        """Add an action to the list of actions of the transition

        This writes the action to the EFA transition but it also
        keeps a reference to the action in the list of actions.

        Args:
            action (ActionInfo): The action to add
        """

        self._actions.append(action)
        action.setTransition(self)

    def setOrigin(self, origin: StateSection) -> None:
        """Set the origin of the transition"""
        self._originState = origin

    def setDestination(self, destination: StateSection) -> None:
        """Set the destination of the transition"""
        self._destinationState = destination

    def setLabelName(self, labelName: str) -> None:
        """Set the label name of the transition"""
        if self.isEventTransition:
            return super().setLabelName(labelName)

    def setLinkableModule(self, linkableModule: "LinkableModule") -> None:
        super().setLinkableModule(linkableModule)
        for action in self._actions:
            action.setLinkableModule(linkableModule)

    @property
    def isEventTransition(self) -> bool:
        """Check if the transition is an event transition

        Returns:
            bool: True if the transition is an event transition
        """
        return self._originState.isNullState

    @property
    def origin(self) -> StateSection:
        """Get the origin of the transition"""
        return self._originState

    @property
    def destination(self) -> StateSection:
        """Get the destination of the transition"""
        return self._destinationState

    @property
    def label(self) -> str:
        """Get the label of the transition"""
        return str(self.labelName)

    @property
    def type(self) -> str:
        """Get the type of the transition"""
        return str(self._type)

    def renameStates(self, oldName: str, newName: str) -> None:
        """Rename the states of the transition

        Args:
            oldName (str): Old name of the state
            newName (str): New name of the state
        """
        if self._originState.name == oldName:
            self._originState = newName
        if self._destinationState.name == oldName:
            self._destinationState = newName

    def __str__(self) -> str:
        """Get the string representation of the transition

        Returns:
            str: String representation of the transition
        """
        actions = [f"  {a}" for a in self._actions]
        actions = "\n".join(actions)
        return (
            f"Transition [{self._type}] {self.labelName} "
            f"{self._originState.name} -> {self._destinationState.name}"
            f"\n{actions}"
        )

    def combineSection(self, other: Section) -> None:
        super().combineSection(other)
        errorMsg("TransitionSection.combineSection not implemented")
