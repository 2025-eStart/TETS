# app/graph/summarize_update.py
from app.state_types import State
from app.services.summaries import persist_turn
from app.services import REPO
from app.services.llm import get_llm # LLM 모델 가져오기

def _create_summary(user_id: str, week: int) -> str:
    """
    지정된 주차의 전체 대화 내용을 기반으로 요약본을 생성
    """
    try:
        # 1. DB에서 '모든' 메시지를 가져옴 (2단계에서 구현한 함수)
        all_messages = REPO.get_messages(user_id)
        
        # 2. '현재 주차'의 메시지만 필터링
        week_messages = [
            msg for msg in all_messages 
            if msg.get("week") == week and msg.get("text")
        ]

        if not week_messages:
            return "요약할 대화 내용이 없습니다."

        # 3. LLM에 전달할 대화록(Transcript) 생성
        transcript = "\n".join(
            [f"{msg['role']}: {msg['text']}" for msg in week_messages]
        )

        # 4. 요약 프롬프트
        prompt = f"""
        다음은 사용자의 {week}주차 CBT 상담 대화 내용입니다. 
        이 세션의 핵심 성과(사용자가 완료한 과제, 주요 발견, 합의 사항, 감정 변화)를 
        다음 세션의 상담사가 빠르게 파악할 수 있도록 5줄 이내의 핵심 요약본으로 만드세요.
        
        [대화 내용]
        {transcript}
        
        [핵심 요약]
        """
        
        # 5. LLM 호출
        llm = get_llm() # 새 LLM 인스턴스 (설정 재사용)
        summary = llm.invoke(prompt).content
        return summary

    except Exception as e:
        print(f"ERROR: Summary creation failed for user {user_id}, week {week}: {e}")
        return f"{week}주차 요약 생성에 실패했습니다. (오류: {e})"

def summarize_update(state: State) -> State:
    # 1. 현재 턴의 메시지 저장
    persist_turn(
        state.user_id, 
        state.session_type.lower(), 
        state.current_week, 
        state.last_user_message, # 사용자의 마지막 메시지 전달
        state.llm_output or "", 
        state.exit
    )
    
    # 2. 세션이 '종료'되었을 때만 요약 생성
    if state.exit and state.session_type == "WEEKLY":
        print(f"--- Session {state.current_week} ended. Creating summary... ---")
        try:
            # 요약 생성 (LLM 호출)
            summary_text = _create_summary(state.user_id, state.current_week)
            
            # 요약본 DB에 저장
            REPO.save_session_summary(state.user_id, state.current_week, summary_text)
            print(f"--- Summary for week {state.current_week} saved. ---")
            
        except Exception as e:
            # 요약에 실패해도 그래프가 멈추지 않도록 처리
            print(f"CRITICAL: Failed to generate or save summary: {e}")
    return state