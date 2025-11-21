# coach_agent/graph/route_session.py
from ..state_types import State
from ..services import REPO
from ..utils._days_since import _days_since

# --- 1. "작업자" 함수 ---
# (build_graph의 g.add_node("RouteSession", route_session)가 호출)
# 이 함수는 State를 수정하고, 다음 목적지를 'state.next_route'에 저장
def route_session(state: State) -> dict: 
    now = state.now_utc
    user = state.user
    active_session = state.weekly_session 
    last_seen_at = user.get("last_seen_at")
    last_completed_at = user.get("last_weekly_session_completed_at")

    days_since_last_seen = _days_since(last_seen_at, now)
    days_since_last_completion = _days_since(last_completed_at, now)

    # --- 1. 롤백 규칙 ---
    if days_since_last_seen >= 21:
        REPO.rollback_user_to_week_1(state.user_id)
        # [수정] 'dict'를 반환하여 State를 갱신
        return {
            "current_week": 1,
            "next_route": "WEEKLY" # 다음 목적지를 state에 저장
        }

    # --- 2. '진행 중인' 세션이 있는 경우 ---
    if active_session:
        if days_since_last_seen < 1:
            return {"next_route": "WEEKLY"} # 다음 목적지를 state에 저장
        else:
            REPO.restart_current_week_session(state.user_id, state.current_week)
            return {"next_route": "WEEKLY"}

    # --- 3. '진행 중인' 세션이 없는 경우 ---
    if last_completed_at and days_since_last_completion < 7:
        return {"next_route": "GENERAL"}
    else:
        new_week = state.current_week
        if last_completed_at: # 7일이 지나서 다음 주차로 진급
            new_week = REPO.advance_to_next_week(state.user_id)
        
        return {
            "current_week": new_week,
            "next_route": "WEEKLY"
        }

# --- 2. "라우터" 함수 ---
# (build_graph의 add_conditional_edges가 호출)
# 이 함수는 'route_session' 작업자가 State에 저장한 값을 읽기만 합니다.
def cond_route_session(state: State) -> str:
    """state.next_route에 저장된 목적지를 반환합니다."""
    
    if not state.next_route:
        # 비상 상황 (route_session이 next_route를 설정하지 않은 경우)
        return "GENERAL"
        
    return state.next_route