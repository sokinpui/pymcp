# src/pymcp/client/exceptions.py
"""
Custom exceptions for the PyMCP client.

Defining specific exceptions allows users of the client to write more precise
error-handling logic.
"""


class MCPClientError(Exception):
    """Base exception for all PyMCP client errors."""

    pass


class ConnectionFailedError(MCPClientError):
    """Raised when the client fails to connect to the server."""

    pass


class ToolExecutionError(MCPClientError):
    """
    Raised when the server reports an error during tool execution.

    Attributes:
        code (str): The error code from the server.
        message (str): The error message from the server.
    """

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Tool execution failed with code '{code}': {message}")
