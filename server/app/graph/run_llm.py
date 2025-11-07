# app/graph/run_llm.py
from app.state_types import State
from app.services.llm import LLM_CHAIN # [수정] 미리 빌드된 체인 임포트

def run_llm(state: State) -> State: # [수정]
    
    # [수정] LCEL 체인 호출 (입력: BaseMessage 리스트)
    # LLM_CHAIN은 CounselorTurn 객체를 반환합니다.
    structured_output = LLM_CHAIN.invoke(state.messages)
    
    # [수정] 결과를 state에 다시 채워넣습니다.
    state.llm_output = structured_output.response_text
    state.exit = structured_output.session_goals_met
    
    # (선택적) LLM의 판단 근거를 메트릭에 저장
    if structured_output.reasoning:
        state.metrics["exit_reasoning"] = structured_output.reasoning
    
    return state