"""Unit tests for NewsService."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from services.news import NewsService


class TestNewsService:
    """Test cases for NewsService."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        with patch('services.news.config', mock_config):
            service = NewsService()
            assert service.api_key == "test_api_key"
            assert service.base_url == "https://test.api.com"
            assert service.max_articles == 5
    
    def test_get_news_no_api_key(self, mock_config):
        """Test news service without API key."""
        mock_config.get_api_key.return_value = None
        with patch('services.news.config', mock_config):
            service = NewsService()
            result = service.get_news({"city": "Paris"}, None)
            
            assert len(result) == 1
            assert "not configured" in result[0].lower() or "error" in result[0].lower()
    
    def test_get_news_success(self, mock_config, sample_news_data):
        """Test successful news retrieval."""
        with patch('services.news.config', mock_config):
            service = NewsService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "articles": [
                    {"title": "Breaking: Major event in Paris"},
                    {"title": "Local news update"},
                    {"title": "Weather forecast for the week"},
                    {"title": "[Removed]"},
                    {"title": ""}
                ]
            }
            
            with patch('services.news.requests.get', return_value=mock_response):
                result = service.get_news({"city": "Paris", "country": "France"}, None)
                
                assert len(result) == 3  # Should filter out [Removed] and empty titles
                assert "Breaking" in result[0]
                assert "Local news" in result[1]
    
    def test_get_news_fallback_to_headlines(self, mock_config):
        """Test news service falls back to top headlines."""
        with patch('services.news.config', mock_config):
            service = NewsService()
            
            # First call fails (location search)
            mock_response_fail = Mock()
            mock_response_fail.status_code = 400
            
            # Second call succeeds (headlines)
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "articles": [
                    {"title": "Top headline 1"},
                    {"title": "Top headline 2"}
                ]
            }
            
            with patch('services.news.requests.get', side_effect=[mock_response_fail, mock_response_success]):
                result = service.get_news({"city": "Unknown"}, None)
                
                assert len(result) == 2
                assert "Top headline" in result[0]
    
    def test_get_news_exception(self, mock_config):
        """Test news service exception handling."""
        with patch('services.news.config', mock_config):
            service = NewsService()
            
            with patch('services.news.requests.get', side_effect=Exception("Network error")):
                result = service.get_news({"city": "Paris"}, None)
                
                assert len(result) == 1
                assert "unavailable" in result[0].lower() or "error" in result[0].lower()
    
    def test_get_news_filters_removed_articles(self, mock_config):
        """Test that [Removed] articles are filtered out."""
        with patch('services.news.config', mock_config):
            service = NewsService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "articles": [
                    {"title": "Valid article"},
                    {"title": "[Removed]"},
                    {"title": "Another valid article"}
                ]
            }
            
            with patch('services.news.requests.get', return_value=mock_response):
                result = service.get_news({"city": "Paris"}, None)
                
                assert len(result) == 2
                assert "[Removed]" not in result
                assert "Valid article" in result[0]
    
    def test_get_news_with_city_and_country(self, mock_config):
        """Test news query building with city and country."""
        with patch('services.news.config', mock_config):
            service = NewsService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"articles": [{"title": "Test article"}]}
            
            with patch('services.news.requests.get', return_value=mock_response) as mock_get:
                service.get_news({"city": "Paris", "country": "France"}, None)
                
                # Check that the query includes both city and country
                assert mock_get.called
                # Get the first call (everything endpoint)
                first_call = mock_get.call_args_list[0]
                # first_call is a tuple: (args, kwargs)
                call_kwargs = first_call[1] if len(first_call) > 1 else {}
                params = call_kwargs.get('params', {})
                query = params.get('q', '')
                assert "Paris" in query and "France" in query
    
    def test_get_news_with_city_only(self, mock_config):
        """Test news query building with city only."""
        with patch('services.news.config', mock_config):
            service = NewsService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"articles": [{"title": "Test article"}]}
            
            with patch('services.news.requests.get', return_value=mock_response) as mock_get:
                service.get_news({"city": "Tokyo"}, None)
                
                # Check that the query is just the city name
                assert mock_get.called
                # Get the first call (everything endpoint)
                first_call = mock_get.call_args_list[0]
                call_kwargs = first_call[1] if len(first_call) > 1 else {}
                params = call_kwargs.get('params', {})
                assert params.get('q') == "Tokyo"
