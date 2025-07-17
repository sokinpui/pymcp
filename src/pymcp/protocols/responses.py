# src/pymcp/protocols/responses.py
from typing import Any, Literal, Union

from pydantic import BaseModel

from .base_msg import Error, MCPResponse


# Tool Call Response
class ToolCallResponseBody(BaseModel):
    tool: str
    result: Any


class ToolCallResponse(MCPResponse):
    """A response indicating a successful tool execution."""

    status: Literal["success"] = "success"
    body: ToolCallResponseBody
    error: None = None


class ErrorResponse(MCPResponse):
    """A response indicating an error occurred during processing."""

    status: Literal["error"]
    body: None = None
    error: Error


# This is now a valid discriminated union that Pydantic can parse automatically.
ServerMessage = Union[ToolCallResponse, ErrorResponse]
