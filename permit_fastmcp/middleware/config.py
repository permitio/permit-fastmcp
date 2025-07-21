"""
Configuration settings for PermitMcpMiddleware using pydantic-settings.

All settings can be configured via environment variables with sensible
defaults.
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
    """Configuration settings for PermitMcpMiddleware.

    All settings can be configured via environment variables with the prefix PERMIT_MCP_.
    """

    model_config = SettingsConfigDict(
        env_prefix="PERMIT_MCP_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Methods recognized for resource/action mapping (PERMIT_MCP_KNOWN_METHODS)
    known_methods: List[str] = [
        "tools/list",
        "prompts/list",
        "resources/list",
        "tools/call",
        "resources/read",
        "prompts/get",
    ]

    # Methods that bypass authorization checks (PERMIT_MCP_BYPASSED_METHODS)
    bypassed_methods: List[str] = [
        "initialize",
        "ping",
        "notifications/*",
    ]

    # Prefix for Permit.io action mapping (PERMIT_MCP_ACTION_PREFIX)
    action_prefix: str = ""
    # Prefix for Permit.io resource mapping (PERMIT_MCP_RESOURCE_PREFIX)
    resource_prefix: str = "mcp_"

    # Name of the MCP server, used as resource name for tool calls (PERMIT_MCP_MCP_SERVER_NAME)
    mcp_server_name: str = "mcp_server"

    # Permit.io PDP URL (PERMIT_MCP_PERMIT_PDP_URL)
    permit_pdp_url: str = "http://localhost:7766"
    # Permit.io API key (PERMIT_MCP_PERMIT_API_KEY)
    permit_api_key: str = ""

    # Enable or disable audit logging (PERMIT_MCP_ENABLE_AUDIT_LOGGING)
    enable_audit_logging: bool = True

    # Identity extraction mode: 'jwt', 'fixed', 'header', or 'source' (PERMIT_MCP_IDENTITY_MODE)
    identity_mode: IdentityMode = IdentityMode.fixed
    # Header to extract identity from (for 'jwt' and 'header' modes) (PERMIT_MCP_IDENTITY_HEADER)
    identity_header: str = "Authorization"
    # Regex to extract token from header (for 'jwt' mode) (PERMIT_MCP_IDENTITY_HEADER_REGEX)
    identity_header_regex: str = r"[Bb]earer (.+)"
    # JWT secret or public key (for 'jwt' mode) (PERMIT_MCP_IDENTITY_JWT_SECRET)
    identity_jwt_secret: str = ""
    # JWT field to use as identity (for 'jwt' mode) (PERMIT_MCP_IDENTITY_JWT_FIELD)
    identity_jwt_field: str = "sub"
    # Fixed identity value (for 'fixed' mode) (PERMIT_MCP_IDENTITY_FIXED_VALUE)
    identity_fixed_value: str = "client"

    # Allowed JWT algorithms (for 'jwt' mode) (PERMIT_MCP_JWT_ALGORITHMS)
    jwt_algorithms: list[str] = ["HS256", "RS256"]

    # Whether to prefix resources with the MCP server name (for non-tool calls) (PERMIT_MCP_PREFIX_RESOURCE_WITH_SERVER_NAME)
    prefix_resource_with_server_name: bool = True

    # Whether to flatten tool arguments as individual attributes with prefix (PERMIT_MCP_FLATTEN_TOOL_ARGUMENTS)
    flatten_tool_arguments: bool = True
    # Prefix for flattened tool argument attributes (PERMIT_MCP_TOOL_ARGUMENT_PREFIX)
    tool_argument_prefix: str = "arg_"


SETTINGS = Settings()


# RESOURCE TYPES
