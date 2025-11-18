# coach_agent/graph/pick_week.py
from state_types import State
from utils.protocol_loader import load_week_spec
from services import REPO

def pick_week(state: State) -> State:
    s = state
    spec = load_week_spec("v1", s.current_week)
    s.protocol = spec
    # 세션이 없으면 생성
    if not s.weekly_session:
        s.weekly_session = REPO.create_weekly_session(s.user_id, s.current_week)
    return s
