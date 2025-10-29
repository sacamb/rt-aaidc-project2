from dotenv import load_dotenv
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import gradio as gr
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
import requests
from datetime import datetime, timezone
from config_loader import config


class DestinationCompassState(TypedDict):
    user_query: str
    location_string: str | None
    structured_location: dict | None
    local_time: str | None
    weather: dict | None
    news_headlines: list[str] | None
    events: list[dict] | None
    final_output: str | None
    messages: list[str] | None


def extract_location_from_query(user_query: str) -> str:
    """Extract location from user query using LLM"""
    llm_config = config.get_llm_config()
    model_name = llm_config.get("model", "llama-3.1-8b-instant")
    groq_api_key = config.get_api_key("groq")
    temperature = llm_config.get("temperature", {}).get("location_extraction", 0)
    
    print(f"Using Groq model: {model_name} for determining location")
    llm = ChatGroq(api_key=groq_api_key, model=model_name, temperature=temperature)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract the location from the user's query. Return only the location name in the format "City, Country" or "City, State, Country". 
        If no clear location is mentioned, return "Unknown".
        Examples:
        - "What's the weather in Paris?" -> "Paris, France"
        - "Tell me about New York" -> "New York, USA"
        - "What's happening in Tokyo tonight?" -> "Tokyo, Japan"
        - "How's the weather?" -> "Unknown"
        """),
        ("user", "{query}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"query": user_query})
    #print(f"LLM Location Response : {response}")
    return response.content.strip()


def geocode_api(location_string: Optional[str]) -> dict:
    """Resolve a free-form location string to structured data using OpenStreetMap (OSM) Nominatim.

    Returns a dict with keys: city, state, country, lat, lon.
    Falls back to simple echo if lookup fails.
    """
    if not location_string:
        return {"city": None, "state": None, "country": None, "lat": None, "lon": None}

    geocoding_config = config.get_api_config("geocoding")
    base_url = geocoding_config.get("base_url", "https://nominatim.openstreetmap.org/search")
    timeout = geocoding_config.get("timeout", 10)
    user_agent = config.get_api_key("nominatim_user_agent") or geocoding_config.get("user_agent", "destination-compass/0.1 (contact: example@example.com)")
    params = geocoding_config.get("params", {})

    try:
        resp = requests.get(
            base_url,
            params={**params, "q": location_string},
            headers={"User-Agent": user_agent},
            timeout=timeout,
        )
        if resp.status_code == 200:
            results = resp.json() or []
            if results:
                r0 = results[0]
                address = r0.get("address", {})
                city_like = address.get("city") or address.get("town") or address.get("village") or address.get("hamlet") or address.get("municipality")
                state = address.get("state") or address.get("region")
                country = address.get("country")
                lat = float(r0.get("lat")) if r0.get("lat") else None
                lon = float(r0.get("lon")) if r0.get("lon") else None
                return {
                    "city": city_like or location_string,
                    "state": state,
                    "country": country,
                    "lat": lat,
                    "lon": lon,
                }
    except Exception:
        pass

    # Fallback: echo the string without coordinates
    return {"city": location_string, "state": None, "country": None, "lat": None, "lon": None}


def time_api(structured_location: Optional[dict]) -> str:
    """Return local time using the free Open-Meteo API via coordinates.

    If lat/lon are missing or API fails, fall back to UTC.
    """
    if not structured_location:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    time_config = config.get_api_config("time")
    base_url = time_config.get("base_url", "https://api.open-meteo.com/v1/forecast")
    timeout = time_config.get("timeout", 10)
    params = time_config.get("params", {})

    lat = structured_location.get("lat") if isinstance(structured_location, dict) else None
    lon = structured_location.get("lon") if isinstance(structured_location, dict) else None
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        try:
            resp = requests.get(
                base_url,
                params={
                    **params,
                    "latitude": lat,
                    "longitude": lon,
                },
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                #print(data)
                tz = data.get("timezone")
                current = data.get("current") or {}
                current_time = current.get("time")
                if current_time and tz:
                    return f"{current_time} {tz}"
        except Exception:
            pass

    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def weather_api(structured_location: Optional[dict]) -> dict:
    """Fetch current weather using OpenWeatherMap API.
    
    Uses coordinates if available, otherwise falls back to city name search.
    """
    api_key = config.get_api_key("openweather")
    if not api_key:
        return {"summary": config.get_error_message("api_key_not_configured"), "temperature_c": None}
    
    if not structured_location:
        return {"summary": config.get_error_message("no_location_data"), "temperature_c": None}
    
    weather_config = config.get_api_config("weather")
    base_url = weather_config.get("base_url", "https://api.openweathermap.org/data/2.5/weather")
    timeout = weather_config.get("timeout", 10)
    units = weather_config.get("units", "metric")
    
    lat = structured_location.get("lat")
    lon = structured_location.get("lon")
    city = structured_location.get("city")
    
    try:
        # Try coordinates first if available
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            resp = requests.get(
                base_url,
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": api_key,
                    "units": units
                },
                timeout=timeout
            )
        elif city:
            # Fallback to city name search
            resp = requests.get(
                base_url,
                params={
                    "q": city,
                    "appid": api_key,
                    "units": units
                },
                timeout=timeout
            )
        else:
            return {"summary": config.get_error_message("no_valid_location"), "temperature_c": None}
        
        print(resp.json())

        if resp.status_code == 200:
            data = resp.json()
            weather = data.get("weather", [{}])[0]
            main = data.get("main", {})
            
            return {
                "summary": weather.get("description", "Unknown").title(),
                "temperature_c": round(main.get("temp", 0), 1),
                "feels_like_c": round(main.get("feels_like", 0), 1),
                "humidity": main.get("humidity"),
                "pressure": main.get("pressure"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country")
            }
        else:
            return {"summary": f"Weather API error: {resp.status_code}", "temperature_c": None}
            
    except Exception as e:
        print(f"Weather API error: {e}")
        return {"summary": config.get_error_message("temporarily_unavailable"), "temperature_c": None}


def news_api(structured_location: Optional[dict], local_time: Optional[str]) -> list[str]:
    """Fetch news headlines using NewsAPI with location-based search.
    
    Falls back to general news if location-specific results aren't available.
    """
    api_key = config.get_api_key("news")
    if not api_key:
        return [config.get_error_message("api_key_not_configured")]
    
    news_config = config.get_api_config("news")
    base_url = news_config.get("base_url", "https://newsapi.org/v2")
    everything_endpoint = news_config.get("endpoints", {}).get("everything", "/everything")
    timeout = news_config.get("timeout", 10)
    params = news_config.get("params", {})
    max_articles = config.get_limit("max_news_articles")
    
    # Build search query based on location
    query = "news"
    if structured_location and isinstance(structured_location, dict):
        city = structured_location.get("city")
        country = structured_location.get("country")
        if city and country:
            query = f"{city} {country}"
        elif city:
            query = city
    
    try:
        # Try location-specific news first
        resp = requests.get(
            f"{base_url}{everything_endpoint}",
            params={
                **params,
                "q": query,
            },
            headers={"X-API-Key": api_key},
            timeout=timeout
        )
        
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get("articles", [])
            headlines = []
            for article in articles[:max_articles]:  # Use configured limit
                title = article.get("title", "").strip()
                if title and title != "[Removed]":
                    headlines.append(title)
            
            if headlines:
                return headlines
        
        # Fallback to top headlines if location search fails
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "country": "us",  # Default to US headlines
                "pageSize": 3
            },
            headers={"X-API-Key": api_key},
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get("articles", [])
            return [article.get("title", "").strip() for article in articles if article.get("title", "").strip()]
            
    except Exception as e:
        print(f"News API error: {e}")
    
    return [config.get_error_message("temporarily_unavailable")]


def events_api(structured_location: Optional[dict], weather: Optional[dict], local_time: Optional[str]) -> list[dict]:
    """Search for local events using Tavily search API.
    
    Uses Tavily to find real, current local events and activities.
    """
    if not structured_location:
        return [{"title": config.get_error_message("no_location_data"), "url": "", "date": ""}]
    
    city = structured_location.get("city")
    country = structured_location.get("country")
    
    # Build location query
    location_query = ""
    if city and country:
        location_query = f"{city}, {country}"
    elif city:
        location_query = city
    
    if not location_query:
        return [{"title": config.get_error_message("no_valid_location"), "url": "", "date": ""}]
    
    api_key = config.get_api_key("tavily")
    if not api_key:
        return [{"title": config.get_error_message("api_key_not_configured"), "url": "", "date": ""}]
    
    events_config = config.get_api_config("events")
    base_url = events_config.get("base_url", "https://api.tavily.com/search")
    timeout = events_config.get("timeout", 10)
    search_depth = events_config.get("search_depth", "basic")
    max_results = events_config.get("max_results", 5)
    include_domains = events_config.get("include_domains", [])
    exclude_domains = events_config.get("exclude_domains", [])
    
    # Prepare search query
    search_query = f"upcoming events {location_query} this week"
    
    # Add weather context to search
    if weather and isinstance(weather, dict):
        weather_summary = weather.get("summary", "").lower()
        if "rain" in weather_summary or "storm" in weather_summary:
            search_query += " indoor events"
        elif "sunny" in weather_summary or "clear" in weather_summary:
            search_query += " outdoor events"
    
    try:
        # Search using Tavily API
        response = requests.post(
            base_url,
            json={
                "api_key": api_key,
                "query": search_query,
                "search_depth": search_depth,
                "include_answer": False,
                "include_raw_content": False,
                "max_results": max_results,
                "include_domains": include_domains,
                "exclude_domains": exclude_domains
            },
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            max_events = config.get_limit("max_events")
            formatted_events = []
            for result in results[:max_events]:  # Use configured limit
                title = result.get("title", "Local Event")
                url = result.get("url", "")
                content = result.get("content", "")
                
                # Extract date and venue from content if possible
                date = "TBD"
                venue = "TBD"
                
                # Extract date and venue using configured patterns
                import re
                date_patterns = config.get_patterns("date_patterns")
                venue_patterns = config.get_patterns("venue_patterns")
                
                for pattern in date_patterns:
                    match = re.search(pattern, content)
                    if match:
                        date = match.group(1)
                        break
                
                for pattern in venue_patterns:
                    match = re.search(pattern, content)
                    if match:
                        venue = match.group(1).strip()
                        break
                
                description_length = config.get_limit("description_length")
                formatted_events.append({
                    "title": title,
                    "url": url,
                    "date": date,
                    "venue": venue,
                    "description": content[:description_length] + "..." if len(content) > description_length else content
                })
            
            if formatted_events:
                return formatted_events
        
        # Fallback: return a generic message if no events found
        return [{"title": config.get_error_message("no_events_found").format(location=location_query), "url": "", "date": ""}]
        
    except Exception as e:
        print(f"Tavily API error: {e}")
        return [{"title": config.get_error_message("temporarily_unavailable"), "url": "", "date": ""}]


def format_output(
    location: Optional[dict],
    weather: Optional[dict],
    time: Optional[str],
    news: Optional[list[str]],
    events: Optional[list[dict]],
) -> str:
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


def parse_query(state: DestinationCompassState) -> dict:
    # LLM parses user query for location
    location = extract_location_from_query(state["user_query"])
    print(f"location : {location}")
    return {"location_string": location, "messages": state.get("messages") or []}


def geocode_location(state: DestinationCompassState) -> dict:
    # Use geocoding API (e.g., Google Maps) to get lat/lon/city
    results = geocode_api(state["location_string"])
    print(f"geocode : {results}")
    return {"structured_location": results}


def get_local_time(state: DestinationCompassState) -> dict:
    current_time = time_api(state["structured_location"])
    print(f"current_time : {current_time}")
    return {"local_time": current_time}


def get_weather(state: DestinationCompassState) -> dict:
    weather = weather_api(state["structured_location"])
    print(f"weather : {weather}")
    return {"weather": weather}


def get_news(state: DestinationCompassState) -> dict:
    headlines = news_api(state["structured_location"], state.get("local_time"))
    print(f"headlines : {headlines}")
    return {"news_headlines": headlines}


def get_events(state: DestinationCompassState) -> dict:
    events = events_api(state["structured_location"], state.get("weather"), state.get("local_time"))
    print(f"events : {events}")
    return {"events": events}


def aggregate_results(state: DestinationCompassState) -> dict:
    """Generate a comprehensive markdown report using LLM with all destination information."""
    
    # Get all the data from state
    location = state.get("structured_location")
    weather = state.get("weather")
    local_time = state.get("local_time")
    news = state.get("news_headlines")
    events = state.get("events")
    
    # Prepare context for LLM
    llm_config = config.get_llm_config()
    model_name = llm_config.get("model", "llama-3.1-8b-instant")
    groq_api_key = config.get_api_key("groq")
    temperature = llm_config.get("temperature", {}).get("report_generation", 0.3)
    
    if not groq_api_key:
        # Fallback to simple formatting if no API key
        output = format_output(location, weather, local_time, news, events)
        return {"final_output": output}
    
    try:
        llm = ChatGroq(api_key=groq_api_key, model=model_name, temperature=temperature)
        
        # Build context string for LLM
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
        
        # Create LLM prompt for markdown generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel and destination expert. Create a beautiful, comprehensive markdown report about a destination using the provided information.

            Format your response as a well-structured markdown document with:
            - A compelling title with emoji
            - Executive summary section
            - Weather section with current conditions and recommendations
            - Local time and timezone info
            - Recent news highlights (if available)
            - Upcoming events and activities (if available)
            - Travel tips and recommendations based on the data
            - Use emojis, headers, bullet points, and formatting to make it engaging
            - Keep it informative but conversational
            - Include practical advice based on weather and local conditions
            """),
            ("user", """Create a destination report using this information:

            {context}

            Make it engaging and useful for someone planning to visit or currently in this location.""")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"context": context})
        
        return {"final_output": response.content}
        
    except Exception as e:
        print(f"LLM aggregation error: {e}")
        # Fallback to simple formatting
        output = format_output(location, weather, local_time, news, events)
        return {"final_output": output}


# Build the graph after functions are defined
workflow = StateGraph(DestinationCompassState)

workflow.add_node("parse_query", parse_query)
workflow.add_node("geocode_location", geocode_location)
workflow.add_node("get_local_time", get_local_time)
workflow.add_node("get_weather", get_weather)
workflow.add_node("get_news", get_news)
workflow.add_node("get_events", get_events)
workflow.add_node("aggregate_results", aggregate_results)

workflow.add_edge(START, "parse_query")
workflow.add_edge("parse_query", "geocode_location")
workflow.add_edge("geocode_location", "get_local_time")
workflow.add_edge("geocode_location", "get_weather")
workflow.add_edge("geocode_location", "get_news")
workflow.add_edge("geocode_location", "get_events")
workflow.add_edge("get_local_time", "aggregate_results")
workflow.add_edge("get_weather", "aggregate_results")
workflow.add_edge("get_news", "aggregate_results")
workflow.add_edge("get_events", "aggregate_results")
workflow.add_edge("aggregate_results", END)

# Load environment variables
load_dotenv()

# Get app configuration
app_config = config.get_app_config()
langgraph_config = app_config.get("langgraph", {})
checkpointer_type = langgraph_config.get("checkpointer", "memory")
thread_id = langgraph_config.get("thread_id", "1")

# Initialize checkpointer
if checkpointer_type == "memory":
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
else:
    graph = workflow.compile()

# Create execution config
execution_config = {"configurable": {"thread_id": thread_id}}

#result = graph.invoke({"user_query": "Get me the info for Kingston"}, config=config)

#print(graph.get_state(config))

#print(f"\n\n{result["final_output"]}")

def chat(user_input: str, history):
    result = graph.invoke({"user_query": user_input}, config=execution_config)
    return result["final_output"]


# Get Gradio configuration
gradio_config = app_config.get("gradio", {})
interface_type = gradio_config.get("interface_type", "messages")
title = gradio_config.get("title", "Destination Compass")
description = gradio_config.get("description", "Get comprehensive destination information including weather, news, and events")

gr.ChatInterface(chat, type=interface_type, title=title, description=description).launch()

