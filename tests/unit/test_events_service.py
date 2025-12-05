"""Unit tests for EventsService."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from services.events import EventsService


class TestEventsService:
    """Test cases for EventsService."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            assert service.api_key == "test_api_key"
            assert service.base_url == "https://test.api.com"
            assert service.max_results == 5
            assert service.max_events == 5
    
    def test_get_events_no_location(self, mock_config):
        """Test events service without location data."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            result = service.get_events(None, None, None)
            
            assert len(result) == 1
            assert "no location" in result[0]["title"].lower() or "error" in result[0]["title"].lower()
    
    def test_get_events_no_api_key(self, mock_config):
        """Test events service without API key."""
        mock_config.get_api_key.return_value = None
        with patch('services.events.config', mock_config):
            service = EventsService()
            result = service.get_events({"city": "Paris"}, None, None)
            
            assert len(result) == 1
            assert "not configured" in result[0]["title"].lower() or "error" in result[0]["title"].lower()
    
    def test_get_events_success(self, mock_config, sample_events_data):
        """Test successful events retrieval."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "title": "Paris Fashion Week",
                        "url": "https://example.com/event1",
                        "content": "Event on 11/01/2025 at Louvre Museum. Annual fashion event."
                    },
                    {
                        "title": "Jazz Concert",
                        "url": "https://example.com/event2",
                        "content": "Concert on 11/05/2025 at Jazz Club. Evening performance."
                    }
                ]
            }
            
            with patch('services.events.requests.post', return_value=mock_response):
                result = service.get_events(
                    {"city": "Paris", "country": "France"},
                    None,
                    None
                )
                
                assert len(result) == 2
                assert result[0]["title"] == "Paris Fashion Week"
                assert result[1]["title"] == "Jazz Concert"
                assert "https://example.com" in result[0]["url"]
    
    def test_get_events_weather_aware_indoor(self, mock_config):
        """Test events service adjusts search for rainy weather."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            
            with patch('services.events.requests.post', return_value=mock_response) as mock_post:
                service.get_events(
                    {"city": "Paris"},
                    {"summary": "Heavy rain"},
                    None
                )
                
                # Check that search query includes "indoor events"
                call_args = mock_post.call_args
                json_data = call_args[1].get('json', {})
                query = json_data.get('query', '')
                assert "indoor" in query.lower()
    
    def test_get_events_weather_aware_outdoor(self, mock_config):
        """Test events service adjusts search for sunny weather."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            
            with patch('services.events.requests.post', return_value=mock_response) as mock_post:
                service.get_events(
                    {"city": "Paris"},
                    {"summary": "Sunny"},
                    None
                )
                
                call_args = mock_post.call_args
                json_data = call_args[1].get('json', {})
                query = json_data.get('query', '')
                assert "outdoor" in query.lower()
    
    def test_get_events_date_extraction(self, mock_config):
        """Test events service extracts dates from content."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            mock_config.get_patterns.return_value = [
                r"(\d{1,2}/\d{1,2}/\d{4})",  # MM/DD/YYYY
            ]
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [{
                    "title": "Test Event",
                    "url": "https://example.com",
                    "content": "Event happening on 11/15/2025 at Central Park"
                }]
            }
            
            with patch('services.events.requests.post', return_value=mock_response):
                result = service.get_events({"city": "New York"}, None, None)
                
                assert result[0]["date"] == "11/15/2025"
    
    def test_get_events_venue_extraction(self, mock_config):
        """Test events service extracts venue from content."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            mock_config.get_patterns.return_value = [
                r"at\s+([A-Z][^,]+)",  # "at Venue Name"
            ]
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [{
                    "title": "Test Event",
                    "url": "https://example.com",
                    "content": "Event happening at Central Park on November 15"
                }]
            }
            
            with patch('services.events.requests.post', return_value=mock_response):
                result = service.get_events({"city": "New York"}, None, None)
                
                assert "Central Park" in result[0]["venue"]
    
    def test_get_events_api_error(self, mock_config):
        """Test events service with API error."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            
            mock_response = Mock()
            mock_response.status_code = 500
            
            with patch('services.events.requests.post', return_value=mock_response):
                result = service.get_events({"city": "Paris"}, None, None)
                
                assert len(result) == 1
                assert "not found" in result[0]["title"].lower() or "error" in result[0]["title"].lower()
    
    def test_get_events_exception(self, mock_config):
        """Test events service exception handling."""
        with patch('services.events.config', mock_config):
            service = EventsService()
            
            with patch('services.events.requests.post', side_effect=Exception("Network error")):
                result = service.get_events({"city": "Paris"}, None, None)
                
                assert len(result) == 1
                assert "unavailable" in result[0]["title"].lower() or "error" in result[0]["title"].lower()
    

