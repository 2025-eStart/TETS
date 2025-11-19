# coach_agent/graph/generate_and_save_summary.py
from state_types import State
from services import REPO
from services.summarizer import create_session_summary # 요약 생성 로직

def generate_and_save_summary(state: State) -> dict:
    """
    세션 메시지를 기반으로 요약을 생성하고 데이터베이스에 저장합니다.
    (이 노드는 세션 목표 달성 후에만 호출되어야 함)
    """
    try:
        print(f"--- [GenerateSummary] Week {state.current_week} 요약 생성 시작 ---")
        
        # 1. 서비스 함수 호출 (코드가 훨씬 간결해짐)
        summary_text = create_session_summary(state.messages, state.current_week)
        
        if summary_text:
            # 2. 저장
            REPO.save_session_summary(
                user_id=state.user_id,
                week=state.current_week,
                summary=summary_text
            )
            print(f"   ✅ 요약 저장 완료: {summary_text[:30]}...")
        else:
            print("   ⚠️ 생성된 요약 내용이 없습니다.")
        
    except Exception as e:
        print(f"   ❌ 요약 생성/저장 실패: {e}")
    
    return {}