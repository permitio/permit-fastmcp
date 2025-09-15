import pytest
from permit_fastmcp.middleware.utils import generate_action_from_tool_name


def test_generate_action_from_tool_name_basic():
    """Test basic tool name conversion."""
    assert generate_action_from_tool_name("test_tool") == "test-tool"
    assert generate_action_from_tool_name("my.tool") == "my-tool"
    assert generate_action_from_tool_name("path/to/tool") == "path-to-tool"


def test_generate_action_from_tool_name_multiple_replacements():
    """Test tool names with multiple special characters."""
    assert generate_action_from_tool_name("test.tool_name") == "test-tool-name"
    assert generate_action_from_tool_name("path/to/my_tool") == "path-to-my-tool"
    assert (
        generate_action_from_tool_name("com.example.tool_name")
        == "com-example-tool-name"
    )


def test_generate_action_from_tool_name_edge_cases():
    """Test edge cases for tool name conversion."""
    # Empty string
    assert generate_action_from_tool_name("") == "unknown-tool"

    # None value
    assert generate_action_from_tool_name(None) == "unknown-tool"

    # Only special characters
    assert generate_action_from_tool_name("...") == "---"
    assert generate_action_from_tool_name("///") == "---"
    assert generate_action_from_tool_name("___") == "---"

    # Mixed special characters
    assert (
        generate_action_from_tool_name("test.tool_name/path") == "test-tool-name-path"
    )


def test_generate_action_from_tool_name_no_changes():
    """Test tool names that don't need any replacements."""
    assert generate_action_from_tool_name("simpletool") == "simpletool"
    assert generate_action_from_tool_name("tool-name") == "tool-name"
    assert generate_action_from_tool_name("toolname") == "toolname"
