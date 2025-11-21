# coach_agent/graph/pick_week.py
from ..state_types import State
from ..utils.protocol_loader import load_week_spec
from ..services import REPO

def pick_week(state: State) -> dict:
    spec = load_week_spec("v1", state.current_week)

    weekly_session = state.weekly_session
    if not weekly_session:
        weekly_session = REPO.create_weekly_session(state.user_id, state.current_week)

    return {
        "protocol": spec,
        "weekly_session": weekly_session
    }
