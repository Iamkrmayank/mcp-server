"""
Configuration Management
Centralized configuration for the Agno orchestration system.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


@dataclass
class AgnoConfig:
    """Configuration for the Agno orchestration system."""
    
    # API Keys
    tavily_api_key: Optional[str] = None
    jina_api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "agno_system.log"
    
    # Execution
    timeout_seconds: int = 30
    max_retries: int = 3
    min_confidence: float = 0.5
    
    # Tool Configuration
    max_results: int = 5
    search_depth: str = "basic"  # "basic" or "advanced"
    
    @classmethod
    def from_env(cls) -> "AgnoConfig":
        """Create configuration from environment variables."""
        return cls(
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            jina_api_key=os.getenv("JINA_API_KEY"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "agno_system.log"),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            min_confidence=float(os.getenv("MIN_CONFIDENCE", "0.5")),
            max_results=int(os.getenv("MAX_RESULTS", "5")),
            search_depth=os.getenv("SEARCH_DEPTH", "basic")
        )
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if at least one API key is available
        if not self.tavily_api_key and not self.jina_api_key:
            return False, "At least one API key (Tavily or Jina) must be configured"
        
        # Validate timeout
        if self.timeout_seconds <= 0:
            return False, "Timeout must be greater than 0"
        
        # Validate confidence threshold
        if not 0.0 <= self.min_confidence <= 1.0:
            return False, "Min confidence must be between 0.0 and 1.0"
        
        # Validate max results
        if self.max_results <= 0:
            return False, "Max results must be greater than 0"
        
        # Validate search depth
        if self.search_depth not in ["basic", "advanced"]:
            return False, "Search depth must be 'basic' or 'advanced'"
        
        return True, None
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "tavily_api_key": "***" if self.tavily_api_key else None,
            "jina_api_key": "***" if self.jina_api_key else None,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "min_confidence": self.min_confidence,
            "max_results": self.max_results,
            "search_depth": self.search_depth
        }


# Global configuration instance
_config_instance: Optional[AgnoConfig] = None


def get_config() -> AgnoConfig:
    """Get or create the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AgnoConfig.from_env()
    return _config_instance


def reload_config() -> AgnoConfig:
    """Reload configuration from environment."""
    global _config_instance
    load_dotenv(override=True)
    _config_instance = AgnoConfig.from_env()
    return _config_instance

