# coach_agent/graph/run_llm.py
from state_types import State
from services.llm import LLM_CHAIN # 미리 빌드된 체인 임포트
from langchain_core.messages import AIMessage

def run_llm(state: State) -> dict:
    print(f"\n=== [DEBUG] RunLLM Node Started ===")
    
    # 1. LLM 호출 (CounselorTurn 객체 반환)
    structured_output = LLM_CHAIN.invoke(state.llm_prompt_messages)
    
    # --- [디버깅 코드 추가] ---
    print(f"🤖 LLM Response Generated:")
    print(f"   - Session Goals Met?: {structured_output.session_goals_met}")
    print(f"   - Reasoning (근거): {structured_output.reasoning}")
    print(f"   - Assistant Says: {structured_output.response_text[:50]}...") # 너무 기니까 앞부분만
    # -----------------------

    # 2. 상태 업데이트
    # LLM의 답변 텍스트 저장
    state.llm_output = structured_output.response_text
    
    # ★ 핵심: 여기서 LLM의 판단이 State의 exit 변수로 넘어감
    state.exit = structured_output.session_goals_met
    
    # (선택적) 근거를 metrics에 저장해두면 나중에 분석 가능
    if structured_output.reasoning:
        state.metrics["exit_reasoning"] = structured_output.reasoning

    # 3. 메시지 추가 및 반환
    return {
        "messages": [AIMessage(content=structured_output.response_text)],
        # 업데이트한 state.exit의 값 반환 -> 다음 노드로 전달
        "exit": structured_output.session_goals_met,
        "llm_output": structured_output.response_text
    }