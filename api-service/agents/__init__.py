from langgraph.graph import StateGraph, END
from agents.state import PlannerState
from agents.planner import planner_agent
from agents.scraper import scraper_agent
from agents.responder import responder_agent

def build_graph():
    graph = StateGraph(PlannerState)

    graph.add_node("planner", planner_agent)
    graph.add_node("scraper", scraper_agent)
    graph.add_node("responder", responder_agent)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "scraper")
    graph.add_edge("scraper", "responder")
    graph.add_edge("responder", END)

    return graph.compile()

agent_graph = build_graph()
