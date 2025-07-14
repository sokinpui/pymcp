# server/server.py

import asyncio

import websockets
from tools.registry import ToolRegistry
from websockets.server import WebSocketServerProtocol

from .commands import ExecutionCommand, ResponseCommand
from .connection_manager import ConnectionManager
from .router import Router
from .sender import SenderWorker
from .worker import ExecutorWorker


class MCPServer:
    """
    Router -> WorkQueue -> Executor -> ResponseQueue -> Sender -> ConnectionManager
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

        # Queues (the "data tunnels")
        self.work_queue: asyncio.Queue[ExecutionCommand] = asyncio.Queue()
        self.response_queue: asyncio.Queue[ResponseCommand] = asyncio.Queue()

        # Pipeline stages
        self.router = Router(self.tool_registry, self.work_queue)
        self.executors: list[ExecutorWorker] = []
        self.senders: list[SenderWorker] = []

        self._tasks: list[asyncio.Task] = []

    async def _handler(self, websocket: WebSocketServerProtocol):
        """The main WebSocket handler for each client connection."""
        connection_id = await self.connection_manager.connect(websocket)
        try:
            async for message in websocket:
                immediate_response = await self.router.route_request(
                    message, connection_id
                )
                if immediate_response:
                    # For simple requests (like list_tools or validation errors),
                    # create a ResponseCommand and queue it for the SenderWorker.
                    # This maintains a consistent outbound path.
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
