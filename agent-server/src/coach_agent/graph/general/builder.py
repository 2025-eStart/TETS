# coach_agent/graph/general/builder.py

from langgraph.graph import StateGraph, START, END

from coach_agent.graph.state import State
from coach_agent.graph.general.nodes import (
    init_general_state,
    generate_general_answer,
)


def build_general_subgraph():
    builder = StateGraph(State)

    # ====== Nodes ======
    builder.add_node("Init", init_general_state)
    builder.add_node("GenerateAnswer", generate_general_answer)

    # ====== Edges ======
    builder.add_edge(START, "Init")
    builder.add_edge("Init", "GenerateAnswer")
    builder.add_edge("GenerateAnswer", END)

    return builder.compile()
