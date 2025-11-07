# app/graph/check_exit_or_pause.py
from app.state_types import State

def check_exit_or_pause(state: State) -> State:
    return state

def cond_exit_or_loop(state: State) -> str: 
    return "TAIL" if (state.exit or state.expired) else "LOOP"