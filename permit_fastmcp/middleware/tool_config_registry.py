"""
Singleton registry for tool-specific identity configurations.

This module provides a centralized registry that maps server name + tool name
to identity configuration settings, allowing per-tool identity mode overrides.
"""

from typing import Optional, Dict, Any
from .config import IdentityMode


class ToolConfigRegistry:
    """
    Singleton registry for storing tool-specific identity configurations.
    
    Maps (server_name, tool_name) tuples to identity configuration dictionaries.
    """
    
    _instance = None
    _configs: Dict[tuple[str, str], Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolConfigRegistry, cls).__new__(cls)
        return cls._instance
    
    def register_tool_config(
        self,
        server_name: str,
        tool_name: str,
        mode: IdentityMode,
        header_name: Optional[str] = None,
        fixed_value: Optional[str] = None,
        jwt_secret: Optional[str] = None,
        jwt_field: Optional[str] = None,
        bypass_authorization: bool = False,
    ) -> None:
        """
        Register identity configuration for a specific tool.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            mode: Identity extraction mode
            header_name: Header name for header/jwt modes
            fixed_value: Fixed identity value for fixed mode
            jwt_secret: JWT secret for jwt mode
            jwt_field: JWT field for jwt mode
            bypass_authorization: Whether to bypass authorization for this tool
        """
        key = (server_name, tool_name)
        self._configs[key] = {
            'mode': mode,
            'header_name': header_name,
            'fixed_value': fixed_value,
            'jwt_secret': jwt_secret,
            'jwt_field': jwt_field,
            'bypass_authorization': bypass_authorization,
        }
    
    def get_tool_config(self, server_name: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get identity configuration for a specific tool.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            
        Returns:
            Configuration dictionary or None if not found
        """
        key = (server_name, tool_name)
        return self._configs.get(key)
    
    def clear(self) -> None:
        """Clear all registered configurations (useful for testing)."""
        self._configs.clear()


# Global instance
tool_config_registry = ToolConfigRegistry() 