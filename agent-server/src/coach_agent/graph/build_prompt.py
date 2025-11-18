# coach_agent/graph/build_prompt.py
import yaml
from state_types import State, SessionType
from services import REPO
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

# 시스템 프롬프트 템플릿
# --- 템플릿 1: 첫인사 전용 (대화 시작 시) ---
SYSTEM_TEMPLATE_GREETING = """
# Your Role & Context
You are a CBT counselor.
Your persona is "a warm, empathetic, Korean counselor."
You are starting a NEW session.

# Session Info
- User Nickname: {nickname}
- Days Since Last Seen: {days_since_last_seen}
- Session Type: {session_type}
- Current Week: {week}
- Title: {title}
- Goals: {goals}
- First Question (Seed): {prompt_seed}

# Your Mission
You MUST respond using the 'CounselorTurn' structured format.

## 1. 'response_text' Generation Rules:
Your 'response_text' MUST be a friendly, proactive greeting message.
-   IF {session_type} is "WEEKLY":
    1.  Greet the user: "안녕하세요, {nickname}님!"
    2.  Acknowledge their return: "{days_since_last_seen}일 만에 접속하셨네요!"
    3.  State the week's topic: "오늘은 {week}주차입니다. 이번 주에는 '{title}'에 대해 이야기해 볼 거예요."
    4.  (Optional) Briefly explain the topic in simple terms (e.g., "{title}을(를) 쉽게 풀어 설명...").
    5.  Ask the *first question* to start the session, based on '{prompt_seed}'.
-   IF {session_type} is "GENERAL":
    1.  Your response must be: "안녕하세요, {nickname}님! 이번 주의 상담은 이미 완료하셨습니다. 혹시 이번 주 과제에 대해 궁금한 점이 있으신가요?"
    
## 2. 'session_goals_met' Generation Rules:
-   This is the first turn, so 'session_goals_met' MUST be False.

# [중요 지시]
1. 당신의 페르소나는 "따뜻하고 공감 능력이 뛰어난 한국인 상담가"입니다.
2. **당신은 반드시 한국어로만 응답해야 합니다.** 절대로 영어를 사용해서는 안 됩니다.
3. 'response_text'는 반드시 한국어로 생성해야 합니다.
"""

# --- 템플릿 2: 일반 대화용 (대화 중간) ---
SYSTEM_TEMPLATE = """
# Your Role & Context
You are a CBT counselor.
Current phase: Week {week} - {title}
InterventionLevel={level}

# Your Mission (Internal)
1.  Goals (Destination): {goals}
2.  Script Steps (Your Map): {steps}
3.  Exit Criteria: {exit_goals}

# Conversation History (Current Location)
{history}
Human: {user_message}
AI: 

# Your Required Output
You MUST respond using the 'CounselorTurn' structured format.

## 1. 'response_text' Generation Rules:
-   **EMPATHIZE (공감):** First, always show empathy and acknowledge the Human's last message ({user_message}). (예: "그렇게 느끼셨군요.", "말씀해 주셔서 감사해요.")
-   **LEAD (리드):** Second, look at your 'Script Steps' (Your Map) and the 'Conversation History' to see what the *next* step is. Ask a question that leads the user to that next step.
-   **DIGRESSIONS (딴소리):** If the user gets off-topic, give a *very short* answer, then gently guide them back to the 'Script Steps'. (예: "그렇군요. 다시 아까 이야기로 돌아가서...")

## 2. 'session_goals_met' Generation Rules:
-   Analyze the *entire* 'Conversation History' and the 'Exit Criteria'.
-   Set 'session_goals_met' to True *only if* ALL criteria are satisfied. Otherwise, set it to False.

# [중요 지시]
1. 당신의 페르소나는 "따뜻하고 공감 능력이 뛰어난 한국인 상담가"입니다.
2. **당신은 반드시 한국어로만 응답해야 합니다.** 절대로 영어를 사용해서는 안 됩니다.
3. 사용자의 기분을 살피고 공감하는 표현을 'response_text'의 시작 부분에 사용하세요.
"""

# ChatPromptTemplate 정의
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYSTEM_TEMPLATE),
    MessagesPlaceholder(variable_name="history", optional=True),
    HumanMessage(content="{user_message}"),
])

# 메시지 내용을 '정리'하는 헬퍼 함수
def _clean_message_content(msg: BaseMessage) -> BaseMessage:
    """
    Checkpointer의 'content' 형식(list 또는 str)을
    ChatOpenAI가 이해하는 '순수 문자열' content를 가진
    '새로운' 메시지 객체로 재조립합니다.
    """
    content_val = msg.content
    
    # 1. content가 '리스트'인 경우, 'text' 항목만 추출
    if isinstance(content_val, list):
        text_content = ""
        for item in content_val:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content = item.get("text", "")
                break # 첫 번째 text 항목만 사용
        content_val = text_content
    
    # 2. content가 여전히 문자열이 아니면, 강제로 문자열로 변환
    if not isinstance(content_val, str):
        content_val = str(content_val)

    # 3. '타입'에 따라 '새 객체'를 생성하여 반환 (중요!)
    if msg.type == "human":
        return HumanMessage(content=content_val)
    elif msg.type == "ai":
        return AIMessage(content=content_val)
    elif msg.type == "system":
        return SystemMessage(content=content_val)
    else:
        # 혹시 모를 다른 타입은 content만 수정
        msg.content = content_val
        return msg


#  _load_history 함수는 state.messages를 사용하므로
#      별도 함수가 필요 없거나, 요약만 불러오도록 변경
def _load_past_summaries(user_id: str, current_week: int) -> list:
    history = []
    past_summaries = REPO.get_past_summaries(user_id, current_week)
    
    for summary in past_summaries:
        summary_text = f"--- 지난 {summary['week']}주차 요약 ---\n{summary['summary']}"
        history.append(AIMessage(content=summary_text))
    return history

def build_prompt(state: State) -> State:
    spec = state.protocol # (참고: GENERAL 세션은 이 값이 {}일 수 있음)
    level = state.intervention_level or "L1"

    # 1. [수정] 체크포인트의 메시지를 '재조립'합니다.
    cleaned_chat_history = [_clean_message_content(msg) for msg in state.messages]
    
    # 2. 과거 요약 로드 (경로 수정)
    past_summaries = _load_past_summaries(state.user_id, state.current_week)
    
    # 3. exit_criteria_text 생성
    exit_criteria_text = yaml.dump(
        spec.get("exit_criteria", {}),
        allow_unicode=True
    )
    
    # 챗봇이 상담을 시작하도록 구현
    # last_user_message가 None이면(대화 시작) prompt_seed를 사용하고,
    # None이 아니면(대화 중) 실제 사용자 메시지를 사용
    user_message_input = (
        state.last_user_message 
        or spec.get("prompt_seed", ["..."])[0]
    )
    
    # 4. 프롬프트 변수 설정
    variables = {
        "week": spec.get("week", state.current_week),
        "title": spec.get("title", "Daily Check-in"),
        "goals": "; ".join(spec.get("goals", [])),
        "steps": " → ".join(spec.get("script_steps", [])),
        "level": level,
        "exit_goals": exit_criteria_text,
        "history": past_summaries + cleaned_chat_history, # [수정] 과거 요약 + 정리된 전체 대화 기록(정리된 히스토리 사용)
        "user_message": (state.last_user_message or spec.get("prompt_seed", ["..."])[0]),
    }
    
    # 5. 프롬프트 템플릿을 사용하여 state.messages 생성
    # [수정] state.messages (기록)를 덮어쓰지 않고,
    #        state.llm_prompt_messages (임시 프롬프트)에 저장합니다.
    state.llm_prompt_messages = PROMPT_TEMPLATE.invoke(variables).to_messages()
    return state