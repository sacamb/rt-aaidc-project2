"""Unit tests for TimeService."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from services.time import TimeService


class TestTimeService:
    """Test cases for TimeService."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        with patch('services.time.config', mock_config):
            service = TimeService()
            assert service.base_url == "https://test.api.com"
            assert service.timeout == 10
    
    def test_get_local_time_no_location(self, mock_config):
        """Test time service without location data."""
        with patch('services.time.config', mock_config):
            service = TimeService()
            result = service.get_local_time(None)
            
            assert "UTC" in result
            assert isinstance(result, str)
    
    def test_get_local_time_success(self, mock_config, sample_location_data):
        """Test successful time retrieval."""
        with patch('services.time.config', mock_config):
            service = TimeService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "timezone": "Europe/Paris",
                "current": {
                    "time": "2025-10-29T14:30:00"
                }
            }
            
            with patch('services.time.requests.get', return_value=mock_response):
                result = service.get_local_time(sample_location_data)
                
                assert "2025-10-29T14:30:00" in result
                assert "Europe/Paris" in result
    
    def test_get_local_time_no_coordinates(self, mock_config):
        """Test time service with location but no coordinates."""
        with patch('services.time.config', mock_config):
            service = TimeService()
            
            # Location without lat/lon
            result = service.get_local_time({"city": "Paris"})
            
            # Should return UTC fallback
            assert "UTC" in result
    
    def test_get_local_time_api_error(self, mock_config, sample_location_data):
        """Test time service with API error."""
        with patch('services.time.config', mock_config):
            service = TimeService()
            
            mock_response = Mock()
            mock_response.status_code = 500
            
            with patch('services.time.requests.get', return_value=mock_response):
                result = service.get_local_time(sample_location_data)
                
                # Should return UTC fallback
                assert "UTC" in result
    
    def test_get_local_time_exception(self, mock_config, sample_location_data):
        """Test time service exception handling."""
        with patch('services.time.config', mock_config):
            service = TimeService()
            
            with patch('services.time.requests.get', side_effect=Exception("Network error")):
                result = service.get_local_time(sample_location_data)
                
                # Should return UTC fallback
                assert "UTC" in result
    
    def test_get_local_time_missing_timezone(self, mock_config, sample_location_data):
        """Test time service when timezone is missing from response."""
        with patch('services.time.config', mock_config):
            service = TimeService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "current": {
                    "time": "2025-10-29T14:30:00"
                }
                # Missing timezone
            }
            
            with patch('services.time.requests.get', return_value=mock_response):
                result = service.get_local_time(sample_location_data)
                
                # Should return UTC fallback when timezone is missing
                assert "UTC" in result
