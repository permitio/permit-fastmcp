# FastMCP Gateway Refactoring

## Overview

The FastMCP Gateway has been refactored to use FastMCP's built-in proxy functionality instead of a custom proxy implementation. This change leverages FastMCP's native `as_proxy()` and `mount()` capabilities for better integration and performance.

## Key Changes

### 1. Removed Custom Proxy Implementation

- **Deleted**: `permit_fastmcp/gateway/proxy.py` - Custom proxy server implementation
- **Replaced**: `DynamicProxyServer` and `GatewayProxyMiddleware` with FastMCP's built-in functionality

### 2. Updated Gateway Architecture

#### Before (Custom Proxy):
```python
# Custom proxy server with manual routing
class DynamicProxyServer(ProxyServer):
    async def _route_request(self, context, server_name, server_url):
        # Manual request forwarding logic
        pass
```

#### After (FastMCP Built-in):
```python
# FastMCP server with mounted proxies
class GatewayServer:
    def _create_and_mount_proxy(self, proxy_config: ProxyConfig) -> FastMCP:
        # Create proxy using FastMCP.as_proxy()
        proxy_server = FastMCP.as_proxy(proxy_config.to_dict())
        
        # Mount the proxy server using server name as prefix (without leading "/")
        server_name = proxy_config.get_server_name(self._existing_server_names)
        self.server.mount(proxy_server, prefix=server_name)
        
        return proxy_server
```

### 3. URL-Based Routing

The gateway now uses URL parameters to dynamically route requests:

#### URL Format:
```
http://gateway-host:port/mcp/?remote_mcp=target-server-url&transport=protocol&name=server-name
```

#### Parameters:
- `remote_mcp`: The URL of the target MCP server (required, URL-encoded)
- `transport`: The transport protocol (optional, default: `http`)
- `name`: Custom server name (optional, auto-generated if not provided)

#### Examples:
```bash
# Connect to local MCP server
http://localhost:8080/mcp/?remote_mcp=localhost:8001/mcp&transport=http

# Connect to remote MCP server
http://localhost:8080/mcp/?remote_mcp=api.example.com/mcp&transport=http

# Connect with URL encoding
http://localhost:8080/mcp/?remote_mcp=api.example.com%2Fmcp&transport=http

# Connect with different transport
http://localhost:8080/mcp/?remote_mcp=localhost:8001/mcp&transport=stdio

# Connect with custom server name
http://localhost:8080/mcp/?remote_mcp=api.example.com/mcp&transport=http&name=my-server

# Auto-generated names (when no name provided)
# http://localhost:8080/mcp/?remote_mcp=api.example.com/v1/mcp&transport=http
# → Server name: "api.example.com/v1/mcp"
# → Mount path: "/api.example.com/v1/mcp"
# 
# http://localhost:8080/mcp/?remote_mcp=localhost:8001/mcp&transport=stdio
# → Server name: "localhost/mcp/stdio"
# → Mount path: "/localhost/mcp/stdio"
# 
# Custom names
# http://localhost:8080/mcp/?remote_mcp=api.example.com/mcp&transport=http&name=my-server
# → Server name: "my-server"
# → Mount path: "/my-server"
```

### 4. New Components

#### ProxyConfig Class
```python
class ProxyConfig:
    """Configuration for a proxy server."""
    
    def __init__(self, url: str, transport: str = "http", name: Optional[str] = None):
        self.url = url
        self.transport = transport
        self.name = name
    
    @classmethod
    def from_url_params(cls, remote_mcp: str, transport: str = "http", name: Optional[str] = None) -> "ProxyConfig":
        """Create a proxy config from URL parameters."""
        decoded_url = urllib.parse.unquote(remote_mcp)
        return cls(decoded_url, transport, name)
    
    def _generate_descriptive_name(self) -> str:
        """Generate a descriptive server name from URL and transport."""
        # Extracts hostname, path, and transport
        # Format: {hostname}/{path}/{transport} (transport only if not "http")
        # Removes trailing slashes and spaces
        pass
    
    def get_server_name(self, existing_names: Optional[set] = None) -> str:
        """Get server name, handling conflicts."""
        # Uses explicit name if provided and no conflict
        # Otherwise generates descriptive name
        # Removes trailing slashes and spaces from all names
        # Adds hash suffix if conflict detected
        pass
    
    def to_dict(self, server_name: str = "default") -> Dict[str, Any]:
        """Convert to MCPConfig format for FastMCP.as_proxy."""
        return {
            "mcpServers": {
                server_name: {
                    "url": self.url,
                    "transport": self.transport
                }
            }
        }
```

#### Simplified Middleware Architecture
- **Single `GatewayMiddleware`**: Handles both proxy configuration extraction and routing
- **Direct Method Access**: Uses `_extract_proxy_config()` directly where needed
- **Reduced Complexity**: Eliminated the need for separate routing middleware

### 5. FastMCP Integration

#### Server Creation:
```python
# Create main FastMCP server
self.server = FastMCP("Gateway")

# Add middleware
self.server.add_middleware(self.gateway_middleware)
self.server.add_middleware(self.permit_middleware)
self.server.add_middleware(self.proxy_routing_middleware)
```

#### Proxy Creation and Mounting:
```python
# Create proxy using FastMCP.as_proxy() with MCPConfig format
proxy_config = ProxyConfig("target-server-url", "http")
proxy_server = FastMCP.as_proxy(proxy_config.to_dict("unique_server_name"))

# Mount the proxy using server name as prefix (without leading "/")
server_name = proxy_config.get_server_name()
self.server.mount(proxy_server, prefix=server_name)
```

## Benefits

### 1. **Better Integration**
- Uses FastMCP's native proxy functionality
- Leverages FastMCP's built-in routing and composition features
- Consistent with FastMCP's design patterns

### 2. **Improved Performance**
- FastMCP's built-in proxy is optimized for performance
- Automatic connection pooling and management
- Better error handling and recovery

### 3. **Simplified Architecture**
- Removed custom proxy implementation
- Cleaner separation of concerns
- Easier to maintain and extend

### 4. **Dynamic Routing**
- URL-based routing allows for dynamic proxy creation
- No need to pre-configure servers
- Support for URL encoding for special characters

### 5. **Intelligent Server Naming**
- **Explicit Names**: Use `name` parameter for custom server names
- **Auto-Generated Names**: Descriptive names from URL structure
  - Format: `{hostname}/{path}/{transport}` (transport only if not "http")
  - Example: `api.example.com/v1/mcp` or `localhost/mcp/stdio`
- **Name Cleaning**: Automatically removes trailing slashes and spaces
- **Conflict Resolution**: Automatic hash suffix for duplicate names
- **URL Parsing**: Handles complex URLs with paths and different transports
- **Mount Paths**: Server names are used as mount prefixes (e.g., `/api.example.com/v1/mcp`)

### 6. **Better Error Handling**
- FastMCP's built-in error handling
- Consistent error responses
- Better debugging capabilities

### 7. **Server Isolation**
- **Isolated Authorization**: Each mounted server is isolated, ensuring that authorization only applies to tools from the specific server being accessed
- **Context-Aware Middleware**: The Permit middleware uses the target server name from the gateway context to determine which server's tools to authorize
- **Prevents Tool Leakage**: Eliminates the issue where passing a server name via query param would cause all variations of tool names to be returned

## Usage Examples

### Basic Gateway Usage
```python
from permit_fastmcp.gateway.gateway import create_gateway

async def main():
    async with create_gateway(
        # permit_api_key="your-permit-api-key",  # Optional: can use GATEWAY_PERMIT_API_KEY env var
        # permit_pdp_url="http://localhost:7766",  # Optional: can use GATEWAY_PERMIT_PDP_URL env var
        host="0.0.0.0",
        port=8080,
    ) as gateway:
        # Gateway automatically creates proxy servers based on URL parameters
        print("Gateway running at http://localhost:8080")
        print("Example: http://localhost:8080/mcp/?remote_mcp=localhost:8001/mcp&transport=http")
        
        # Keep running
        await asyncio.Event().wait()

asyncio.run(main())
```

### Environment Variable Configuration
```bash
# Set your Permit.io API key
export GATEWAY_PERMIT_API_KEY="your-permit-api-key"

# Set your Permit PDP URL (optional, defaults to http://localhost:7766)
export GATEWAY_PERMIT_PDP_URL="http://localhost:7766"

# Run the gateway
python -m permit_fastmcp.gateway.run_gateway
```

### Authorization Modes
The gateway supports different authorization modes:

1. **With API Key (Authorization Enabled)**:
   - Provide API key via parameter or environment variable
   - All requests are authorized against Permit.io policies
   - Audit logging is enabled

2. **Without API Key (Authorization Disabled)**:
   - No API key provided
   - All requests are allowed (authorization bypassed)
   - Audit logging still works for monitoring
   - Warning message is logged

### Running the Gateway
```bash
# Run the gateway directly
python -m permit_fastmcp.gateway.run_gateway

# Or use the example
python permit_fastmcp/gateway/example.py
```

## Migration Guide

### For Existing Users

1. **Update URL Format**: Change from server-based routing to URL parameter routing
   - Old: `http://gateway:8080?server=server1`
   - New: `http://gateway:8080/mcp/?remote_mcp=server1-url&transport=http`

2. **Remove Server Registration**: No need to pre-register servers
   - Old: `gateway.add_server("server1", "http://localhost:8001")`
   - New: Use URL parameters directly

3. **Update Client Code**: Update client applications to use the new URL format

### Server Isolation Fix

The gateway now properly isolates servers to prevent tool leakage:

**Before**: When passing a server name via query param, all variations of tool names from all mounted servers would be returned.

**After**: Each mounted server is isolated, and authorization only applies to tools from the specific server being accessed.

**Implementation**:
- The `GatewayMiddleware` stores the target server name in the request context
- The `PermitMcpMiddleware` uses this target server name to determine which server's tools to authorize
- This ensures that only tools from the requested server are visible and authorized

### Canonical Name System

The gateway now uses a dual naming system with "pretty" names for users and "canonical" names for internal tracking:

**Before**: Server names could change between requests due to race conditions, and resource names would include hash suffixes.

**After**: 
- **Pretty names**: User-friendly names that appear in URLs and logs (e.g., "simple", "my-server")
- **Canonical names**: Internal unique identifiers that never change (e.g., "server_123456789")
- Resource names are consistent and use the pretty names
- No more race conditions or unnecessary hash suffixes

**Implementation**:
- `ProxyConfig.get_server_name()` now returns `(pretty_name, canonical_name)`
- `_mounted_proxies` uses canonical names as keys for conflict-proof lookup
- `_existing_server_names` maps canonical names to pretty names
- `_get_or_create_proxy()` returns `(proxy_server, pretty_name, canonical_name)`
- Canonical names are generated using a hash of the URL and transport
- Pretty names handle conflicts by adding hash suffixes when needed
- This ensures consistent resource names and eliminates race conditions

### Backward Compatibility

The gateway maintains the same middleware chain for authentication and authorization:
- Permit.io integration remains unchanged
- Audit logging continues to work
- Health checks are still available (for registered servers)

## Testing

All tests have been updated and pass:
```bash
python -m pytest tests/test_gateway.py -v
```

## Documentation

Updated documentation includes:
- README.md with new gateway usage examples
- Example scripts demonstrating the new functionality
- Comprehensive test coverage

## Future Enhancements

1. **Connection Pooling**: Leverage FastMCP's built-in connection pooling
2. **Load Balancing**: Add support for multiple target servers
3. **Caching**: Implement response caching for improved performance
4. **Metrics**: Add detailed metrics and monitoring
5. **Configuration**: Support for configuration files and environment variables 