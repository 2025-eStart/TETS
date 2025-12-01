# coach_agent/services/history.py
from typing import Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from coach_agent.services import REPO

def _to_text(content: Any) -> str:
    """BaseMessage.content를 안전하게 str로 변환."""
    # OpenAI-style: [{"type": "text", "text": "..."}]
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return item.get("text", "")
        return ""
    if isinstance(content, str):
        return content
    return str(content)


def persist_turn(
    user_id: str,
    week: int,
    messages: List[BaseMessage],
    session_type: str,
) -> None:
    """
    가장 최근의 대화 턴(User -> AI)을 DB에 영구 저장합니다.
    - user / assistant 각각 한 메시지씩.
    - WEEKLY / GENERAL 공통.
    """
    if len(messages) < 2:
        return

    last_human = messages[-2]
    last_ai = messages[-1]

    if isinstance(last_human, HumanMessage) and isinstance(last_ai, AIMessage):
        # User 메시지 저장
        REPO.save_message(
            user_id,
            session_type,
            week,
            "user",
            _to_text(last_human.content),
        )

        # Assistant 메시지 저장
        REPO.save_message(
            user_id,
            session_type,
            week,
            "assistant",
            _to_text(last_ai.content),
        )
    # else:
    #     print(
    #         f"[persist_turn] 마지막 두 메시지가 Human/AI가 아님: "
    #         f"{type(last_human)}, {type(last_ai)}"
    #     )
