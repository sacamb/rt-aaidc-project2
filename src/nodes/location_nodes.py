"""Location-related nodes for the LangGraph workflow."""

from typing import Dict
from models.state import DestinationCompassState
from services.llm import LLMService
from services.geocoding import GeocodingService


# Initialize services
llm_service = LLMService()
geocoding_service = GeocodingService()


def parse_query(state: DestinationCompassState) -> Dict:
    """Parse user query; if it's not destination-related, answer directly.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict: Updated state with location_string
    """
    user_query = state["user_query"]

    # 1) Classify intent
    is_destination = llm_service.classify_destination_intent(user_query)
    if not is_destination:
        # Non-destination: answer directly and short-circuit the graph
        direct_answer = llm_service.general_chat(user_query)
        return {
            "final_output": direct_answer,
            "location_string": None,
            "messages": state.get("messages") or []
        }

    # 2) Destination-related: extract location and continue normal flow
    location = llm_service.extract_location(user_query)
    print(f"location : {location}")
    
    # clear the final_output from any previous non-destination related response
    return {"location_string": location, "final_output": "", "messages": state.get("messages") or []}


def geocode_location(state: DestinationCompassState) -> Dict:
    """Geocode location string to structured data.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict: Updated state with structured_location
    """
    results = geocoding_service.geocode(state["location_string"])
    print(f"geocode : {results}")
    return {"structured_location": results}
