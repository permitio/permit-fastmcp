# Import the example MCP server instance
from permit_fastmcp.example_server.example import mcp as mcp_server

# Import the PermitMcpMiddleware for authorization
from permit_fastmcp.middleware.middleware import PermitMcpMiddleware

import os

# import logger_config  # Ensures logging is configured (not needed if not used)
from permit_fastmcp.logger_config import logger

# For testing purposes, we use the cloud PDP URL
CLOUD_PDP_URL = "https://cloudpdp.api.permit.io"


def main(port=8000, permit_api_key=None, permit_pdp_url=None):
    logger.info("Starting the example MCP server")
    if permit_api_key is not None:
        # Create the PermitMcpMiddleware with your Permit API key
        middleware = PermitMcpMiddleware(
            permit_api_key=permit_api_key, permit_pdp_url=permit_pdp_url
        )
        # Add the middleware to the example MCP server
        mcp_server.add_middleware(middleware)
    # Run the MCP server using HTTP transport
    mcp_server.run(transport="http", port=port)


if __name__ == "__main__":
    # Read the Permit API key from the environment variable
    permit_api_key = os.environ.get("PERMIT_API_KEY")
    permit_pdp_url = os.environ.get("PERMIT_PDP_URL")
    main(
        8000, permit_api_key, permit_pdp_url=permit_pdp_url
    )  # Entry point: start the example server
