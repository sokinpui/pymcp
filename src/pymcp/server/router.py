# src/pymcp/server/router.py
"""
Component responsible for routing validated requests.
"""
from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ClientMessage
from pymcp.protocols.responses import ErrorResponse, ServerMessage


class Router:
    """
    Routes validated incoming messages.
    It performs a primary check on the message type and passes supported
    messages to the next stage of processing. For unsupported message types,
    it constructs an error response.
    """

    def __init__(self):
        pass

    def route_request(self, message: ClientMessage) -> ServerMessage | None:
        """
        Routes a validated client request.

        Returns None if the request requires asynchronous tool execution,
        otherwise returns an immediate error response for unsupported types.
        """
        # Since ClientMessage can currently only be ToolCallRequest, this is simple.
        # We keep the match statement for clarity and future extensibility.
        match message.type:
            case "tool_call":
                # Signal to the caller that this needs to be executed.
                return None

            case _:
                # This case is theoretically unreachable if the ClientMessage Union
                # is comprehensive and validation is correct.
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

