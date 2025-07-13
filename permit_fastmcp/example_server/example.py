from fastmcp import FastMCP, Context
import jwt
import datetime
from middleware.config import SETTINGS

SECRET_KEY = "mysecretkey"  # In production, use a secure, environment-based secret!
SETTINGS.identity_mode = "jwt"
SETTINGS.identity_jwt_secret = SECRET_KEY
mcp = FastMCP("My MCP Server")

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool(description="Login to the system and get a JWT token, use the JWT as the Authorization header in subsequent requests")
def login(username: str, password: str) -> str:
    # Demo: hardcoded user/password check
    if username == "admin" and password == "password" or username == "client" and password == "client":
        payload = {
            "sub": username,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=100),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    else:
        raise Exception("Invalid username or password")

@mcp.tool(name="greet-jwt", description="Greet a user by extracting their name from a JWT in the Authorization header.")
async def greet_jwt(ctx: Context) -> str:
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
    mcp.run(transport="http")