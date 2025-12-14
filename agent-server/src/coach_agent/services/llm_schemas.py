# coach_agent/services/llm_schemas.py

from typing import Optional, Literal, List
from pydantic import BaseModel, Field

class ProgressUpdate(BaseModel):
    
    # 예: 내담자의 통찰력 점수 (변화 없으면 None)
    insight_score: Optional[int] = Field(
        default=None, 
        description="내담자의 인사이트 수준 (1~10). 변화가 없으면 null."
    )
    
    # 예: 저항감 수준
    resistance_level: Optional[Literal["LOW", "MEDIUM", "HIGH"]] = Field(
        default=None,
        description="내담자의 저항 수준. 변화가 없으면 null."
    )
    
    # 예: 이번에 완료한 상담 단계
    completed_step: Optional[str] = Field(
        default=None,
        description="이번 턴에서 완료한 상담 단계 (예: 'identify_trigger'). 없으면 null."
    )
    
    # 예: 내담자가 언급한 핵심 키워드 추가
    add_keyword: Optional[str] = Field(
        default=None,
        description="내담자 프로필에 추가할 새로운 키워드."
    )

class CriterionEvaluation(BaseModel):
    criterion_id: str = Field(..., description="기준 ID (예: 'min_turns', 'insight_sufficient')")
    met: bool = Field(..., description="이번 턴까지 이 기준을 충족했는지 여부")
    reason: Optional[str] = Field(
        default=None,
        description="선택 사항: True/False 판단 근거"
    )

class CounselorTurn(BaseModel):
    response_text: str = Field(
        description="사용자에게 전달할 실제 상담 메시지."
    )

    reasoning: str = Field(
        default="",
        description=(
            "이번 턴에서 어떤 기법을 어떻게 적용했는지에 대한 설명.\n"
            "예: '사용자가 자동사고를 명확히 드러냈기 때문에 "
            "Socratic questioning을 사용해 근거 탐색을 유도함.'"
        )
    )

    progress_delta: Optional[ProgressUpdate] = Field(
        default=None,
        description="이번 턴으로 인해 session_progress에 반영해야 할 변화 정보."
    )
    
    criteria_evaluations: List[CriterionEvaluation] = Field(
        default_factory=list,
        description=(
            "이번 턴까지의 success_criteria 달성 여부 평가."
            "각 항목의 criterion_id는 state.success_criteria에 정의된 id 중 하나여야 한다."
        )       
    )    

    suggest_end_session: bool = Field(
        default=False,
        description="상담사가 보기에 세션 목표를 달성하여 종료해도 되는지 여부"
    )
    
    session_goals_met: bool = Field(
        default=False,
        description="세션 목표가 달성되었는지 여부"
    )




class TechniqueSelection(BaseModel):
    """
    '이번 턴에 어떤 CBT 기법을 쓸지 + micro-goal은 뭔지'를
    LLM이 결정해서 돌려줄 때의 구조화 출력 스키마.
    """

    technique_id: str = Field(
        description="선택된 CBT 기법의 ID (intervention.yaml에 정의된 id와 동일)."
    )

    micro_goal: str = Field(
        description=(
            "이번 턴에서 그 기법으로 달성하고자 하는 구체적인 목표.\n"
            "예: '이번 턴 안에 대표 사례 1개에 대한 자동사고 문장을 명확히 말하게 하기'"
        )
    )

    reason: str = Field(
        default="",
        description=(
            "왜 이 기법과 micro-goal이 현재 상황에 적합하다고 판단했는지에 대한 설명."
        )
    )
