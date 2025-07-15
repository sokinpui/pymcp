# src/pymcp/server/server.py
"""
The main MCP server orchestrator.
"""

import asyncio

import websockets
from websockets.server import WebSocketServerProtocol

from pymcp.tools.registry import ToolRegistry

from .commands import ExecutionCommand, ResponseCommand
from .connection_manager import ConnectionManager
from .router import Router
from .sender import SenderWorker
from .validator import Validator
from .worker import ExecutorWorker


class MCPServer:
    """
    The main server class that orchestrates the entire request-response pipeline.
    Flow: ConnectionManager -> Validator -> Router -> WorkQueue -> Executor -> ResponseQueue -> Sender
    """

    def __init__(
        self,
        host: str,
        port: int,
        tool_registry: ToolRegistry,
        num_executors: int = 2,
        num_senders: int = 1,
    ):
        self.host = host
        self.port = port
        self.num_executors = num_executors
        self.num_senders = num_senders

        # Core components
        self.tool_registry = tool_registry
        self.connection_manager = ConnectionManager()

        # Queues for inter-component communication
        self.work_queue: asyncio.Queue[ExecutionCommand] = asyncio.Queue()
        self.response_queue: asyncio.Queue[ResponseCommand] = asyncio.Queue()

        # Pipeline stages
        self.validator = Validator(self.response_queue)
        self.router = Router(self.tool_registry, self.work_queue)
        self.executors: list[ExecutorWorker] = []
        self.senders: list[SenderWorker] = []

        self._tasks: list[asyncio.Task] = []

    async def _handler(self, websocket: WebSocketServerProtocol):
        """The main WebSocket handler for each client connection."""
        connection_id = await self.connection_manager.connect(websocket)
        try:
            async for message_json in websocket:
                # 1. Validate the incoming raw message.
                # If invalid, the validator queues an error and returns None.
                validated_message = await self.validator.validate_message(
                    message_json, connection_id
                )
                if not validated_message:
                    continue  # Move to the next message

                # 2. Route the validated message.
                # The router may return an immediate response or None for queued tasks.
                immediate_response = await self.router.route_request(
                    validated_message, connection_id
                )

                # 3. Queue any immediate response.
                if immediate_response:
                    # For simple/synchronous requests (e.g., list_tools, routing errors),
                    # queue the response to be sent by a SenderWorker.
                    response_command = ResponseCommand(
                        connection_id=connection_id, message=immediate_response
                    )
                    await self.response_queue.put(response_command)
        except websockets.exceptions.ConnectionClosedError:
            print(f"Connection closed unexpectedly for {connection_id}")
        finally:
            self.connection_manager.disconnect(connection_id)

    def _start_workers(self):
        """Creates and starts all background worker tasks."""
        # Start Executor Workers
        for i in range(self.num_executors):
            executor = ExecutorWorker(
                worker_id=i + 1,
                tool_registry=self.tool_registry,
                work_queue=self.work_queue,
                response_queue=self.response_queue,
            )
            self.executors.append(executor)
            self._tasks.append(asyncio.create_task(executor.start()))
        print(f"Started {self.num_executors} executor workers.")

        # Start Sender Workers
        for i in range(self.num_senders):
            sender = SenderWorker(
                worker_id=i + 1,
                connection_manager=self.connection_manager,
                response_queue=self.response_queue,
            )
            self.senders.append(sender)
            self._tasks.append(asyncio.create_task(sender.start()))
        print(f"Started {self.num_senders} sender workers.")

    async def _stop_workers(self):
        """Stops all background worker tasks gracefully."""
        if not self._tasks:
            return
        print("Stopping all workers...")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        print("All workers stopped.")

    async def start(self):
        """Starts the WebSocket server and the background workers."""
        self._start_workers()
        print(f"Starting MCP Server on ws://{self.host}:{self.port}")
        try:
            async with websockets.serve(self._handler, self.host, self.port):
                await asyncio.Future()  # Run forever
        finally:
            await self._stop_workers()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Start the MCP WebSocket server.")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    args = parser.parse_args()

    # Initialize tool registry (this should be defined in your application)
    tool_registry = ToolRegistry()

    server = MCPServer(
        host=args.host,
        port=args.port,
        tool_registry=tool_registry,
        num_executors=2,
        num_senders=1,
    )
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
