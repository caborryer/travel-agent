from typing import TypedDict, Optional, Annotated, List
from langgraph.graph import add_messages


class TravelPreferences(TypedDict):
    origin: Optional[str]
    budget: Optional[str]
    dates: Optional[str]
    duration: Optional[str]
    interests: list[str]
    travel_style: Optional[str]


Destination = dict


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    preferences: TravelPreferences
    search_queries: list[str]
    search_results: list[dict]
    raw_content: list[dict]
    destinations: list[Destination]
    language: str
    iteration: int
    response_message: str
