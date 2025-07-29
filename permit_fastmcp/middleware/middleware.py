import fnmatch
import logging
from typing import Any, Optional
from permit import Permit
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import McpError
from mcp.types import ErrorData
from fastmcp.server.dependencies import get_http_request, get_http_headers
import re
import jwt
from .config import SETTINGS, IdentityMode
from .decorators import get_tool_identity_config

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
        
        # Only create Permit client if API key is provided
        if permit_api_key or permit_client:
            try:
                self._permit_client = permit_client or Permit(
                    pdp=permit_pdp_url or "http://localhost:7766", token=permit_api_key
                )
                self._authorization_enabled = True
                logger.info("Permit client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Permit client: {e}")
                self._permit_client = None
                self._authorization_enabled = False
                logger.warning("Authorization is disabled due to Permit client initialization failure")
        else:
            self._permit_client = None
            self._authorization_enabled = False
            logger.warning("No Permit API key provided - authorization is disabled")
        
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
            
            # Check if we have a target server name from the gateway context
            target_server_name = None
            if hasattr(context, 'fastmcp_context') and hasattr(context.fastmcp_context, 'target_server_name'):
                target_server_name = context.fastmcp_context.target_server_name
            
            # Prefix resource with server name or default prefix
            if SETTINGS.prefix_resource_with_server_name:
                server_name = target_server_name or SETTINGS.mcp_server_name
                resource = server_name + "_" + resource
            else:
                resource = SETTINGS.resource_prefix + resource
            # Prefix the action if needed
            action = SETTINGS.action_prefix + action
            logger.debug(f"Mapped method to action: {action} and resource: {resource}")
            user_id, _ = self._extract_principal_info(context, None)
            
            # Skip authorization if not enabled
            if not self._authorization_enabled:
                if self._enable_audit_logging:
                    self._log_access_event(
                        context, message, user_id, resource, action, permitted=True, reason="Authorization disabled"
                    )
            else:
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
        
        # Get server name for tool configuration lookup
        server_name = SETTINGS.mcp_server_name
        if hasattr(context, 'fastmcp_context') and hasattr(context.fastmcp_context, 'target_server_name'):
            server_name = context.fastmcp_context.target_server_name or server_name
        
        # Strip server name prefix from tool name if it exists (for mounted tools)
        # This handles cases where FastMCP prefixes tool names with the mount path
        # According to FastMCP docs, prefixes use underscore separator: {prefix}_{tool_name}
        if tool_name and server_name and tool_name.startswith(f"{server_name}_"):
            tool_name = tool_name[len(f"{server_name}_"):]
            logger.debug(f"Stripped server prefix '{server_name}_' from tool name, result: {tool_name}")
        
        # Check for tool-specific identity configuration
        tool_config = get_tool_identity_config(server_name, tool_name)
        logger.debug(f"Tool config for {server_name}:{tool_name}: {tool_config}")
        
        # Check if authorization should be bypassed for this tool
        if tool_config and tool_config.get('bypass_authorization'):
            logger.debug(f"Authorization bypassed for tool: {tool_name}")
            return await call_next(context)
        
        # Check if we have a target server name from the gateway context
        target_server_name = None
        if hasattr(context, 'fastmcp_context') and hasattr(context.fastmcp_context, 'target_server_name'):
            target_server_name = context.fastmcp_context.target_server_name
        
        # Use target server name if available, otherwise fall back to default
        resource = target_server_name or SETTINGS.mcp_server_name
        action = tool_name or "unknown_tool"

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
        user_id, _ = self._extract_principal_info(context, tool_config)
        
        # Skip authorization if not enabled
        if not self._authorization_enabled:
            if self._enable_audit_logging:
                self._log_access_event(
                    context, message, user_id, resource, action, permitted=True, reason="Authorization disabled"
                )
        else:
            permitted, reason = await self._authorize_request(
                resource, action, attributes, context, tool_config
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
        self, resource, action, attributes, context: MiddlewareContext, tool_config: Optional[dict] = None
    ) -> tuple[bool, str]:
        # If no permit client is available, authorization is disabled
        if not self._permit_client:
            return True, "Authorization disabled"
        
        try:
            user_id, user_attrs = self._extract_principal_info(context, tool_config)
            resource_dict = {"type": resource}
            if attributes:
                resource_dict["attributes"] = attributes
            if "tenant" in attributes:
                resource_dict["tenant"] = attributes["tenant"]
            user_obj = user_id
            if user_attrs:
                user_obj = {"key": user_id, "attributes": user_attrs}
            
            # Add timeout to prevent hanging
            import asyncio
            try:
                permitted = await asyncio.wait_for(
                    self._permit_client.check(user_obj, action, resource_dict),
                    timeout=10.0  # 10 second timeout
                )
                return permitted, ""
            except asyncio.TimeoutError:
                logger.error(f"Authorization check timed out for {action} on {resource}")
                return False, "Authorization check timed out"
            except Exception as e:
                logger.error(f"Permit client check failed: {e}")
                return False, f"Authorization system error: {str(e)}"
                
        except Exception as e:
            logger.error(f"Authorization check failed: {e}")
            return False, f"Authorization system error: {str(e)}"

    def _extract_principal_info(
        self, context: MiddlewareContext, tool_config: Optional[dict] = None
    ) -> tuple[str, dict[str, Any]]:
        # Use FastMCP dependency functions to get headers
        headers = get_http_headers()
        
        # Use tool-specific configuration if available, otherwise fall back to global settings
        identity_mode = tool_config.get('mode') if tool_config else SETTINGS.identity_mode
        header_name = tool_config.get('header_name') if tool_config else SETTINGS.identity_header
        fixed_value = tool_config.get('fixed_value') if tool_config else SETTINGS.identity_fixed_value
        jwt_secret = tool_config.get('jwt_secret') if tool_config else SETTINGS.identity_jwt_secret
        jwt_field = tool_config.get('jwt_field') if tool_config else SETTINGS.identity_jwt_field
        
        # Identity extraction logic based on config
        if identity_mode == IdentityMode.jwt:
            # Extract JWT from headers using regex
            header_val = headers.get(header_name) or headers.get(header_name.lower())
            if not header_val:
                return "unknown", {"type": "missing_jwt_header"}
            match = re.match(SETTINGS.identity_header_regex, header_val)
            if not match:
                return "unknown", {"type": "invalid_jwt_header_format"}
            token = match.group(1)
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=SETTINGS.jwt_algorithms,
                    options={"verify_aud": False},
                )
                identity = payload.get(jwt_field, "unknown")
                return identity, {"jwt": payload}
            except Exception as e:
                logger.error(f"JWT decode/verify failed: {e}")
                return "unknown", {"type": "jwt_error", "error": str(e)}
        elif identity_mode == IdentityMode.header:
            # Extract identity from a specific header
            identity = headers.get(header_name) or headers.get(header_name.lower())
            if not identity:
                return "unknown", {"type": "missing_identity_header"}
            return identity, {"header": header_name}
        elif identity_mode == IdentityMode.source:
            # Extract identity from context.source
            identity = getattr(context, "source", None) or "unknown"
            return identity, {"type": "source_field"}
        else:  # IdentityMode.fixed
            # Use a fixed identity value
            return fixed_value, {"type": "fixed_identity"}

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
