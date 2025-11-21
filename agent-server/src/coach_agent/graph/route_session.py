# coach_agent/graph/route_session.py
from ..state_types import State
from ..services import REPO
from ..utils._days_since import _days_since

# --- 1. "작업자" 함수 ---
# (build_graph의 g.add_node("RouteSession", route_session)가 호출)
# 이 함수는 State를 수정하고, 다음 목적지를 'state.next_route'에 저장
def route_session(state: State) -> dict:
    """
    유저의 최근 접속일, 최근 주간 세션 완료일, 진행 중인 세션 여부 등을 기반으로
    이번 턴에서 어떤 흐름으로 보낼지(WEEKLY / GENERAL)를 결정하는 노드.

    - 21일 이상 미접속: week 1로 롤백
    - 진행 중인 세션 있음:
        - 1일 미만 미접속: 그대로 이어서 WEEKLY
        - 1일 이상 미접속: 현재 주차 세션 재시작 후 WEEKLY
    - 진행 중인 세션 없음:
        - 최근 주간 세션 완료 후 7일 미만: GENERAL
        - 그 외(7일 이상 지남): 다음 주차로 advance_to_next_week() 후 WEEKLY
    """
    now = state.now_utc
    user = state.user
    active_session = state.weekly_session

    last_seen_at = user.get("last_seen_at")
    last_completed_at = user.get("last_weekly_session_completed_at")

    days_since_last_seen = _days_since(last_seen_at, now)
    days_since_last_completion = _days_since(last_completed_at, now)

    # --- 1. 롤백 규칙 (21일 이상 미접속 시 week 1로 복귀) ---
    if days_since_last_seen >= 21:
        REPO.rollback_user_to_week_1(state.user_id)
        return {
            "current_week": 1,
            "next_route": "WEEKLY",
            "session_type": "WEEKLY",
        }

    # --- 2. 미접속일 21일 미만 && '진행 중인' 세션이 있는 경우  ---
    if active_session:
        # (1) 미접속일 1일 미만 → 그대로 이어서 WEEKLY 세션
        if days_since_last_seen < 1:
            return {"next_route": "WEEKLY",
            "session_type": "WEEKLY",
        }
        # (2) 미접속일 1일 이상 21일 미만 → 현재 주차 세션 재시작 후 WEEKLY
        else:
            REPO.restart_current_week_session(state.user_id, state.current_week)
            return {"next_route": "WEEKLY",
                    "session_type": "WEEKLY",
            }

    # --- 3. '진행 중인' 세션이 없는 경우 ---
    if last_completed_at and days_since_last_completion < 7:
        # 최근 주간 세션을 끝낸 지 7일이 안 됐으면 이번주는 이미 끝,
        # 일반 상담(GENERAL)로 보냄
        return {"next_route": "GENERAL",
                "session_type": "GENERAL",
        }
    else:
        # 7일 이상 지났거나(저번 주차 상담까지 완료), 아직 완료 기록이 없는 경우(첫 번째 상담)
        new_week = state.current_week

        # 첫 번째 상담이 아닌 경우(이전에 완료한 기록이 있을 경우) → 다음 주차로 진급
        if last_completed_at:
            new_week = REPO.advance_to_next_week(state.user_id)

        return {
            "current_week": new_week,
            "next_route": "WEEKLY",
            "session_type": "WEEKLY",
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
