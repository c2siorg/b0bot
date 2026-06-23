from langgraph.graph import StateGraph, END
from agents.state import PlannerState
from agents.planner import planner_agent
from agents.scraper import scraper_agent
from agents.analyzer import analyzer_agent
from agents.responder import responder_agent
from agents.notification import notification_agent

def _route_after_planner(state: PlannerState) -> str:
    if state.get("intent") == "subscribe":
        return "notification"
    return "scraper"

def build_graph():
    graph = StateGraph(PlannerState)

    graph.add_node("planner", planner_agent)
    graph.add_node("scraper", scraper_agent)
    graph.add_node("analyzer", analyzer_agent)
    graph.add_node("responder", responder_agent)
    graph.add_node("notification", notification_agent)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", _route_after_planner, {
        "scraper": "scraper",
        "notification": "notification",
    })
    graph.add_edge("scraper", "analyzer")
    graph.add_edge("analyzer", "responder")
    graph.add_edge("notification", "responder")
    graph.add_edge("responder", END)

    return graph.compile()

agent_graph = build_graph()
