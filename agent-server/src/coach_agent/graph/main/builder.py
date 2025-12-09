# coach_agent/graph/main/builder.py

from langgraph.graph import StateGraph, START, END
from coach_agent.graph.state import State
from coach_agent.graph.main.edge import route_session
from coach_agent.graph.main.load_state import load_state
from coach_agent.graph.main.persist_turn_node import persist_turn_node
from coach_agent.graph.main.update_progress import update_progress
from coach_agent.graph.main.load_protocol import load_protocol
from coach_agent.services.checkpointer import firestore_checkpointer
from coach_agent.graph.state import State

def build_main_graph(weekly_app, general_app, checkpointer=None):
    """
    MainGraph 

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
    builder.add_node("LoadState", load_state)
    builder.add_node("LoadProtocol", load_protocol)
    builder.add_node("PersistTurn", persist_turn_node)
    builder.add_node("UpdateProgress", update_progress)

    # 흐름: START → LoadState -> HandleOffTopic → RouteSession(conditional) → SubGraph → END
    builder.add_edge(START, "LoadState")
    builder.add_edge("LoadState", "LoadProtocol")
    
    builder.add_conditional_edges(
        "LoadProtocol",
        route_session,
        {
            "WEEKLY": "WeeklySubGraph",
            "GENERAL": "GeneralSubGraph",
        }
    )
    builder.add_edge("WeeklySubGraph", "UpdateProgress")
    builder.add_edge("GeneralSubGraph", "UpdateProgress")
    # persistTurn node 삭제 -> 저장은 FastAPI 서버에서
    # SubGraph 실행 후 바로 END
    builder.add_edge("UpdateProgress", END)

    # langgraph API (langgraph dev servver)로 테스트 시 사용자정의 checkpointer 사용 금지
    # app = builder.compile() 
    app = builder.compile(checkpointer=firestore_checkpointer)
    
    return app
