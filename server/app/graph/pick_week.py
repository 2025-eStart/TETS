from app.state_types import State
from ._helpers import ensure_state
from app.utils.protocol_loader import load_week_spec

def pick_week(state: dict) -> dict:
    s = ensure_state(state)
    spec = load_week_spec("v1", s.current_week)
    s.protocol = spec
    # 세션이 없으면 생성
    from app.services.memory_repo import REPO
    if not s.weekly_session:
        s.weekly_session = REPO.create_weekly_session(s.user_id, s.current_week)
    return s
