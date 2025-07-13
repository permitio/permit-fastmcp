"""
Configuration settings for PermitMcpMiddleware using pydantic-settings.

All settings can be configured via environment variables with sensible defaults.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class IdentityMode(str, Enum):
    jwt = "jwt"
    fixed = "fixed"
    header = "header"
    source = "source"

class Settings(BaseSettings):
    """Configuration settings for PermitMcpMiddleware."""
    
    model_config = SettingsConfigDict(
        env_prefix="PERMIT_MCP_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Methods recognized for resource/action mapping
    known_methods: List[str] = [
        "tools/list",
        "prompts/list", 
        "resources/list",
        "tools/call",
        "resources/read",
        "prompts/get",
    ]
    
    # Methods that bypass authorization checks
    bypassed_methods: List[str] = [
        "initialize",
        "ping",
        "notifications/*",
    ]
    
    # Prefixes for mapping MCP methods to Permit.io actions and resources
    action_prefix: str = ""
    resource_prefix: str = "mcp_"
    
    # Name of the MCP server (used as resource name for tool calls)
    mcp_server_name: str = "mcp_server"
    
    # Permit.io configuration
    permit_pdp_url: str = "http://localhost:7766"
    permit_api_key: str = ""
    
    # Logging configuration
    enable_audit_logging: bool = True

    # Identity extraction mode: 'jwt', 'fixed', 'header', or 'source'
    identity_mode: IdentityMode = IdentityMode.fixed
    # Header to extract identity from (for 'jwt' and 'header' modes)
    identity_header: str = "Authorization"
    # Regex to extract token from header (for 'jwt' mode)
    identity_header_regex: str = r"[Bb]earer (.+)"
    # JWT secret or public key (for 'jwt' mode)
    identity_jwt_secret: str = ""
    # JWT field to use as identity (for 'jwt' mode)
    identity_jwt_field: str = "sub"
    # Fixed identity value (for 'fixed' mode)
    identity_fixed_value: str = "client"

    # Allowed JWT algorithms (for 'jwt' mode)
    jwt_algorithms: list[str] = ["HS256", "RS256"]

    # Whether to prefix resources with the MCP server name (for non-tool calls)
    prefix_resource_with_server_name: bool = True


SETTINGS = Settings()


# RESOURCE TYPES
