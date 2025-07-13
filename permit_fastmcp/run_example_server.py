# Import the example MCP server instance
from example_server.example import mcp as example_mcp

# Import the PermitMcpMiddleware for authorization
from middleware.middleware import PermitMcpMiddleware

# Import and set up logging configuration
from logger_config import setup_logging

setup_logging()  # Initialize logging for the application


def main():
    # Create the PermitMcpMiddleware with your Permit API key
    middleware = PermitMcpMiddleware(
        permit_api_key="permit_key_i9y97df9eO0JsXcwAvVL2ZoAEWkBPbjuCz7dDPu1gIvVwrP2aqkTM5zW4MwOE7e63Q8gbPBYBLtfLUVgrVTUhx"
    )
    # Add the middleware to the example MCP server
    example_mcp.add_middleware(middleware)
    # Run the MCP server using HTTP transport
    example_mcp.run(transport="http")


if __name__ == "__main__":
    main()  # Entry point: start the example server
