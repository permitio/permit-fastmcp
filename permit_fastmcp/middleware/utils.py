def generate_action_from_tool_name(tool_name: str) -> str:
    """
    Generate an action string from a tool name for Permit.io action name standard by replacing special characters with hyphens.

    Args:
        tool_name: The original tool name

    Returns:
        The formatted action string with dots, slashes, and underscores replaced by hyphens
    """
    if not tool_name:
        return "unknown-tool"

    return tool_name.replace(".", "-").replace("/", "-").replace("_", "-")
