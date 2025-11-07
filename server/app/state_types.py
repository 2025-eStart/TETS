# app/state_types.py
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

SessionType = Literal["WEEKLY", "DAILY", "GENERAL"]

class State(BaseModel):
    user_id: str
    now_utc: datetime
    session_type: SessionType = "WEEKLY"
    
    # API에서 받은 사용자 메시지
    last_user_message: Optional[str] = None

    user: Dict[str, Any] = {}
    weekly_session: Optional[Dict[str, Any]] = None
    daily_session: Optional[Dict[str, Any]] = None
    current_week: int = 1
    protocol: Dict[str, Any] = {}

    metrics: Dict[str, Any] = {}
    intervention_level: Optional[str] = None  # "L1".."L5"
    
    # LLM에 전달할 최종 메시지 리스트
    messages: List[BaseMessage] = []
    llm_output: Optional[str] = None

    exit: bool = False
    expired: bool = False

# [추가] LLM 구조화된 출력을 위한 Pydantic 스키마
class CounselorTurn(BaseModel):
    """LLM이 생성하는 답변과 세션 상태 평가를 포함하는 구조"""
    response_text: str = Field(
        description="사용자에게 전달할 실제 상담 메시지."
    )
    session_goals_met: bool = Field(
        description="""
        대화 맥락과 사용자의 최근 답변을 바탕으로, 
        이번 주차의 핵심 목표(exit_criteria)가 '모두' 달성되었는지 여부. 
        (예: '사례 요약', '감정 기술', '과제 동의' 등이 완료되었는지)
        """
    )
    reasoning: Optional[str] = Field(
        description="session_goals_met을 True/False로 판단한 근거 요약."
    )