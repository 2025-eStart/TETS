# coach_agent/graph/maybe_schedule_nudge.py
from coach_agent.state_types import State
from coach_agent.services import REPO

def maybe_schedule_nudge(state: State) -> dict:
    """
    세션이 끝난 뒤에:
    1) 주간 상담이면 세션 완료 처리 + 마지막 주간 상담 완료 시점 기록
    2) 공통적으로 '마지막 접속 시간(last_seen_at)' 갱신
    3) (추후) FCM 푸시/리마인드 스케줄링을 붙일 위치

    ⚠️ 중요한 포인트:
    - '주차 진급(week+1)'은 여기서 하지 않는다.
    - 주차 진급은 route_session()에서 REPO.advance_to_next_week()를 통해 처리한다.
    """
    # 1. 주간 상담이면서, 이번 턴에서 exit 조건을 충족했다면 => 이번 주차 세션 '완료'
    if state.exit and state.session_type == "WEEKLY":
        REPO.mark_session_as_completed(
            user_id=state.user_id,
            week=state.current_week,
            completed_at=state.now_utc,   # load_state에서 세팅된 now_utc 사용
        )

    # 2. 마지막 접속 시간을 항상 갱신
    REPO.last_seen_touch(state.user_id)

    # 3. (나중에) FCM 푸시, 리마인드 스케줄링 로직은 여기서 추가 예정
    #    예: REPO.schedule_nudge(...), 또는 scheduler 서비스 호출 등

    return {}
