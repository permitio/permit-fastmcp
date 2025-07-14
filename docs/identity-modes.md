# Identity Modes & Environment Variables

This document explains the identity extraction modes and environment variables for `permit-fastmcp`.

## Identity Extraction Modes

Set the mode with the `PERMIT_MCP_IDENTITY_MODE` environment variable. Supported modes:

- **fixed**: Always use a fixed identity value.
- **header**: Extract the identity from a specific HTTP header.
- **jwt**: Extract and verify a JWT from a header, using a field from the JWT payload as the identity.
- **source**: Use the `source` field from the context (if present).

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PERMIT_MCP_IDENTITY_MODE` | Extraction mode: `fixed`, `header`, `jwt`, or `source` | `fixed` |
| `PERMIT_MCP_IDENTITY_HEADER` | Header to extract identity/JWT from | `Authorization` |
| `PERMIT_MCP_IDENTITY_HEADER_REGEX` | Regex to extract JWT from header (for `jwt` mode) | `[Bb]earer (.+)` |
| `PERMIT_MCP_IDENTITY_JWT_SECRET` | Secret or public key for JWT verification (for `jwt` mode) | *(empty)* |
| `PERMIT_MCP_IDENTITY_JWT_FIELD` | JWT payload field to use as identity (for `jwt` mode) | `sub` |
| `PERMIT_MCP_IDENTITY_FIXED_VALUE` | Fixed identity value (for `fixed` mode) | `client` |
| `PERMIT_MCP_JWT_ALGORITHMS` | Allowed JWT algorithms (for `jwt` mode) | `["HS256", "RS256"]` |

## Examples

### Fixed Identity (default)
```env
PERMIT_MCP_IDENTITY_MODE=fixed
PERMIT_MCP_IDENTITY_FIXED_VALUE=my-client-id
```

### Identity from HTTP Header
```env
PERMIT_MCP_IDENTITY_MODE=header
PERMIT_MCP_IDENTITY_HEADER=X-Client-ID
```

### Identity from JWT in Authorization Header
```env
PERMIT_MCP_IDENTITY_MODE=jwt
PERMIT_MCP_IDENTITY_HEADER=Authorization
PERMIT_MCP_IDENTITY_HEADER_REGEX=[Bb]earer (.+)
PERMIT_MCP_IDENTITY_JWT_SECRET=your-jwt-secret-or-public-key
PERMIT_MCP_IDENTITY_JWT_FIELD=sub
```

### Identity from Context Source Field
```env
PERMIT_MCP_IDENTITY_MODE=source
```

## Security Best Practices
- Never commit your JWT secret or private key to version control.
- Use environment variables or a secure secret manager for secrets in production.
- Always use HTTPS in production to protect headers and tokens in transit.
- Validate the JWT's expiration (`exp`) and issued-at (`iat`) claims.
- Use strong, unique secrets for HMAC (HS256) or a secure public/private key pair for RSA (RS256). 