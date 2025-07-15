# src/pymcp/server/tool_executor.py
"""
Service responsible for executing tools.
"""
from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ToolCallRequest
from pymcp.protocols.responses import (
    ErrorResponse,
    ServerMessage,
    ToolCallResponse,
    ToolCallResponseBody,
)
from pymcp.tools.registry import ToolRegistry


class ToolExecutor:
    """
    A service that encapsulates the logic for finding and executing a tool.
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    async def execute(self, request: ToolCallRequest) -> ServerMessage:
        """
        Executes the requested tool and builds a response message.
        """
        tool = self.tool_registry.get_tool(request.body.tool_name)

        if not tool:
            return ErrorResponse(
                header={"correlation_id": request.header.correlation_id, "status": "error"},
                error=Error(
                    code="tool_not_found",
                    message=f"Tool '{request.body.tool_name}' not found.",
                ),
            )

        try:
            result = await tool.execute(**request.body.args)
            return ToolCallResponse(
                header={"correlation_id": request.header.correlation_id, "status": "success"},
                body=ToolCallResponseBody(
                    tool_name=request.body.tool_name, result=result
                ),
            )
        except Exception as e:
            return ErrorResponse(
                header={"correlation_id": request.header.correlation_id, "status": "error"},
                error=Error(
                    code="execution_error",
                    message=f"Error executing tool '{request.body.tool_name}': {e}",
                ),
            )
