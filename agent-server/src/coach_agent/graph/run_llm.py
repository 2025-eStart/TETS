# coach_agent/graph/run_llm.py
from state_types import State
from services.llm import LLM_CHAIN # 미리 빌드된 체인 임포트
from langchain_core.messages import AIMessage

def run_llm(state: State) -> dict:
    print(f"\n=== [DEBUG] RunLLM Node Started ===")
    
    # 0. LLM 호출 (CounselorTurn 객체 반환)
    structured_output = LLM_CHAIN.invoke(state.llm_prompt_messages)
    
    # 1. Metrics 업데이트 준비 (딕셔너리 병합을 위해 기존 metrics 가져오기)
    # 주의: LangGraph의 Dict 리턴 방식은 최상위 키를 덮어쓰기(Overwrite) 하는 것이 기본입니다.
    # metrics 딕셔너리 전체를 교체하지 않으려면, 기존 값을 복사해서 합쳐야 안전합니다.
    new_metrics = state.metrics.copy()
    if structured_output.reasoning:
        new_metrics["exit_reasoning"] = structured_output.reasoning
    
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
        # 후처리모델 RewriteTone에서 messages에 추가하므로 여기서는 messages를 반환하지 않음
        # "messages": [AIMessage(content=structured_output.response_text)],
        # 업데이트한 state.exit의 값 반환 -> 다음 노드로 전달
        "exit": structured_output.session_goals_met,
        "llm_output": structured_output.response_text,
        "metrics": new_metrics
    }