# coach_agent/services/history.py
from services import REPO
from langchain_core.messages import BaseMessage

def persist_turn(user_id: str, week: int, messages: list[BaseMessage]):
    """
    가장 최근의 대화 턴(User -> AI)을 DB에 영구 저장합니다.
    """
    # 보통 마지막 2개(User 질문, AI 답변)만 저장하거나,
    # 아직 저장되지 않은 것을 찾아 저장하는 로직 구현
    if len(messages) < 2:
        return

    last_human = messages[-2]
    last_ai = messages[-1]
    
    # 안전장치: 순서 확인
    if last_human.type == "human" and last_ai.type == "ai":
        REPO.save_message(user_id, week, last_human.content, last_ai.content)
