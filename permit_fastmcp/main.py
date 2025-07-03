from example_server.example import mcp as example_mcp
from middleware.middleware import PermitMcpMiddleware

from fastmcp.server.middleware import Middleware, MiddlewareContext

from logger_config import setup_logging
setup_logging()

class LoggingMiddleware(Middleware):
    """Middleware that logs all MCP operations."""
    
    async def on_message(self, context: MiddlewareContext, call_next):
        """Called for all MCP messages."""
        print(f"Processing {context.method} from {context.source}")
        
        result = await call_next(context)
        
        print(f"Completed {context.method}")
        return result


def main():
    middleware = PermitMcpMiddleware(permit_api_key="permit_key_i9y97df9eO0JsXcwAvVL2ZoAEWkBPbjuCz7dDPu1gIvVwrP2aqkTM5zW4MwOE7e63Q8gbPBYBLtfLUVgrVTUhx")
    example_mcp.add_middleware(middleware)
    example_mcp.run(transport="http")


if __name__ == "__main__":
    main()
