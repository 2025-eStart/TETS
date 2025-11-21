# coach_agent/graph/persist_turn.py
from ..state_types import State
from ..services.history import persist_turn 

def persist_turn_node(state: State) -> dict:
    persist_turn(
        user_id=state.user_id,
        week=state.current_week,
        messages=state.messages,
        session_type=state.session_type
    )
    return {}