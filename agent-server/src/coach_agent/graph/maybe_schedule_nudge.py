# coach_agent/graph/maybe_schedule_nudge.py
from state_types import State
from services import REPO

def maybe_schedule_nudge(state: State) -> dict:
    # 개발 단계: 예약 생략. Firestore/Cloud Tasks 붙일 때 구현.
    
    # '주간 상담 완료' 여부를 DB에 기록해야 함
    if state.exit == True and state.session_type == "WEEKLY":
        REPO.mark_session_as_completed(state.user_id, state.now_utc) # -> last_weekly_session_completed_at 갱신

    REPO.last_seen_touch(state.user_id) # 마지막 접속 시간 갱신
    return {}
