# app/graph/build_graph.py
from langgraph.graph import StateGraph, END
from app.state_types import State
from app.graph.load_state import load_state
from app.graph.route_session import route_session, cond_route_session
from app.graph.pick_week import pick_week
from app.graph.build_prompt import build_prompt
from app.graph.decide_intervention import decide_intervention
from app.graph.run_llm import run_llm
from app.graph.check_exit_or_pause import check_exit_or_pause, cond_exit_or_loop
from app.graph.summarize_update import summarize_update
from app.graph.maybe_schedule_nudge import maybe_schedule_nudge


def build_graph(checkpointer=None):
    """
    LangGraph 빌더.
    - 엔트리 포인트: LoadState
    - 세션 라우팅: WEEKLY / DAILY / GENERAL (기본 __else__는 BuildPrompt)
    - 공통 꼬리: SummarizeUpdate -> MaybeScheduleNudge -> END
    - 체크포인터를 주입받아 상태 복구 가능
    """
    g = StateGraph(State, checkpointer=checkpointer)

    # 공통
    g.add_node("LoadState", load_state)
    g.add_node("RouteSession", route_session)
    g.add_edge("LoadState", "RouteSession")

    # Weekly 서브플로우(+ 공통 본문)
    g.add_node("PickWeek", pick_week)
    g.add_node("BuildPrompt", build_prompt)
    g.add_node("DecideIntervention", decide_intervention)
    g.add_node("RunLLM", run_llm)
    g.add_node("CheckExitOrPause", check_exit_or_pause)

    # Tail
    g.add_node("SummarizeUpdate", summarize_update)
    g.add_node("MaybeScheduleNudge", maybe_schedule_nudge)
    g.add_edge("SummarizeUpdate", "MaybeScheduleNudge")
    g.add_edge("MaybeScheduleNudge", END)

    # 세션 라우팅
    # cond_route_session은 "WEEKLY"|"DAILY"|"GENERAL" 중 하나를 반환
    # 혹시 모를 값에 대비하여 __else__를 BuildPrompt로 안전 처리
    g.add_conditional_edges(
        "RouteSession",
        cond_route_session,
        {
            "WEEKLY": "PickWeek",
            "DAILY": "BuildPrompt",
            "GENERAL": "BuildPrompt",
            "__else__": "BuildPrompt",
        },
    )

    # WEEKLY 흐름
    g.add_edge("PickWeek", "BuildPrompt")

    # 본문 공통 흐름
    g.add_edge("BuildPrompt", "DecideIntervention")
    g.add_edge("DecideIntervention", "RunLLM")
    
    # 그래프는 매 턴(invoke)마다 END에 도달, summarize_update에서 state.exit == True일 때만 요약 생성, 대화 종료.
    g.add_edge("RunLLM", "SummarizeUpdate")

    # ★ 엔트리 포인트 지정 (필수)
    g.set_entry_point("LoadState")

    return g.compile()
