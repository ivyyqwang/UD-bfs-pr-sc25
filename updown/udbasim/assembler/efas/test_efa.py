from EFA_v2 import *


def test_efa():
    efa = EFA([])
    efa.code_level = 'machine'

    state = State() #Initial State
    efa.add_initId(state.state_id)
    efa.add_state(state)

    tran = state.writeTransition("eventCarry", state, state, 0)
    tran.writeAction("addi X7 X18 -8")
    tran.writeAction("movbil X16 4 12 ")
    tran.writeAction("add X7 X18 X28")
    tran.writeAction("yield 1")

    tran = state.writeTransition("eventCarry", state, state, 1)
    tran.writeAction("addi X26 X26 64")
    tran.writeAction(f"yieldt 1")

    return efa

