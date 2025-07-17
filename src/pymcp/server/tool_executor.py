# src/pymcp/server/tool_executor.py
"""
Service responsible for executing tools.
"""
import inspect

from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ToolCallRequest
from pymcp.protocols.responses import (
    ErrorResponse,
    ServerMessage,
    ToolCallResponse,
    ToolCallResponseBody,
)
from pymcp.tools.registry import Tool, ToolRegistry


class ToolExecutor:
    """
    A service that encapsulates the logic for finding and executing a tool.
    It supports dependency injection of the ToolRegistry into core tools.
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    async def execute(self, request: ToolCallRequest) -> ServerMessage:
        """
        Finds the requested tool, injects dependencies if needed, executes it,
        and builds a response message.
        """
        tool_name = request.body.tool
        tool = self.tool_registry.get_tool(tool_name)

        if not tool:
            return ErrorResponse(
                status="error",
                header={"correlation_id": request.header.correlation_id},
                error=Error(
                    code="tool_not_found",
                    message=f"Tool '{tool_name}' not found.",
                ),
            )

        try:
            # Prepare arguments for execution.
            execution_args = request.body.args.copy()

            # --- Dependency Injection Logic ---
            # Inspect the tool's actual function signature.
            sig = inspect.signature(tool.func)
            # If the function expects the special 'tool_registry' parameter, inject it.
            if Tool.INJECTED_REGISTRY_PARAM in sig.parameters:
                execution_args[Tool.INJECTED_REGISTRY_PARAM] = self.tool_registry
            # This pattern is extensible for other server-side dependencies.

            result = await tool.execute(**execution_args)

            # status="success" is set by default in the ToolCallResponse model.
            return ToolCallResponse(
                header={"correlation_id": request.header.correlation_id},
                body=ToolCallResponseBody(tool=tool_name, result=result),
            )
        except Exception as e:
            # Provide a detailed error message for easier debugging.
            return ErrorResponse(
                status="error",
                header={"correlation_id": request.header.correlation_id},
                error=Error(
                    code="execution_error",
                    message=f"Error executing tool '{tool_name}': {type(e).__name__}: {e}",
                ),
            )
