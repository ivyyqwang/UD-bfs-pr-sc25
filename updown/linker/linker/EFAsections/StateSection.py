from linker.EFAsections.Section import Section

from common.debug import *


class StateSection(Section):
    def __init__(
        self,
        stateName: str,
        linkableModule: "LinkableModule",
    ):
        """Wrapper object of an EFA state to keep information during linking

        Args:
            state (EFA.State): State
        """
        super().__init__(linkableModule, stateName)
        self._in_transitions = []
        self._out_transitions = []
        self._alphabet = []
        self._linkedSharedBlocks = []

    def addInTransition(self, transition: "TransitionSection"):
        """Add an in transition to the list of in transitions of the state

        This writes the transition to the EFA state but it also
        keeps a reference to the transition in the list of in transitions.

        Args:
            transition (TransitionInfo): The transition to add
        """
        self._in_transitions.append(transition)

    def addOutTransition(self, transition: "TransitionSection"):
        """Add an out transition to the list of out transitions of the state

        This writes the transition to the EFA state but it also
        keeps a reference to the transition in the list of out transitions.

        Args:
            transition (TransitionInfo): The transition to add
        """
        self._out_transitions.append(transition)

    """Delete the transition section from the list of egress transitions"""
    def deleteOutTransition(self, transition: "TransitionSection"):
        self._out_transitions.remove(transition)

    @property
    def getOutTransitions(self) -> list:
        return self._out_transitions

    def getTransitionsWithLabel(self, label:str):
        res = []

        trans = self.getOutTransitions
        for tran in trans:
            if tran.label == label:
                res.append(tran)

        return res

    @property
    def name(self) -> str:
        """Get the name of the state"""
        return self.labelName

    @property
    def alphabet(self) -> list:
        """Get the alphabet of the state"""
        return self._alphabet

    def setAlphabet(self, alphabet: list):
        """Set the alphabet of the state"""
        self._alphabet = alphabet

    def linkBlockToState(self, block: "SharedBlockSection"):
        """Link a shared block to the state"""
        self._linkedSharedBlocks.append(block)
        block.addLinkedState(self)

    @property
    def linkedSharedBlocks(self) -> list:
        """Get the linked shared blocks of the state"""
        return self._linkedSharedBlocks

    @property
    def isNullState(self) -> bool:
        """Check if the state is a null state"""
        return self._symbol.isNullState

    def __str__(self) -> str:
        """Get the string representation of the state

        Returns:
            str: String representation of the state
        """

        return (
            f"State: {self.labelName} InTransitions: [{len(self._in_transitions)}] "
            f"OutTransitions: [{len(self._out_transitions)}]"
        )

    def combineSection(self, other: "StateSection") -> None:
        assert self.name == other.name, "Cannot combine sections with different names"
        super().combineSection(other)
        debugMsg(15, f"Combining state {self.name} with {other.name}")
        self._in_transitions.extend(other._in_transitions)
        self._out_transitions.extend(other._out_transitions)
        for tran in other._in_transitions:
            debugMsg(25, f"Setting destination of {tran.label} to {self.name}")
            tran.setDestination(self)
        for tran in other._out_transitions:
            debugMsg(25, f"Setting origin of {tran.label} to {self.name}")
            tran.setOrigin(self)
        self._alphabet.extend(other._alphabet)
        self._linkedSharedBlocks.extend(other._linkedSharedBlocks)
        for block in other._linkedSharedBlocks:
            block.replaceLinkedState(other, self)
