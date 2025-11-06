from app.state_types import State
from app.utils.protocol_loader import meets_exit_criteria

def check_exit_or_pause(state: dict) -> dict:
    s = State(**state)
    s.exit = meets_exit_criteria(s.llm_output, s.protocol.get("exit_criteria", {}))
    return s.model_dump()

def cond_exit_or_loop(state: dict) -> str:
    s = State(**state)
    return "TAIL" if (s.exit or s.expired) else "LOOP"
