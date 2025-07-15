# src/pymcp/server/router.py
"""
Component responsible for routing validated requests.
"""
from uuid import UUID

from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ClientMessage
from pymcp.protocols.responses import (
    ErrorResponse,
    ListToolsResponse,
    ListToolsResponseBody,
    ServerMessage,
)
from pymcp.tools.registry import ToolRegistry


class Router:
    """
    Routes validated incoming messages.
    For simple queries, it builds and returns a response message directly.
    For complex queries (like tool_call), it returns None, indicating
    that further processing is required by the caller.
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry: ToolRegistry = tool_registry

    def route_request(self, message: ClientMessage) -> ServerMessage | None:
        """
        Routes a validated client request.

        Returns a ServerMessage for immediate responses (e.g., list_tools)
        or None if the request requires further, asynchronous processing (e.g., tool_call).
        """
        match message.type:
            case "list_tools":
                return self._handle_list_tools(message.header.correlation_id)

            case "tool_call":
                # Signal to the caller that this needs further processing
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
