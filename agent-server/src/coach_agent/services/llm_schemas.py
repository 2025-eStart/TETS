# coach_agent/services/llm_schemas.py

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


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

    progress_delta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="이번 턴으로 인해 session_progress에 반영해야 할 변화 정보."
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
