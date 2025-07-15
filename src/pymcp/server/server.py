# src/pymcp/server/server.py
"""
The main MCP server orchestrator.
"""

import asyncio
from uuid import UUID

import websockets
from websockets.server import WebSocketServerProtocol

from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ClientMessage, ToolCallRequest
from pymcp.protocols.responses import ErrorResponse, ServerMessage
from pymcp.tools.registry import ToolRegistry

from .connection_manager import ConnectionManager
from .response_sender import ResponseSender
from .router import Router
from .tool_executor import ToolExecutor
from .validator import Validator


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
        self.router = Router(tool_registry)
        self.tool_executor = ToolExecutor(tool_registry)
        self.response_sender = ResponseSender(self.connection_manager)

        # To keep track of running tasks for graceful shutdown
        self._running_tasks: set[asyncio.Task] = set()

    async def _handler(self, websocket: WebSocketServerProtocol):
        """The main WebSocket handler for each client connection."""
        connection_id = await self.connection_manager.connect(websocket)
        try:
            async for message_json in websocket:
                # Dynamically allocate a worker (task) for each message.
                task = asyncio.create_task(
                    self._process_message(connection_id, message_json)
                )
                self._running_tasks.add(task)
                task.add_done_callback(self._running_tasks.discard)

        except websockets.exceptions.ConnectionClosedError:
            print(f"Connection closed unexpectedly for {connection_id}")
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
        response_message: ServerMessage
        if message.type == "tool_call":
            assert isinstance(message, ToolCallRequest)
            response_message = await self.tool_executor.execute(message)
        else:
            # Safeguard if router logic and this logic diverge
            response_message = ErrorResponse(
                header={"correlation_id": message.header.correlation_id, "status": "error"},
                error=Error(
                    code="internal_server_error",
                    message=f"Server could not handle request type '{message.type}'.",
                ),
            )

        # 4. Send Response
        await self.response_sender.send(connection_id, response_message)

    async def _shutdown(self):
        """Gracefully shuts down all running tasks."""
        if not self._running_tasks:
            return
        print(f"Shutting down... waiting for {len(self._running_tasks)} tasks to complete.")
        await asyncio.gather(*self._running_tasks, return_exceptions=True)
        print("All tasks completed.")


    async def start(self):
        """Starts the WebSocket server."""
        print(f"Starting MCP Server on ws://{self.host}:{self.port}")
        server = await websockets.serve(self._handler, self.host, self.port)

        try:
            await asyncio.Future()  # Run forever
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("Server shutting down.")
        finally:
            server.close()
            await server.wait_closed()
            await self._shutdown()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Start the MCP WebSocket server.")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    args = parser.parse_args()

    # In a real app, you would register your tools here.
    tool_registry = ToolRegistry()

    server = MCPServer(
        host=args.host,
        port=args.port,
        tool_registry=tool_registry,
    )
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("MCP Server stopped.")


if __name__ == "__main__":
    main()
