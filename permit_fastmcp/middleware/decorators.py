"""
Decorators for Permit.io MCP middleware configuration.

This module provides decorators that allow fine-grained control over
identity extraction and authorization settings on a per-tool basis.
"""

import functools
from typing import Optional, Callable, Any
from enum import Enum
from .config import IdentityMode
from .tool_config_registry import tool_config_registry


def identity_mode(
    mode: IdentityMode,
    header_name: Optional[str] = None,
    fixed_value: Optional[str] = None,
    jwt_secret: Optional[str] = None,
    jwt_field: Optional[str] = None,
):
    """
    Decorator to set the identity extraction mode for a specific tool.
    
    Args:
        mode: The identity extraction mode to use for this tool
        header_name: Header name to extract identity from (for 'header' and 'jwt' modes)
        fixed_value: Fixed identity value to use (for 'fixed' mode)
        jwt_secret: JWT secret for verification (for 'jwt' mode)
        jwt_field: JWT field to extract identity from (for 'jwt' mode)
    
    Example:
        @mcp.tool
        @identity_mode(IdentityMode.jwt, jwt_secret="my_secret")
        def secure_tool():
            return "This tool uses JWT authentication"
            
        @mcp.tool
        @identity_mode(IdentityMode.fixed, fixed_value="admin")
        def admin_tool():
            return "This tool always uses admin identity"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Store the configuration in the registry when the function is called
        # We'll need to get the server name and tool name at runtime
        original_func = func
        
        def register_config(server_name: str, tool_name: str):
            tool_config_registry.register_tool_config(
                server_name=server_name,
                tool_name=tool_name,
                mode=mode,
                header_name=header_name,
                fixed_value=fixed_value,
                jwt_secret=jwt_secret,
                jwt_field=jwt_field,
            )
        
        # Store the registration function on the wrapper
        wrapper._register_permit_config = register_config
        return wrapper
    
    return decorator


def bypass_authorization():
    """
    Decorator to bypass authorization for a specific tool.
    
    Example:
        @mcp.tool
        @bypass_authorization()
        def public_tool():
            return "This tool doesn't require authorization"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        def register_config(server_name: str, tool_name: str):
            tool_config_registry.register_tool_config(
                server_name=server_name,
                tool_name=tool_name,
                mode=IdentityMode.fixed,  # Doesn't matter for bypass
                bypass_authorization=True,
            )
        
        # Store the registration function on the wrapper
        wrapper._register_permit_config = register_config
        return wrapper
    
    return decorator


def register_tool_config(server_name: str, tool_name: str, func: Callable) -> None:
    """
    Register tool configuration from a decorated function.
    
    This function should be called when a tool is registered with FastMCP.
    
    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool
        func: The decorated function
    """
    if hasattr(func, '_register_permit_config'):
        func._register_permit_config(server_name, tool_name)


def get_tool_identity_config(server_name: str, tool_name: str) -> Optional[dict]:
    """
    Get the identity configuration for a tool.
    
    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool
        
    Returns:
        Dictionary with identity configuration or None if not configured
    """
    return tool_config_registry.get_tool_config(server_name, tool_name) 