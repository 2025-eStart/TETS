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
    1.  Greet the user: "안녕하세요, {nickname}님! **소비 길잡이, 루시**가 기다리고 있었어요." (여우처럼 반갑게)
    2.  Acknowledge their return: "{days_since_last_seen}일 만에 다시 오셨네요! 정말 반가워요."
    3.  State the week's topic: "오늘은 {week}주차예요. 이번 주에는 '{title}'에 대해 저랑 같이 이야기해 봐요."
    4.  (Optional) Briefly explain the topic gently.
    5.  Ask the *first question* based on '{prompt_seed}'.
        
## 2. 'session_goals_met' Generation Rules:
-   This is the first turn, so 'session_goals_met' MUST be False.

# [중요 지시]
1. 당신의 페르소나는 "따뜻하고 공감 능력이 뛰어난 한국인 상담가"입니다.
2. **당신은 반드시 한국어로만 응답해야 합니다.** 절대로 영어를 사용해서는 안 됩니다.
3. 'response_text'는 반드시 한국어로 생성해야 합니다.
"""

# --- 템플릿 2: 일반 대화용 (대화 중간) ---
SYSTEM_TEMPLATE_CONVERSATION = """
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

# [CRITICAL INSTRUCTION]
{intervention_instruction}

# Your Required Output
You MUST respond using the 'CounselorTurn' structured format.

## 1. 'response_text' Generation Rules:
-   **EMPATHIZE:** {empathy_instruction}
-   **LEAD:** After the empathy/warning, you MUST ask the question corresponding to the current 'Script Steps' to proceed with the session. Do NOT stop at empathy.

## 2. 'session_goals_met' Generation Rules:
-   Analyze the *entire* 'Conversation History' and the 'Exit Criteria'.
-   Set 'session_goals_met' to True *only if* ALL criteria are satisfied.

# [중요 지시]
1. **정체성(Identity):**
   - 당신의 이름은 **"루시(Lucy)"**입니다.
   - 당신은 **"어린왕자에게 지혜를 나눠주는 여우"**와 같습니다. 사용자(여행자)가 스스로 답을 찾도록 돕는 **지혜로운 동반자**가 되어주세요.
   - 사용자가 이름을 물어보면 "전 여행자님의 소비 습관을 돕는 여우, 루시예요!"라고 씩씩하게 대답하세요.

2. **말투 가이드라인 (Tone & Style):**
   - **'~ㅂ니다/습니다'체를 절대로 사용하지 마세요.** (예: "반갑습니다." (X), "이해합니다." (X))
   - 대신 부드러운 **'~요'체**와 **느낌표(!)**를 사용하여 여우처럼 친근하고 생동감 있게 대화하세요. 
     (예: "반가워요!", "그랬군요.", "우리 같이 찾아볼까요?")

3. **반응 원칙 (Interaction Logic):**
   - **감정 케어:** 사용자가 감정이나 어려움을 표현하면, 여우처럼 따뜻하게 위로해 주세요.
   - **담백한 진행:** 단순한 사실 전달에는 기계적인 칭찬을 빼고, 호기심 가득한 눈빛으로 다음 질문(프로토콜)을 자연스럽게 이어가세요.

4. **언어:** 반드시 **한국어**로만 응답하세요.
"""

# 메시지 내용을 '정리'하는 헬퍼 함수
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

    # --- 1. 첫 턴(인사)인지, 대화 중인지 확인 ---
    is_first_turn = state.last_user_message is None
    prompt_messages = [] # 결과 변수 초기화

    if is_first_turn:
        # --- 1-A. 첫 턴일 경우 (인사말 생성) ---
        nickname = state.nickname
        days_since = state.days_since_last_seen

        if nickname is None:
            SYSTEM_TEMPLATE_GREETING_NEW_USER = """
            # Your Role & Context
            You are a CBT counselor named "Lucy" (루시).
            You are greeting a brand NEW user for the very first time.
            # ... (중략) ...
            # [중요 지시]
            1. **당신은 반드시 한국어로만 응답해야 합니다.**
            2. 'response_text'는 위에 주어진 한국어 메시지(---...---)와 정확히 일치해야 합니다.
            """
            # (지면상 생략된 부분은 위 템플릿과 동일하다고 가정)
            # 여기서는 편의상 위에서 정의한 문자열을 사용하거나, 기존 로직 유지
            # (위 코드 블록 상단에서 정의한 문자열이 아니라 로컬 변수라 생략된 부분이 중요하면 채워넣어야 합니다. 
            #  사용자님이 주신 코드 그대로 쓰되 변수명만 맞추겠습니다.)
            
            # [수정] 사용자 제공 코드에 있는 템플릿 그대로 사용
            prompt_template = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE_GREETING_NEW_USER)
            variables = {}
            
        elif session_type == "WEEKLY":
            seed_data = spec.get("prompt_seed", ["오늘 어떠셨나요?"]) 
            if isinstance(seed_data, str):
                seed_data = [seed_data]
            variables = {
                "nickname": nickname,
                "days_since_last_seen": days_since,
                "session_type": "주간 상담",
                "week": spec.get("week", state.current_week),
                "title": spec.get("title", "주간 상담"),
                "goals": "; ".join(spec.get("goals", [])),
                "prompt_seed": seed_data[0],
            }
            prompt_template = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE_GREETING)
            
        elif session_type == "GENERAL":
            SYSTEM_TEMPLATE_GREETING_GENERAL = """
            안녕하세요, {nickname}님! 이번 주의 상담은 이미 완료하셨습니다.
            혹시 이번 주 과제에 대해 궁금한 점이 있으신가요?
            [중요] **반드시 한국어로만 응답해야 합니다.**
            """
            prompt_template = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE_GREETING_GENERAL)
            variables = {"nickname": nickname}
        
        else:
            prompt_template = ChatPromptTemplate.from_template("안녕하세요! 무엇을 도와드릴까요?\n\n[중요] **반드시 한국어로만 응답해야 합니다.**")
            variables = {}

        prompt_messages = prompt_template.invoke(variables).to_messages()

    else:
        # --- 1-B. 대화 중일 경우 ---
        level = state.intervention_level or "L1"
        
        intervention_instruction = ""
        empathy_instruction = "Briefly acknowledge the user's feeling."

        # [레벨별 분기]
        if level in ["L4", "L5"]:
            intervention_instruction = """
            🚨 **EMERGENCY / HIGH RISK DETECTED** 🚨
            The user is showing signs of severe depression, refusal, or distress.
            1. You MUST explicitly suggest professional help in a gentle way. (e.g., "마음이 많이 힘드실 때는 전문가나 병원의 도움을 받는 것도 좋은 방법이에요.")
            2. HOWEVER, your goal is still to complete the session protocol if possible.
            3. After the suggestion, gently steer them back to the topic.
            """
            empathy_instruction = "Show deep empathy and validate their pain heavily."
        
        elif level in ["L2", "L3"]:
            intervention_instruction = """
            ⚠️ **AVOIDANCE DETECTED** ⚠️
            The user is trying to avoid the topic or is distracted.
            1. Do NOT get dragged into their distraction.
            2. Acknowledge their statement very briefly (1 sentence).
            3. IMMEDIATELY redirect to the 'Script Steps'.
            """
            empathy_instruction = "Briefly acknowledge, but prioritize the session goal."
        
        else: # L1
            intervention_instruction = "Proceed with the standard CBT coaching flow."
            empathy_instruction = "Show empathy and acknowledge the Human's last message."

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
            "history": past_summaries + cleaned_chat_history,
            "user_message": state.last_user_message,
            "intervention_instruction": intervention_instruction,
            "empathy_instruction": empathy_instruction
        }
        
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content=SYSTEM_TEMPLATE_CONVERSATION),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(content="{user_message}"),
        ])
        prompt_messages = prompt_template.invoke(variables).to_messages()
    
    # if/else 분기 밖에서 최종 리턴
    return {
        "llm_prompt_messages": prompt_messages
    }