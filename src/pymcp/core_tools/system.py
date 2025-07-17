# src/pymcp/core_tools/system.py
"""
Core system-level tools for health checks and basic interactions.
"""

import pymcp


@pymcp.tool
def ping() -> str:
    """
    A simple tool to check if the server is responsive.

    A successful call to this tool confirms that the server's request
    processing and tool execution pipeline is operational.

    Returns:
        A string confirmation 'pong'.
    """
    return "pong"
