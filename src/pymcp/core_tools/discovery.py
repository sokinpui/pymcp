# src/pymcp/core_tools/discovery.py
"""
Core discovery tools for the MCP server.
"""

import pymcp
from pymcp.protocols.tools_def import ToolDefinition
from pymcp.tools.registry import ToolRegistry


@pymcp.tool
def list_tools_available(tool_registry: ToolRegistry) -> list[ToolDefinition]:
    """
    Lists the definitions of all available tools in the MCP server.

    This tool demonstrates dependency injection, as the server provides the
    `tool_registry` argument automatically at execution time.

    Returns:
        A list of tool definitions, including name, description, and arguments.
    """
    return tool_registry.get_all_definitions()
