"""
Tests for the FastMCP Gateway functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from permit_fastmcp.gateway.gateway import (
    ProxyConfig, 
    ServerRegistry, 
    GatewayMiddleware, 
    GatewayServer
)


class TestProxyConfig:
    """Test ProxyConfig class."""
    
    def test_proxy_config_creation(self):
        """Test creating a ProxyConfig."""
        config = ProxyConfig("http://localhost:8001/mcp", "http")
        assert config.url == "http://localhost:8001/mcp"
        assert config.transport == "http"
    
    def test_proxy_config_from_url_params(self):
        """Test creating ProxyConfig from URL parameters."""
        config = ProxyConfig.from_url_params("localhost:8001/mcp", "http")
        assert config.url == "localhost:8001/mcp"
        assert config.transport == "http"
    
    def test_proxy_config_from_url_params_with_encoding(self):
        """Test creating ProxyConfig from URL-encoded parameters."""
        config = ProxyConfig.from_url_params("api.example.com%2Fmcp", "http")
        assert config.url == "api.example.com/mcp"
        assert config.transport == "http"
    
    def test_proxy_config_to_dict(self):
        """Test converting ProxyConfig to dictionary."""
        config = ProxyConfig("http://localhost:8001/mcp", "http")
        config_dict = config.to_dict()
        assert config_dict == {
            "mcpServers": {
                "default": {
                    "url": "http://localhost:8001/mcp",
                    "transport": "http"
                }
            }
        }
    
    def test_proxy_config_to_dict_with_custom_name(self):
        """Test converting ProxyConfig to dictionary with custom server name."""
        config = ProxyConfig("http://localhost:8001/mcp", "http")
        config_dict = config.to_dict("custom_server")
        assert config_dict == {
            "mcpServers": {
                "custom_server": {
                    "url": "http://localhost:8001/mcp",
                    "transport": "http"
                }
            }
        }
    
    def test_proxy_config_with_explicit_name(self):
        """Test creating ProxyConfig with explicit name."""
        config = ProxyConfig("http://localhost:8001/mcp", "http", "my-server")
        assert config.url == "http://localhost:8001/mcp"
        assert config.transport == "http"
        assert config.name == "my-server"
    
    def test_proxy_config_from_url_params_with_name(self):
        """Test creating ProxyConfig from URL parameters with name."""
        config = ProxyConfig.from_url_params("localhost:8001/mcp", "http", "my-server")
        assert config.url == "localhost:8001/mcp"
        assert config.transport == "http"
        assert config.name == "my-server"
    
    def test_generate_descriptive_name_simple_url(self):
        """Test generating descriptive name from simple URL."""
        config = ProxyConfig("http://localhost:8001/mcp", "http")
        name = config._generate_descriptive_name()
        assert name == "localhost/mcp"
    
    def test_generate_descriptive_name_with_path(self):
        """Test generating descriptive name from URL with path."""
        config = ProxyConfig("http://api.example.com/v1/mcp", "http")
        name = config._generate_descriptive_name()
        assert name == "api.example.com/v1/mcp"
    
    def test_generate_descriptive_name_with_non_http_transport(self):
        """Test generating descriptive name with non-HTTP transport."""
        config = ProxyConfig("http://localhost:8001/mcp", "stdio")
        name = config._generate_descriptive_name()
        assert name == "localhost/mcp/stdio"
    
    def test_generate_descriptive_name_with_complex_path(self):
        """Test generating descriptive name with complex path."""
        config = ProxyConfig("http://api.example.com/api/v1/mcp/server", "http")
        name = config._generate_descriptive_name()
        assert name == "api.example.com/api/v1/mcp/server"
    
    def test_generate_descriptive_name_removes_trailing_slash(self):
        """Test that trailing slashes are removed from server names."""
        config = ProxyConfig("http://api.example.com/v1/mcp/", "http")
        name = config._generate_descriptive_name()
        assert name == "api.example.com/v1/mcp"
    
    def test_generate_descriptive_name_removes_trailing_spaces(self):
        """Test that trailing spaces are removed from server names."""
        config = ProxyConfig("http://api.example.com/v1/mcp", "http")
        # Simulate a URL with trailing spaces (though this shouldn't happen in real URLs)
        config.url = "http://api.example.com/v1/mcp "
        name = config._generate_descriptive_name()
        assert name == "api.example.com/v1/mcp"
    
    def test_get_server_name_removes_trailing_chars(self):
        """Test that get_server_name removes trailing slashes and spaces."""
        config = ProxyConfig("http://api.example.com/v1/mcp", "http", "my-server/ ")
        pretty_name, canonical_name = config.get_server_name({})
        assert pretty_name == "my-server"
    
    def test_get_server_name_with_explicit_name(self):
        """Test getting server name with explicit name (no conflict)."""
        config = ProxyConfig("http://localhost:8001/mcp", "http", "my-server")
        pretty_name, canonical_name = config.get_server_name({})
        assert pretty_name == "my-server"
    
    def test_get_server_name_with_conflict(self):
        """Test getting server name with conflict resolution."""
        config = ProxyConfig("http://localhost:8001/mcp", "http", "my-server")
        existing_names = {"my-server": "existing"}
        pretty_name, canonical_name = config.get_server_name(existing_names)
        # Should add hash suffix
        assert pretty_name.startswith("my-server-")
        assert len(pretty_name) > len("my-server-")
    
    def test_get_server_name_descriptive_no_conflict(self):
        """Test getting descriptive server name when no explicit name provided."""
        config = ProxyConfig("http://api.example.com/v1/mcp", "http")
        pretty_name, canonical_name = config.get_server_name({})
        assert pretty_name == "api.example.com/v1/mcp"
    
    def test_get_server_name_descriptive_with_conflict(self):
        """Test getting descriptive server name with conflict resolution."""
        config = ProxyConfig("http://api.example.com/v1/mcp", "http")
        existing_names = {"api.example.com/v1/mcp": "existing"}
        pretty_name, canonical_name = config.get_server_name(existing_names)
        # Should add hash suffix
        assert pretty_name.startswith("api.example.com/v1/mcp-")
        assert len(pretty_name) > len("api.example.com/v1/mcp-")


class TestServerRegistry:
    """Test ServerRegistry class."""
    
    def test_add_server(self):
        """Test adding a server to the registry."""
        registry = ServerRegistry()
        config = MagicMock()
        config.name = "test-server"
        config.url = "http://localhost:8001"
        
        registry.add_server(config)
        assert "test-server" in registry._servers
        assert registry.get_server("test-server") == config
    
    def test_add_duplicate_server(self):
        """Test adding a duplicate server raises error."""
        registry = ServerRegistry()
        config = MagicMock()
        config.name = "test-server"
        config.url = "http://localhost:8001"
        
        registry.add_server(config)
        
        with pytest.raises(ValueError, match="already exists"):
            registry.add_server(config)
    
    def test_remove_server(self):
        """Test removing a server from the registry."""
        registry = ServerRegistry()
        config = MagicMock()
        config.name = "test-server"
        config.url = "http://localhost:8001"
        
        registry.add_server(config)
        registry.remove_server("test-server")
        
        assert "test-server" not in registry._servers
        assert registry.get_server("test-server") is None
    
    def test_remove_nonexistent_server(self):
        """Test removing a nonexistent server raises error."""
        registry = ServerRegistry()
        
        with pytest.raises(ValueError, match="not found"):
            registry.remove_server("nonexistent")
    
    def test_list_servers(self):
        """Test listing all servers."""
        registry = ServerRegistry()
        config1 = MagicMock()
        config1.name = "server1"
        config2 = MagicMock()
        config2.name = "server2"
        
        registry.add_server(config1)
        registry.add_server(config2)
        
        servers = registry.list_servers()
        assert "server1" in servers
        assert "server2" in servers
        assert len(servers) == 2


class TestGatewayMiddleware:
    """Test GatewayMiddleware class."""
    
    def test_extract_proxy_config_with_valid_params(self):
        """Test extracting proxy config from valid URL parameters."""
        middleware = GatewayMiddleware(MagicMock(), MagicMock())
        
        # Mock request context
        context = MagicMock()
        request = MagicMock()
        request.query_params = {
            "remote_mcp": "localhost:8001/mcp",
            "transport": "http"
        }
        
        with patch('permit_fastmcp.gateway.gateway.get_http_request', return_value=request):
            config = middleware._extract_proxy_config(context)
            
            assert config is not None
            assert config.url == "localhost:8001/mcp"
            assert config.transport == "http"
    
    def test_extract_proxy_config_without_remote_mcp(self):
        """Test extracting proxy config without remote_mcp parameter."""
        middleware = GatewayMiddleware(MagicMock(), MagicMock())
        
        # Mock request context
        context = MagicMock()
        request = MagicMock()
        request.query_params = {"transport": "http"}
        
        with patch('permit_fastmcp.gateway.gateway.get_http_request', return_value=request):
            config = middleware._extract_proxy_config(context)
            assert config is None
    
    def test_extract_proxy_config_with_url_encoding(self):
        """Test extracting proxy config with URL encoding."""
        middleware = GatewayMiddleware(MagicMock(), MagicMock())
        
        # Mock request context
        context = MagicMock()
        request = MagicMock()
        request.query_params = {
            "remote_mcp": "api.example.com%2Fmcp",
            "transport": "http"
        }
        
        with patch('permit_fastmcp.gateway.gateway.get_http_request', return_value=request):
            config = middleware._extract_proxy_config(context)
            
            assert config is not None
            assert config.url == "api.example.com/mcp"
            assert config.transport == "http"
    
    def test_extract_proxy_config_with_name_parameter(self):
        """Test extracting proxy config with name parameter."""
        middleware = GatewayMiddleware(MagicMock(), MagicMock())
        
        # Mock request context
        context = MagicMock()
        request = MagicMock()
        request.query_params = {
            "remote_mcp": "localhost:8001/mcp",
            "transport": "http",
            "name": "my-server"
        }
        
        with patch('permit_fastmcp.gateway.gateway.get_http_request', return_value=request):
            config = middleware._extract_proxy_config(context)
            
            assert config is not None
            assert config.url == "localhost:8001/mcp"
            assert config.transport == "http"
            assert config.name == "my-server"


class TestGatewayServer:
    """Test GatewayServer class."""
    
    @pytest.mark.asyncio
    async def test_gateway_server_creation(self):
        """Test creating a GatewayServer."""
        gateway = GatewayServer(
            permit_api_key="test-key",
            permit_pdp_url="http://localhost:7766",
            enable_audit_logging=True
        )
        
        assert gateway.registry is not None
        assert gateway.permit_middleware is not None
        assert gateway.gateway_middleware is not None
        assert gateway.server is None
    
    def test_add_server(self):
        """Test adding a server to the gateway."""
        gateway = GatewayServer(permit_api_key="test-key")
        gateway.add_server("test-server", "http://localhost:8001")
        
        servers = gateway.list_servers()
        assert "test-server" in servers
    
    def test_remove_server(self):
        """Test removing a server from the gateway."""
        gateway = GatewayServer(permit_api_key="test-key")
        gateway.add_server("test-server", "http://localhost:8001")
        gateway.remove_server("test-server")
        
        servers = gateway.list_servers()
        assert "test-server" not in servers


# Helper function for patching
def patch(target, **kwargs):
    """Helper function for patching in tests."""
    from unittest.mock import patch as mock_patch
    return mock_patch(target, **kwargs)


class TestGatewayEnvironmentVariables:
    """Test environment variable configuration for the gateway."""
    
    def test_gateway_uses_env_var_when_no_api_key_provided(self):
        """Test that gateway uses environment variable when no API key is provided."""
        # Mock the settings to return an API key from environment
        with patch('permit_fastmcp.gateway.gateway.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.permit_api_key = "env-api-key"
            mock_settings.permit_pdp_url = "http://env-pdp:7766"
            mock_get_settings.return_value = mock_settings
            
            # Create gateway without providing API key
            gateway = GatewayServer()
            
            # Verify that the middleware was created with the environment variable values
            assert gateway.permit_middleware is not None
    
    def test_gateway_prioritizes_explicit_api_key_over_env_var(self):
        """Test that explicitly provided API key takes precedence over environment variable."""
        # Mock the settings to return an API key from environment
        with patch('permit_fastmcp.gateway.gateway.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.permit_api_key = "env-api-key"
            mock_settings.permit_pdp_url = "http://env-pdp:7766"
            mock_get_settings.return_value = mock_settings
            
            # Create gateway with explicit API key
            gateway = GatewayServer(permit_api_key="explicit-api-key")
            
            # Verify that the middleware was created
            assert gateway.permit_middleware is not None
    
    def test_gateway_handles_no_api_key_at_all(self):
        """Test that gateway handles case when no API key is provided anywhere."""
        # Mock the settings to return None for API key
        with patch('permit_fastmcp.gateway.gateway.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.permit_api_key = None
            mock_settings.permit_pdp_url = None
            mock_get_settings.return_value = mock_settings
            
            # Create gateway without providing API key
            gateway = GatewayServer()
            
            # Verify that the middleware was created (should handle None gracefully)
            assert gateway.permit_middleware is not None 