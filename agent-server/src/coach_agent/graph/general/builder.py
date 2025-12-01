# app/graph/general.py
# general subgraph nodes, edges, builder for CBT Coach Agent (dummy version)

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from coach_agent.graph.state import State

def general_turn(state: State) -> dict:
    """General 모드 한 턴: 자유 상담 더미 응답."""
    content = (
        "소비나 감정에 대해 편하게 이야기해줘요. "
        "지금은 WEEKLY가 아닌 일반 상담 모드예요. (더미 응답)"
    )
    msg = AIMessage(content=content)

    # 여기서는 exit은 항상 False 유지
    return {
        "messages": [msg],
    }

def build_general_subgraph():
    """
    GeneralSubGraph (더미 버전)

    - 한 턴에 general_turn만 실행
    - exit은 항상 False.
    """
    builder = StateGraph(State)
    builder.add_node("GeneralTurn", general_turn)
    builder.add_edge(START, "GeneralTurn")
    builder.add_edge("GeneralTurn", END)

    app = builder.compile()
    return app
