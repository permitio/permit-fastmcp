import fnmatch
import logging
from typing import Any, Optional
from permit import Permit
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

import re
import jwt
from .config import SETTINGS
from .utils import generate_action_from_tool_name

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
            pdp=permit_pdp_url or "http://localhost:7766", token=permit_api_key
        )
        self._enable_audit_logging = enable_audit_logging
        self._bypass_methods = bypass_methods or SETTINGS.bypassed_methods

    async def on_message(self, context: MiddlewareContext, call_next):
        message = context.message
        method = getattr(message, "method", None) or context.method
        params = getattr(message, "params", None) or {}
        # msg_id = getattr(message, "id", None)  # F841: unused variable

        if not method:
            return await call_next(context)

        if any(fnmatch.fnmatch(method, pattern) for pattern in self._bypass_methods):
            return await call_next(context)

        # Only handle non-tool calls here
        if method != "tools/call":
            # Inline mapping logic for non-tool calls
            known_methods = SETTINGS.known_methods
            if method in known_methods:
                # Split method into resource type and action
                resource_type, action = method.split("/")
                resource = resource_type
            else:
                # Fallback for unknown methods
                resource_type = "unknown"
                resource = f"method:{method}"
                action = "access"
            # Build attributes for authorization
            attributes = {
                "mcp_method": method,
                "resource_type": resource_type,
                "arguments": params.get("arguments", {}),
            }
            if method == "resources/read":
                # Special-case for resource reads
                action = "read"
                resource = resource + f":{params.get('uri')}"
                attributes["resource_uri"] = params.get("uri")
            elif method == "prompts/get":
                # Special-case for prompt gets
                action = "read"
                resource = resource + f":{params.get('name')}"
                attributes["prompt_name"] = params.get("name")
            # Add tenant if present
            if "tenant" in params:
                attributes["tenant"] = params["tenant"]
            # Prefix resource with server name or default prefix
            if SETTINGS.prefix_resource_with_server_name:
                resource = SETTINGS.mcp_server_name + "_" + resource
            else:
                resource = SETTINGS.resource_prefix + resource
            # Prefix the action if needed
            action = SETTINGS.action_prefix + action
            logger.debug(f"Mapped method to action: {action} and resource: {resource}")
            user_id, _ = self._extract_principal_info(context)
            permitted, reason = await self._authorize_request(
                resource, action, attributes, context
            )
            if not permitted:
                if self._enable_audit_logging:
                    self._log_access_event(
                        context,
                        message,
                        user_id,
                        resource,
                        action,
                        permitted=False,
                        reason=reason,
                    )
                raise McpError(
                    ErrorData(code=-32010, message="Unauthorized", data=reason)
                )
            if self._enable_audit_logging:
                self._log_access_event(
                    context, message, user_id, resource, action, permitted=True
                )

        return await call_next(context)

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        message = context.message
        method = getattr(message, "method", None) or context.method
        params = getattr(message, "params", None) or {}
        tool_name = getattr(message, "name", None)
        arguments = getattr(message, "arguments", {})
        # New mapping: resource = MCP_SERVER_NAME, action = tool_name (no prefix)
        resource = SETTINGS.mcp_server_name
        action = generate_action_from_tool_name(tool_name)

        # Build attributes based on configuration
        attributes = {
            "tool_name": tool_name,
            "mcp_method": method,
        }

        # Handle tool arguments based on flatten_tool_arguments setting
        if SETTINGS.flatten_tool_arguments:
            # Flatten arguments as individual attributes with prefix
            for arg_name, arg_value in arguments.items():
                prefixed_name = SETTINGS.tool_argument_prefix + arg_name
                attributes[prefixed_name] = arg_value
        else:
            # Keep arguments nested under "arguments" key (default behavior)
            attributes["arguments"] = arguments

        logger.debug(f"Mapped tool call to action: {action} and resource: {resource}")
        user_id, _ = self._extract_principal_info(context)
        permitted, reason = await self._authorize_request(
            resource, action, attributes, context
        )
        if not permitted:
            if self._enable_audit_logging:
                self._log_access_event(
                    context,
                    message,
                    user_id,
                    resource,
                    action,
                    permitted=False,
                    reason=reason,
                )
            raise McpError(ErrorData(code=-32010, message="Unauthorized", data=reason))
        if self._enable_audit_logging:
            self._log_access_event(
                context, message, user_id, resource, action, permitted=True
            )
        return await call_next(context)

    async def _authorize_request(
        self, resource, action, attributes, context: MiddlewareContext
    ) -> tuple[bool, str]:
        try:
            user_id, user_attrs = self._extract_principal_info(context)
            resource_dict = {"type": resource}
            if attributes:
                resource_dict["attributes"] = attributes
            if "tenant" in attributes:
                resource_dict["tenant"] = attributes["tenant"]
            user_obj = user_id
            if user_attrs:
                user_obj = {"key": user_id, "attributes": user_attrs}
            permitted = await self._permit_client.check(user_obj, action, resource_dict)
            return permitted, ""
        except Exception as e:
            logger.error(f"Authorization check failed: {e}")
            return False, f"Authorization system error: {str(e)}"

    def _extract_principal_info(
        self, context: MiddlewareContext
    ) -> tuple[str, dict[str, Any]]:
        request = context.fastmcp_context.request_context.request
        headers = getattr(request, "headers", {}) or {}
        # Identity extraction logic based on config
        if SETTINGS.identity_mode == "jwt":
            # Extract JWT from headers using regex
            header_val = headers.get(SETTINGS.identity_header) or headers.get(
                SETTINGS.identity_header.lower()
            )
            if not header_val:
                return "unknown", {"type": "missing_jwt_header"}
            match = re.match(SETTINGS.identity_header_regex, header_val)
            if not match:
                return "unknown", {"type": "invalid_jwt_header_format"}
            token = match.group(1)
            try:
                payload = jwt.decode(
                    token,
                    SETTINGS.identity_jwt_secret,
                    algorithms=SETTINGS.jwt_algorithms,
                    options={"verify_aud": False},
                )
                identity = payload.get(SETTINGS.identity_jwt_field, "unknown")
                return identity, {"jwt": payload}
            except Exception as e:
                logger.error(f"JWT decode/verify failed: {e}")
                return "unknown", {"type": "jwt_error", "error": str(e)}
        elif SETTINGS.identity_mode == "header":
            # Extract identity from a specific header
            identity = headers.get(SETTINGS.identity_header) or headers.get(
                SETTINGS.identity_header.lower()
            )
            if not identity:
                return "unknown", {"type": "missing_identity_header"}
            return identity, {"header": SETTINGS.identity_header}
        elif SETTINGS.identity_mode == "source":
            # Extract identity from context.source
            identity = getattr(context, "source", None) or "unknown"
            return identity, {"type": "source_field"}
        else:  # fixed
            # Use a fixed identity value
            return SETTINGS.identity_fixed_value, {"type": "fixed_identity"}

    def _log_access_event(
        self,
        context: MiddlewareContext,
        message,
        user_id,
        resource,
        action,
        permitted: bool,
        reason: str = "",
    ):
        # Unified logging for both authorized and denied access events
        method = getattr(message, "method", "unknown")
        source = getattr(context, "source", "unknown")
        log_msg = (
            f"{'Authorized' if permitted else 'Denied'} MCP request | "
            f"User: {user_id} | Method: {method} | Resource: {resource} | Action: {action} | Source: {source}"
        )
        if not permitted and reason:
            log_msg += f" | Reason: {reason}"
        if permitted:
            logger.info(log_msg)
        else:
            logger.warning(log_msg)
