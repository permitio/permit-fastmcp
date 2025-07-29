import pytest
import asyncio
import multiprocessing
import time
import os
from fastmcp import Client
import jwt

# Use a different port for this test server
TEST_SERVER_PORT = 8766
TEST_SERVER_URL = f"http://localhost:{TEST_SERVER_PORT}/mcp"


def start_server_with_fixed_identity(port, permit_api_key, permit_pdp_url):
    """Start the server with fixed identity mode configuration."""
    # Now create a custom server with the configured middleware
    from fastmcp import FastMCP
    from permit_fastmcp.middleware.middleware import PermitMcpMiddleware
    from permit_fastmcp.middleware.decorators import identity_mode
    from permit_fastmcp.middleware.config import IdentityMode
    
    # Create the MCP server
    mcp_server = FastMCP("Test MCP Server")
    
    # Add the greet tool with fixed identity decorator
    @mcp_server.tool
    @identity_mode(IdentityMode.fixed, fixed_value="client")
    def greet(name: str) -> str:
        """Greet a user by name (no authentication required)."""
        return f"Hello, {name}!"
    
    # Register the tool configuration
    from permit_fastmcp.middleware.decorators import register_tool_config
    register_tool_config("Test MCP Server", "greet", greet)
    
    # Create and add the middleware
    if permit_api_key:
        middleware = PermitMcpMiddleware(
            permit_api_key=permit_api_key, 
            permit_pdp_url=permit_pdp_url
        )
        mcp_server.add_middleware(middleware)
    
    # Run the server
    mcp_server.run(transport="http", port=port)


@pytest.fixture(scope="module")
def start_example_server_fixed_identity():
    """Start the example server with a fixed identity mode configuration."""
    # Get the API key and PDP URL from the environment variables
    permit_api_key = os.environ.get("PERMIT_API_KEY")
    permit_pdp_url = (
        os.environ.get("PERMIT_PDP_URL") or "https://cloudpdp.api.permit.io"
    )
    
    proc = multiprocessing.Process(
        target=start_server_with_fixed_identity, 
        args=(TEST_SERVER_PORT, permit_api_key, permit_pdp_url)
    )
    proc.start()
    
    # Wait for server to be up using MCP client ping
    for _ in range(20):
        try:
            client = Client(TEST_SERVER_URL)
            asyncio.get_event_loop().run_until_complete(client.ping())
            break
        except Exception:
            time.sleep(0.2)
    
    yield
    
    proc.terminate()
    proc.join()


@pytest.mark.asyncio
async def test_greet_fixed_identity(start_example_server_fixed_identity):
    """Test the greet function with a fixed identity mode configuration."""
    client = Client(TEST_SERVER_URL)
    async with client:
        result = await client.call_tool("greet", {"name": "Alice"})
        assert "Hello, Alice" in result.data 