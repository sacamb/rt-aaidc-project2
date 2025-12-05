"""Shared pytest fixtures for Destination Compass tests."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any


@pytest.fixture
def mock_config():
    """Mock configuration loader."""
    config_mock = Mock()
    config_mock.get_api_key.return_value = "test_api_key"
    config_mock.get_api_config.return_value = {
        "base_url": "https://test.api.com",
        "timeout": 10,
        "params": {}
    }
    config_mock.get_llm_config.return_value = {
        "model": "llama-3.1-8b-instant",
        "temperature": {"location_extraction": 0, "report_generation": 0.3}
    }
    config_mock.get_error_message.return_value = "Test error message"
    config_mock.get_default.return_value = "Unknown"
    config_mock.get_limit.return_value = 5
    config_mock.get_patterns.return_value = []
    config_mock.get_app_config.return_value = {
        "langgraph": {"checkpointer": "memory", "thread_id": "1"},
        "gradio": {"interface_type": "messages", "title": "Test"}
    }
    return config_mock


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables."""
    env_vars = {
        "GROQ_API_KEY": "test_groq_key",
        "NEWS_API_KEY": "test_news_key",
        "OPENWEATHER_API_KEY": "test_weather_key",
        "TAVILY_API_KEY": "test_tavily_key",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def sample_location_data():
    """Sample structured location data."""
    return {
        "city": "Paris",
        "state": "Île-de-France",
        "country": "France",
        "lat": 48.8566,
        "lon": 2.3522
    }


@pytest.fixture
def sample_weather_data():
    """Sample weather data."""
    return {
        "summary": "Clear sky",
        "temperature_c": 20.5,
        "feels_like_c": 19.8,
        "humidity": 65,
        "pressure": 1013,
        "wind_speed": 3.2,
        "city": "Paris",
        "country": "FR"
    }


@pytest.fixture
def sample_news_data():
    """Sample news headlines."""
    return [
        "Breaking: Major event in Paris",
        "Local news update",
        "Weather forecast for the week"
    ]


@pytest.fixture
def sample_events_data():
    """Sample events data."""
    return [
        {
            "title": "Paris Fashion Week",
            "url": "https://example.com/event1",
            "date": "2025-11-01",
            "venue": "Louvre Museum",
            "description": "Annual fashion event"
        },
        {
            "title": "Jazz Concert",
            "url": "https://example.com/event2",
            "date": "2025-11-05",
            "venue": "Jazz Club",
            "description": "Evening jazz performance"
        }
    ]


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Mock requests.get for API calls."""
    def _mock_get(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        return mock_response
    
    monkeypatch.setattr("requests.get", _mock_get)
    return _mock_get


@pytest.fixture
def mock_requests_post(monkeypatch):
    """Mock requests.post for API calls."""
    def _mock_post(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        return mock_response
    
    monkeypatch.setattr("requests.post", _mock_post)
    return _mock_post


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    mock_response = Mock()
    mock_response.content = "Paris, France"
    return mock_response


@pytest.fixture
def sample_state():
    """Sample workflow state."""
    from src.models.state import DestinationCompassState
    
    return {
        "user_query": "What's the weather in Paris?",
        "location_string": None,
        "structured_location": None,
        "local_time": None,
        "weather": None,
        "news_headlines": None,
        "events": None,
        "final_output": None,
        "messages": None
    }
