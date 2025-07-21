import pytest
import asyncio
import multiprocessing
import time
import os
from fastmcp import Client
import jwt

# Use a free port for the test server
TEST_SERVER_PORT = 8765
TEST_SERVER_URL = f"http://localhost:{TEST_SERVER_PORT}/mcp"


@pytest.fixture(scope="module")
def start_example_server():
    # Get the API key and PDP URL from the environment variables
    permit_api_key = os.environ.get("PERMIT_API_KEY")
    permit_pdp_url = (
        os.environ.get("PERMIT_PDP_URL") or "https://cloudpdp.api.permit.io"
    )
    from permit_fastmcp.run_example_server import main as server_main

    proc = multiprocessing.Process(
        target=server_main, args=(TEST_SERVER_PORT, permit_api_key, permit_pdp_url)
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
async def test_greet(start_example_server):
    client = Client(TEST_SERVER_URL)
    async with client:
        result = await client.call_tool("greet", {"name": "Alice"})
        assert "Hello, Alice" in result.data


@pytest.mark.asyncio
async def test_login_and_greet_jwt(start_example_server):
    client = Client(TEST_SERVER_URL)
    async with client:
        # Login to get JWT
        login_result = await client.call_tool(
            "login", {"username": "admin", "password": "password"}
        )
        token = login_result.data
        assert token is not None

    # Use JWT to call greet-jwt
    client = Client(TEST_SERVER_URL, auth=token)
    async with client:
        result = await client.call_tool("greet-jwt", {"ctx": {}})
        assert "Hello, admin" in result.data


@pytest.mark.asyncio
async def test_greet_jwt_missing_header(start_example_server):
    client = Client(TEST_SERVER_URL)
    async with client:
        with pytest.raises(Exception):
            await client.call_tool("greet-jwt", {"ctx": {}})


@pytest.mark.asyncio
async def test_greet_jwt_invalid_token(start_example_server):
    client = Client(TEST_SERVER_URL)
    async with client:
        headers = {"Authorization": "Bearer invalidtoken"}
        with pytest.raises(Exception):
            await client.call_tool("greet-jwt", {"ctx": {}}, headers=headers)


@pytest.mark.asyncio
async def test_login_invalid_credentials(start_example_server):
    client = Client(TEST_SERVER_URL)
    async with client:
        with pytest.raises(Exception):
            await client.call_tool("login", {"username": "wrong", "password": "wrong"})
