"""Unit tests for WeatherService."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from services.weather import WeatherService


class TestWeatherService:
    """Test cases for WeatherService."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            assert service.api_key == "test_api_key"
            assert service.base_url == "https://test.api.com"
            assert service.units == "metric"
    
    def test_get_weather_no_api_key(self, mock_config):
        """Test weather service without API key."""
        mock_config.get_api_key.return_value = None
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            result = service.get_weather({"city": "Paris"})
            
            assert "error" in result["summary"].lower() or "not configured" in result["summary"].lower()
            assert result["temperature_c"] is None
    
    def test_get_weather_no_location(self, mock_config):
        """Test weather service without location data."""
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            result = service.get_weather(None)
            
            assert "no location" in result["summary"].lower() or "error" in result["summary"].lower()
            assert result["temperature_c"] is None
    
    def test_get_weather_with_coordinates(self, mock_config, sample_location_data, sample_weather_data):
        """Test weather retrieval using coordinates."""
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "weather": [{"description": "clear sky"}],
                "main": {
                    "temp": 20.5,
                    "feels_like": 19.8,
                    "humidity": 65,
                    "pressure": 1013
                },
                "wind": {"speed": 3.2},
                "name": "Paris",
                "sys": {"country": "FR"}
            }
            
            with patch('services.weather.requests.get', return_value=mock_response):
                result = service.get_weather(sample_location_data)
                
                assert result["summary"] == "Clear Sky"
                assert result["temperature_c"] == 20.5
                assert result["feels_like_c"] == 19.8
                assert result["humidity"] == 65
                assert result["wind_speed"] == 3.2
    
    def test_get_weather_with_city_name(self, mock_config, sample_weather_data):
        """Test weather retrieval using city name."""
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "weather": [{"description": "light rain"}],
                "main": {"temp": 15.0, "feels_like": 14.5, "humidity": 80, "pressure": 1005},
                "wind": {"speed": 5.0},
                "name": "London",
                "sys": {"country": "GB"}
            }
            
            with patch('services.weather.requests.get', return_value=mock_response):
                result = service.get_weather({"city": "London"})
                
                assert result["summary"] == "Light Rain"
                assert result["temperature_c"] == 15.0
                assert result["city"] == "London"
    
    def test_get_weather_api_error(self, mock_config, sample_location_data):
        """Test weather service with API error."""
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            
            mock_response = Mock()
            mock_response.status_code = 401  # Unauthorized
            
            with patch('services.weather.requests.get', return_value=mock_response):
                result = service.get_weather(sample_location_data)
                
                assert "error" in result["summary"].lower()
                assert result["temperature_c"] is None
    
    def test_get_weather_exception(self, mock_config, sample_location_data):
        """Test weather service exception handling."""
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            
            with patch('services.weather.requests.get', side_effect=Exception("Network error")):
                result = service.get_weather(sample_location_data)
                
                assert "unavailable" in result["summary"].lower() or "error" in result["summary"].lower()
                assert result["temperature_c"] is None
    
    def test_get_weather_invalid_location_data(self, mock_config):
        """Test weather service with invalid location data."""
        with patch('services.weather.config', mock_config):
            service = WeatherService()
            
            # Location with no city and no coordinates
            result = service.get_weather({"state": "Some State"})
            
            assert "no valid location" in result["summary"].lower() or "error" in result["summary"].lower()
            assert result["temperature_c"] is None
