# mcp_server/worker.py
import asyncio

from protocols.base_msg import Error
from protocols.responses import ErrorResponse, ToolCallResponse, ToolCallResponseBody
from tools.registry import ToolRegistry

from .commands import ExecutionCommand, ResponseCommand
from .connection_manager import ConnectionManager


class ExecutorWorker:
    """
    A worker that pulls execution commands from a work queue,
    executes them, and places a response command on a response queue.
    It is completely decoupled from any networking components.
    """

    def __init__(
        self,
        worker_id: int,
        tool_registry: ToolRegistry,
        work_queue: asyncio.Queue[ExecutionCommand],
        response_queue: asyncio.Queue[ResponseCommand],
    ):
        self.worker_id = worker_id
        self.tool_registry = tool_registry
        self.work_queue = work_queue
        self.response_queue = response_queue

    async def start(self):
        """Starts the worker's main loop to process commands."""
        print(f"[Executor-{self.worker_id}] Started and waiting for tasks.")
        while True:
            try:
                command = await self.work_queue.get()
                await self._process_command(command)
            except asyncio.CancelledError:
                print(f"[Executor-{self.worker_id}] Shutting down.")
                break
            except Exception as e:
                print(
                    f"[Executor-{self.worker_id}] CRITICAL ERROR: Unhandled exception: {e}"
                )

    async def _process_command(self, command: ExecutionCommand):
        """
        Handles the execution of a single command and queues the response.
        """
        print(
            f"[Executor-{self.worker_id}] Processing command for tool: {command.tool_name}"
        )
        tool = self.tool_registry.get_tool(command.tool_name)

        if not tool:
            response_message = ErrorResponse(
                header={"correlation_id": command.correlation_id, "status": "error"},
                error=Error(
                    code="tool_not_found",
                    message=f"Tool '{command.tool_name}' not found.",
                ),
            )
        else:
            try:
                result = await tool.execute(**command.args)
                response_message = ToolCallResponse(
                    header={
                        "correlation_id": command.correlation_id,
                        "status": "success",
                    },
                    body=ToolCallResponseBody(
                        tool_name=command.tool_name, result=result
                    ),
                )
            except Exception as e:
                response_message = ErrorResponse(
                    header={
                        "correlation_id": command.correlation_id,
                        "status": "error",
                    },
                    error=Error(
                        code="execution_error",
                        message=f"Error executing tool '{command.tool_name}': {e}",
                    ),
                )

        # Create a response command and put it on the outgoing queue
        response_command = ResponseCommand(
            connection_id=command.connection_id, message=response_message
        )
        await self.response_queue.put(response_command)

        self.work_queue.task_done()
