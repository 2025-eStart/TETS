# app/graph/run_llm.py
from state_types import State
from services.llm import LLM_CHAIN # 미리 빌드된 체인 임포트
from langchain_core.messages import AIMessage

def run_llm(state: State) -> State:
    
    # LCEL 체인 호출 (입력: BaseMessage 리스트)
    # LLM_CHAIN은 CounselorTurn 객체를 반환합니다.
    structured_output = LLM_CHAIN.invoke(state.llm_prompt_messages)
    
    # 결과를 state에 다시 채워넣습니다.
    state.llm_output = structured_output.response_text
    state.exit = structured_output.session_goals_met
    
    # (선택적) LLM의 판단 근거를 메트릭에 저장
    if structured_output.reasoning:
        state.metrics["exit_reasoning"] = structured_output.reasoning
    
    # AI 응답(문자열)을 'AIMessage'로 감싸서 'messages' 키로 반환합니다.
    # state_types.py의 'add_messages' 어노테이션이 이 메시지를
    # 'state.messages' 리스트에 자동으로 '추가'해 줍니다.
    # 이렇게 해야 과거 대화(Hello)가 지워지지 않습니다.
    return {
        "messages": [AIMessage(content=structured_output.response_text)]
    }