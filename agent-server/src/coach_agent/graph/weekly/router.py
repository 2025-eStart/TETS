# coach_agent/graph/weekly/router.py
from langgraph.graph import END
from coach_agent.graph.state import State


def after_offtopic_router(state: State) -> str:
    last = state.messages[-1] if state.messages else None
    if last and getattr(last, "type", "") == "ai":
        # HandleOffTopic에서 AIMessage를 생성한 경우 → 이 턴은 여기서 끝
        return END
    return "RoutePhase"

def route_phase(state: State) -> str:
    if state.phase == "GREETING":
        return "GREETING"
    if state.phase == "COUNSEL":
        return "COUNSEL"
    return "EXIT"

def route_exit(state: State) -> str:
    if state.phase == "EXIT":
        return "EXIT"
    else:
        return "CONTINUE"
    
    