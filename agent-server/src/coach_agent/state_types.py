# coach_agent/state_types.py
from typing import Optional, List, Annotated, Dict, Any, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

SessionType = Literal["WEEKLY", "GENERAL"]

class State(BaseModel):
    # --- 1. 핵심 세션 상태 (Config + Checkpointer) ---
    
    # Checkpointer가 자동으로 관리할 '영구' 대화 기록 (가장 중요)
    messages: Annotated[List[BaseMessage], add_messages] = []
    
    # load_state에서 Config로부터 주입
    user_id: Optional[str] = None
    
    # load_state에서 런타임에 주입
    # utcnow() 대신 권장되는 방식 사용
    now_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # --- 2. 비즈니스 로직 상태 (REPO에서 로드) ---
    user: Dict[str, Any] = Field(default_factory=dict)
    current_week: int = 1
    session_type: SessionType = "WEEKLY"
    weekly_session: Optional[Dict[str, Any]] = None
    protocol: Dict[str, Any] = Field(default_factory=dict)
    
    # --- 3. 인사말 생성용 데이터 ---
    # LoadState가 user 객체에서 로드
    nickname: Optional[str] = None 
    # LoadState가 user.last_seen_at과 now_utc로 계산
    days_since_last_seen: int = 0
    
    # RouteSession이 결정한 '다음 목적지'를 저장할 임시 필드
    next_route: Optional[str] = None

    # --- 4. 개입/분석 상태 (노드에서 계산) ---
    metrics: Dict[str, Any] = Field(default_factory=dict)
    intervention_level: Optional[str] = None  # "L1".."L5"

    # --- 5. 턴(Turn) 단위 임시 상태 (메모리만 사용) ---
    # load_state가 messages에서 추출하여 저장
    last_user_message: Optional[str] = None
    # build_prompt -> run_llm 전달용 임시 프롬프트
    llm_prompt_messages: List[BaseMessage] = Field(default_factory=list)
    # run_llm -> summarize_update 전달용 임시 출력
    llm_output: Optional[str] = None

    # --- 6. 제어 플래그 ---
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