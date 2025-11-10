# app/graph/build_prompt.py
import yaml # [추가]
from app.state_types import State, SessionType
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

def _load_history(user_id: str, session_type: SessionType) -> list:
    """
    DB에서 사용자의 '모든' 메시지를 가져온 후,
    현재 세션 타입에 맞게 필터링하여 BaseMessage 리스트로 변환
    """
    # [수정] REPO.get_messages는 이제 user_id만 받음 (모든 메시지 반환)
    all_messages = REPO.get_messages(user_id)
    history = []
    
    for msg in all_messages:
        role = msg.get("role")
        msg_session_type = msg.get("session_type")

        # 1. 현재 세션이 'WEEKLY'일 경우: 모든(WEEKLY + DAILY) 메시지 로드
        if session_type == "WEEKLY":
            if role == "user":
                history.append(HumanMessage(content=msg["text"]))
            elif role == "assistant":
                history.append(AIMessage(content=msg["text"]))
        
        # 2. 현재 세션이 'DAILY'일 경우: 'WEEKLY' 메시지만 로드
        elif session_type == "DAILY":
            if msg_session_type == "weekly": # 'weekly' 타입 메시지만 필터링
                if role == "user":
                    history.append(HumanMessage(content=msg["text"]))
                elif role == "assistant":
                    history.append(AIMessage(content=msg["text"]))
        
        # 3. (옵션) GENERAL 세션 등은 일단 무시
        else:
            pass 
            
    return history
    ''' 과거 코드
    for msg in all_messages:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["text"]))
        elif msg["role"] == "assistant":
            # [주의] summarize_update가 assistant 메시지를 저장하므로,
            # 다음 턴의 _load_history는 이전 턴의 AI 응답을 포함합니다.
            history.append(AIMessage(content=msg["text"]))
    return history
    '''

def build_prompt(state: State) -> State:
    spec = state.protocol # (참고: DAILY/GENERAL 세션은 이 값이 {}일 수 있음)
    level = state.intervention_level or "L1"
    
    # 1. 이전 대화 기록 로드
    chat_history = _load_history(state.user_id, state.session_type)

    # 2. LLM이 참고할 수 있도록 exit_criteria를 텍스트로 변환
    exit_criteria_text = yaml.dump(
        spec.get("exit_criteria", {}), 
        allow_unicode=True
    )
    
    # 3. 프롬프트 변수 설정 (spec이 비어있을 경우 대비 .get() 사용)
    variables = {
        "week": spec.get("week", state.current_week),
        "title": spec.get("title", "Daily Check-in"), # DAILY일 경우 기본값
        "goals": "; ".join(spec.get("goals", [])),
        "steps": " → ".join(spec.get("script_steps", [])),
        "level": level,
        "exit_goals": exit_criteria_text,
        "history": chat_history,
        "user_message": (state.last_user_message or spec.get("prompt_seed", ["오늘 어떠셨나요?"])[0]),
    }
    
    # 4. 프롬프트 템플릿을 사용하여 state.messages 생성
    state.messages = PROMPT_TEMPLATE.invoke(variables)
    
    return state