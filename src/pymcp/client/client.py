# src/pymcp/client/client.py
"""
The official asynchronous client for the PyMCP protocol.
"""
import asyncio
import logging
from typing import Any, Dict
from uuid import UUID, uuid4

import websockets
from pydantic import TypeAdapter, ValidationError
from websockets.client import ClientConnection
from websockets.exceptions import WebSocketException

from pymcp.protocols.base_msg import Header
from pymcp.protocols.requests import ToolCallRequest, ToolCallRequestBody
from pymcp.protocols.responses import ErrorResponse, ServerMessage, ToolCallResponse

from .exceptions import ConnectionFailedError, MCPClientError, ToolExecutionError

logger = logging.getLogger(__name__)


class MCPClient:
    """An asynchronous client for interacting with an MCP server."""

    def __init__(self, host: str, port: int, timeout: float = 10.0):
        """
        Initializes the MCPClient.

        Args:
            host: The server hostname or IP address.
            port: The server port.
            timeout: Default timeout in seconds for operations.
        """
        self._uri = f"ws://{host}:{port}"
        self._timeout = timeout
        self._connection: ClientConnection | None = None
        self._listener_task: asyncio.Task | None = None
        self._pending_requests: Dict[UUID, asyncio.Future] = {}
        # Create a TypeAdapter for robust parsing of the response Union type.
        self._server_message_adapter = TypeAdapter(ServerMessage)

    async def connect(self):
        """
        Connects to the MCP server and starts the response listener.
        This is typically called via 'async with'.
        """
        if self.is_connected:
            return

        try:
            # Set a timeout for the initial connection attempt.
            self._connection = await asyncio.wait_for(
                websockets.connect(self._uri), self._timeout
            )
            self._listener_task = asyncio.create_task(self._listen_for_responses())
        except (WebSocketException, asyncio.TimeoutError) as e:
            raise ConnectionFailedError(f"Failed to connect to {self._uri}: {e}") from e

    async def close(self):
        """Closes the connection to the server and cleans up resources."""
        if not self.is_connected or not self._connection:
            return

        # Cancel the listener task
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            await asyncio.gather(self._listener_task, return_exceptions=True)

        # Abort any pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(
                    MCPClientError("Connection closed before response was received.")
                )
        self._pending_requests.clear()

        # Close the websocket connection
        await self._connection.close()
        self._connection = None

    @property
    def is_connected(self) -> bool:
        """Returns True if the client is currently connected."""
        return self._connection is not None and not self._connection.close_code

    async def _listen_for_responses(self):
        """A background task that listens for messages from the server."""
        if not self._connection:
            return

        try:
            async for message_json in self._connection:
                try:
                    # Use the TypeAdapter for robust discriminated union parsing
                    response = self._server_message_adapter.validate_json(message_json)
                    correlation_id = response.header.correlation_id
                except ValidationError as e:
                    # Log the specific validation error for better debugging.
                    logger.warning(
                        "Failed to parse server message: %s. Raw message: %s",
                        e,
                        message_json,
                    )
                    continue  # Ignore malformed messages

                future = self._pending_requests.pop(correlation_id, None)
                if not future or future.done():
                    logger.warning(
                        "Received unsolicited response for correlation_id: %s",
                        correlation_id,
                    )
                    continue

                if isinstance(response, ToolCallResponse):
                    future.set_result(response.body.result)
                elif isinstance(response, ErrorResponse):
                    exc = ToolExecutionError(
                        code=response.error.code, message=response.error.message
                    )
                    future.set_exception(exc)

        except websockets.exceptions.ConnectionClosed:
            pass  # Expected when the connection is closed
        except Exception:
            # A critical error in the listener should be logged with its traceback.
            logger.exception("Unhandled exception in client listener task")
        finally:
            # Ensure all pending requests are cleaned up on exit
            if self._pending_requests:
                exc = MCPClientError("Listener task terminated unexpectedly.")
                for future in self._pending_requests.values():
                    if not future.done():
                        future.set_exception(exc)
                self._pending_requests.clear()

    async def call(self, tool: str, **args: Any) -> Any:
        """
        Calls a remote tool on the MCP server and waits for the result.

        Args:
            tool: The name of the tool to execute.
            **args: Keyword arguments to pass to the tool.

        Returns:
            The result of the tool execution from the server.

        Raises:
            MCPClientError: If the client is not connected.
            ToolExecutionError: If the server returns an error.
            asyncio.TimeoutError: If the server does not respond within the timeout.
        """
        if not self.is_connected or not self._connection:
            raise MCPClientError("Client is not connected.")

        correlation_id = uuid4()
        request = ToolCallRequest(
            header=Header(correlation_id=correlation_id),
            body=ToolCallRequestBody(tool=tool, args=args),
        )

        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending_requests[correlation_id] = future

        try:
            await self._connection.send(request.model_dump_json())
            return await asyncio.wait_for(future, self._timeout)
        except (WebSocketException, asyncio.TimeoutError) as e:
            # If we fail, ensure the pending future is removed
            self._pending_requests.pop(correlation_id, None)
            if isinstance(e, asyncio.TimeoutError):
                raise asyncio.TimeoutError(
                    f"Call to tool '{tool}' timed out after {self._timeout}s"
                ) from e
            raise MCPClientError(f"Connection error during call: {e}") from e

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

