# server/router.py

import asyncio
from uuid import UUID

from pydantic import ValidationError

from protocols.base_msg import Error
from protocols.requests import ClientMessage, ToolCallRequest
from protocols.responses import (
    ErrorResponse,
    ListToolsResponse,
    ListToolsResponseBody,
    ServerMessage,
)
from tools.registry import ToolRegistry

from .commands import ExecutionCommand


class Router:
    # TODO: it should only routes request, parser should be handle by other component
    """
    Parses incoming messages, routes them to the correct logic.
    For tool calls, it places a command on a work queue.
    For simple queries, it responds directly by placing a response on the response queue.
    """

    def __init__(self, tool_registry: ToolRegistry, work_queue: asyncio.Queue):
        self.tool_registry: ToolRegistry = tool_registry
        self.work_queue: asyncio.Queue = work_queue

    async def route_request(
        self, message_json: str, connection_id: UUID
    ) -> ServerMessage | None:
        """
        Parses and routes a client request.
        This function returns a ServerMessage if an immediate response (like validation error or list_tools)
        can be generated, or None if the request is queued for asynchronous processing by an executor.
        """
        try:
            message = ClientMessage.model_validate_json(message_json)
        except ValidationError as e:
            # For validation errors, we can't get a correlation_id, so we send an un-correlated error.
            return ErrorResponse(
                header={
                    "correlation_id": "00000000-0000-0000-0000-000000000000",
                    "status": "error",
                },
                error=Error(code="validation_error", message=str(e)),
            )

        # Route based on the message type
        match message.type:
            case "list_tools":
                # This is a synchronous, simple request. Handle it directly and return the response.
                return self._handle_list_tools(message.header.correlation_id)

            case "tool_call":
                # This is an asynchronous request. Queue it for a worker.
                await self._queue_tool_call(message, connection_id)
                # Return None to signify no immediate response should be sent by the server handler;
                # the response will come from a sender worker later.
                return None

            case _:
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
        This is a synchronous operation.
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
