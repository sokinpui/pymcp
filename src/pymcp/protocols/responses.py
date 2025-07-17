# src/pymcp/protocols/responses.py
from typing import Any, Literal, Union

from pydantic import BaseModel

from .base_msg import Error, Header, MCPResponse


# Define specialized Header models for discriminated union
class SuccessHeader(Header):
    status: Literal["success"] = "success"


class ErrorHeader(Header):
    status: Literal["error"]


# Tool Call Response
class ToolCallResponseBody(BaseModel):
    tool: str
    result: Any


class ToolCallResponse(MCPResponse):
    """A response indicating a successful tool execution."""

    header: SuccessHeader
    body: ToolCallResponseBody
    error: None = None


class ErrorResponse(MCPResponse):
    """A response indicating an error occurred during processing."""

    header: ErrorHeader
    body: None = None
    error: Error


ServerMessage = Union[ToolCallResponse, ErrorResponse]
