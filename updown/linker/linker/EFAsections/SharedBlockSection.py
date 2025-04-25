from linker.EFAsections.Section import Section
from linker.EFAsections.ActionSection import ActionSection
from linker.EFAsections.Section import Section

from common.debug import *


class SharedBlockSection(Section):
    def __init__(
        self,
        label: str,
        linkableModule: "LinkableModule",
    ):
        """Wrapper object of an EFA transition to keep information during linking

        Args:
            transition (EFA.Transition): Transition
        """
        super().__init__(linkableModule, label)
        self._actions = []
        self._linkedStates = []

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

    def addAction(self, action: ActionSection):
        """Add an action to the list of actions of the transition

        This writes the action to the EFA transition but it also
        keeps a reference to the action in the list of actions.

        Args:
            action (ActionInfo): The action to add
        """

        self._actions.append(action)
        action.setSharedBlock(self)

    def replaceLinkedState(self, oldState: "StateSection", newState: "StateSection"):
        """Replace a linked state with another one

        Args:
            oldState (StateSection): The old state to replace
            newState (StateSection): The new state to replace with
        """
        self._linkedStates.remove(oldState)
        self._linkedStates.append(newState)

    def addLinkedState(self, state: "StateSection"):
        """Add a linked state to the list of linked states of the shared block

        This writes the state to the EFA shared block but it also
        keeps a reference to the state in the list of linked states.

        Args:
            state (StateInfo): The state to add
        """
        self._linkedStates.append(state)

    @property
    def linkedStates(self) -> list:
        """Get the list of linked states of the shared block

        Returns:
            list: List of linked states
        """
        return self._linkedStates

    def __str__(self) -> str:
        """Get the string representation of the transition

        Returns:
            str: String representation of the transition
        """
        actions = [f"    {a}" for a in self._actions]
        actions = "\n".join(actions)
        return f"Shared Block: {self.labelName}\n{actions}"

    def setLinkableModule(self, linkableModule: "LinkableModule") -> None:
        super().setLinkableModule(linkableModule)
        for action in self._actions:
            action.setLinkableModule(linkableModule)

    def combineSection(self, other: Section) -> None:
        super().combineSection(other)
        errorMsg("SharedBlockSection.combineSection() not implemented")
