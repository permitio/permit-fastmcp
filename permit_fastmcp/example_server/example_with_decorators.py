"""
Example FastMCP server demonstrating per-tool identity configuration decorators.

This example shows how to use the @identity_mode and @bypass_authorization decorators
to configure different identity extraction modes for different tools.
"""

from fastmcp import FastMCP, Context
import jwt
import datetime
from permit_fastmcp.middleware.config import SETTINGS, IdentityMode
from permit_fastmcp.middleware.decorators import identity_mode, bypass_authorization

# Secret key for signing JWTs (in production, use a secure, environment-based secret!)
SECRET_KEY = "mysecretkey"

# Configure the middleware to use fixed identity mode as default
SETTINGS.identity_mode = IdentityMode.fixed.value
SETTINGS.identity_jwt_secret = SECRET_KEY

# Create the FastMCP server
mcp = FastMCP("Decorator Example MCP Server")


@mcp.tool
@bypass_authorization()
def public_greet(name: str) -> str:
    """Public greeting tool that bypasses authorization entirely."""
    return f"Hello, {name}! (public)"


@mcp.tool
@identity_mode(IdentityMode.fixed, fixed_value="admin")
def admin_greet(name: str) -> str:
    """Admin greeting tool that always uses 'admin' identity regardless of global settings."""
    return f"Hello, {name}! (admin only)"


@mcp.tool
@identity_mode(IdentityMode.header, header_name="X-User-Id")
def header_greet(name: str) -> str:
    """Greeting tool that extracts identity from X-User-Id header."""
    return f"Hello, {name}! (header-based identity)"


@mcp.tool
@identity_mode(IdentityMode.jwt, jwt_secret=SECRET_KEY, jwt_field="sub")
def secure_greet(name: str) -> str:
    """Secure greeting tool that uses JWT authentication with custom secret."""
    return f"Hello, {name}! (JWT authenticated)"


@mcp.tool
def default_greet(name: str) -> str:
    """Default greeting tool that uses the global identity mode (JWT in this case)."""
    return f"Hello, {name}! (default identity mode)"


@mcp.tool(
    description=(
        "Login to the system and get a JWT token, use the JWT as the Authorization "
        "header in subsequent requests"
    )
)
def login(username: str, password: str) -> str:
    """
    Authenticate a user and return a JWT token if credentials are valid.
    Demo: hardcoded user/password check for 'admin'/'password' or 'client'/'client'.
    """
    if (
        username == "admin"
        and password == "password"
        or username == "client"
        and password == "client"
    ):
        payload = {
            "sub": username,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=100),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    else:
        raise Exception("Invalid username or password")


if __name__ == "__main__":
    # Start the FastMCP server with HTTP transport
    mcp.run(transport="http") 