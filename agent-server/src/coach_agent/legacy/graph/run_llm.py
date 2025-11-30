# coach_agent/graph/run_llm.py
from coach_agent.graph.state import State
from coach_agent.services.llm import LLM_CHAIN
from coach_agent.services import REPO
from langchain_core.messages import AIMessage # 후처리 노드 사용 시 삭제


def run_llm(state: State) -> dict:
    print(f"\n=== [DEBUG] RunLLM Node Started ===")
    
    # 1. 안전장치: 프롬프트가 없으면 건너뜀
    if not state.llm_prompt_messages:
        print("⏩ [RunLLM] 프롬프트 없음 -> 스킵")
        return {
            "llm_output": None,
            "exit": False
        }
    
    # 2. LLM 호출
    structured_output = LLM_CHAIN.invoke(state.llm_prompt_messages)
    
    # 3. [Progress] 단계 이동 로직
    llm_decided_step = structured_output.current_step_index
    current_idx = getattr(state, "current_step_index", 0) # 0부터 시작 가정
    
    new_step_idx = current_idx
    
    if llm_decided_step > current_idx:
        new_step_idx = llm_decided_step
        print(f"⏩ [Progress] 단계 이동: {current_idx} -> {new_step_idx}")
        
        # [핵심] DB 저장 시도 (에러 핸들링 추가)
        try:
            REPO.update_checkpoint(state.user_id, state.current_week, new_step_idx)
            print(f"💾 [DB Save] 저장 성공: Step {new_step_idx}")
        except Exception as e:
            print(f"🔥 [DB Save Error] 저장 실패: {e}")
            
    else:
        # (선택) 유지될 때도 확실히 하기 위해 저장할 수 있음
        new_step_idx = current_idx
        print(f"⚓ [Progress] 단계 유지: {current_idx}")
        
    # 4. [Metrics] 속마음 노트 업데이트
    # 기존 metrics를 복사한 뒤, 새로운 근거를 추가합니다.
    new_metrics = state.metrics.copy()
    if structured_output.reasoning:
        new_metrics["exit_reasoning"] = structured_output.reasoning
    
    # --- 디버깅 출력 ---
    print(f"🤖 LLM Response:")
    print(f"   - Step: {new_step_idx}")
    print(f"   - Goals Met?: {structured_output.session_goals_met}")
    print(f"   - Reasoning: {structured_output.reasoning}")
    print(f"   - Assistant: {structured_output.response_text}...")
    # ------------------

    # 5. 최종 반환 (여기서 리턴한 값이 State에 반영됩니다)
    return {
        "messages": [AIMessage(content=structured_output.response_text)],  # 후처리 노드 사용 시 삭제
        "current_step_index": new_step_idx,   # 단계 업데이트
        "exit": structured_output.session_goals_met,
        "llm_output": structured_output.response_text,
        "metrics": new_metrics                # metrics 업데이트
    }