"""Geocoding service for location resolution."""

from typing import Optional
import requests
from config_loader import config


class GeocodingService:
    """Service for geocoding location strings to structured data."""
    
    def __init__(self):
        self.config = config.get_api_config("geocoding")
        self.base_url = self.config.get("base_url", "https://nominatim.openstreetmap.org/search")
        self.timeout = self.config.get("timeout", 10)
        self.user_agent = config.get_api_key("nominatim_user_agent") or self.config.get("user_agent", "destination-compass/0.1 (contact: example@example.com)")
        self.params = self.config.get("params", {})
    
    def geocode(self, location_string: Optional[str]) -> dict:
        """Resolve a free-form location string to structured data using OpenStreetMap Nominatim.

        Args:
            location_string: The location string to geocode

        Returns:
            dict: Structured location data with keys: city, state, country, lat, lon
        """
        if not location_string:
            return {"city": None, "state": None, "country": None, "lat": None, "lon": None}

        try:
            resp = requests.get(
                self.base_url,
                params={**self.params, "q": location_string},
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
            
            print (resp.json())
            
            if resp.status_code == 200:
                results = resp.json() or []
                if results:
                    r0 = results[0]
                    address = r0.get("address", {})
                    city_like = (address.get("city") or 
                               address.get("town") or 
                               address.get("village") or 
                               address.get("hamlet") or 
                               address.get("municipality"))
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
