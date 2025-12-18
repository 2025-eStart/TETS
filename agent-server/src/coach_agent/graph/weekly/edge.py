# coach_agent/graph/weekly/edge.py
from langgraph.graph import END
from coach_agent.graph.state import State


def after_offtopic_router(state: State) -> str:
    last = state.messages[-1] if state.messages else None
    if last and getattr(last, "type", "") == "ai":
        # HandleOffTopic에서 AIMessage를 생성한 경우 → 이 턴은 여기서 끝
        return END
    return "RoutePhase"

def route_phase(state: State) -> str:
    # 1. 이미 phase가 COUNSEL이거나, 메시지 기록에 AI 메시지가 1개 이상 있다면
    ai_messages = [m for m in state.messages if m.type == "ai"]
    
    if state.phase == "COUNSEL" or len(ai_messages) > 0:
        return "COUNSEL"
    if state.phase == "GREETING":
        return "GREETING"
    return "EXIT"

def route_exit(state: State) -> str:
    if state.phase == "EXIT":
        return "EXIT"
    else:
        return "CONTINUE"
    
    