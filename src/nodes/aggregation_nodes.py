"""Aggregation and output nodes for the LangGraph workflow."""

from typing import Dict, Optional
from models.state import DestinationCompassState
from services.llm import LLMService
from config_loader import config


# Initialize services
llm_service = LLMService()


def format_output(
    location: Optional[dict],
    weather: Optional[dict],
    time: Optional[str],
    news: Optional[list[str]],
    events: Optional[list[dict]],
) -> str:
    """Format output as a simple string (fallback when LLM is not available).
    
    Args:
        location: Structured location data
        weather: Weather data
        time: Local time string
        news: List of news headlines
        events: List of event dictionaries
        
    Returns:
        str: Formatted output string
    """
    city = (location or {}).get("city") if isinstance(location, dict) else None
    country = (location or {}).get("country") if isinstance(location, dict) else None
    default_city = config.get_default("location")
    default_country = config.get_default("country")
    
    return (
        f"Location: {city or default_city},{country or default_country}\n"
        f"Local time: {time or 'N/A'}\n"
        f"Weather: {(weather or {}).get('summary', 'N/A')}\n"
        f"News: {'\n'.join(news or [])}\n"
        f"Events: {events or []}"
    )


def aggregate_results(state: DestinationCompassState) -> Dict:
    """Generate a comprehensive markdown report using LLM with all destination information.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict: Updated state with final_output
    """
    # Get all the data from state
    location = state.get("structured_location")
    weather = state.get("weather")
    local_time = state.get("local_time")
    news = state.get("news_headlines")
    events = state.get("events")
    
    # Prepare context for LLM
    context_parts = []
    
    # Location info
    if location and isinstance(location, dict):
        city = location.get("city", "Unknown")
        country = location.get("country", "Unknown")
        context_parts.append(f"Location: {city}, {country}")
    
    # Weather info
    if weather and isinstance(weather, dict):
        summary = weather.get("summary", "N/A")
        temp = weather.get("temperature_c")
        feels_like = weather.get("feels_like_c")
        humidity = weather.get("humidity")
        wind_speed = weather.get("wind_speed")
        
        weather_info = f"Weather: {summary}"
        if temp is not None:
            weather_info += f", {temp}°C"
        if feels_like is not None:
            weather_info += f" (feels like {feels_like}°C)"
        if humidity is not None:
            weather_info += f", Humidity: {humidity}%"
        if wind_speed is not None:
            weather_info += f", Wind: {wind_speed} m/s"
        context_parts.append(weather_info)
    
    # Time info
    if local_time:
        context_parts.append(f"Local time: {local_time}")
    
    # News info
    if news and len(news) > 0:
        news_list = "\n".join([f"- {headline}" for headline in news])
        context_parts.append(f"Recent news:\n{news_list}")
    
    # Events info
    if events and len(events) > 0:
        events_list = []
        for event in events:
            title = event.get("title", "Untitled Event")
            date = event.get("date", "TBD")
            venue = event.get("venue", "TBD")
            description = event.get("description", "")
            url = event.get("url", "")
            
            event_str = f"- **{title}**"
            if date != "TBD":
                event_str += f" - {date}"
            if venue != "TBD":
                event_str += f" at {venue}"
            if description:
                event_str += f"\n  {description}"
            if url:
                event_str += f"\n  [More info]({url})"
            
            events_list.append(event_str)
        
        context_parts.append(f"Upcoming events:\n" + "\n".join(events_list))
    
    context = "\n\n".join(context_parts)
    
    try:
        # Try to generate report using LLM
        final_output = llm_service.generate_report(context)
        return {"final_output": final_output}
    except Exception as e:
        print(f"LLM aggregation error: {e}")
        # Fallback to simple formatting
        output = format_output(location, weather, local_time, news, events)
        return {"final_output": output}
