# src/pymcp/config.py
"""
MCP Server Configuration.

This file centralizes all static configuration for the server.
Since this is a Python file, you can use any Python code to define your settings.
"""
from pathlib import Path

# Path to the directory containing built-in framework tools.
# These are always loaded.
CORE_TOOL_REPOS = [str(Path(__file__).parent / "core_tools")]

# List of paths to directories containing user-defined tool files.
USER_TOOL_REPOS = [
    "tools_repo",
]

# The default list of all tool repositories to load.
TOOL_REPOS = CORE_TOOL_REPOS + USER_TOOL_REPOS


# Server network settings
SERVER_HOST = "localhost"
SERVER_PORT = 8765
