"""Integration tests for LangGraph workflow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from models.state import DestinationCompassState
from app import DestinationCompassApp


class TestWorkflowIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.fixture
    def mock_all_services(self, mock_config):
        """Mock all external services for integration testing."""
        with patch('services.geocoding.config', mock_config), \
             patch('services.weather.config', mock_config), \
             patch('services.news.config', mock_config), \
             patch('services.events.config', mock_config), \
             patch('services.time.config', mock_config), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config):
            
            # Mock geocoding
            with patch('services.geocoding.requests.get') as mock_geo:
                mock_geo.return_value.status_code = 200
                mock_geo.return_value.json.return_value = [{
                    "lat": "48.8566",
                    "lon": "2.3522",
                    "address": {
                        "city": "Paris",
                        "country": "France"
                    }
                }]
                
                # Mock time
                with patch('services.time.requests.get') as mock_time:
                    mock_time.return_value.status_code = 200
                    mock_time.return_value.json.return_value = {
                        "timezone": "Europe/Paris",
                        "current": {"time": "2025-10-29T14:30:00"}
                    }
                    
                    # Mock weather
                    with patch('services.weather.requests.get') as mock_weather:
                        mock_weather.return_value.status_code = 200
                        mock_weather.return_value.json.return_value = {
                            "weather": [{"description": "clear sky"}],
                            "main": {"temp": 20.5, "feels_like": 19.8, "humidity": 65, "pressure": 1013},
                            "wind": {"speed": 3.2},
                            "name": "Paris",
                            "sys": {"country": "FR"}
                        }
                        
                        # Mock news
                        with patch('services.news.requests.get') as mock_news:
                            mock_news.return_value.status_code = 200
                            mock_news.return_value.json.return_value = {
                                "articles": [
                                    {"title": "Paris news 1"},
                                    {"title": "Paris news 2"}
                                ]
                            }
                            
                            # Mock events
                            with patch('services.events.requests.post') as mock_events:
                                mock_events.return_value.status_code = 200
                                mock_events.return_value.json.return_value = {
                                    "results": [{
                                        "title": "Paris Event",
                                        "url": "https://example.com",
                                        "content": "Event on 11/01/2025"
                                    }]
                                }
                                
                                # Mock LLM
                                mock_llm_response = Mock()
                                mock_llm_response.content = "Paris, France"
                                
                                mock_llm_report = Mock()
                                mock_llm_report.content = "# Paris Report\n\nWeather: Clear, 20°C"
                                
                                with patch('services.llm.ChatGroq') as mock_groq, \
                                     patch('services.llm.ChatPromptTemplate') as mock_prompt:
                                    mock_chain = Mock()
                                    mock_chain.invoke.side_effect = [mock_llm_response, mock_llm_report]
                                    mock_prompt.from_messages.return_value = Mock()
                                    mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                                    
                                    yield {
                                        'geo': mock_geo,
                                        'time': mock_time,
                                        'weather': mock_weather,
                                        'news': mock_news,
                                        'events': mock_events,
                                        'llm': mock_groq
                                    }
    
    def test_full_workflow_destination_query(self, mock_all_services, mock_env_vars):
        """Test complete workflow for destination query."""
        with patch('dotenv.load_dotenv'), \
             patch('nodes.location_nodes.llm_service.extract_location', return_value="Paris, France"), \
             patch('nodes.location_nodes.llm_service.classify_destination_intent', return_value=True), \
             patch('nodes.aggregation_nodes.llm_service.generate_report', return_value="# Paris Report\n\nWeather: Clear, 20°C"):
            app = DestinationCompassApp()
            
            initial_state = {
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
            
            result = app.graph.invoke(initial_state, config=app.execution_config)
            
            # Verify final output exists
            assert result.get("final_output") is not None
            assert len(result["final_output"]) > 0
            
            # Verify intermediate steps were executed
            assert result.get("location_string") is not None
            assert result.get("structured_location") is not None
    
    def test_workflow_non_destination_query(self, mock_config, mock_env_vars):
        """Test workflow for non-destination query (should short-circuit)."""
        with patch('dotenv.load_dotenv'), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config), \
             patch('nodes.location_nodes.llm_service.classify_destination_intent', return_value=False), \
             patch('nodes.location_nodes.llm_service.general_chat', return_value="2 + 2 equals 4."):
            
            app = DestinationCompassApp()
            
            initial_state = {
                "user_query": "What is 2+2?",
                "location_string": None,
                "structured_location": None,
                "local_time": None,
                "weather": None,
                "news_headlines": None,
                "events": None,
                "final_output": None,
                "messages": None
            }
            
            result = app.graph.invoke(initial_state, config=app.execution_config)
            
            # Should have final_output but no location processing
            assert result.get("final_output") is not None
            assert "4" in result["final_output"]
            # Should not have processed location
            assert result.get("structured_location") is None
    
    def test_workflow_invalid_location(self, mock_config, mock_env_vars):
        """Test workflow with invalid location."""
        with patch('dotenv.load_dotenv'), \
             patch('services.geocoding.config', mock_config), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config), \
             patch('nodes.location_nodes.llm_service.extract_location', return_value="Unknown"), \
             patch('nodes.location_nodes.llm_service.classify_destination_intent', return_value=True), \
             patch('nodes.aggregation_nodes.llm_service.generate_report', return_value="# Report\n\nLimited data available."):
            
            # Mock geocoding to return empty
            with patch('services.geocoding.requests.get') as mock_geo:
                mock_geo.return_value.status_code = 200
                mock_geo.return_value.json.return_value = []
                
                app = DestinationCompassApp()
                
                initial_state = {
                    "user_query": "Tell me about XYZ123",
                    "location_string": None,
                    "structured_location": None,
                    "local_time": None,
                    "weather": None,
                    "news_headlines": None,
                    "events": None,
                    "final_output": None,
                    "messages": None
                }
                
                result = app.graph.invoke(initial_state, config=app.execution_config)
                
                # Should still complete but with limited data
                assert result.get("final_output") is not None
    
    def test_workflow_api_failures(self, mock_config, mock_env_vars):
        """Test workflow resilience to API failures."""
        with patch('dotenv.load_dotenv'), \
             patch('services.geocoding.config', mock_config), \
             patch('services.weather.config', mock_config), \
             patch('services.news.config', mock_config), \
             patch('services.events.config', mock_config), \
             patch('services.time.config', mock_config), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config), \
             patch('nodes.location_nodes.llm_service.extract_location', return_value="Paris, France"), \
             patch('nodes.location_nodes.llm_service.classify_destination_intent', return_value=True), \
             patch('nodes.aggregation_nodes.llm_service.generate_report', return_value="# Report\n\nSome data available."):
            
            with patch('services.geocoding.requests.get') as mock_geo, \
                 patch('services.time.requests.get') as mock_time, \
                 patch('services.weather.requests.get') as mock_weather, \
                 patch('services.news.requests.get') as mock_news, \
                 patch('services.events.requests.post') as mock_events:
                
                # Geocoding succeeds
                mock_geo.return_value.status_code = 200
                mock_geo.return_value.json.return_value = [{
                    "lat": "48.8566",
                    "lon": "2.3522",
                    "address": {"city": "Paris", "country": "France"}
                }]
                
                # Time fails
                mock_time.side_effect = Exception("Time API error")
                
                # Weather fails
                mock_weather.return_value.status_code = 500
                
                # News succeeds
                mock_news.return_value.status_code = 200
                mock_news.return_value.json.return_value = {"articles": [{"title": "News"}]}
                
                # Events fails
                mock_events.side_effect = Exception("Events API error")
                
                app = DestinationCompassApp()
                
                initial_state = {
                    "user_query": "What's happening in Paris?",
                    "location_string": None,
                    "structured_location": None,
                    "local_time": None,
                    "weather": None,
                    "news_headlines": None,
                    "events": None,
                    "final_output": None,
                    "messages": None
                }
                
                result = app.graph.invoke(initial_state, config=app.execution_config)
                
                # Should still complete with partial data
                assert result.get("final_output") is not None
                # Should have news (which succeeded)
                assert result.get("news_headlines") is not None
