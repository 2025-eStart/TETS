# coach_agent/state.py

from typing import Any, Dict, List, Optional, Literal, Annotated
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

SessionType = Literal["WEEKLY", "GENERAL"]
WeeklyPhase = Literal["GREETING", "COUNSEL", "EXIT"]


class State(BaseModel):
    # 1-1. 공통: 대화 히스토리
    messages: Annotated[List[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="이 thread의 전체 메시지 기록. 항상 append-only."
    )

    # 1-2. 공통: 세션 타입 (thread 단위 label)
    session_type: Optional[SessionType] = Field(
        default=None,
        description=(
            "이 thread가 WEEKLY/GENERAL 중 어떤 세션 타입인지 나타내는 label. "
            "처음에는 None일 수 있고, MainGraph가 첫 턴에서 설정하며 "
            "그 이후에는 변경하지 않는다."
        ),
    )

    # 1-3. 공통: 사용자 식별자
    user_id: Optional[str] = Field(
        default=None,
        description="이 thread와 연결된 사용자의 고유 식별자."
    )
    user_nickname: Optional[str] = Field(
        default=None,
        description="사용자 닉네임. 인사말 생성 등에 사용."
    )

    current_week: int = Field(
        default=1,
        description="주간 상담 프로토콜의 기준이 되는 현재 주차. weekly thread 시작 시 결정, 이후 불변."
    )
    phase: WeeklyPhase = Field(
        default="GREETING",
        description="weekly 세션에서의 현재 phase (GREETING / COUNSEL / EXIT)."
    )
    weekly_turn_count: int = Field(
        default=0,
        description="이 weekly thread에서 WeeklySubGraph가 처리한 턴 수."
    )

    # --- 새 프로토콜 메타 반영 ---
    agenda: Optional[str] = Field(
        default=None,
        description="이번 주차의 핵심 주제/agenda 요약 문자열."
    )

    session_goal: Optional[str] = Field(
        default=None,
        description="이번 주차 세션의 상위 목표 ID 또는 설명."
    )
    core_task_tags: List[str] = Field(
        default_factory=list,
        description="이번 주차에서 집중할 core task를 나타내는 태그 리스트."
    )
    allowed_techniques: List[str] = Field(
        default_factory=list,
        description="이 세션에서 사용할 수 있는 CBT 기법 ID 목록."
    )
    blocked_techniques: List[str] = Field(
        default_factory=list,
        description="이번 주차에서 사용하지 않기로 한 CBT 기법 ID 목록."
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "세션 제약 조건. 예: {'min_turns': 4, "
            "'exit_policy': {...}} 등."
        ),
    )

    # 세션 진행 상태 (동적 진행도)
    turn_index: int = Field(
        default=0,
        description="이 thread에서 COUNSEL 턴이 몇 번째인지 나타내는 인덱스."
    )
    session_progress: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "세션 진행도/상태를 나타내는 동적 딕셔너리. "
            "예: {'turn_count': 3, 'identified_automatic_thought': True} 등."
        ),
    )
    technique_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "턴별로 사용된 기법 히스토리.\n"
            "예: [{'technique_id': 'socratic_questioning', 'micro_goal': '...', 'reasoning': '...'}, ...]"
        ),
    )

    # core task success 기준 (criterion별 정의 + 충족 여부)
    success_criteria: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "weekly success_criteria의 원본 정의 목록. "
            "예: [{'id': 'defined_budget_rule', 'required': True, ...}, ...]"
        ),
    )
    
    # core task success 기준 (criterion별 충족 여부)
    criteria_status: Dict[str, bool] = Field(
        default_factory=dict,
        description=(
            "weekly success_criteria의 각 criterion_id별 충족 여부. "
            "예: {'defined_budget_rule': True, 'agreed_access_reduction': False}"
        ),
    )
    
    # 룰베이스 개입 레벨 & 메트릭
    intervention_level: str = Field(
        default="L3_NORMAL",
        description="사용자 발화 분석을 통해 결정된 개입 단계 (L1~L5)"
    )
    input_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="completeness, avoidance, risk 등 룰베이스 분석 결과"
    )

    # 이번 턴용
    candidate_techniques: List[str] = Field(
        default_factory=list,
        description="counsel_prepare에서 이번 턴에 사용할 수 있다고 판단한 기법 ID 후보."
    )
    selected_technique_id: Optional[str] = Field(
        default=None,
        description="select_technique_llm에서 이번 턴에 최종 선택된 기법 ID."
    )
    selected_technique_meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="선택된 기법의 메타데이터 (intervention.yaml에서 로드한 내용 + LLM reason 등)."
    )
    micro_goal: Optional[str] = Field(
        default=None,
        description="이번 COUNSEL 턴에서 달성하고자 하는 구체적인 micro goal."
    )

    active_strategy: Optional[str] = Field(
        default=None,
        description=(
            "현재 세션에서 '지속적으로 활용 중인' 대표 CBT 전략 ID. "
            "보통 마지막 COUNSEL 턴의 selected_technique_id로 업데이트 가능."
        ),
    )

    # RAG 관련
    rag_queries: List[str] = Field(
        default_factory=list,
        description="이번 세션/턴에서 CBT/CBD RAG를 검색하기 위해 사용한 질의 문자열 리스트."
    )
    rag_snippets: List[str] = Field(
        default_factory=list,
        description="RAG에서 검색되어 LLM 프롬프트에 포함된 텍스트 스니펫들."
    )

    summary: str = Field(
        default="",
        description=(
            "지금까지의 상담 흐름을 bullet 포인트 형태로 요약한 텍스트.\n"
            "- 내담자의 핵심 고민\n"
            "- 이번 주차 목표 및 진행 상황\n"
            "- 사용된 주요 CBT 기법\n"
            "- 얻은 인사이트 / 앞으로의 행동 계획\n"
            "등을 3~6줄 bullet로 정리."
        ),
    )

    # LLM I/O
    llm_output: Optional[str] = Field(
        default=None,
        description="run_llm에서 생성된 LLM의 원시 응답 텍스트(상담 발화)."
    )

    # Homework (이번 주차 과제 정의 자체)
    homework: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "이번 주차 프로토콜에서 정의한 과제 정보. "
            "예: {'description': '...', 'examples': [...]}."
        ),
    )

    # 공통 제어 플래그
    exit: bool = Field(
        default=False,
        description=(
            "weekly 세션에서만 의미 있게 사용. "
            "ShouldEndSession 노드가 True로 설정하면, "
            "이번 주차 weekly COUNSEL 루프를 종료해야 함을 의미한다."
        ),
    )
    # context
    counsel_completed_at: Optional[datetime] = Field(
        default=None,
        description="COUNSEL phase가 완료된 UTC timestamp."
    )
    llm_suggest_end_session: bool = Field(
        default=False,
        description=(
            "마지막 COUNSEL 턴에서 LLM이 '이제 세션을 끝내도 되겠다'고 제안했는지 여부.\n"
            "should_end_session에서 require_llm_confirmation=True일 때 참고용."
        )
    )
    
    # General 상담용 필드
    general_turn_count: int | None  = 0     # General Q&A 턴 수