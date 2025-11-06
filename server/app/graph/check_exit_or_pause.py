from app.state_types import State
from app.utils.protocol_loader import meets_exit_criteria
from ._helpers import ensure_state

def check_exit_or_pause(state: dict) -> dict:
    s = ensure_state(state)
    s.exit = meets_exit_criteria(s.llm_output, s.protocol.get("exit_criteria", {}))
    return s

def cond_exit_or_loop(state: dict) -> str:
    s = ensure_state(state)
    return "TAIL" if (s.exit or s.expired) else "LOOP"
