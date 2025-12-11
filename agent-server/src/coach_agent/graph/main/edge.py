# coach_agent/graph/main/edge.py
# main graph의 엣지 라우터 함수들

from __future__ import annotations
from typing import Literal
from coach_agent.graph.state import State

SessionType = Literal["WEEKLY", "GENERAL"]

def route_session(state: State) -> str:
    """
    날짜 계산, week 롤백, 쿨다운 로직은 모두 FastAPI /session/init에서 처리.
    """
    # 방어적 기본값
    session_type: SessionType = state.session_type or "GENERAL"  # 기본 GENERAL
    if session_type not in ("WEEKLY", "GENERAL"): session_type = "GENERAL"

    # session_type에 따라 라우팅
    print(f"   [Maingraph Edge: RouteSession] 결정된 경로: {session_type}") # [DEBUG]
    return session_type
