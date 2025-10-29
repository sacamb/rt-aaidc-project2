"""Events service for fetching local events."""

from typing import Optional
import requests
import re
from config_loader import config


class EventsService:
    """Service for fetching local events using Tavily search API."""
    
    def __init__(self):
        self.api_key = config.get_api_key("tavily")
        self.config = config.get_api_config("events")
        self.base_url = self.config.get("base_url", "https://api.tavily.com/search")
        self.timeout = self.config.get("timeout", 10)
        self.search_depth = self.config.get("search_depth", "basic")
        self.max_results = self.config.get("max_results", 5)
        self.include_domains = self.config.get("include_domains", [])
        self.exclude_domains = self.config.get("exclude_domains", [])
        self.max_events = config.get_limit("max_events")
        self.description_length = config.get_limit("description_length")
    
    def get_events(self, structured_location: Optional[dict], weather: Optional[dict], local_time: Optional[str]) -> list[dict]:
        """Search for local events using Tavily search API.
        
        Args:
            structured_location: Location data for event search
            weather: Weather data for context-aware search
            local_time: Local time for context
            
        Returns:
            list[dict]: List of event dictionaries with title, url, date, venue, description
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
        
        if not self.api_key:
            return [{"title": config.get_error_message("api_key_not_configured"), "url": "", "date": ""}]
        
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
                self.base_url,
                json={
                    "api_key": self.api_key,
                    "query": search_query,
                    "search_depth": self.search_depth,
                    "include_answer": False,
                    "include_raw_content": False,
                    "max_results": self.max_results,
                    "include_domains": self.include_domains,
                    "exclude_domains": self.exclude_domains
                },
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                formatted_events = []
                for result in results[:self.max_events]:
                    title = result.get("title", "Local Event")
                    url = result.get("url", "")
                    content = result.get("content", "")
                    
                    # Extract date and venue from content if possible
                    date = "TBD"
                    venue = "TBD"
                    
                    # Extract date and venue using configured patterns
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
                    
                    formatted_events.append({
                        "title": title,
                        "url": url,
                        "date": date,
                        "venue": venue,
                        "description": content[:self.description_length] + "..." if len(content) > self.description_length else content
                    })
                
                if formatted_events:
                    return formatted_events
            
            # Fallback: return a generic message if no events found
            return [{"title": config.get_error_message("no_events_found").format(location=location_query), "url": "", "date": ""}]
            
        except Exception as e:
            print(f"Tavily API error: {e}")
            return [{"title": config.get_error_message("temporarily_unavailable"), "url": "", "date": ""}]
