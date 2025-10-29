"""Weather service for fetching weather data."""

from typing import Optional
import requests
from config_loader import config


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""
    
    def __init__(self):
        self.api_key = config.get_api_key("openweather")
        self.config = config.get_api_config("weather")
        self.base_url = self.config.get("base_url", "https://api.openweathermap.org/data/2.5/weather")
        self.timeout = self.config.get("timeout", 10)
        self.units = self.config.get("units", "metric")
    
    def get_weather(self, structured_location: Optional[dict]) -> dict:
        """Fetch current weather using OpenWeatherMap API.
        
        Args:
            structured_location: Location data with lat/lon or city name
            
        Returns:
            dict: Weather data including summary, temperature, humidity, etc.
        """
        if not self.api_key:
            return {"summary": config.get_error_message("api_key_not_configured"), "temperature_c": None}
        
        if not structured_location:
            return {"summary": config.get_error_message("no_location_data"), "temperature_c": None}
        
        lat = structured_location.get("lat")
        lon = structured_location.get("lon")
        city = structured_location.get("city")
        
        try:
            # Try coordinates first if available
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                resp = requests.get(
                    self.base_url,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": self.units
                    },
                    timeout=self.timeout
                )
            elif city:
                # Fallback to city name search
                resp = requests.get(
                    self.base_url,
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": self.units
                    },
                    timeout=self.timeout
                )
            else:
                return {"summary": config.get_error_message("no_valid_location"), "temperature_c": None}
            
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
