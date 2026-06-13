"""
Configuration management for IBM BAW MCP Server.

Handles environment variables, validation, and configuration settings.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Server configuration with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # IBM CP4BA Configuration
    cp4ba_base_url: str = Field(
        ...,
        description="Base URL of the CP4BA instance",
        alias="CP4BA_BASE_URL"
    )
    
    cp4ba_username: str = Field(
        ...,
        description="CP4BA username",
        alias="CP4BA_USERNAME"
    )
    
    cp4ba_password: str = Field(
        ...,
        description="CP4BA password",
        alias="CP4BA_PASSWORD"
    )
    
    token_lifetime: int = Field(
        default=7200,
        description="Token lifetime in seconds",
        alias="TOKEN_LIFETIME",
        ge=60,
        le=86400
    )
    
    # Server Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        alias="LOG_LEVEL"
    )
    
    request_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        alias="REQUEST_TIMEOUT",
        ge=5,
        le=300
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests",
        alias="MAX_RETRIES",
        ge=0,
        le=10
    )
    
    verify_ssl: bool = Field(
        default=False,
        description="Verify SSL certificates (set to True for production)",
        alias="VERIFY_SSL"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
        alias="RATE_LIMIT_ENABLED"
    )
    
    rate_limit_calls: int = Field(
        default=100,
        description="Maximum number of calls per period",
        alias="RATE_LIMIT_CALLS",
        ge=1
    )
    
    rate_limit_period: int = Field(
        default=60,
        description="Rate limit period in seconds",
        alias="RATE_LIMIT_PERIOD",
        ge=1
    )
    
    @field_validator("cp4ba_base_url")
    @classmethod
    def validate_base_url(cls, url_value: str) -> str:
        """
        Validate and normalize base URL.
        
        Args:
            url_value: Base URL to validate
            
        Returns:
            Normalized URL
            
        Raises:
            ValueError: If URL is invalid
        """
        if not url_value:
            raise ValueError("CP4BA_BASE_URL cannot be empty")
        
        # Remove trailing slash
        normalized_url = url_value.rstrip("/")
        
        # Ensure it starts with http:// or https://
        if not normalized_url.startswith(("http://", "https://")):
            raise ValueError("CP4BA_BASE_URL must start with http:// or https://")
        
        return normalized_url
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, level_value: str) -> str:
        """
        Validate log level.
        
        Args:
            level_value: Log level to validate
            
        Returns:
            Uppercase log level
            
        Raises:
            ValueError: If log level is invalid
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        normalized_level = level_value.upper()
        
        if normalized_level not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        
        return normalized_level
    
    def get_ssl_verify(self) -> bool:
        """
        Get SSL verification setting.
        
        Returns:
            SSL verification boolean
        """
        return self.verify_ssl
    
    def get_timeout(self) -> float:
        """
        Get request timeout as float.
        
        Returns:
            Timeout in seconds
        """
        return float(self.request_timeout)


def load_config() -> ServerConfig:
    """
    Load and validate configuration.
    
    Returns:
        Validated ServerConfig instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        config = ServerConfig()  # type: ignore[call-arg]
        return config
    except Exception as e:
        raise ValueError(f"Configuration error: {e}")


# Global config instance (lazy loaded)
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """
    Get the global configuration instance.
    
    Returns:
        ServerConfig instance
    """
    global _config
    
    if _config is None:
        _config = load_config()
    
    return _config

# Made with Bob
