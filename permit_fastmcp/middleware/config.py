"""
Constants for known and bypassed MCP methods used in PermitMcpMiddleware.

- KNOWN_METHODS: Methods recognized for resource/action mapping.
- BYPASSED_METHODS: Methods that bypass authorization checks.
"""

# Methods recognized for resource/action mapping
KNOWN_METHODS = [
    "tools/list",
    "prompts/list",
    "resources/list",
    "tools/call",
    "resources/read",
    "prompts/get",
]

# Methods that bypass authorization checks
BYPASSED_METHODS = [
    "initialize",
    "ping",
    "notifications/*",
]


# PREFIXES for mapping MCP methods to Permit.io actions and resources
ACTION_PREFIX = ""
RESOURCE_PREFIX = "mcp_"


# RESOURCE TYPES
