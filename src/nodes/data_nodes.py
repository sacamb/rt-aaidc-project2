"""Data collection nodes for the LangGraph workflow."""

from typing import Dict
from models.state import DestinationCompassState
from services.time import TimeService
from services.weather import WeatherService
from services.news import NewsService
from services.events import EventsService


# Initialize services
time_service = TimeService()
weather_service = WeatherService()
news_service = NewsService()
events_service = EventsService()


def get_local_time(state: DestinationCompassState) -> Dict:
    """Get local time for the location.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict: Updated state with local_time
    """
    current_time = time_service.get_local_time(state["structured_location"])
    print(f"current_time : {current_time}")
    return {"local_time": current_time}


def get_weather(state: DestinationCompassState) -> Dict:
    """Get weather data for the location.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict: Updated state with weather
    """
    weather = weather_service.get_weather(state["structured_location"])
    print(f"weather : {weather}")
    return {"weather": weather}


def get_news(state: DestinationCompassState) -> Dict:
    """Get news headlines for the location.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict: Updated state with news_headlines
    """
    headlines = news_service.get_news(state["structured_location"], state.get("local_time"))
    print(f"headlines : {headlines}")
    return {"news_headlines": headlines}


def get_events(state: DestinationCompassState) -> Dict:
    """Get local events for the location.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict: Updated state with events
    """
    events = events_service.get_events(
        state["structured_location"], 
        state.get("weather"), 
        state.get("local_time")
    )
    print(f"events : {events}")
    return {"events": events}
