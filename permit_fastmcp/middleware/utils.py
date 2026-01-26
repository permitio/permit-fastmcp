import re


def generate_action_from_tool_name(tool_name: str) -> str:
    """
    Generate an action string from a tool name for Permit.io.

    Permit.io resource and action keys must match: ^[A-Za-z0-9\\-_]+$
    (alphanumeric, hyphens, and underscores only)

    Args:
        tool_name: The original tool name

    Returns:
        The formatted action string with invalid characters replaced by hyphens
    """
    if not tool_name:
        return "unknown-tool"

    # Replace any character not in [A-Za-z0-9\-_] with a hyphen
    return re.sub(r"[^A-Za-z0-9\-_]", "-", tool_name)
