"""Time service for fetching local time."""

from typing import Optional
import requests
from datetime import datetime, timezone
from config_loader import config


class TimeService:
    """Service for fetching local time using Open-Meteo API."""
    
    def __init__(self):
        self.config = config.get_api_config("time")
        self.base_url = self.config.get("base_url", "https://api.open-meteo.com/v1/forecast")
        self.timeout = self.config.get("timeout", 10)
        self.params = self.config.get("params", {})
    
    def get_local_time(self, structured_location: Optional[dict]) -> str:
        """Return local time using the free Open-Meteo API via coordinates.
        
        Args:
            structured_location: Location data with lat/lon coordinates
            
        Returns:
            str: Local time string with timezone
        """
        if not structured_location:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        lat = structured_location.get("lat") if isinstance(structured_location, dict) else None
        lon = structured_location.get("lon") if isinstance(structured_location, dict) else None
        
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            try:
                resp = requests.get(
                    self.base_url,
                    params={
                        **self.params,
                        "latitude": lat,
                        "longitude": lon,
                    },
                    timeout=self.timeout,
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    tz = data.get("timezone")
                    current = data.get("current") or {}
                    current_time = current.get("time")
                    if current_time and tz:
                        return f"{current_time} {tz}"
            except Exception:
                pass
        
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
