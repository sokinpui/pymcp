# src/pymcp/config.py
"""
MCP Server Configuration.

This file centralizes all static configuration for the server.
Since this is a Python file, you can use any Python code to define your settings.
"""

# Server network settings
SERVER_HOST = "localhost"
SERVER_PORT = 8765

# List of paths to directories containing your tool files.
# The loader will recursively search for .py files in these directories.
TOOL_REPOS = [
    "tools_repo",
    # You could add more, e.g.:
    # from pathlib import Path
    # str(Path(__file__).parent.parent.parent / "another_project/tools")
]
