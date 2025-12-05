"""Unit tests for LLMService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from services.llm import LLMService


class TestLLMService:
    """Test cases for LLMService."""
    
    def test_init(self, mock_config):
        """Test service initialization."""
        with patch('services.llm.config', mock_config):
            service = LLMService()
            assert service.model_name == "llama-3.1-8b-instant"
            assert service.location_temperature == 0
            assert service.report_temperature == 0.3
    
    def test_extract_location_success(self, mock_config, mock_llm_response):
        """Test successful location extraction."""
        with patch('services.llm.config', mock_config):
            service = LLMService()
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_llm_response
            
            with patch('services.llm.ChatGroq') as mock_groq, \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                result = service.extract_location("What's the weather in Paris?")
                
                assert result == "Paris, France"
    
    def test_extract_location_no_api_key(self, mock_config):
        """Test location extraction without API key."""
        mock_config.get_api_key.return_value = None
        with patch('services.llm.config', mock_config):
            service = LLMService()
            result = service.extract_location("What's the weather in Paris?")
            
            assert result == "Unknown"
    
    def test_classify_destination_intent_yes(self, mock_config):
        """Test intent classification for destination query."""
        with patch('services.llm.config', mock_config):
            service = LLMService()
            
            mock_response = Mock()
            mock_response.content = "YES"
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                result = service.classify_destination_intent("What's the weather in Paris?")
                
                assert result is True
    
    def test_classify_destination_intent_no(self, mock_config):
        """Test intent classification for non-destination query."""
        with patch('services.llm.config', mock_config):
            service = LLMService()
            
            mock_response = Mock()
            mock_response.content = "NO"
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                result = service.classify_destination_intent("What is 2+2?")
                
                assert result is False
    
    def test_classify_destination_intent_no_api_key(self, mock_config):
        """Test intent classification without API key."""
        mock_config.get_api_key.return_value = None
        with patch('services.llm.config', mock_config):
            service = LLMService()
            result = service.classify_destination_intent("What's the weather?")
            
            # Should default to True to preserve existing flow
            assert result is True
    
    def test_general_chat_success(self, mock_config):
        """Test general chat response."""
        with patch('services.llm.config', mock_config):
            service = LLMService()
            
            mock_response = Mock()
            mock_response.content = "2 + 2 equals 4."
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                result = service.general_chat("What is 2+2?")
                
                assert "4" in result
    
    def test_general_chat_no_api_key(self, mock_config):
        """Test general chat without API key."""
        mock_config.get_api_key.return_value = None
        with patch('services.llm.config', mock_config):
            service = LLMService()
            result = service.general_chat("What is 2+2?")
            
            assert "destination" in result.lower() or "location" in result.lower()
    
    def test_generate_report_success(self, mock_config):
        """Test report generation."""
        with patch('services.llm.config', mock_config):
            service = LLMService()
            
            mock_response = Mock()
            mock_response.content = "# Paris Destination Report\n\n## Weather\nClear sky, 20°C"
            
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_response
            
            with patch('services.llm.ChatGroq'), \
                 patch('services.llm.ChatPromptTemplate') as mock_prompt:
                mock_prompt.from_messages.return_value = Mock()
                mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
                
                context = "Location: Paris, France\nWeather: Clear sky, 20°C"
                result = service.generate_report(context)
                
                assert "Paris" in result
                assert "Weather" in result
    
    def test_generate_report_no_api_key(self, mock_config):
        """Test report generation without API key."""
        mock_config.get_api_key.return_value = None
        with patch('services.llm.config', mock_config):
            service = LLMService()
            result = service.generate_report("Location: Paris")
            
            assert "not available" in result.lower() or "LLM" in result
