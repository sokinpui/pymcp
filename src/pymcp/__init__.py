# src/pymcp/__init__.py

from .client.client import MCPClient as Client
from .client.exceptions import (
    ConnectionFailedError,
    MCPClientError,
    ToolExecutionError,
)
from .lib import start_server
from .tools.decorators import tool

__all__ = [
    "tool",
    "start_server",
    "Client",
    "MCPClientError",
    "ConnectionFailedError",
    "ToolExecutionError",
]
