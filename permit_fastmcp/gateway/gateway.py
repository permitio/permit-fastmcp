"""
FastMCP Gateway - A dynamic proxy server for MCP servers with authentication and authorization.
"""

import asyncio
import logging
import urllib.parse
from typing import Dict, Optional, Any, List
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware
from fastmcp.server.dependencies import get_http_request, get_http_headers
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from permit_fastmcp.middleware.middleware import PermitMcpMiddleware
from permit_fastmcp.logger_config import setup_logging
from permit_fastmcp.gateway.config import get_settings, ServerConfigModel

logger = setup_logging(logger_name="permit_fastmcp.gateway")



class ProxyConfig:
    """Configuration for a proxy server."""
    
    def __init__(self, url: str, transport: str = "http", name: Optional[str] = None):
        self.url = url
        self.transport = transport
        self.name = name
    
    @classmethod
    def from_url_params(cls, remote_mcp: str, transport: str = "http", name: Optional[str] = None) -> "ProxyConfig":
        """Create a proxy config from URL parameters."""
        # URL decode the remote_mcp parameter
        decoded_url = urllib.parse.unquote(remote_mcp)
        return cls(decoded_url, transport, name)
    
    def _generate_descriptive_name(self) -> str:
        """Generate a descriptive server name from URL and transport."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            
            # Extract hostname
            hostname = parsed.hostname or parsed.netloc or "unknown"
            
            # Extract path and keep "/" separators
            path = parsed.path or ""
            if path.startswith("/"):
                path = path[1:]  # Remove leading slash
            
            # Build the name
            name_parts = [hostname]
            if path:
                name_parts.append(path)
            if self.transport != "http":
                name_parts.append(self.transport)
            
            # Join with "/" and remove trailing "/" and spaces
            result = "/".join(name_parts)
            return result.rstrip("/ ")
        except Exception as e:
            logger.warning(f"Failed to generate descriptive name for {self.url}: {e}")
            return f"proxy-{hash(self.url + self.transport)}"
    
    def get_server_name(self, existing_names: Optional[dict] = None) -> tuple[str, str]:
        """Get server name and canonical server name. Returns (server_name, canonical_server_name)."""
        if existing_names is None:
            existing_names = {}
        
        # Generate the pretty server name
        if self.name:
            # If a name is explicitly provided, use it (if no conflict)
            pretty_name = self.name.rstrip("/ ")
            if pretty_name not in existing_names:
                # No conflict, use the pretty name as-is
                canonical_name = self._generate_canonical_name()
                return pretty_name, canonical_name
        else:
            # Generate descriptive name
            pretty_name = self._generate_descriptive_name()
        
        # Clean the name of trailing "/" and spaces
        pretty_name = pretty_name.rstrip("/ ")
        
        # Check for conflicts and add hash if needed
        if pretty_name in existing_names:
            hash_suffix = str(hash(self.url + self.transport))[-8:]  # Use last 8 chars of hash
            pretty_name = f"{pretty_name}-{hash_suffix}"
        
        # Always generate canonical name
        canonical_name = self._generate_canonical_name()
        
        return pretty_name, canonical_name
    
    def _generate_canonical_name(self) -> str:
        """Generate a canonical server name that is always unique for this config."""
        # Use a hash of the URL and transport to create a unique identifier
        config_hash = str(hash(self.url + self.transport))
        return f"server_{config_hash}"
    
    def to_dict(self, server_name: str = "default") -> Dict[str, Any]:
        """Convert to dictionary for FastMCP.as_proxy in MCPConfig format."""
        return {
            "mcpServers": {
                server_name: {
                    "url": self.url,
                    "transport": self.transport
                }
            }
        }


class ServerRegistry:
    """Registry for managing remote MCP servers."""
    
    def __init__(self):
        self._servers: Dict[str, ServerConfigModel] = {}
        self._health_status: Dict[str, bool] = {}
        self._health_tasks: Dict[str, asyncio.Task] = {}
    
    def add_server(self, config: ServerConfigModel) -> None:
        """Add a server to the registry."""
        if config.name in self._servers:
            raise ValueError(f"Server '{config.name}' already exists")
        
        self._servers[config.name] = config
        self._health_status[config.name] = True  # Assume healthy initially
        logger.info(f"Added server: {config.name} -> {config.url}")
    
    def remove_server(self, name: str) -> None:
        """Remove a server from the registry."""
        if name not in self._servers:
            raise ValueError(f"Server '{name}' not found")
        
        # Cancel health check task if running
        if name in self._health_tasks:
            self._health_tasks[name].cancel()
            del self._health_tasks[name]
        
        del self._servers[name]
        del self._health_status[name]
        logger.info(f"Removed server: {name}")
    
    def get_server(self, name: str) -> Optional[ServerConfigModel]:
        """Get server configuration by name."""
        return self._servers.get(name)
    
    def list_servers(self) -> List[str]:
        """List all server names."""
        return list(self._servers.keys())
    
    def is_healthy(self, name: str) -> bool:
        """Check if a server is healthy."""
        return self._health_status.get(name, False)
    
    async def start_health_checks(self) -> None:
        """Start health check tasks for all servers."""
        for config in self._servers.values():
            await self._start_server_health_check(config)
    
    async def _start_server_health_check(self, config: ServerConfigModel) -> None:
        """Start health check task for a specific server."""
        if config.name in self._health_tasks:
            return  # Already running
        
        async def health_check_loop():
            while True:
                try:
                    # Simple health check - could be enhanced with actual MCP health check
                    self._health_status[config.name] = True
                    await asyncio.sleep(config.health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health check failed for {config.name}: {e}")
                    self._health_status[config.name] = False
                    await asyncio.sleep(config.health_check_interval)
        
        self._health_tasks[config.name] = asyncio.create_task(health_check_loop())


class GatewayMiddleware(Middleware):
    """Middleware for handling gateway-specific routing and authentication."""
    
    def __init__(self, registry: ServerRegistry, gateway_server: 'GatewayServer'):
        super().__init__()
        self.registry = registry
        self.gateway_server = gateway_server
    
    async def on_request(self, context, call_next):
        """Process the request through the gateway middleware."""
        # Extract proxy configuration from URL parameters
        proxy_config = self._extract_proxy_config(context)
        
        if not proxy_config:
            raise McpError(
                ErrorData(
                    code=-32001, 
                    message="No proxy configuration specified", 
                    data="Use 'remote_mcp' and 'transport' query parameters (e.g., ?remote_mcp=mymcp.com/mcp&transport=http&name=my-server)"
                )
            )
        
        try:
            # Get or create the proxy server and get the server names
            proxy_server, pretty_name, canonical_name = self.gateway_server._get_or_create_proxy(proxy_config)
            
            # Store the target server name in the context for the Permit middleware
            # This allows the Permit middleware to know which server's tools to authorize
            if hasattr(context, 'fastmcp_context'):
                context.fastmcp_context.target_server_name = pretty_name
            
            # Forward the request to the mounted proxy
            # This will be handled by FastMCP's built-in routing
            logger.debug(f"Routing request to proxy at /{pretty_name} for {proxy_config.url}")
            
            # The request will be automatically routed to the mounted proxy
            # by FastMCP's built-in routing mechanism
            return await call_next(context)
            
        except Exception as e:
            logger.error(f"Failed to route request to proxy: {e}")
            if e is McpError:
                raise e
            else:
                raise McpError(
                    ErrorData(
                        code=-32007,
                    message="Proxy routing failed",
                    data=f"Failed to route request to proxy: {str(e)}"
                )
            )
    
    def _extract_proxy_config(self, context) -> Optional[ProxyConfig]:
        """Extract proxy configuration from request context."""
        # Get HTTP request using FastMCP dependency
        request = get_http_request()
        
        if not request or not hasattr(request, 'query_params'):
            return None
        
        # Extract remote_mcp, transport, and name parameters
        remote_mcp = request.query_params.get('remote_mcp')
        transport = request.query_params.get('transport', 'http')
        name = request.query_params.get('name')  # Optional name parameter
        
        if not remote_mcp:
            return None
        
        try:
            return ProxyConfig.from_url_params(remote_mcp, transport, name)
        except Exception as e:
            logger.error(f"Failed to parse proxy config: {e}")
            return None


class GatewayServer:
    """Main gateway server that proxies requests to remote MCP servers using FastMCP's built-in proxy."""
    
    def __init__(
        self,
        permit_api_key: Optional[str] = None,
        permit_pdp_url: Optional[str] = None,
        enable_audit_logging: bool = True,
    ):
        # Get settings to extract environment variables
        settings = get_settings()
        
        # Use provided API key or fall back to environment variable
        api_key = permit_api_key or settings.permit_api_key
        pdp_url = permit_pdp_url or settings.permit_pdp_url
        
        self.registry = ServerRegistry()
        self.permit_middleware = PermitMcpMiddleware(
            permit_api_key=api_key,
            permit_pdp_url=pdp_url,
            enable_audit_logging=enable_audit_logging,
        )
        # Create gateway middleware with reference to self (will be set after initialization)
        self.gateway_middleware = None  # Will be set after initialization
        self.server: Optional[FastMCP] = None
        self._mounted_proxies: Dict[str, FastMCP] = {}  # canonical_name -> proxy_server
        self._existing_server_names: Dict[str, str] = {}  # canonical_name -> pretty_name
        
        # Set the gateway middleware after initialization to avoid circular reference
        self.gateway_middleware = GatewayMiddleware(self.registry, self)
    
    def add_server(self, name: str, url: str, **kwargs) -> None:
        """Add a remote server to the registry (for health checks and management)."""
        config = ServerConfigModel(name=name, url=url, **kwargs)
        self.registry.add_server(config)
    
    def remove_server(self, name: str) -> None:
        """Remove a remote server from the registry."""
        self.registry.remove_server(name)
    
    def list_servers(self) -> List[str]:
        """List all registered servers."""
        return self.registry.list_servers()
    
    def _create_and_mount_proxy(self, proxy_config: ProxyConfig, pretty_name: str, canonical_name: str) -> FastMCP:
        """Create a proxy server and mount it to the main server."""
        try:
            # Create proxy server using FastMCP.as_proxy with MCPConfig format
            proxy_server = FastMCP.as_proxy(proxy_config.to_dict(pretty_name))
            
            # Use pretty name as mount prefix (without leading "/")
            mount_path = pretty_name
            
            # Mount the proxy server
            if self.server:
                self.server.mount(proxy_server, prefix=mount_path)
                self._mounted_proxies[canonical_name] = proxy_server
                # Only add to existing server names after successful creation
                self._existing_server_names[canonical_name] = pretty_name
                logger.info(f"Mounted proxy '{pretty_name}' (canonical: {canonical_name}) at /{mount_path} for {proxy_config.url}")
            
            return proxy_server
            
        except Exception as e:
            logger.error(f"Failed to create proxy for {proxy_config.url}: {e}")
            raise McpError(
                ErrorData(
                    code=-32006,
                    message="Proxy creation failed",
                    data=f"Failed to create proxy for {proxy_config.url}: {str(e)}"
                )
            )
    
    def _get_or_create_proxy(self, proxy_config: ProxyConfig) -> tuple[FastMCP, str, str]:
        """Get existing proxy or create a new one. Returns (proxy_server, pretty_name, canonical_name)."""
        # Generate server names
        pretty_name, canonical_name = proxy_config.get_server_name(self._existing_server_names)
        
        # Check if proxy already exists using canonical name
        if canonical_name in self._mounted_proxies:
            return self._mounted_proxies[canonical_name], pretty_name, canonical_name
        
        proxy_server = self._create_and_mount_proxy(proxy_config, pretty_name, canonical_name)
        return proxy_server, pretty_name, canonical_name
    
    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Start the gateway server."""
        settings = get_settings()
        
        # Create the main server
        self.server = FastMCP("Gateway")
        
        # Add middleware to the server
        self.server.add_middleware(self.gateway_middleware)
        self.server.add_middleware(self.permit_middleware)
        
        # Start health checks if enabled
        if settings.enable_health_checks:
            await self.registry.start_health_checks()
        
        # Start the server
        await self.server.run_http_async(host=host, port=port)
        logger.info(f"Gateway started on {host}:{port}")
        logger.info("Use URL format: http://host:port/mcp/?remote_mcp=target_url&transport=http")
    
    async def stop(self) -> None:
        """Stop the gateway server."""
        if self.server:
            # Clean up mounted proxies
            for canonical_name, proxy_server in self._mounted_proxies.items():
                try:
                    pretty_name = self._existing_server_names.get(canonical_name, canonical_name)
                    # FastMCP proxies are automatically cleaned up
                    logger.info(f"Cleaned up proxy {pretty_name} (canonical: {canonical_name})")
                except Exception as e:
                    logger.error(f"Error cleaning up proxy {canonical_name}: {e}")
            
            self._mounted_proxies.clear()
            self._existing_server_names.clear()
            
            # FastMCP server is automatically cleaned up
            logger.info("Gateway stopped")


@asynccontextmanager
async def create_gateway(
    permit_api_key: Optional[str] = None,
    permit_pdp_url: Optional[str] = None,
    enable_audit_logging: bool = True,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> GatewayServer:
    """Context manager for creating and managing a gateway server."""
    # Get settings to extract environment variables
    settings = get_settings()
    
    # Use provided values or fall back to environment variables
    api_key = permit_api_key or settings.permit_api_key
    pdp_url = permit_pdp_url or settings.permit_pdp_url
    
    # Log configuration source for debugging
    if api_key:
        if permit_api_key:
            logger.debug("Using explicitly provided Permit API key")
        else:
            logger.debug("Using Permit API key from environment variable GATEWAY_PERMIT_API_KEY")
    else:
        logger.warning("No Permit API key provided - authorization will be disabled")
    
    if pdp_url:
        if permit_pdp_url:
            logger.debug(f"Using explicitly provided PDP URL: {pdp_url}")
        else:
            logger.debug(f"Using PDP URL from environment variable GATEWAY_PERMIT_PDP_URL: {pdp_url}")
    else:
        logger.warning("No PDP URL provided - authorization will be disabled")
    
    gateway = GatewayServer(
        permit_api_key=api_key,
        permit_pdp_url=pdp_url,
        enable_audit_logging=enable_audit_logging,
    )
    
    try:
        await gateway.start(host=host, port=port)
        yield gateway
    finally:
        await gateway.stop()


async def main():
    """Main entry point for the gateway server."""
    setup_logging()
    
    # Example usage
    async with create_gateway(
        permit_pdp_url="http://localhost:7766",
        host="0.0.0.0",
        port=8080,
    ) as gateway:
        
        # Add some example servers for health checks
        gateway.add_server("server1", "http://localhost:8001")
        gateway.add_server("server2", "http://localhost:8002")
        
        logger.info("Gateway running. Press Ctrl+C to stop.")
        logger.info("Example usage:")
        logger.info("  http://localhost:8080/mcp/?remote_mcp=localhost:8001/mcp&transport=http")
        logger.info("  http://localhost:8080/mcp/?remote_mcp=localhost:8002/mcp&transport=http")
        
        try:
            # Keep the server running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
