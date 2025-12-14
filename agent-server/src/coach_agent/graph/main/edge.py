# coach_agent/graph/main/edge.py
# main graph의 엣지 라우터 함수들

from __future__ import annotations
from typing import Literal
from coach_agent.graph.state import State
from coach_agent.services import REPO

SessionType = Literal["WEEKLY", "GENERAL"]

def route_session(state: State) -> str:
    """
    날짜 계산, week 롤백, 쿨다운 로직은 모두 FastAPI /session/init에서 처리.
    state.exit 여부와 session_type을 확인하여 경로를 결정.
    - ENDED: 이미 종료된 세션 (안내 메시지 노드로 이동)
    - WEEKLY / GENERAL: 정상 상담 진행
    """
    # 1) [Backend Defense] 이미 종료된 상태(exit=True)라면 그래프 실행 차단, 안내 메시지 출력
    if state.exit == True:
        print("   [RouteSession] ⛔ 세션 종료 상태(state.exit=True) 감지 -> ENDED 경로로 이동") # [DEBUG]
        return "ENDED"
    
    # 2) 종료 상태 아니면 정상 진행: session_type 확인, session_type에 따라 라우팅
    session_type = state.session_type or "GENERAL"  # 기본 GENERAL
    if session_type not in ("WEEKLY", "GENERAL"): session_type = "GENERAL"
    
    print(f"   [Maingraph Edge: RouteSession] 결정된 경로: {session_type}") # [DEBUG]
    return session_type
