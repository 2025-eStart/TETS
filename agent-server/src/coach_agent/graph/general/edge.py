# coach_agent/graph/general/edge.py

from typing import Literal
from coach_agent.graph.state import State

def route_general(state: State) -> Literal["GREETING", "QA"]:
    """
    GeneralSubGraph의 첫 분기:
      - 아직 안내 멘트를 한 번도 안 보냈으면 → GREETING
      - 이미 안내 멘트를 보냈으면 → QA (실제 질문에 답하기)
    """
    has_greeted = getattr(state, "general_has_greeted", None)
    if not has_greeted:
        return "GREETING"
    return "QA"
