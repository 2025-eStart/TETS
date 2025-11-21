# coach_agent/graph/generate_and_save_summary.py
from ..state_types import State
from ..services import REPO
from ..services.summarizer import create_session_summary # 요약 생성 로직

def generate_and_save_summary(state: State) -> dict:
    """
    세션 메시지를 기반으로 요약을 생성하고 데이터베이스에 저장합니다.
    (이 노드는 세션 목표 달성 후에만 호출되어야 함)
    """
    try:
        # state.protocol에서 필요한 메타데이터 추출
        spec = state.protocol
        title = spec.get("title", "주간 상담")
        exit_criteria = spec.get("exit_criteria", {})
        
        # 1. 서비스 함수 호출
        summary_text = create_session_summary(
            messages=state.messages, 
            current_week=state.current_week,
            title=title,
            exit_criteria=exit_criteria 
        )
        
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