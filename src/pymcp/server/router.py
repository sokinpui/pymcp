# src/pymcp/server/router.py
"""
Component responsible for routing validated requests.
"""

import asyncio
from uuid import UUID

from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ClientMessage, ToolCallRequest
from pymcp.protocols.responses import (
    ErrorResponse,
    ListToolsResponse,
    ListToolsResponseBody,
    ServerMessage,
)
from pymcp.tools.registry import ToolRegistry

from .commands import ExecutionCommand


class Router:
    """
    Routes validated incoming messages.
    For tool calls, it places a command on a work queue.
    For simple queries, it responds directly by returning a response message.
    """

    def __init__(self, tool_registry: ToolRegistry, work_queue: asyncio.Queue):
        self.tool_registry: ToolRegistry = tool_registry
        self.work_queue: asyncio.Queue = work_queue

    async def route_request(
        self, message: ClientMessage, connection_id: UUID
    ) -> ServerMessage | None:
        """
        Routes a validated client request.
        This function returns a ServerMessage for immediate responses (like list_tools)
        or None if the request is queued for asynchronous processing.
        """
        # Route based on the message type. Validation is assumed to be done.
        match message.type:
            case "list_tools":
                # This is a synchronous, simple request. Handle it directly.
                return self._handle_list_tools(message.header.correlation_id)

            case "tool_call":
                # This is an asynchronous request. Queue it for a worker.
                # The validator ensures `message` is a valid `ToolCallRequest`.
                await self._queue_tool_call(message, connection_id)
                # Return None to signify no immediate response. The response
                # will be sent later by a SenderWorker.
                return None

            case _:
                # This case is theoretically unreachable if the ClientMessage Union
                # is comprehensive, but it's a good safeguard.
                return ErrorResponse(
                    header={
                        "correlation_id": message.header.correlation_id,
                        "status": "error",
                    },
                    error=Error(
                        code="unsupported_request",
                        message=f"Request type '{message.type}' is not supported.",
                    ),
                )

    def _handle_list_tools(self, correlation_id: UUID) -> ListToolsResponse:
        """
        Handles the request to list all available tools.
        """
        tool_defs = self.tool_registry.get_all_definitions()
        return ListToolsResponse(
            header={"correlation_id": correlation_id, "status": "success"},
            body=ListToolsResponseBody(tools=tool_defs),
        )

    async def _queue_tool_call(self, request: ToolCallRequest, connection_id: UUID):
        """
        Creates an ExecutionCommand from a ToolCallRequest and puts it on the work queue.
        """
        command = ExecutionCommand(
            connection_id=connection_id,
            correlation_id=request.header.correlation_id,
            tool_name=request.body.tool_name,
            args=request.body.args,
        )
        await self.work_queue.put(command)
