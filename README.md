# permit-fastmcp

A FastMCP middleware that adds Permit.io authorization to your MCP servers. This middleware intercepts MCP requests and validates them against Permit.io policies before allowing them to proceed.

## Installation

```bash
# Using UV (recommended)
uv add permit-fastmcp

# Using pip
pip install permit-fastmcp
```

## Quick Start

### Basic Middleware Usage

```python
from fastmcp import FastMCP
from permit_fastmcp.middleware.middleware import PermitMcpMiddleware

mcp = FastMCP("My MCP Server")

# Add Permit.io authorization middleware
mcp.add_middleware(PermitMcpMiddleware(
    permit_pdp_url="http://localhost:7766",
    permit_api_key="your-permit-api-key"
))

@mcp.tool
def my_tool(data: str) -> str:
    return f"Processed: {data}"

if __name__ == "__main__":
    mcp.run(transport="http")
```

### FastMCP Gateway with Built-in Proxy

The package also includes a FastMCP Gateway that provides dynamic proxy routing to remote MCP servers using FastMCP's built-in proxy functionality.

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

# Run the gateway
asyncio.run(main())
```

#### Environment Variables

The gateway supports configuration via environment variables:

```bash
# Set your Permit.io API key
export GATEWAY_PERMIT_API_KEY="your-permit-api-key"

# Set your Permit PDP URL (optional, defaults to http://localhost:7766)
export GATEWAY_PERMIT_PDP_URL="http://localhost:7766"

# Run the gateway
python -m permit_fastmcp.gateway.run_gateway
```

#### Gateway URL Format

The gateway uses URL parameters to dynamically route requests to remote MCP servers:

```
http://gateway-host:port/mcp/?remote_mcp=target-server-url&transport=protocol&name=server-name
```

**Parameters:**
- `remote_mcp`: The URL of the target MCP server (required, URL-encoded)
- `transport`: The transport protocol (optional, default: `http`)
- `name`: Custom server name (optional, auto-generated if not provided)

**Examples:**
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

The gateway automatically:
- Creates proxy servers for each unique `remote_mcp` URL using FastMCP's built-in proxy functionality
- Uses a **canonical name system** with pretty names for users and unique internal identifiers
- Generates descriptive server names from URLs (e.g., `api.example.com/v1/mcp`) or uses custom names
- Cleans server names by removing trailing slashes and spaces
- Handles naming conflicts by adding hash suffixes to pretty names while keeping canonical names stable
- Mounts them at paths matching their pretty server names (e.g., `/api.example.com/v1/mcp` or `/my-server`)
- Routes requests to the appropriate proxy
- Handles authentication and authorization (if configured)
- **Server Isolation**: Each mounted server is isolated, ensuring that authorization only applies to tools from the specific server being accessed

## How Policy Mapping Works

- **MCP server methods** (e.g., `tools/list`, `resources/read`):
  - **Resource**: `{server_name}_{component}` (e.g., `myserver_tools`)
  - **Action**: The method verb (e.g., `list`, `read`)
- **Tool execution** (method `tools/call`):
  - **Resource**: `{server_name}` (e.g., `myserver`)
  - **Action**: The tool name (e.g., `greet`)

![Permit.io Policy Mapping Example](./docs/images/policy_mapping.png)

*Example: In Permit.io, the 'Admin' role is granted permissions on resources and actions as mapped by the middleware. For example, 'greet', 'greet-jwt', and 'login' are actions on the 'mcp_server' resource, and 'list' is an action on the 'mcp_server_tools' resource.*

> **Note:**
> Don’t forget to assign the relevant role (e.g., Admin, User) to the user authenticating to your MCP server (such as the user in the JWT) in the Permit.io Directory. Without the correct role assignment, users will not have access to the resources and actions you’ve configured in your policies.
>
> ![Permit.io Directory Role Assignment Example](./docs/images/role_assignement.png)
>
> *Example: In Permit.io Directory, both 'client' and 'admin' users are assigned the 'Admin' role, granting them the permissions defined in your policy mapping.*

## ABAC Policies with Tool Arguments

The middleware supports Attribute-Based Access Control (ABAC) policies that can evaluate tool arguments as attributes. Tool arguments are automatically flattened as individual attributes (e.g., `arg_name`, `arg_number`) for granular policy conditions.

![ABAC Condition Example](./docs/images/abac_condition_example.png)

*Example: Create dynamic resources with conditions like `resource.arg_number greater-than 10` to allow the `conditional-greet` tool only when the number argument exceeds 10.*

For detailed ABAC configuration and examples, see [ABAC Policies with Tool Arguments](./docs/policy-mapping.md#abac-policies-with-tool-arguments).

## Example: JWT Authentication

See [`permit_fastmcp/example_server/example.py`](permit_fastmcp/example_server/example.py) for a full example of JWT-based authentication and usage.

## More Documentation

- [Advanced Configuration](./docs/advanced-configuration.md)
- [Identity Modes & Environment Variables](./docs/identity-modes.md)
- [Detailed Policy Mapping](./docs/policy-mapping.md)
- [Configuration Reference](./docs/configuration-reference.md)
- [Troubleshooting](./docs/troubleshooting.md)
- [Getting Started & FAQ](./docs/getting-started.md)

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.

