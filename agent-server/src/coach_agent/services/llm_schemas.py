# coach_agent/services/llm_schemas.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CriterionEvaluation(BaseModel):
    """
    Weekly core_task.success_criteria 각각에 대한 충족 여부 평가.
    - LLM이 한 턴 기준으로 평가한 결과를 구조화해서 전달받기 위한 모델.
    """

    criterion_id: str = Field(
        description=(
            "protocol.success_criteria[*].id 값과 동일해야 하는 ID. "
            "예: 'picked_one_case', 'defined_budget_rule' 등."
        )
    )
    met: bool = Field(
        description=(
            "이번 턴까지의 대화 기준으로 "
            "이 criterion이 충족되었다고 판단하는지 여부."
        )
    )


class CounselorTurn(BaseModel):
    """
    Weekly COUNSEL 한 턴에서 LLM이 생성해야 하는 구조화된 출력.

    - response_text: 실제 사용자에게 보여줄 상담 멘트
    - selected_technique_id: 이번 턴에 적용한 CBT 기법 ID
    - reasoning: 왜 이 기법/질문을 선택했는지에 대한 설명
    - criteria_evaluations: success_criteria 충족 여부 평가
    - session_goals_met: LLM 관점에서 회기 목표 달성 여부
    - suggest_end_session: '이제 마무리해도 되겠다'는 LLM의 주관적 제안
    - progress_delta / metadata: 필요 시 session_progress 확장용
    """

    response_text: str = Field(
        description="이번 턴에 사용자에게 보내는 상담 메시지."
    )

    # --- 기법 선택 관련 ---
    selected_technique_id: Optional[str] = Field(
        default=None,
        description=(
            "이번 턴에서 적용한 CBT 기법의 ID. "
            "예: 'problem_solving_CBT', 'behavioral_activation', 'socratic_questioning' 등."
        ),
    )

    reasoning: str = Field(
        default="",
        description=(
            "이번 턴에서 선택된 기법/전략을 왜 적용했는지에 대한 설명.\n"
            "예: '사용자가 금전 관리 계획을 구체적으로 만들 준비가 되어 있어 "
            "'problem_solving_CBT를 사용해 단계별 계획 수립을 도왔다.'"
        )
    )

    # --- success_criteria 평가 ---
    criteria_evaluations: List[CriterionEvaluation] = Field(
        default_factory=list,
        description=(
            "protocol.success_criteria의 각 항목에 대해, "
            "현재까지의 대화 기준으로 충족 여부를 평가한 리스트."
        ),
    )

    # --- 회기 목표 / 종료 관련 ---
    session_goals_met: bool = Field(
        default=False,
        description=(
            "LLM 관점에서 이번 Weekly session의 session_goal이 "
            "'사실상 달성되었다'고 볼 수 있는지 여부. "
            "exit_policy와 함께 최종 종료 여부를 판단할 때 참고용."
        ),
    )

    suggest_end_session: bool = Field(
        default=False,
        description=(
            "LLM 입장에서 '이제 세션을 마무리해도 괜찮겠다'고 느끼는지 여부. "
            "이 값 하나만으로 종료하지 않고, "
            "exit_policy + criteria_status와 함께 검증한 뒤 종료한다."
        ),
    )

    # --- 선택: 추가 진행도/메타 정보 ---
    progress_delta: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "이번 턴을 통해 session_progress에 반영해야 할 변화 정보.\n"
            "예: {'identified_automatic_thought': True}\n"
            "꼭 필요하지는 않으며, 없으면 None."
        )
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "추가적인 참고 정보. 예: {'evidence_used': [...], 'note': '...'}\n"
            "프롬프트 설계 상황 또는 디버깅용."
        )
    )
