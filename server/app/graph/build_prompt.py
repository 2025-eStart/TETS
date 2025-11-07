# app/graph/build_prompt.py
import yaml # [추가]
from app.state_types import State
from app.services import REPO # [추가]
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 시스템 프롬프트 템플릿
SYSTEM_TEMPLATE = (
"You are a CBT counselor.\n"
"Current phase: Week {week} - {title}\n"
"Goals: {goals}\n"
"Script Steps: {steps}\n"
"InterventionLevel={level}\n"
"---"
"This week's session goals (exit criteria) are:\n"
"{exit_goals}\n"
"---"
"You MUST respond using the 'CounselorTurn' structured format.\n"
"1. First, craft the 'response_text' to the user based on the protocol.\n"
"2. Second, analyze the conversation and the user's *last message* to determine if "
"the 'session_goals_met' (listed above) are ALL met. "
"Set 'session_goals_met' to True only if all criteria are satisfied."
)

# ChatPromptTemplate 정의
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYSTEM_TEMPLATE),
    MessagesPlaceholder(variable_name="history", optional=True),
    HumanMessage(content="{user_message}"),
])

def _load_history(user_id: str, week: int) -> list:
    """DB에서 메시지를 가져와 LangChain BaseMessage 객체로 변환"""
    db_messages = REPO.get_messages(user_id, week)
    history = []
    for msg in db_messages:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["text"]))
        elif msg["role"] == "assistant":
            # [주의] summarize_update가 assistant 메시지를 저장하므로,
            # 다음 턴의 _load_history는 이전 턴의 AI 응답을 포함합니다.
            history.append(AIMessage(content=msg["text"]))
    return history

def build_prompt(state: State) -> State: # [수정]
    spec = state.protocol
    level = state.intervention_level or "L1"
    
    # 1. 이전 대화 기록 로드
    chat_history = _load_history(state.user_id, state.current_week)

    # 2. LLM이 참고할 수 있도록 exit_criteria를 텍스트로 변환
    exit_criteria_text = yaml.dump(
        spec.get("exit_criteria", {}), 
        allow_unicode=True
    )

    # 3. 프롬프트 변수 설정
    variables = {
        "week": spec["week"],
        "title": spec["title"],
        "goals": "; ".join(spec["goals"]),
        "steps": " → ".join(spec["script_steps"]),
        "level": level,
        "exit_goals": exit_criteria_text,
        "history": chat_history,
        "user_message": (state.last_user_message or spec["prompt_seed"][0]),
    }
    
    # 4. 프롬프트 템플릿을 사용하여 state.messages 생성
    state.messages = PROMPT_TEMPLATE.invoke(variables)
    
    return state