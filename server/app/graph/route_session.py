from app.state_types import State
from app.services import REPO
from datetime import timedelta, datetime

def route_session(state: State) -> State:
    return state

def _days_since(ts, now):
    """
    타임스탬프(ts)가 'now'로부터 며칠 전인지 계산합니다.
    ts가 None이거나 datetime이 아니면 0을 반환합니다.
    """
    if not isinstance(ts, datetime):
        return 0 # 혹은 9999 (로직에 따라 다름. 여기선 0이 안전)
        
    return (now - ts).days

def cond_route_session(state: State) -> str:
    s = state
    u = s.user
    now = s.now_utc
    
# 0. 유저의 마지막 앱 접속 시간 (마지막 API 호출)
    user_last_seen = u.get("last_seen_at")
    
    # 1. [21일 규칙] 프로그램 리셋
    # 마지막 접속이 21일 이상 지났다면, 1주차로 리셋합니다.
    if user_last_seen and _days_since(user_last_seen, now) >= 21:
        if u.get("program_status") != "completed":
            REPO.upsert_user(s.user_id, {"current_week": 1})
            s.weekly_session = None # 로드된 세션 무효화
            s.current_week = 1      # state 객체도 갱신
        return "WEEKLY" # 1주차 상담 시작

    # 2. [24시간 ~ 14일 규칙] 주간 상담 리셋
    # 현재 진행 중인 주간 세션이 있는지 확인합니다.
    if s.weekly_session:
        # 세션의 마지막 활동 시간
        session_last_activity = s.weekly_session.get("last_activity_at")
        
        days_since_activity = _days_since(session_last_activity, now)
        
        # 24시간(1일) 이상, 14일 미만으로 지났다면
        if 1 <= days_since_activity < 14:
            # 주차(current_week)는 유지하되,
            # 현재 로드된 세션을 무효화(None)하여
            # PickWeek 노드가 이 주차의 '새로운' 세션을 만들도록 합니다.
            s.weekly_session = None 
            return "WEEKLY"
            
        # 3. [24시간 미만 규칙] 주간 상담 이어하기
        # 24시간이 지나지 않았다면(days_since_activity < 1), 
        # 로드된 세션(s.weekly_session)을 그대로 사용합니다.
        return "WEEKLY"

    # 4. [기본] 진행 중인 세션이 없는 경우
    # (예: 1주차 완료 후 2주차 첫 방문)
    if u.get("program_status") != "completed":
        return "WEEKLY"

    # 5. [기타]
    return "GENERAL"
