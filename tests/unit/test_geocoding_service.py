"""Unit tests for GeocodingService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from services.geocoding import GeocodingService


class TestGeocodingService:
    """Test cases for GeocodingService."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        with patch('services.geocoding.config', mock_config):
            service = GeocodingService()
            assert service.base_url == "https://test.api.com"
            assert service.timeout == 10
    
    def test_geocode_success(self, mock_config, sample_location_data):
        """Test successful geocoding."""
        with patch('services.geocoding.config', mock_config):
            service = GeocodingService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{
                "lat": "48.8566",
                "lon": "2.3522",
                "address": {
                    "city": "Paris",
                    "state": "Île-de-France",
                    "country": "France"
                }
            }]
            
            with patch('services.geocoding.requests.get', return_value=mock_response):
                result = service.geocode("Paris, France")
                
                assert result["city"] == "Paris"
                assert result["country"] == "France"
                assert result["lat"] == 48.8566
                assert result["lon"] == 2.3522
    
    def test_geocode_no_location_string(self, mock_config):
        """Test geocoding with None location."""
        with patch('services.geocoding.config', mock_config):
            service = GeocodingService()
            result = service.geocode(None)
            
            assert result["city"] is None
            assert result["lat"] is None
            assert result["lon"] is None
    
    def test_geocode_api_failure(self, mock_config):
        """Test geocoding when API fails."""
        with patch('services.geocoding.config', mock_config):
            service = GeocodingService()
            
            mock_response = Mock()
            mock_response.status_code = 500
            
            with patch('services.geocoding.requests.get', return_value=mock_response):
                result = service.geocode("Paris")
                
                # Should return fallback with city name only
                assert result["city"] == "Paris"
                assert result["lat"] is None
    
    def test_geocode_empty_response(self, mock_config):
        """Test geocoding with empty API response."""
        with patch('services.geocoding.config', mock_config):
            service = GeocodingService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            
            with patch('services.geocoding.requests.get', return_value=mock_response):
                result = service.geocode("Unknown Place")
                
                # Should return fallback
                assert result["city"] == "Unknown Place"
                assert result["lat"] is None
    
    def test_geocode_exception_handling(self, mock_config):
        """Test geocoding exception handling."""
        with patch('services.geocoding.config', mock_config):
            service = GeocodingService()
            
            with patch('services.geocoding.requests.get', side_effect=Exception("Network error")):
                result = service.geocode("Paris")
                
                # Should return fallback on exception
                assert result["city"] == "Paris"
                assert result["lat"] is None
    
    def test_geocode_various_city_types(self, mock_config):
        """Test geocoding handles different city types (town, village, etc.)."""
        with patch('services.geocoding.config', mock_config):
            service = GeocodingService()
            
            # Test with "town" instead of "city"
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{
                "lat": "40.7128",
                "lon": "-74.0060",
                "address": {
                    "town": "New York",
                    "state": "New York",
                    "country": "United States"
                }
            }]
            
            with patch('services.geocoding.requests.get', return_value=mock_response):
                result = service.geocode("New York")
                
                assert result["city"] == "New York"
                assert result["country"] == "United States"
