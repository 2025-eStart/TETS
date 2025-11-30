# coach_agent/graph/main/build.py

from langgraph.graph import StateGraph, START, END
from coach_agent.graph.state import State
from coach_agent.graph.main.edge import init_session_type, route_session

def build_main_graph(weekly_app, general_app, checkpointer=None):
    """
    MainGraph (더미 버전)

    - State를 로드(checkpointer)한 뒤,
    - session_type을 초기화(init_session_type)하고,
    - route_session으로 WEEKLY/GENERAL 중 하나를 선택,
    - 해당 SubGraph를 한 턴 실행한다.
    """
    builder = StateGraph(State)

    # SubGraph를 노드처럼 등록
    builder.add_node("WeeklySubGraph", weekly_app)
    builder.add_node("GeneralSubGraph", general_app)

    # session_type 초기화 노드
    builder.add_node("InitSessionType", init_session_type)

    # 흐름: START → InitSessionType → RouteSession(conditional) → SubGraph → END
    builder.add_edge(START, "InitSessionType")

    # RouteSession을 별도 노드로 추가할 필요 없이,
    # add_conditional_edges에서 직접 함수 사용
    builder.add_conditional_edges(
        "InitSessionType",
        route_session,
        {
            "WEEKLY": "WeeklySubGraph",
            "GENERAL": "GeneralSubGraph",
        },
    )

    # SubGraph 실행 후 바로 END
    builder.add_edge("WeeklySubGraph", END)
    builder.add_edge("GeneralSubGraph", END)

    app = builder.compile(checkpointer=checkpointer)
    return app
