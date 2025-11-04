from langgraph.graph import StateGraph, END
from app.state_types import State
from app.nodes.load_state import load_state
from app.nodes.route_session import route_session, cond_route_session
from app.nodes.pick_week import pick_week
from app.nodes.build_prompt import build_prompt
from app.nodes.decide_intervention import decide_intervention
from app.nodes.run_llm import run_llm
from app.nodes.check_exit_or_pause import check_exit_or_pause, cond_exit_or_loop
from app.nodes.summarize_update import summarize_update
from app.nodes.maybe_schedule_nudge import maybe_schedule_nudge

def build_graph():
    g = StateGraph(State)

    # 공통
    g.add_node("LoadState", load_state)
    g.add_node("RouteSession", route_session)
    g.add_edge("LoadState", "RouteSession")

    # Weekly subgraph
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

    # 라우팅
    g.add_conditional_edges(
        "RouteSession",
        cond_route_session,  # "WEEKLY"|"DAILY"|"GENERAL"
        {"WEEKLY": "PickWeek", "DAILY": "BuildPrompt", "GENERAL": "BuildPrompt"},
    )

    # Weekly 흐름
    g.add_edge("PickWeek", "BuildPrompt")
    g.add_edge("BuildPrompt", "DecideIntervention")
    g.add_edge("DecideIntervention", "RunLLM")
    g.add_edge("RunLLM", "CheckExitOrPause")
    g.add_conditional_edges(
        "CheckExitOrPause",
        cond_exit_or_loop,  # "TAIL"|"LOOP"
        {"TAIL": "SummarizeUpdate", "LOOP": "BuildPrompt"},
    )
    return g.compile()
