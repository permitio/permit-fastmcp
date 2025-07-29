"""
Example usage of the FastMCP Gateway with built-in proxy functionality.
"""

import asyncio
import logging
from permit_fastmcp.gateway.gateway import create_gateway
from permit_fastmcp.logger_config import setup_logging

logger = logging.getLogger(__name__)


async def main():
    """Example of using the FastMCP Gateway."""
    setup_logging()
    
    # Create and start the gateway
    # API key and PDP URL can be provided explicitly or via environment variables:
    # - GATEWAY_PERMIT_API_KEY: Your Permit.io API key
    # - GATEWAY_PERMIT_PDP_URL: Your Permit PDP URL (default: http://localhost:7766)
    async with create_gateway(
        # permit_api_key="your-permit-api-key",  # Optional: can use GATEWAY_PERMIT_API_KEY env var
        # permit_pdp_url="http://localhost:7766",  # Optional: can use GATEWAY_PERMIT_PDP_URL env var
        enable_audit_logging=True,
        host="0.0.0.0",
        port=8080,
    ) as gateway:
        
        # Add some example servers for health checks and management
        gateway.add_server("local-server", "http://localhost:8001")
        gateway.add_server("remote-server", "https://api.example.com/mcp")
        
        logger.info("🚀 FastMCP Gateway is running!")
        logger.info("📍 Gateway URL: http://localhost:8080")
        logger.info("")
        logger.info("📋 Example usage:")
        logger.info("")
        logger.info("1. Connect to a local MCP server:")
        logger.info("   http://localhost:8080/mcp/?remote_mcp=localhost:8001/mcp&transport=http")
        logger.info("")
        logger.info("2. Connect to a remote MCP server:")
        logger.info("   http://localhost:8080/mcp/?remote_mcp=api.example.com/mcp&transport=http")
        logger.info("")
        logger.info("3. Connect with URL encoding (for special characters):")
        logger.info("   http://localhost:8080/mcp/?remote_mcp=api.example.com%2Fmcp&transport=http")
        logger.info("")
        logger.info("4. Connect with different transport:")
        logger.info("   http://localhost:8080/mcp/?remote_mcp=localhost:8001/mcp&transport=stdio")
        logger.info("")
        logger.info("🔧 URL Parameters:")
        logger.info("   - remote_mcp: The URL of the target MCP server (required)")
        logger.info("   - transport: The transport protocol (default: http)")
        logger.info("")
        logger.info("💡 The gateway will automatically:")
        logger.info("   - Create proxy servers for each unique remote_mcp URL")
        logger.info("   - Mount them at unique paths")
        logger.info("   - Route requests to the appropriate proxy")
        logger.info("   - Handle authentication and authorization (if configured)")
        logger.info("")
        logger.info("Press Ctrl+C to stop the gateway...")
        
        try:
            # Keep the server running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down gateway...")


if __name__ == "__main__":
    asyncio.run(main()) 