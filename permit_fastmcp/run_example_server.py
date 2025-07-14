# Import the example MCP server instance
from example_server.example import mcp as example_mcp

# Import the PermitMcpMiddleware for authorization
from middleware.middleware import PermitMcpMiddleware

# Import and set up logging configuration
import os

# import logger_config  # Ensures logging is configured (not needed if not used)
from logger_config import logger


def main():
    logger.info("Starting the example MCP server")
    # Read the Permit API key from the environment variable
    permit_api_key = os.environ.get("PERMIT_API_KEY")
    if not permit_api_key:
        raise RuntimeError("PERMIT_API_KEY environment variable is not set.")
    # Create the PermitMcpMiddleware with your Permit API key
    middleware = PermitMcpMiddleware(permit_api_key=permit_api_key)
    # Add the middleware to the example MCP server
    example_mcp.add_middleware(middleware)
    # Run the MCP server using HTTP transport
    example_mcp.run(transport="http")


if __name__ == "__main__":
    main()  # Entry point: start the example server
