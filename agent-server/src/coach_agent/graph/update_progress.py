# coach_agent/graph/update_progress.py
from state_types import State
from services import REPO # REPO가 데이터베이스 인터페이스일 때

def update_progress(state: State) -> dict:
    """
    현재 주차의 세션 진행도(progress)를 업데이트하여 저장합니다.
    (세션 요약 생성과는 무관)
    """
    try:
        # 1. 현재 주차와 사용자 ID를 가져옴
        user_id = state.user_id
        current_week = state.current_week
        
        # 2. REPO를 통해 진행도 업데이트
        # (REPO 구현체에 따라 messages 길이, 완료 조건 등을 체크하여 진행도를 계산)
        REPO.update_progress(user_id, current_week, state.exit)
        
        print(f"[{current_week}주차] 진행 상태 업데이트 (완료여부: {state.exit})")
        
    except Exception as e:
        print(f"진행 상태 업데이트 중 오류 발생: {e}")

    return {}