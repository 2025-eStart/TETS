from datetime import datetime, timezone
from app.state_types import State
from ._helpers import ensure_state
from app.services import REPO

def load_state(state: dict) -> dict:
    s = ensure_state(state)
    s.now_utc = datetime.now(timezone.utc)
    user = REPO.get_user(s.user_id)
    REPO.last_seen_touch(s.user_id)
    s.user = user
    s.current_week = user.get("current_week", 1)
    s.weekly_session = REPO.get_active_weekly_session(s.user_id, s.current_week)
    return s
