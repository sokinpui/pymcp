# src/pymcp/server/server.py
"""
The main MCP server orchestrator.
"""

import asyncio
import logging
from uuid import UUID

import websockets
from websockets.server import ServerConnection

from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ClientMessage, ToolCallRequest
from pymcp.protocols.responses import ErrorResponse
from pymcp.tools.registry import ToolRegistry

from .connection_manager import ConnectionManager
from .response_sender import ResponseSender
from .router import Router
from .tool_executor import ToolExecutor
from .validator import Validator

logger = logging.getLogger(__name__)


class MCPServer:
    """
    The main server class that orchestrates the entire request-response pipeline.
    It uses a dynamic, task-based approach, coordinating stateless services.
    """

    def __init__(
        self,
        host: str,
        port: int,
        tool_registry: ToolRegistry,
    ):
        self.host = host
        self.port = port

        # Core components (services)
        self.connection_manager = ConnectionManager()
        self.validator = Validator()
        self.router = Router()
        self.tool_executor = ToolExecutor(tool_registry)
        self.response_sender = ResponseSender(self.connection_manager)

        # To keep track of running tasks for graceful shutdown
        self._running_tasks: set[asyncio.Task] = set()

    def update_tool_registry(self, new_registry: ToolRegistry):
        """
        Atomically updates the tool registry used by the tool executor.
        """
        logger.info("Server is now using the updated tool registry.")
        self.tool_executor.tool_registry = new_registry

    async def _handler(self, websocket: ServerConnection):
        """The main WebSocket handler for each client connection."""
        connection_id = await self.connection_manager.connect(websocket)
        remote_addr = websocket.remote_address
        try:
            async for message_json in websocket:
                # Dynamically allocate a worker (task) for each message.
                task = asyncio.create_task(
                    self._process_message(connection_id, message_json)
                )
                self._running_tasks.add(task)
                task.add_done_callback(self._running_tasks.discard)

        except websockets.exceptions.ConnectionClosedError:
            logger.warning(
                "Connection %s from %s:%s closed unexpectedly.",
                connection_id,
                remote_addr[0],
                remote_addr[1],
            )
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(
                "Connection %s from %s:%s closed.",
                connection_id,
                remote_addr[0],
                remote_addr[1],
            )
        finally:
            self.connection_manager.disconnect(connection_id)

    async def _process_message(self, connection_id: UUID, message_json: str):
        """
        Orchestrates the processing of a single message by calling services.
        This function runs in its own task for each message.
        """
        # 1. Validate
        validated_result = self.validator.validate_message(message_json)
        if isinstance(validated_result, ErrorResponse):
            await self.response_sender.send(connection_id, validated_result)
            return

        message: ClientMessage = validated_result

        # 2. Route
        immediate_response = self.router.route_request(message)
        if immediate_response:
            await self.response_sender.send(connection_id, immediate_response)
            return

        # 3. Execute
        # Since validation and routing passed, we know it's a valid tool call.
        # As ClientMessage is an alias for ToolCallRequest, we can execute directly.
        response_message = await self.tool_executor.execute(message)

        # 4. Send Response
        await self.response_sender.send(connection_id, response_message)

    async def _shutdown_client_tasks(self):
        """Gracefully shuts down all client-processing tasks."""
        if not self._running_tasks:
            return
        logger.info("Shutting down %d client tasks...", len(self._running_tasks))
        await asyncio.gather(*self._running_tasks, return_exceptions=True)
        logger.info("All client tasks completed.")

    async def start(self):
        """Starts the WebSocket server and serves until cancelled."""
        logger.info("Starting MCP Server on ws://%s:%s", self.host, self.port)
        try:
            # The websockets.serve context manager handles server startup and shutdown.
            async with websockets.serve(self._handler, self.host, self.port):
                await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            logger.info("Server shutdown signal received.")
        finally:
            await self._shutdown_client_tasks()
            logger.info("Server has stopped.")
