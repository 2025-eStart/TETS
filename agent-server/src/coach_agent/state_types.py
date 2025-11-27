# coach_agent/state_types.py
from typing import Optional, List, Annotated, Dict, Any, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

SessionType = Literal["WEEKLY", "GENERAL"]

class State(BaseModel):
    # --- 1. 핵심 세션 상태 (Config + Checkpointer) ---
    
    messages: Annotated[List[BaseMessage], add_messages] = [] # Checkpointer가 자동으로 관리할 '영구' 대화 기록 (가장 중요)
    user_id: Optional[str] = None # load_state에서 Config로부터 주입
    
    # load_state에서 런타임에 주입
    # utcnow() 대신 권장되는 방식 사용
    now_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # --- 2. 비즈니스 로직 상태 (REPO에서 로드) ---
    user: Dict[str, Any] = Field(default_factory=dict)
    current_week: int = 1
    session_type: SessionType = "WEEKLY"
    weekly_session: Optional[Dict[str, Any]] = None
    protocol: Dict[str, Any] = Field(default_factory=dict)
    current_step_index: int = 0 # 현재 진행 중인 스텝의 인덱스 (기본값 0)
    
    # --- 3. 인사말 생성용 데이터 ---
    nickname: Optional[str] = None  # LoadState가 user 객체에서 로드
    days_since_last_seen: int = 0 # LoadState가 user.last_seen_at과 now_utc로 계산
    
    next_route: Optional[str] = None # RouteSession이 결정한 '다음 목적지'를 저장할 임시 필드

    # --- 4. 개입/분석 상태 (노드에서 계산) ---
    metrics: Dict[str, Any] = Field(default_factory=dict)
    intervention_level: Optional[str] = None  # "L1".."L5"

    # --- 5. 턴(Turn) 단위 임시 상태 (메모리만 사용) ---
    last_user_message: Optional[str] = None # load_state가 messages에서 추출하여 저장
    llm_prompt_messages: List[BaseMessage] = Field(default_factory=list) # build_prompt -> run_llm 전달용 임시 프롬프트
    llm_output: Optional[str] = None # run_llm -> summarize_update 전달용 임시 출력

    # --- 6. 제어 플래그 ---
    exit: bool = False
    expired: bool = False

# LLM 구조화된 출력을 위한 Pydantic 스키마
class CounselorTurn(BaseModel):
    """LLM이 생성하는 답변과 세션 상태 평가를 포함하는 구조"""
    response_text: str = Field(
        description="사용자에게 전달할 실제 상담 메시지."
    )
    current_step_index: int = Field(    # 현재 진행 중인 단계의 인덱스 (0, 1, 2...)
        default=0,
        description="""
        [Step Navigation Decision]
        제공된 [Script Steps] 전체 목록을 검토하고, 다음에 수행해야 할 단계의 번호(Index)를 결정하세요.
        
        1. 기본적으로는 현재 단계가 완료되면 '다음 단계(current + 1)'를 선택합니다.
        2. ★ 중요: 만약 사용자의 답변이 '현재 단계'뿐만 아니라 '그 다음 단계'의 내용까지 모두 포함하고 있다면, 
           이미 완료된 단계들을 건너뛰고(Skip) '그다음 수행해야 할 단계'의 번호를 선택하세요.
           (예: 0번 질문을 했는데 사용자가 0번, 1번 내용을 다 말했다면 -> 2번 선택)
           
        3. [Leniency Policy (유연한 판단 기준)]:
           - 사용자의 답변을 너무 엄격하게 평가하지 마세요. (Do not be too strict.)
           - 사용자가 완벽한 문장이나 형식을 갖추지 않았더라도, **대화의 맥락상 의미가 통하고 핵심 키워드가 스치듯이라도 언급되었다면** 과감하게 통과(Pass)시키고 다음 단계로 넘어가세요.
           - 사용자를 지루하게 만들지 않는 것이 완벽한 정보 수집보다 중요합니다.

        4. 정말로 답변이 아예 없거나 동문서답을 할 때만 현재 단계(Index)를 유지하세요.
        """
    )
    session_goals_met: bool = Field(
        default=False,
        description="""
        대화 맥락과 사용자의 최근 답변을 바탕으로, 
        이번 주차의 핵심 목표(exit_criteria)가 '모두' 달성되었는지 여부. 
        (예: '사례 요약', '감정 기술', '과제 동의' 등이 완료되었는지)
        """
    )
    reasoning: str = Field(
        default="",
        description="session_goals_met을 True/False로 판단한 근거. 어떤 조건이 충족되었고 어떤 것이 부족한지 설명. 어떤 언어로 답변하든 내용이 충족되면 True로 판단할 것"
    )