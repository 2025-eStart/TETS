# coach_agent/graph/weekly/offtopic.py
from __future__ import annotations
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from coach_agent.graph.state import State
from coach_agent.services.llm import CHAT_LLM


def _extract_last_user_text(messages: list[BaseMessage]) -> Optional[str]:
    """
    messages 리스트에서 마지막 Human(사용자) 메시지의 텍스트만 뽑는다.
    - 없으면 None
    """
    if not messages:
        return None

    # 뒤에서부터 훑어서 human 찾기
    for msg in reversed(messages):
        msg_type = getattr(msg, "type", None)
        if msg_type == "human":
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                return content
            # content가 list 구조일 수 있을 때 안전 처리
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                if parts:
                    return "\n".join(parts)
    return None


def _is_offtopic_for_weekly(state: State, user_text: str) -> bool:
    """
    LLM을 이용해 '이번 발화가 weekly CBT-소비 상담 주제에서 벗어났는지' 판단.

    반환:
        True  → OFF_TOPIC (이번 턴은 HandleOffTopic에서 처리하고 종료)
        False → ON_TOPIC (그냥 다음 노드로 넘김)
    """
    # weekly 아젠다/goal 정보를 컨텍스트로 같이 넘겨서 좀 더 정교하게 판단
    agenda = state.agenda or ""
    session_goal = state.session_goal or ""
    core_tags = ", ".join(state.core_task_tags or [])

    system_prompt = (
        "너는 CBT 기반 '소비 습관 교정' 챗봇의 필터 역할을 하는 분류기야.\n"
        "지금 들어온 사용자의 발화가 **이번 주차 소비/돈/쇼핑/지출 관련 CBT 상담 주제**와 "
        "충분히 관련이 있는지 판단해야 한다.\n\n"
        "아래 기준을 사용해:\n"
        "1) 소비, 돈, 지출, 쇼핑, 예산, 카드값, 소비 후 감정(죄책감/후회 등), "
        "   충동구매, 습관적 소비와 직접적으로 연결되면 → ON_TOPIC\n"
        "2) 상담 챗봇 자체에 대한 질문, 앱/기술 질문, 전혀 다른 고민(연애, 가족, 학업 등)만 이야기하면 → OFF_TOPIC\n"
        "3) 소비 이야기가 섞여 있더라도, 거의 전부가 다른 주제(예: 인생 전체 고민, 정치, 시사 등)이면 → OFF_TOPIC\n\n"
        "반드시 다음 중 하나만 답해:\n"
        "- ON_TOPIC\n"
        "- OFF_TOPIC\n"
    )

    human_prompt = (
        f"이번 주차 아젠다: {agenda}\n"
        f"세션 목표: {session_goal}\n"
        f"core_task_tags: {core_tags}\n\n"
        f"사용자 발화:\n```{user_text}```\n\n"
        "위 기준에 따라 이 발화가 이번 '소비 CBT 주간 상담'과 관련이 있으면 'ON_TOPIC', "
        "관련이 거의 없으면 'OFF_TOPIC'만 정확히 한 줄로 출력해."
    )

    res = CHAT_LLM.invoke(
        [SystemMessage(content=system_prompt),
         HumanMessage(content=human_prompt)]
    )
    decision = (res.content or "").strip().upper()
    return decision.startswith("OFF")  # 'OFF_TOPIC', 'OFF-TOPIC' 등 방어적 처리
    # 필요하면 여기서 로그도 찍어도 됨.


def handle_offtopic(state: State) -> Dict[str, Any]:
    """
    Main Graph용 HandleOffTopic 노드.

    역할:
      - WEEKLY 세션일 때, 이번 유저 발화가 '소비 CBT 주간 상담' 주제에서 크게 벗어났는지 판별.
      - ON_TOPIC  → {} 리턴 (아무것도 안 함, 다음 라우터로 진행)
      - OFF_TOPIC → 짧은 안내/리다이렉션 메시지를 보내고 이번 턴 종료.
                    (그래프 상에서는 이 노드 뒤에서 __end__ 로 분기시키면 됨)
    """

    # WEEKLY가 아니면 아무 것도 하지 않음
    if state.session_type != "WEEKLY":
        return {}

    last_user_text = _extract_last_user_text(state.messages)
    if not last_user_text:
        # 유저 발화가 없으면 할 수 있는 게 없음 → 그냥 패스
        return {}

    # LLM으로 오프토픽 여부 판별
    is_offtopic = _is_offtopic_for_weekly(state, last_user_text)

    if not is_offtopic:
        # 주제 안에 있으면 아무 것도 하지 않고 다음 노드로 넘김
        print("[HandleOffTopic] ON_TOPIC → route_phase로 진행")
        return {}

    # 여기까지 왔으면 OFF_TOPIC
    print("[HandleOffTopic] OFF_TOPIC 감지 → 안내 메시지 후 턴 종료")

    week = state.current_week
    agenda = state.agenda or f"{week}주차 상담"

    reply = (
        f"이번 대화는 원래 **{week}주차 주간 상담**이고, 주제는 "
        f"'{agenda}' 에요.\n\n"
        "지금 이야기해준 내용도 중요한 고민이지만, 이 세션에서는 "
        "**소비 습관, 돈/지출, 쇼핑, 충동구매**에 대한 이야기를 중심으로 다루고 있어요.\n\n"
        "만약 지금은 소비/지출 이야기를 이어가고 싶지 않다면,\n"
        "• 이 대화는 여기까지만 진행하고,\n"
        "• 상단에서 **자유 상담(FAQ/일반 상담)** 세션을 새로 열어서 아무 이야기나 편하게 나눌 수도 있어요.\n\n"
        "주간 상담을 계속하고 싶다면, 최근에 있었던 소비 상황이나 돈 때문에 신경 쓰였던 순간을\n"
        "하나만 골라서 다시 이야기해 줄 수 있을까요?"
    )

    ai_msg = AIMessage(content=reply)

    return {
        "messages": [ai_msg],
    }