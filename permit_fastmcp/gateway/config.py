"""
Configuration management for the FastMCP Gateway.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ServerConfigModel(BaseModel):
    """Configuration model for a remote server."""
    name: str = Field(..., description="Unique name for the server")
    url: str = Field(..., description="URL of the remote MCP server")
    auth_required: bool = Field(True, description="Whether authentication is required")
    health_check_interval: int = Field(30, description="Health check interval in seconds")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GatewaySettings(BaseSettings):
    """Gateway configuration settings."""
    
    # Server settings
    host: str = Field("0.0.0.0", description="Host to bind the gateway to")
    port: int = Field(8080, description="Port to bind the gateway to")
    
    # Permit settings
    permit_api_key: Optional[str] = Field(None, description="Permit.io API key")
    permit_pdp_url: Optional[str] = Field("http://localhost:7766", description="Permit PDP URL")
    enable_audit_logging: bool = Field(True, description="Enable audit logging")
    
    # Gateway settings
    default_timeout: int = Field(30, description="Default request timeout")
    max_connections: int = Field(100, description="Maximum concurrent connections")
    enable_health_checks: bool = Field(True, description="Enable health checks")
    
    # Logging settings
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Security settings
    enable_cors: bool = Field(False, description="Enable CORS")
    allowed_origins: list[str] = Field(default_factory=list, description="Allowed CORS origins")
    
    class Config:
        env_prefix = "GATEWAY_"
        env_file = ".env"
        case_sensitive = False


# Global settings instance
SETTINGS = GatewaySettings()


def get_settings() -> GatewaySettings:
    """Get the current gateway settings."""
    return SETTINGS


def update_settings(**kwargs) -> None:
    """Update gateway settings."""
    global SETTINGS
    for key, value in kwargs.items():
        if hasattr(SETTINGS, key):
            setattr(SETTINGS, key, value)
        else:
            raise ValueError(f"Unknown setting: {key}")


def load_config_from_file(config_path: str) -> None:
    """Load configuration from a file."""
    # This could be enhanced to load from YAML/JSON files
    # For now, we'll use environment variables and .env files
    pass 