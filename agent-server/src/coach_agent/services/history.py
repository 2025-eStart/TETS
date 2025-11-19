# coach_agent/services/history.py
from services import REPO
from langchain_core.messages import BaseMessage

def persist_turn(user_id: str, week: int, messages: list[BaseMessage], session_type: str):
    """
    가장 최근의 대화 턴(User -> AI)을 DB에 영구 저장합니다.
    """
    if len(messages) < 2:
        return

    last_human = messages[-2]
    last_ai = messages[-1]
    
    if last_human.type == "human" and last_ai.type == "ai":
        # User 메시지 저장
        REPO.save_message(
            user_id, 
            session_type, 
            week, 
            "user", 
            last_human.content
        )
        
        # Assistant 메시지 저장
        REPO.save_message(
            user_id, 
            session_type, 
            week, 
            "assistant", 
            last_ai.content
        )