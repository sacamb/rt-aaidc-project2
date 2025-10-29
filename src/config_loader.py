"""Configuration loader for Destination Compass application."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Loads and manages configuration from YAML file and environment variables."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the configuration value (e.g., 'llm.model')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service, resolving environment variables.
        
        Args:
            service: Service name (e.g., 'groq', 'news', 'openweather')
            
        Returns:
            API key or None if not found
        """
        key_path = f"api_keys.{service}"
        key_template = self.get(key_path)
        
        if not key_template:
            return None
            
        # Resolve environment variable if it's in the format ${VAR_NAME}
        if isinstance(key_template, str) and key_template.startswith("${") and key_template.endswith("}"):
            env_var = key_template[2:-1]
            return os.getenv(env_var)
        
        return key_template
    
    def get_api_config(self, service: str) -> Dict[str, Any]:
        """Get API configuration for a service.
        
        Args:
            service: Service name (e.g., 'geocoding', 'weather', 'news')
            
        Returns:
            API configuration dictionary
        """
        return self.get(f"apis.{service}", {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration.
        
        Returns:
            LLM configuration dictionary
        """
        return self.get("llm", {})
    
    def get_error_message(self, error_type: str) -> str:
        """Get error message for a specific error type.
        
        Args:
            error_type: Error type (e.g., 'api_key_not_configured')
            
        Returns:
            Error message string
        """
        return self.get(f"error_messages.{error_type}", f"Error: {error_type}")
    
    def get_default(self, key: str) -> Any:
        """Get default value for a key.
        
        Args:
            key: Default key name
            
        Returns:
            Default value
        """
        return self.get(f"defaults.{key}")
    
    def get_limit(self, limit_type: str) -> int:
        """Get limit value for a specific type.
        
        Args:
            limit_type: Limit type (e.g., 'max_events', 'max_news_articles')
            
        Returns:
            Limit value
        """
        return self.get(f"data_processing.limits.{limit_type}", 5)
    
    def get_patterns(self, pattern_type: str) -> list:
        """Get regex patterns for data processing.
        
        Args:
            pattern_type: Pattern type (e.g., 'date_patterns', 'venue_patterns')
            
        Returns:
            List of regex patterns
        """
        return self.get(f"data_processing.event_patterns.{pattern_type}", [])
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration.
        
        Returns:
            Application configuration dictionary
        """
        return self.get("app", {})
    
    def get_langsmith_config(self) -> Dict[str, Any]:
        """Get LangSmith configuration.
        
        Returns:
            LangSmith configuration dictionary
        """
        return self.get("langsmith", {})
    
    def is_langsmith_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled.
        
        Returns:
            True if LangSmith is enabled and API key is available
        """
        langsmith_config = self.get_langsmith_config()
        if not langsmith_config.get("enabled", False):
            return False
        
        api_key = self.get_api_key("langsmith")
        return api_key is not None


# Global configuration instance
config = ConfigLoader()
