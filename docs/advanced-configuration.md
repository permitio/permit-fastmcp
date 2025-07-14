# Advanced Configuration

This document covers advanced configuration options for `permit-fastmcp`.

## Custom Middleware Settings

You can customize the middleware by passing additional arguments to `PermitMcpMiddleware`:

```python
from permit_fastmcp.middleware.middleware import PermitMcpMiddleware

middleware = PermitMcpMiddleware(
    permit_pdp_url="http://localhost:7766",
    permit_api_key="your-api-key",
    enable_audit_logging=True,
    bypass_methods=["initialize", "ping", "health/*"]
)
```

- `permit_pdp_url`: URL of the Permit.io PDP (Policy Decision Point)
- `permit_api_key`: Your Permit.io API key
- `enable_audit_logging`: Enable or disable audit logging (default: True)
- `bypass_methods`: List of method patterns to bypass authorization

## Audit Logging

Audit logging records all authorization decisions. You can control this with the `enable_audit_logging` parameter or the `PERMIT_MCP_ENABLE_AUDIT_LOGGING` environment variable.

## Bypass Methods

Some MCP methods (e.g., `initialize`, `ping`) can be configured to bypass authorization checks. Use the `bypass_methods` parameter or the `PERMIT_MCP_BYPASSED_METHODS` environment variable.

## Extending the Middleware

You can subclass `PermitMcpMiddleware` to customize identity extraction or authorization logic:

```python
from permit_fastmcp.middleware.middleware import PermitMcpMiddleware

class CustomPermitMiddleware(PermitMcpMiddleware):
    def _extract_principal_info(self, context):
        # Custom logic to extract user identity
        user_id = getattr(context, 'user_id', None) or getattr(context, 'source', 'unknown')
        attributes = {"user_id": user_id}
        return user_id, attributes
```

## More

For a full list of environment variables and settings, see [Identity Modes & Environment Variables](./identity-modes.md). 