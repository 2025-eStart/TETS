from app.state_types import State
from app.services import REPO
from datetime import timedelta

def route_session(state: State) -> State:
    return state

def _days_since(ts, now):
    return (now - ts).days if ts else 9999

def cond_route_session(state: State) -> str:
    s = state
    u = s.user
    # 21일 규칙(미완)
    if u.get("program_status") != "completed" and _days_since(u.get("last_seen_at"), s.now_utc) >= 21:
        REPO.upsert_user(s.user_id, {"current_week": 1})
        return "WEEKLY"
    # 24h 만료 여부는 세션 재개 시 판단(간단화)
    if s.weekly_session:
        return "WEEKLY"
    return "GENERAL"  # daily 미사용 기본
