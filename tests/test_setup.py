"""Simple test to verify test setup is working."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


def test_imports():
    """Test that all modules can be imported."""
    try:
        from models.state import DestinationCompassState
        from services.geocoding import GeocodingService
        from services.weather import WeatherService
        from services.news import NewsService
        from services.events import EventsService
        from services.time import TimeService
        from services.llm import LLMService
        from nodes.location_nodes import parse_query
        from app import DestinationCompassApp
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_config_loader():
    """Test that config loader works."""
    try:
        from config_loader import config
        assert config is not None
        assert hasattr(config, 'get_api_key')
        assert hasattr(config, 'get_api_config')
    except Exception as e:
        pytest.fail(f"Config loader test failed: {e}")
