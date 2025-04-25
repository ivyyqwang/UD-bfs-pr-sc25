## UpDown Imports
from common.helper import *
from linker.LinkableModule import LinkableModule
from linker.EFAsections.Section import Section
from linker.EFAsections.TransitionSection import TransitionSection
from linker.EFAsections.ActionSection import ActionSection
from linker.EFAsections.StateSection import StateSection
from linker.EFAsections.SharedBlockSection import SharedBlockSection
from linker.EFAsections.StaticDataSection import StaticDataSection, staticDataType
from linker.Symbol.Symbol import Symbol, SymbolType

from typing import Union, List, Type, Any


def efaProgram(method) -> "EFAProgram":
    """Create an EFAProgram object.

    Receives a method and creates a new class that inherits from EFAProgram.
    and includes the method.

    Args:
        name (str): Name of the program.

    Returns:
        EFAProgram: EFAProgram object.
    """

    def anInitiFnc(self, name: str):
        super(self.__class__, self).__init__(name)

    def getEFAPrograms(cls):
        return cls.efaPrograms

    class_name = method.__name__ + "_" + randomString(5)

    class_dict = {
        "__init__": anInitiFnc,
        method.__name__: method,
        "efaPrograms": [method.__name__],
        "getEFAPrograms": classmethod(getEFAPrograms),
    }
    newClass = type(class_name, (EFAProgram,), class_dict)
    LinkableModule.registerEFAclass(newClass)
    return newClass


class EFAProgram(LinkableModule):
    def __init__(self, name: str):
        """Object that represents a complete UpDown program.

        Args:
            name (str, optional): Name of the program. Defaults to None.
        """
        super().__init__(name)

        self.__currentTransitionID = 0
        self.__currentSharedBlockSymbolID = 0
        self.__currentStateID = 0

        self.__current_transition = None

        ## Backwards compatibility API
        self.code_level = "machine"

    ############################################
    ############# Private Methods ##############
    ############################################

    def _getNewStateID(self) -> int:
        """Get a new ID for a state.

        Returns:
            int: New ID for a state.
        """
        self.__currentStateID += 1
        return self.__currentStateID

    def _getNewTransitionID(self) -> int:
        """Get a new ID for a transition.

        Returns:
            int: New ID for a transition.
        """
        self.__currentTransitionID += 1
        return self.__currentTransitionID

    def _getNewSharedBlockSymbolID(self) -> int:
        """Get a new ID for a shared block.

        Returns:
            int: New ID for a shared block.
        """
        self.__currentSharedBlockSymbolID += 1
        return self.__currentSharedBlockSymbolID

    ############################################
    ############# Public Methods ###############
    ############################################

    def addState(self, stateName: Union[str, None] = None) -> Symbol:
        """Add a state to the list of states defined in the program.

        Add a symbol to the list of symbols defined in the Linkable Module.
        Args:
            state (State): State to be added.

        Returns:

        """

        if stateName is None:
            stateName = "state" + str(self._getNewStateID())

        state = StateSection(stateName, self)
        sym = Symbol(stateName, SymbolType.STATE, state)
        sym.setPrivate(True)
        self.addSymbol(sym)

        return sym

    def _create_transition_name(
        self,
        type: str,
        sourceState: Union[Symbol, None],
        targetState: Union[Symbol, None],
        label: Any,
    ) -> str:
        """Obtain the name of the transition based on the type, source state, target state and label.

        Args:
            type (str): Type of the transition.
            sourceState (Union[Symbol, None]): Source state of the transition.
            targetState (Union[Symbol, None]): Target state of the transition.
            label (Any): Label of the transition.

        Returns:
            str: Name of the transition.
        """
        name = (
            type
            + "_"
            + str(sourceState.name)
            + "_"
            + str(targetState.name)
            + "_"
            + str(label)
        )
        return name

    def addTransition(
        self,
        type: str,
        sourceState: Union[Symbol, None],
        targetState: Union[Symbol, None],
        label: Any,
    ) -> Symbol:
        """Add a transition to the list of transitions defined in the program.

        Args:
            type (str): Type of the transition (Defined in EFA).
            EFAType (str): Type of the transition.
            sourceState (str): Name of the source state.
            targetState (str): Name of the target state.
            transitionName (str): Name of the transition.

        Returns:
            EFA.Transition: Transition added to the program.
        """
        sourceState = self.nullState if sourceState is None else sourceState

        targetState = self.nullState if targetState is None else targetState

        # Event transitions use string labels for linking purposes
        if sourceState.isNullState:
            transitionName = str(label)
        else:
            transitionName = self._create_transition_name(
                type, sourceState, targetState, label
            )

        tran = TransitionSection(type, sourceState.section, targetState.section, label, self)  # type: ignore
        sym = Symbol(transitionName, SymbolType.TRANSITION, tran)  # type: ignore

        ## Check if it is an event transition. Any transition starting from the null state is an event transition
        if sourceState.isNullState:
            sym.setPrivate(False)
        else:
            sym.setPrivate(True)
        self.addSymbol(sym)
        return sym

    def addAction(self, action: str, symbol: Union[Symbol, None] = None) -> None:
        """Add an action to a symbol of type transition or shared block.
        By default use current transition.

        Args:
            action: Action to be added.
            symbol: Symbol to which the action is added.
        """
        if symbol is None:
            symbol = self.__current_transition

        assert (
            symbol.symbolType == SymbolType.TRANSITION
            or symbol.symbolType == SymbolType.SHARED_BLOCK
        ), "Symbol must be of type transition or shared block."
        act = ActionSection(action, self)
        symbol.section.addAction(act)  # type: ignore
        label = getTargetLabel(action)
        if label is not None:
            sym = Symbol(label, SymbolType.BRANCH_LABEL, act)  # type: ignore
            sym.setPrivate(True)
            self.addSymbol(sym)

    def addActions(
        self, actions: List[str], transition: Union[Symbol, None] = None
    ) -> None:
        """Add a list of actions to a transition.

        This allows to write multiple actions as a list of strings.

        ```Python
            self.addTransition("eventCarry", "state0", "state1", "t1")
            self.addActions(["add X1, X2, X3", "add X4, X5, X6"], "t1")

        Args:
            actions (List[str]): List of actions to be added.
            transition (Union[Symbol, None], optional): Transition to which the actions are added. Defaults to None.
        """
        for action in actions:
            self.addAction(action, transition)

    def addSharedBlock(self, name: str) -> Symbol:
        """Add a shared block to the program.

        Args:
            name (str): Name of the shared block.

        Returns:
            Symbol: Symbol that represents the shared block.
        """
        sharedBlock = SharedBlockSection(name, self)
        sym = Symbol(name, SymbolType.SHARED_BLOCK, sharedBlock)
        sym.setPrivate(False)
        self.addSymbol(sym)
        return sym

    def addStaticData(
        self, name: str, size: int, type: staticDataType = staticDataType.LANE_PRIVATE
    ) -> Symbol:
        staticData = StaticDataSection(name, size, type, self)
        sym = Symbol(name, SymbolType.STATIC_DATA, staticData)
        sym.setPrivate(False)
        self.addSymbol(sym)
        return sym

    ###########################################################
    ############# Backwards compatible interface ##############
    ###########################################################

    class efaElement:
        """Base interface for EFA elements

        This class is just to provide an API that is similar to that of
        the EFA emulator. Thus ensuring backwards compatibility.
        """

        def __init__(self, efaProgram: "EFAProgram", symbol: Symbol):
            """
            Args:
                efaProgram (EFAProgram): EFA program to which the element belongs.
                symbol (Symbol): Symbol that represents the element.
            """
            self._symbol: Symbol = symbol
            self._efaProgram: EFAProgram = efaProgram

        @property
        def efaProgram(self) -> "EFAProgram":
            return self._efaProgram

        @property
        def symbol(self) -> Symbol:
            return self._symbol

        @property
        def section(self) -> Section:
            return self._symbol.section  # type: ignore

    class Transition(efaElement):
        def __init__(self, efaProgram: "EFAProgram", symbol: Symbol):
            super().__init__(efaProgram, symbol)

        def writeAction(self, action: str) -> None:
            self.efaProgram.addAction(action, self.symbol)

        def getLabel(self) -> str:
            return self.symbol.name

    class state(efaElement):
        """State element of an EFA program.

        This class is just to provide an API that is similar to the EFA
        emulator and to ensure backwards compatibility.
        """

        def __init__(self, efaProgram: "EFAProgram", symbol: Symbol):
            super().__init__(efaProgram, symbol)
            self._state_id = self.symbol.name
            self.alphabet = []

        @property
        def state_id(self) -> str:
            """State ID of the state."""
            return self._state_id

        def __setattr__(self, name, value):
            if name == "alphabet":
                assert isinstance(value, list), "Alphabet must be a list"
                assert isinstance(self.section, StateSection), "Section must be a state"
                self.section.setAlphabet(value)
            else:
                super().__setattr__(name, value)

        def writeTransition(
            self,
            type: str,
            source: Union[None, str, Type],
            target: Union[None, str, Type],
            label: Any,
        ) -> "EFAProgram.Transition":
            """Write a transition from source state to target state.

                This is here for backwards compatibility. Since the current state (self) is
                not really used.
            Args:
                type (str): Transition type as defined by the EFA
                source (Union[str, "state"]): Source state. It can be a string containing the name of the state, or a state object.
                target (Union[str, "state"]): Target state. It can be a string containing the name of the state, or a state object.
                label (Any): Label of the transition. If event, label of the event.

            Returns:
                transition: Transition object that was created.
            """

            return self.efaProgram.writeTransition(type, source, target, label)

    def State(self, name: Union[str, None] = None) -> state:
        sym = self.addState(name)
        st = self.state(self, sym)
        return st

    class StaticData(efaElement):
        def __init__(self, efaProgram: "EFAProgram", symbol: Symbol):
            super().__init__(efaProgram, symbol)

        def appendStaticData(
            self,
            name: str,
            size: int,
            type: staticDataType = staticDataType.LANE_PRIVATE,
        ) -> None:
            self.efaProgram.addStaticData(
                name,
                size,
                type,
            )

    def appendBlockAction(self, name: str, action: str) -> None:
        """Append an action to a block.

        If the action block does not exists. Create one with the
        given name.

        Args:
            name (str): Name of the block.
            action (str): Action to be appended.
        """
        sym = self.getSharedBlockSymbol(name)
        if sym is None:
            sym = self.addSharedBlock(name)

        self.addAction(action, sym)

    def linkBlocktoState(self, blockName: str, state: Union[str, state]) -> None:
        """Link a block to a state.

        Args:
            blockName (str): Name of the block.
            state (Union[str, state]): State to which the block is linked.
        """
        sym = self.getSharedBlockSymbol(blockName)
        if sym is None:
            errorMsg(f"Block {blockName} not found, it cannot be linked to a state")

        if isinstance(state, str):
            stateSym = self.getStateSymbol(state)
        elif isinstance(state, EFAProgram.state):
            stateSym = state.symbol
        else:
            stateSym = None

        if stateSym is None:
            errorMsg(f"State {state} not found, it cannot be linked to a block")

        stateSym.section.linkBlockToState(sym.section)

    def add_state(self, state: state) -> None:
        """This is a backwards compatible interface.
        This does not do anything because State creation is equal to
        state addition in the new interface."""
        warningMsg(
            "add_state is a no-op in the linker interface."
            "Consider removing it from your code."
            "(Creation of a state is enough for adding it to the "
            "program)"
        )
        pass

    def add_initId(self, initId: Union[str, state]) -> None:
        """This allows to define the initial state (i.e., the null state).

        All event transitions must be defined from this state.
        """
        if isinstance(initId, str):
            sym = self.getStateSymbol(initId)
        elif isinstance(initId, EFAProgram.state):
            sym = self.getStateSymbol(initId.state_id)

        if sym is not None:
            self.setNullState(sym)
        else:
            errorMsg(
                f"Attempting to set initial state {initId}. But it has not been declared"
            )

    def writeTransition(
        self,
        type: str,
        source: Union[None, str, state],
        target: Union[None, str, state],
        label: Any,
    ) -> Transition:
        """Write a transition from source to destination

        Args:
            type (str): Transition type as defined by the EFA
            source (Union[str, "state"]): Source state. It can be a string containing the name of the state, or a state object.
            target (Union[str, "state"]): Target state. It can be a string containing the name of the state, or a state object.
            label (Any): Label of the transition. If event, label of the event (str).

        Returns:
            transition: Transition object that was created.
        """

        if isinstance(source, str):
            sourceSym = self.getStateSymbol(source)
            assert sourceSym is not None, f"State {source} not declared"
            assert (
                sourceSym.isDefined
            ), f"State {source} declared but not defined. States cannot be external"
        elif source is not None:
            sourceSym = source.symbol
        else:
            sourceSym = None
        if isinstance(target, str):
            targetSym = self.getStateSymbol(target)
            assert targetSym is not None, f"State {target} not declared"
            assert (
                targetSym.isDefined
            ), f"State {target} declared but not defined. States cannot be external"
        elif target is not None:
            targetSym = target.symbol
        else:
            targetSym = None

        sym = self.addTransition(type, sourceSym, targetSym, label)

        return EFAProgram.Transition(self, sym)

    def writeEventTransition(
        self, type: str, target: Union[str, state, None], label: str
    ) -> Transition:
        """Write an event transition from the null state to another state.

        Args:
            type (str): Type of the transition.
            target (Union[str, state]): Target state.
            label (str): Label of the transition.
        """
        return self.writeTransition(type, None, target, label)

    def writeEvent(self, label: str) -> Transition:
        """Write an event transition from the null state to another state.

        Args:
            label (str): Label of the event.
        """
        return self.writeEventTransition("eventCarry", None, label)
