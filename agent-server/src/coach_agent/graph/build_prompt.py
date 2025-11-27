# coach_agent/graph/build_prompt.py
import yaml
from langchain_core.prompts import (
    ChatPromptTemplate, 
    HumanMessagePromptTemplate, 
    MessagesPlaceholder,
    SystemMessagePromptTemplate
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from coach_agent.state_types import State, CounselorTurn
from coach_agent.services import REPO
from coach_agent.prompts import (
    FIXED_NEW_USER_SCRIPT,
    TEMPLATE_GREETING_WEEKLY,
    TEMPLATE_GREETING_GENERAL,
    TEMPLATE_CONVERSATION
)

# --- 헬퍼 함수 ---

def _clean_message_content(msg: BaseMessage) -> BaseMessage:
    """메시지 컨텐츠가 리스트(멀티모달 등)일 경우 텍스트만 추출하여 단순화"""
    content = msg.content
    if isinstance(content, list):
        # 텍스트 타입의 내용만 추출
        text_content = next(
            (item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"), 
            ""
        )
        content = text_content
    
    # 문자열 보장
    content_str = str(content) if not isinstance(content, str) else content

    if msg.type == "human":
        return HumanMessage(content=content_str)
    elif msg.type == "ai":
        return AIMessage(content=content_str)
    elif msg.type == "system":
        return SystemMessage(content=content_str)
    else:
        msg.content = content_str
        return msg

def _load_past_summaries(user_id: str, current_week: int) -> list:
    """과거 주차 요약본을 가져와 AIMessage 형태로 변환"""
    summaries = REPO.get_past_summaries(user_id, current_week)
    return [
        AIMessage(content=f"--- 지난 {s['week']}주차 요약 ---\n{s['summary']}")
        for s in summaries
    ]

def _format_steps(raw_steps: list) -> str:
    """스텝 리스트를 번호가 매겨진 문자열로 변환"""
    return "\n".join([f"[{i}] {step}" for i, step in enumerate(raw_steps)])

# --- Main Function ---

def build_prompt(state: State) -> dict:
    spec = state.protocol
    session_type = state.session_type
    nickname = state.nickname

    # 1. 첫 턴(인사) 여부 확인
    if state.last_user_message is None:
        # [Case A] 첫 턴: 인사말 생성 모드
        
        # 1-1. 신규 사용자 (닉네임 없음)
        if nickname is None:
            manual_output = CounselorTurn(
                response_text=FIXED_NEW_USER_SCRIPT,
                session_goals_met=False,
                reasoning="신규 사용자 최초 진입. 닉네임 요청.",
                current_step_index=state.current_step_index or 0
            )
            # LLM 호출 없이 바로 결과를 반환 (수동 응답)
            return {
                "messages": [AIMessage(content=manual_output.response_text)],
                "session_goals_met": manual_output.session_goals_met,
                "reasoning": manual_output.reasoning, 
            }
            
        # 1-2. 기존 사용자: 세션 타입별 인사
        if session_type == "WEEKLY":
            template = TEMPLATE_GREETING_WEEKLY
            # prompt_seed가 문자열이면 리스트로 변환, 없으면 기본값
            seed_data = spec.get("prompt_seed", ["오늘 어떠셨나요?"])
            seed_text = seed_data[0] if isinstance(seed_data, list) else seed_data

            variables = {
                "nickname": nickname,
                "days_since_last_seen": state.days_since_last_seen,
                "session_type": "WEEKLY",
                "week": spec.get("week", state.current_week),
                "title": spec.get("title", "주간 상담"),
                "goals": "; ".join(spec.get("goals", [])),
                "prompt_seed": seed_text,
            }
            
        elif session_type == "GENERAL":
            template = TEMPLATE_GREETING_GENERAL
            variables = {"nickname": nickname}
        else:
            # Fallback
            template = "안녕하세요! 무엇을 도와드릴까요?\n\n[중요] **반드시 한국어로만 응답해야 합니다.**"
            variables = {}

        prompt_messages = ChatPromptTemplate.from_template(template).invoke(variables).to_messages()

    else:
        # [Case B] 대화 중 (Conversation Loop)
        
        # 1. 개입 레벨 설정
        level = state.intervention_level or "L1"
        intervention_instruction = "Proceed with the standard CBT coaching flow."
        empathy_instruction = "Show empathy and acknowledge the Human's last message."

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

        # 2. 스텝 및 인덱스 계산
        raw_steps = spec.get("script_steps", [])
        current_idx = state.current_step_index or 0
        
        # 인덱스 범위 보정 (IndexOutOfBounds 방지)
        if raw_steps:
            current_idx = min(current_idx, len(raw_steps) - 1)
            current_step_text = raw_steps[current_idx]
        else:
            current_step_text = "자유 대화"

        # 3. 프롬프트 변수 구성
        variables = {
            "week": spec.get("week", state.current_week),
            "title": spec.get("title", "Daily Check-in"),
            "goals": "; ".join(spec.get("goals", [])),
            
            # 스텝 네비게이션 정보
            "steps": _format_steps(raw_steps),
            "total_steps": len(raw_steps),
            "current_step_index": current_idx,
            "current_step_text": current_step_text,
            "next_step_index": current_idx + 1,
            "prev_step_index": max(0, current_idx - 1),
            
            "level": level,
            "exit_goals": yaml.dump(spec.get("exit_criteria", {}), allow_unicode=True),
            "user_message": state.last_user_message,
            "intervention_instruction": intervention_instruction,
            "empathy_instruction": empathy_instruction,
            "nickname": nickname or "여행자",
        }
        
        # 4. 히스토리 로드 및 결합
        cleaned_chat_history = [_clean_message_content(msg) for msg in state.messages]
        past_summaries = _load_past_summaries(state.user_id, state.current_week)
        
        # 5. 프롬프트 생성
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(TEMPLATE_CONVERSATION),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{user_message}"),
        ])
        
        # history 주입
        invoke_vars = variables.copy()
        invoke_vars["history"] = past_summaries + cleaned_chat_history
        
        prompt_messages = prompt_template.invoke(invoke_vars).to_messages()
    
    return {
        "llm_prompt_messages": prompt_messages
    }