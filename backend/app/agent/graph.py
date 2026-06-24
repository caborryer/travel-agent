from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import AgentState
from app.agent.nodes import (
    collect_preferences,
    generate_queries,
    search_and_scrape,
    extract_and_rank,
    generate_response,
)


def build_agent() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("collect_preferences", collect_preferences)
    workflow.add_node("generate_queries", generate_queries)
    workflow.add_node("search_and_scrape", search_and_scrape)
    workflow.add_node("extract_and_rank", extract_and_rank)
    workflow.add_node("generate_response", generate_response)

    workflow.set_entry_point("collect_preferences")

    workflow.add_edge("collect_preferences", "generate_queries")
    workflow.add_edge("generate_queries", "search_and_scrape")
    workflow.add_edge("search_and_scrape", "extract_and_rank")
    workflow.add_edge("extract_and_rank", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile(checkpointer=MemorySaver())


agent = build_agent()


async def run_agent(user_message: str, session_id: str) -> AgentState:
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": user_message}],
        "preferences": {
            "origin": None,
            "budget": None,
            "dates": None,
            "duration": None,
            "interests": [],
            "travel_style": None,
        },
        "search_queries": [],
        "search_results": [],
        "raw_content": [],
        "destinations": [],
        "language": "en",
        "iteration": 0,
        "response_message": "",
    }

    result = await agent.ainvoke(initial_state, {"configurable": {"thread_id": session_id}})
    return result
