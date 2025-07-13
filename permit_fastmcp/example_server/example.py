"""
Example FastMCP server with Permit.io authorization and JWT-based authentication.

- Provides a login tool to get a JWT token.
- Demonstrates how to use the JWT in the Authorization header for secure tool calls.
- Shows how to configure the middleware for JWT identity extraction.

Run this server and use the login tool to get a token, then call greet-jwt with the token in the Authorization header.
"""

from fastmcp import FastMCP, Context
import jwt
import datetime
from permit_fastmcp.middleware.config import SETTINGS

# Secret key for signing JWTs (in production, use a secure, environment-based secret!)
SECRET_KEY = "mysecretkey"

# Configure the middleware to use JWT mode for identity extraction
SETTINGS.identity_mode = "jwt"
SETTINGS.identity_jwt_secret = SECRET_KEY

# Create the FastMCP server
mcp = FastMCP("My MCP Server")


@mcp.tool
def greet(name: str) -> str:
    """Greet a user by name (no authentication required)."""
    return f"Hello, {name}!"


@mcp.tool(
    description="Login to the system and get a JWT token, use the JWT as the Authorization header in subsequent requests"
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


@mcp.tool(
    name="greet-jwt",
    description="Greet a user by extracting their name from a JWT in the Authorization header.",
)
async def greet_jwt(ctx: Context) -> str:
    """
    Greet a user by extracting their name from a JWT in the Authorization header.
    The JWT is expected in the 'Authorization' header as 'Bearer <token>'.
    """
    import re

    headers = ctx.request_context.request.headers
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if not auth_header:
        raise Exception("Missing Authorization header")
    match = re.match(r"[Bb]earer (.+)", auth_header)
    if not match:
        raise Exception("Invalid or missing Bearer token in Authorization header")
    token = match.group(1)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        name = payload.get("sub", "unknown")
        return f"Hello, {name}! (secure)"
    except Exception as e:
        raise Exception(f"Invalid token: {e}")


if __name__ == "__main__":
    # Start the FastMCP server with HTTP transport
    mcp.run(transport="http")
