# coach_agent/graph/build_prompt.py
import yaml
from ..state_types import State
from ..services import REPO

# 랭체인 관련 임포트
from langchain_core.prompts import (
    ChatPromptTemplate, 
    HumanMessagePromptTemplate, 
    MessagesPlaceholder,
    SystemMessagePromptTemplate # SystemMessage 대신 템플릿용 클래스 사용 권장
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

# [Refactoring] 프롬프트 파일에서 템플릿 가져오기
# (같은 폴더에 prompts.py가 있다고 가정)
from .prompts import (
    TEMPLATE_GREETING_NEW_USER,
    TEMPLATE_GREETING_WEEKLY,
    TEMPLATE_GREETING_GENERAL,
    TEMPLATE_CONVERSATION
)

# --- 헬퍼 함수들 (기존 유지) ---
def _clean_message_content(msg: BaseMessage) -> BaseMessage:
    content_val = msg.content
    if isinstance(content_val, list):
        text_content = ""
        for item in content_val:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content = item.get("text", "")
                break 
        content_val = text_content
    if not isinstance(content_val, str):
        content_val = str(content_val)
    if msg.type == "human":
        return HumanMessage(content=content_val)
    elif msg.type == "ai":
        return AIMessage(content=content_val)
    elif msg.type == "system":
        return SystemMessage(content=content_val)
    else:
        msg.content = content_val
        return msg

def _load_past_summaries(user_id: str, current_week: int) -> list:
    history = []
    past_summaries = REPO.get_past_summaries(user_id, current_week)
    for summary in past_summaries:
        summary_text = f"--- 지난 {summary['week']}주차 요약 ---\n{summary['summary']}"
        history.append(AIMessage(content=summary_text))
    return history

# --- build_prompt 함수 ---
def build_prompt(state: State) -> dict:
    spec = state.protocol
    session_type = state.session_type

    # 1. 첫 턴(인사)인지 확인
    is_first_turn = state.last_user_message is None
    prompt_messages = [] 

    if is_first_turn:
        # --- 1-A. 첫 턴일 경우 (인사말 생성) ---
        nickname = state.nickname
        days_since = state.days_since_last_seen

        if nickname is None:
            # (1) 신규 사용자
            prompt_template = ChatPromptTemplate.from_template(TEMPLATE_GREETING_NEW_USER)
            variables = {
            }
            
        elif session_type == "WEEKLY":
            # (2) 주간 상담 시작
            seed_data = spec.get("prompt_seed", ["오늘 어떠셨나요?"]) 
            if isinstance(seed_data, str):
                seed_data = [seed_data]
                
            prompt_template = ChatPromptTemplate.from_template(TEMPLATE_GREETING_WEEKLY)
            variables = {
                "nickname": nickname,
                "days_since_last_seen": days_since,
                "session_type": "WEEKLY",
                "week": spec.get("week", state.current_week),
                "title": spec.get("title", "주간 상담"),
                "goals": "; ".join(spec.get("goals", [])),
                "prompt_seed": seed_data[0],
            }
            
        elif session_type == "GENERAL":
            # (3) 상담 완료 후 재진입
            prompt_template = ChatPromptTemplate.from_template(TEMPLATE_GREETING_GENERAL)
            variables = {"nickname": nickname}
        
        else:
            # (4) Fallback
            prompt_template = ChatPromptTemplate.from_template(
                "안녕하세요! 무엇을 도와드릴까요?\n\n[중요] **반드시 한국어로만 응답해야 합니다.**"
            )
            variables = {}

        prompt_messages = prompt_template.invoke(variables).to_messages()

    else:
        # --- 1-B. 대화 중일 경우 (Conversation Loop) ---
        level = state.intervention_level or "L1"
        
        intervention_instruction = ""
        empathy_instruction = "Briefly acknowledge the user's feeling."

        # [레벨별 분기 로직]
        if level in ["L4", "L5"]:
            intervention_instruction = """
            🚨 **EMERGENCY / HIGH RISK DETECTED** 🚨
            The user is showing signs of severe depression.
            1. Suggest professional help gently.
            2. Gently steer them back to the topic.
            """
            empathy_instruction = "Show deep empathy and validate their pain heavily."
        
        elif level in ["L2", "L3"]:
            intervention_instruction = """
            ⚠️ **AVOIDANCE DETECTED** ⚠️
            Redirect immediately to the 'Script Steps'.
            """
            empathy_instruction = "Briefly acknowledge, but prioritize the session goal."
        
        else: # L1
            intervention_instruction = "Proceed with the standard CBT coaching flow."
            empathy_instruction = "Show empathy and acknowledge the Human's last message."

        # 데이터 준비
        cleaned_chat_history = [_clean_message_content(msg) for msg in state.messages]
        past_summaries = _load_past_summaries(state.user_id, state.current_week)
        exit_criteria_text = yaml.dump(spec.get("exit_criteria", {}), allow_unicode=True)

        variables = {
            "week": spec.get("week", state.current_week),
            "title": spec.get("title", "Daily Check-in"),
            "goals": "; ".join(spec.get("goals", [])),
            "steps": " → ".join(spec.get("script_steps", [])),
            "level": level,
            "exit_goals": exit_criteria_text,
            # history는 placeholder로 들어가므로 변수에서 제외하거나 text로 넣지 않음
            "user_message": state.last_user_message,
            "intervention_instruction": intervention_instruction,
            "empathy_instruction": empathy_instruction
        }
        
        # [수정] SystemMessage 안에 변수가 있으므로 SystemMessagePromptTemplate 사용 권장
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(TEMPLATE_CONVERSATION),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{user_message}"),
        ])
        
        # history는 invoke 시에 리스트 형태로 주입
        invoke_vars = variables.copy()
        invoke_vars["history"] = past_summaries + cleaned_chat_history
        
        prompt_messages = prompt_template.invoke(invoke_vars).to_messages()
    
    return {
        "llm_prompt_messages": prompt_messages
    }