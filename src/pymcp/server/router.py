# src/pymcp/server/router.py
"""
Component responsible for routing validated requests.
"""
from pymcp.protocols.requests import ClientMessage
from pymcp.protocols.responses import ServerMessage


class Router:
    """
    Routes validated incoming messages.
    With a single request type, this component is a simple pass-through but
    is kept for architectural consistency and future extensibility.
    """

    def __init__(self):
        pass

    def route_request(self, message: ClientMessage) -> ServerMessage | None:
        """
        Routes a validated client request.

        As there is only one supported request type (tool_call), this
        method signals that the request should proceed to execution.
        """
        return None
