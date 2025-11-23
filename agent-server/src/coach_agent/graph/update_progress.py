# coach_agent/graph/update_progress.py
from coach_agent.state_types import State
from coach_agent.services import REPO # REPO가 데이터베이스 인터페이스일 때

def update_progress(state: State) -> dict:
    """
    현재 주차 세션의 '진행 상태(progress)'를 업데이트합니다.

    - 이번 턴에서 사용자가 exit 조건을 충족했는지 여부(state.exit)를
      REPO.update_progress(...)에 전달합니다.
    - 하지만 '주차 진급'이나 '프로그램 완료' 같은 큰 상태 전환은
      여기서 하지 않습니다.

    ✅ 역할 분리:
      - update_progress  : "이 세션이 어떻게 진행 중인지 기록"
      - mark_session_as_completed : "이번 주차 세션이 최종적으로 끝났음을 기록"
      - advance_to_next_week      : "다음 접속에서 다음 주차로 올릴지 결정"
    """
    try:
        # 1. 현재 주차와 사용자 ID 가져오기
        user_id = state.user_id
        current_week = state.current_week

        # 2. REPO를 통해 진행도(최근 활동 기준) 업데이트
        REPO.update_progress(
            user_id=user_id,
            week=current_week,
            exit_hit=state.exit,   # 이번 턴에서 exit 조건을 만족했는지 여부
        )

        print(f"[{current_week}주차] 진행 상태 업데이트 (exit_hit={state.exit})")

    except Exception as e:
        print(f"진행 상태 업데이트 중 오류 발생: {e}")

    return {}
