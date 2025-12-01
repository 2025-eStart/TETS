# coach_agent/graph/general/build.py

from langgraph.graph import StateGraph, START, END

from coach_agent.graph.state import State
from coach_agent.graph.general.nodes import (
    init_general_state,
    general_greeting,
    prepare_general_answer,
    run_general_llm,
)
from coach_agent.graph.general.router import route_general


def build_general_subgraph():
    builder = StateGraph(State)

    # ====== Nodes ======
    builder.add_node("Init", init_general_state)
    builder.add_node("Greeting", general_greeting)
    builder.add_node("PrepareQA", prepare_general_answer)
    builder.add_node("RunLLM", run_general_llm)

    # ====== Edges ======
    builder.add_edge(START, "Init")

    # Init 이후 분기: 안내 멘트 vs Q&A
    builder.add_conditional_edges(
        "Init",
        route_general,
        {
            "GREETING": "Greeting",
            "QA": "PrepareQA",
        },
    )

    # 안내 멘트는 한 번 보여주고 바로 END → 다음 턴에 사용자 질문
    builder.add_edge("Greeting", END)

    # Q&A 흐름: 프롬프트 준비 → LLM→ END
    builder.add_edge("PrepareQA", "RunLLM")
    builder.add_edge("RunLLM", END)

    return builder.compile()
