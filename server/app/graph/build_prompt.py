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

def _load_history(user_id: str, session_type: SessionType, current_week: int) -> list:
    """
    (과거 요약본 + 현재 세션 상세 대화)를 로드하고 세션 타입에 맞게 필터링
    """
    history = []

    # 1. 과거 요약본 로드 (항상 'weekly' 타입임)
    past_summaries = REPO.get_past_summaries(user_id, current_week)
    
    # 2. '현재 주차'의 상세 대화 내용 로드 (2단계에서 구현한 함수)
    all_messages = REPO.get_messages(user_id)
    current_week_messages = [
        msg for msg in all_messages 
        if msg.get("week") == current_week
    ]

    # --- 세션 타입별 필터링 ---

    # 1) 현재 세션이 'WEEKLY'일 경우:
    if session_type == "WEEKLY":
        # (A) 과거 요약본 (모두 'weekly'이므로 전부 포함)
        for summary in past_summaries:
            summary_text = f"--- 지난 {summary['week']}주차 요약 ---\n{summary['summary']}"
            # 요약본은 AI의 기억(AIMessage)으로 주입
            history.append(AIMessage(content=summary_text))
        
        # (B) 현재 주차의 상세 대화 (WEEKLY + DAILY 모두 포함)
        for msg in current_week_messages:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["text"]))
            elif msg["role"] == "assistant":
                history.append(AIMessage(content=msg["text"]))

    # 2) 현재 세션이 'DAILY'일 경우:
    elif session_type == "DAILY":
        # (A) 과거 요약본 (모두 'weekly'이므로 전부 포함)
        for summary in past_summaries:
            summary_text = f"--- 지난 {summary['week']}주차 요약 ---\n{summary['summary']}"
            history.append(AIMessage(content=summary_text))
            
        # (B) 현재 주차의 상세 대화 (오직 'weekly'만 포함)
        for msg in current_week_messages:
            if msg.get("session_type") == "weekly":
                if msg["role"] == "user":
                    history.append(HumanMessage(content=msg["text"]))
                elif msg["role"] == "assistant":
                    history.append(AIMessage(content=msg["text"]))

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
    chat_history = _load_history(state.user_id, state.session_type, state.current_week)

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