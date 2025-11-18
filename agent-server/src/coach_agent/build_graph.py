# coach_agent/graph/build_graph.py
from langgraph.graph import StateGraph, END
from state_types import State
from configuration import Configuration
from graph.load_state import load_state
from graph.route_session import route_session, cond_route_session
from graph.pick_week import pick_week
from graph.build_prompt import build_prompt
from graph.decide_intervention import decide_intervention
from graph.run_llm import run_llm
from graph.summarize_update import summarize_update
from graph.maybe_schedule_nudge import maybe_schedule_nudge


def build_graph(checkpointer=None):
    """
    LangGraph 빌더.
    - 엔트리 포인트: LoadState
    - 세션 라우팅: WEEKLY / DAILY / GENERAL (기본 __else__는 BuildPrompt)
    - 공통 꼬리: SummarizeUpdate -> MaybeScheduleNudge -> END
    - 체크포인터를 주입받아 상태 복구 가능
    """
    # checkpointer와 config_schema를 StateGraph에 등록
    g = StateGraph(
        State, 
        checkpointer=checkpointer,
        config_schema=Configuration
    )

    # 공통
    g.add_node("LoadState", load_state)
    g.add_node("RouteSession", route_session)
    g.add_edge("LoadState", "RouteSession")

    # Weekly 서브플로우(+ 공통 본문)
    g.add_node("PickWeek", pick_week)
    g.add_node("BuildPrompt", build_prompt)
    g.add_node("DecideIntervention", decide_intervention)
    g.add_node("RunLLM", run_llm)

    # Tail
    g.add_node("SummarizeUpdate", summarize_update)
    g.add_node("MaybeScheduleNudge", maybe_schedule_nudge)
    g.add_edge("SummarizeUpdate", "MaybeScheduleNudge")
    g.add_edge("MaybeScheduleNudge", END)

    # 세션 라우팅
    # cond_route_session은 "WEEKLY"|"GENERAL" 중 하나를 반환
    g.add_conditional_edges(
        "RouteSession",
        cond_route_session,
        {
            "WEEKLY": "PickWeek",
            "GENERAL": "DecideIntervention",
            "__else__": "DecideIntervention",
        },
    )

    # WEEKLY 흐름
    g.add_edge("PickWeek", "DecideIntervention")

    # 본문 공통 흐름
    g.add_edge("DecideIntervention", "BuildPrompt")
    g.add_edge("BuildPrompt", "RunLLM")
    
    # 그래프는 매 턴(invoke)마다 END에 도달, summarize_update에서 state.exit == True일 때만 요약 생성, 대화 종료.
    g.add_edge("RunLLM", "SummarizeUpdate")

    # ★ 엔트리 포인트 지정 (필수)
    g.set_entry_point("LoadState")

    return g.compile()
