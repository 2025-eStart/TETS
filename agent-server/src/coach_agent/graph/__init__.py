# coach_agent/graph/__init__.py

from coach_agent.graph.weekly.builder import build_weekly_subgraph
from coach_agent.graph.general.builder import build_general_subgraph
from coach_agent.graph.main.builder import build_main_graph
from coach_agent.services.checkpointer import firestore_checkpointer


# 1) 서브그래프들 먼저 컴파일
weekly_app = build_weekly_subgraph()
general_app = build_general_subgraph()

# 2) 메인 그래프를 checkpointer와 함께 컴파일
app = build_main_graph(
    weekly_app=weekly_app,
    general_app=general_app,
    checkpointer=firestore_checkpointer,
)

__all__ = ["app", "weekly_app", "general_app"]
