# app/graph/weekly/build.py
from langgraph.graph import StateGraph, START, END
from coach_agent.graph.state import State
from coach_agent.graph.weekly.offtopic import handle_offtopic
from coach_agent.graph.weekly.greeting_nodes import greeting
from coach_agent.graph.weekly.counsel_nodes import llm_technique_selector, llm_technique_applier, counsel_prepare
from coach_agent.graph.weekly.exit_nodes import exit_node
from coach_agent.graph.weekly.extra_nodes import should_end_session, init_weekly_state, route_phase_node
from coach_agent.graph.weekly.router import route_phase, route_exit, after_offtopic_router

def build_weekly_subgraph():
    builder = StateGraph(State)

    # ======= nodes ========
    builder.add_node("Init", init_weekly_state)
    builder.add_node("HandleOffTopic", handle_offtopic)
    builder.add_node("RoutePhase", route_phase_node)
    builder.add_node("ShouldEndSession", should_end_session)
    builder.add_node("Greeting", greeting)
    builder.add_node("CounselPrepare", counsel_prepare)
    builder.add_node("TechniqueSelector", llm_technique_selector)
    builder.add_node("TechniqueApplier", llm_technique_applier)
    builder.add_node("Exit", exit_node)

    # ====== edges =======
    builder.add_edge(START, "Init")
    builder.add_edge("Init","HandleOffTopic")
    builder.add_conditional_edges(
        "HandleOffTopic",
        after_offtopic_router,
        {
            "RoutePhase": "RoutePhase",
            "__end__": END
        }
    )
    builder.add_conditional_edges(
        "RoutePhase",
        route_phase,
        {
            "GREETING": "Greeting",
            "COUNSEL": "CounselPrepare",
            "EXIT": "Exit"
        }
    )
    builder.add_edge("CounselPrepare","TechniqueSelector")
    builder.add_edge("TechniqueSelector", "TechniqueApplier")
    builder.add_edge("TechniqueApplier", "ShouldEndSession")
    builder.add_conditional_edges(
        "ShouldEndSession",
        route_exit,
        {
            "CONTINUE": END,
            "EXIT": "Exit"
        }
        
    )
    builder.add_edge("Greeting", END)
    builder.add_edge("Exit", END)

    # ===== compile =======
    app = builder.compile()
    return app
