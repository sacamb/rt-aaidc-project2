"""News service for fetching news headlines."""

from typing import Optional
import requests
from config_loader import config


class NewsService:
    """Service for fetching news headlines from NewsAPI."""
    
    def __init__(self):
        self.api_key = config.get_api_key("news")
        self.config = config.get_api_config("news")
        self.base_url = self.config.get("base_url", "https://newsapi.org/v2")
        self.everything_endpoint = self.config.get("endpoints", {}).get("everything", "/everything")
        self.timeout = self.config.get("timeout", 10)
        self.params = self.config.get("params", {})
        self.max_articles = config.get_limit("max_news_articles")
    
    def get_news(self, structured_location: Optional[dict], local_time: Optional[str]) -> list[str]:
        """Fetch news headlines using NewsAPI with location-based search.
        
        Args:
            structured_location: Location data for news search
            local_time: Local time for context
            
        Returns:
            list[str]: List of news headlines
        """
        if not self.api_key:
            return [config.get_error_message("api_key_not_configured")]
        
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
                f"{self.base_url}{self.everything_endpoint}",
                params={
                    **self.params,
                    "q": query,
                },
                headers={"X-API-Key": self.api_key},
                timeout=self.timeout
            )
            
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])
                headlines = []
                for article in articles[:self.max_articles]:
                    title = article.get("title", "").strip()
                    if title and title != "[Removed]":
                        headlines.append(title)
                
                if headlines:
                    return headlines
            
            # Fallback to top headlines if location search fails
            resp = requests.get(
                f"{self.base_url}/top-headlines",
                params={
                    "country": "us",
                    "pageSize": self.max_articles
                },
                headers={"X-API-Key": self.api_key},
                timeout=self.timeout
            )
            
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])
                return [article.get("title", "").strip() for article in articles if article.get("title", "").strip()]
                
        except Exception as e:
            print(f"News API error: {e}")
        
        return [config.get_error_message("temporarily_unavailable")]
