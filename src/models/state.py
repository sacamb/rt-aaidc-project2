"""State models for Destination Compass."""

from typing import TypedDict, List, Dict, Any, Optional


class DestinationCompassState(TypedDict):
    """State model for the Destination Compass workflow.
    
    This defines the structure of data that flows through the LangGraph workflow.
    Each node can read from and write to this shared state.
    """
    user_query: str
    location_string: str | None
    structured_location: dict | None
    local_time: str | None
    weather: dict | None
    news_headlines: list[str] | None
    events: list[dict] | None
    final_output: str | None
    messages: list[str] | None
