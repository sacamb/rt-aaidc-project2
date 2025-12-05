"""Edge case tests for Destination Compass."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from app import DestinationCompassApp


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_query(self, mock_config, mock_env_vars):
        """Test handling of empty user query."""
        with patch('dotenv.load_dotenv'), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config):
            
            mock_llm_response = Mock()
            mock_llm_response.content = "Unknown"
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_llm_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                app = DestinationCompassApp()
                
                initial_state = {
                    "user_query": "",
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
                
                # Should handle gracefully
                assert result is not None
    
    def test_very_long_query(self, mock_config, mock_env_vars):
        """Test handling of very long user query."""
        with patch('dotenv.load_dotenv'), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config):
            
            mock_llm_response = Mock()
            mock_llm_response.content = "Paris, France"
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_llm_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                app = DestinationCompassApp()
                
                long_query = "What's the weather in " + "Paris " * 1000
                initial_state = {
                    "user_query": long_query,
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
                
                # Should handle long queries
                assert result is not None
    
    def test_special_characters_in_query(self, mock_config, mock_env_vars):
        """Test handling of special characters in query."""
        with patch('dotenv.load_dotenv'), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config):
            
            mock_llm_response = Mock()
            mock_llm_response.content = "Paris, France"
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_llm_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                app = DestinationCompassApp()
                
                special_query = "What's the weather in Paris? @#$%^&*()"
                initial_state = {
                    "user_query": special_query,
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
                
                # Should handle special characters
                assert result is not None
    
    def test_all_apis_fail(self, mock_config, mock_env_vars):
        """Test workflow when all APIs fail."""
        with patch('dotenv.load_dotenv'), \
             patch('services.geocoding.config', mock_config), \
             patch('services.weather.config', mock_config), \
             patch('services.news.config', mock_config), \
             patch('services.events.config', mock_config), \
             patch('services.time.config', mock_config), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config):
            
            # Mock LLM to work
            mock_llm_response = Mock()
            mock_llm_response.content = "Paris, France"
            
            mock_llm_report = Mock()
            mock_llm_report.content = "# Report\n\nLimited data available."
            
            mock_chain = Mock()
            mock_chain.invoke.side_effect = [mock_llm_response, mock_llm_report]
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt, \
                 patch('services.geocoding.requests.get', side_effect=Exception("Geo fail")), \
                 patch('services.time.requests.get', side_effect=Exception("Time fail")), \
                 patch('services.weather.requests.get', side_effect=Exception("Weather fail")), \
                 patch('services.news.requests.get', side_effect=Exception("News fail")), \
                 patch('services.events.requests.post', side_effect=Exception("Events fail")):
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                app = DestinationCompassApp()
                
                initial_state = {
                    "user_query": "What's in Paris?",
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
                
                # Should still complete with error messages
                assert result.get("final_output") is not None
    
    def test_malformed_api_responses(self, mock_config, mock_env_vars):
        """Test handling of malformed API responses."""
        with patch('dotenv.load_dotenv'), \
             patch('services.geocoding.config', mock_config), \
             patch('services.weather.config', mock_config), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config):
            
            mock_llm_response = Mock()
            mock_llm_response.content = "Paris, France"
            
            mock_llm_report = Mock()
            mock_llm_report.content = "# Report"
            
            mock_chain = Mock()
            mock_chain.invoke.side_effect = [mock_llm_response, mock_llm_report]
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt, \
                 patch('services.geocoding.requests.get') as mock_geo, \
                 patch('services.weather.requests.get') as mock_weather:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                # Malformed geocoding response
                mock_geo.return_value.status_code = 200
                mock_geo.return_value.json.return_value = {"invalid": "structure"}
                
                # Malformed weather response
                mock_weather.return_value.status_code = 200
                mock_weather.return_value.json.return_value = None
                
                app = DestinationCompassApp()
                
                initial_state = {
                    "user_query": "Paris weather",
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
                
                # Should handle malformed responses gracefully
                assert result is not None
    
    def test_timeout_scenarios(self, mock_config, mock_env_vars):
        """Test handling of timeout scenarios."""
        import requests
        
        with patch('dotenv.load_dotenv'), \
             patch('services.geocoding.config', mock_config), \
             patch('services.llm.config', mock_config), \
             patch('config_loader.config', mock_config):
            
            mock_llm_response = Mock()
            mock_llm_response.content = "Paris, France"
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_llm_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt, \
                 patch('services.geocoding.requests.get') as mock_geo:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                # Simulate timeout
                mock_geo.side_effect = requests.Timeout("Request timed out")
                
                app = DestinationCompassApp()
                
                initial_state = {
                    "user_query": "Paris",
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
                
                # Should handle timeout gracefully
                assert result is not None
