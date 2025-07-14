# server/commands.py

from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel

from pymcp.protocols.responses import ServerMessage


class ExecutionCommand(BaseModel):
    """
    A data object representing a tool execution request.
    This is the item that will be placed on the work queue.
    """

    connection_id: UUID
    correlation_id: UUID
    tool_name: str
    args: Dict[str, Any]


class ResponseCommand(BaseModel):
    """
    A data object representing a response to be sent to a client.
    This is the item that will be placed on the response queue.
    """

    connection_id: UUID
    message: ServerMessage
