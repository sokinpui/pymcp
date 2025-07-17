# src/pymcp/__init__.py
import logging

from .client.client import MCPClient as Client
from .client.exceptions import (
    ConnectionFailedError,
    MCPClientError,
    ToolExecutionError,
)
from .lib import start_server
from .tools.decorators import tool

# Best practice for libraries: add a NullHandler to the root logger.
# This prevents "No handler found" warnings if the library is used by an
# application that doesn't configure logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = [
    "tool",
    "start_server",
    "Client",
    "MCPClientError",
    "ConnectionFailedError",
    "ToolExecutionError",
]

