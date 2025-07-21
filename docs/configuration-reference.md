# Configuration Reference

This document lists all configuration options and environment variables for `permit-fastmcp`.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PERMIT_MCP_KNOWN_METHODS` | Methods recognized for resource/action mapping | `["tools/list", "prompts/list", "resources/list", "tools/call", "resources/read", "prompts/get"]` |
| `PERMIT_MCP_BYPASSED_METHODS` | Methods that bypass authorization checks | `["initialize", "ping", "notifications/*"]` |
| `PERMIT_MCP_ACTION_PREFIX` | Prefix for Permit.io action mapping | `""` |
| `PERMIT_MCP_RESOURCE_PREFIX` | Prefix for Permit.io resource mapping | `"mcp_"` |
| `PERMIT_MCP_MCP_SERVER_NAME` | Name of the MCP server (used as resource name for tool calls) | `"mcp_server"` |
| `PERMIT_MCP_PERMIT_PDP_URL` | Permit.io PDP URL | `"http://localhost:7766"` |
| `PERMIT_MCP_PERMIT_API_KEY` | Permit.io API key | `""` |
| `PERMIT_MCP_ENABLE_AUDIT_LOGGING` | Enable or disable audit logging | `true` |
| `PERMIT_MCP_IDENTITY_MODE` | Identity extraction mode: 'jwt', 'fixed', 'header', or 'source' | `fixed` |
| `PERMIT_MCP_IDENTITY_HEADER` | Header to extract identity from (for 'jwt' and 'header' modes) | `Authorization` |
| `PERMIT_MCP_IDENTITY_HEADER_REGEX` | Regex to extract token from header (for 'jwt' mode) | `[Bb]earer (.+)` |
| `PERMIT_MCP_IDENTITY_JWT_SECRET` | JWT secret or public key (for 'jwt' mode) | `""` |
| `PERMIT_MCP_IDENTITY_JWT_FIELD` | JWT field to use as identity (for 'jwt' mode) | `sub` |
| `PERMIT_MCP_IDENTITY_FIXED_VALUE` | Fixed identity value (for 'fixed' mode) | `client` |
| `PERMIT_MCP_JWT_ALGORITHMS` | Allowed JWT algorithms (for 'jwt' mode) | `["HS256", "RS256"]` |
| `PERMIT_MCP_PREFIX_RESOURCE_WITH_SERVER_NAME` | Whether to prefix resources with the MCP server name (for non-tool calls) | `true` |
| `PERMIT_MCP_FLATTEN_TOOL_ARGUMENTS` | Whether to flatten tool arguments as individual attributes with prefix | `true` |
| `PERMIT_MCP_TOOL_ARGUMENT_PREFIX` | Prefix for flattened tool argument attributes | `arg_` |

## Example: .env File

```env
PERMIT_MCP_PERMIT_PDP_URL=http://localhost:7766
PERMIT_MCP_PERMIT_API_KEY=your-api-key
PERMIT_MCP_ENABLE_AUDIT_LOGGING=true
PERMIT_MCP_ACTION_PREFIX=mcp_
PERMIT_MCP_RESOURCE_PREFIX=mcp_
```

## Example: Setting Environment Variables

```bash
export PERMIT_MCP_PERMIT_PDP_URL="http://localhost:7766"
export PERMIT_MCP_PERMIT_API_KEY="your-api-key"
export PERMIT_MCP_ENABLE_AUDIT_LOGGING="true"
```

For identity-related variables, see [Identity Modes & Environment Variables](./identity-modes.md).

## Tool Argument Flattening

The `PERMIT_MCP_FLATTEN_TOOL_ARGUMENTS` setting controls how tool arguments are passed to Permit.io for authorization. When enabled (default), tool arguments are flattened as individual attributes with a configurable prefix, making them easier to reference in ABAC policies.

### Default Behavior (Flattened Arguments)

When `PERMIT_MCP_FLATTEN_TOOL_ARGUMENTS=true` (default), tool arguments are flattened:

```python
# For a tool call: conditional-greet(name="Alice", number=5, log_message="User logged in")
attributes = {
    "tool_name": "conditional-greet",
    "arg_name": "Alice",
    "arg_number": 5,
    "arg_log_message": "User logged in",
    "mcp_method": "tools/call"
}
```

### Legacy Behavior (Nested Arguments)

When `PERMIT_MCP_FLATTEN_TOOL_ARGUMENTS=false`, tool arguments remain nested:

```python
# For a tool call: conditional-greet(name="Alice", number=5, log_message="User logged in")
attributes = {
    "tool_name": "conditional-greet",
    "arguments": {
        "name": "Alice",
        "number": 5,
        "log_message": "User logged in"
    },
    "mcp_method": "tools/call"
}
```

### Custom Prefix

You can customize the prefix used for flattened arguments:

```env
PERMIT_MCP_TOOL_ARGUMENT_PREFIX=param_
```

This would result in attributes like `param_name`, `param_number`, etc.

### ABAC Policy Examples

With flattened arguments, you can create more granular policies:

```python
# Allow access only if the name is "admin"
{
    "user.role": "user",
    "resource.type": "mcp_server",
    "action": "conditional-greet",
    "arg_name": "admin"
}

# Allow access only if the number is greater than 10
{
    "user.role": "user", 
    "resource.type": "mcp_server",
    "action": "conditional-greet",
    "arg_number": {"$gt": 10}
}
``` 