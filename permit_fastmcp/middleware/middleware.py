
import fnmatch
import logging
from typing import Any, Optional
from permit import Permit
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from .config import ACTION_PREFIX, BYPASSED_METHODS, KNOWN_METHODS, RESOURCE_PREFIX

logger = logging.getLogger("permit_fastmcp.middleware")

class PermitMcpMiddleware(Middleware):
    """
    Permit.io authorization middleware for FastMCP servers (MCP Middleware).
    Intercepts MCP requests and validates them against Permit.io policies.
    """
    def __init__(
        self,
        permit_client: Optional[Permit] = None,
        enable_audit_logging: bool = True,
        bypass_methods: Optional[list[str]] = None,
        permit_pdp_url: Optional[str] = None,
        permit_api_key: Optional[str] = None,
    ):
        super().__init__()
        self._permit_client = permit_client or Permit(
            pdp=permit_pdp_url or "http://localhost:7766",
            token=permit_api_key
        )
        self._enable_audit_logging = enable_audit_logging
        self._bypass_methods = bypass_methods or BYPASSED_METHODS

    async def on_message(self, context: MiddlewareContext, call_next):
        # Extract the incoming MCP message and its key fields
        message = context.message
        method = getattr(message, "method", None)
        params = getattr(message, "params", None)
        msg_id = getattr(message, "id", None)

        # If there's no method, this isn't a JSON-RPC request we care about
        if not method:
            return await call_next(context)

        # Skip authorization for bypassed methods (e.g., ping, initialize)
        if any(fnmatch.fnmatch(method, pattern) for pattern in self._bypass_methods):
            return await call_next(context)

        # Perform authorization check with Permit.io
        permitted, reason = await self._authorize_request(method, params, msg_id, context)
        if not permitted:
            # Log and raise a FastMCP error if not authorized
            if self._enable_audit_logging:
                self._log_access_denied(context, message, reason)
            raise McpError(ErrorData(code=-32010, message="Unauthorized", data=reason))

        # Log successful authorization if enabled
        if self._enable_audit_logging:
            self._log_authorized_request(context, message)

        # Continue to the next middleware or handler
        return await call_next(context)

    async def _authorize_request(self, method, params, msg_id, context: MiddlewareContext) -> tuple[bool, str]:
        # Map the MCP method and params to Permit.io action/resource
        try:
            user_id, user_attrs = self._extract_principal_info(context)
            action, resource, resource_attrs = self._map_method_to_action_and_resource(
                method, params or {}
            )
            # Build the resource dict for Permit.io
            resource_dict = {"type": resource}
            if resource_attrs:
                resource_dict["attributes"] = resource_attrs
            if "tenant" in resource_attrs:
                resource_dict["tenant"] = resource_attrs["tenant"]
            # Build the user object for Permit.io
            user_obj = user_id
            if user_attrs:
                user_obj = {"key": user_id, "attributes": user_attrs}
            # Call Permit.io to check authorization
            permitted = await self._permit_client.check(user_obj, action, resource_dict)
            return permitted, ""
        except Exception as e:
            logger.error(f"Authorization check failed: {e}")
            return False, f"Authorization system error: {str(e)}"

    def _extract_principal_info(self, context: MiddlewareContext) -> tuple[str, dict[str, Any]]:
        # Extract user identity from the context (customize as needed)
        uri = getattr(context, "source", None) or "unknown"
        attributes = {"source": uri}
        return uri, attributes

    def _map_method_to_action_and_resource(self, method: str, params: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        # Map MCP method to Permit.io action/resource/attributes
        known_methods = KNOWN_METHODS
        if method in known_methods:
            resource_type, action = method.split("/")
            resource = resource_type
        else:
            resource_type = "unknown"
            resource = f"method:{method}"
        attributes = {
            "mcp_method": method,
            "resource_type": resource_type,
            "arguments": params.get("arguments", {}),
        }
        # Special-case mapping for certain methods
        if method == "tools/call":
            action = "execute"
            resource = resource + f":{params.get('name')}"
            attributes["tool_name"] = params.get("name")
        elif method == "resources/read":
            action = "read"
            resource = resource + f":{params.get('uri')}"
            attributes["resource_uri"] = params.get("uri")
        elif method == "prompts/get":
            action = "read"
            resource = resource + f":{params.get('name')}"
            attributes["prompt_name"] = params.get("name")
        if "tenant" in params:
            attributes["tenant"] = params["tenant"]
        # add prefix to action and resource
        action = ACTION_PREFIX + action
        resource = RESOURCE_PREFIX + resource
        return action, resource, attributes

    def _log_access_denied(self, context: MiddlewareContext, message, reason: str):
        # Log an authorization violation
        logger.warning(
            f"Request Denied: {reason} | "
            f"Method: {getattr(message, 'method', 'unknown')} | "
            f"Source: {getattr(context, 'source', 'unknown')}"
        )

    def _log_authorized_request(self, context: MiddlewareContext, message):
        # Log a successful authorization
        logger.info(
            f"Authorized MCP request: {getattr(message, 'method', 'unknown')} | "
            f"Source: {getattr(context, 'source', 'unknown')}"
        )
