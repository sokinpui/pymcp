# src/pymcp/protocols/responses.py
from typing import Any, Union

from pydantic import BaseModel

from .base_msg import MCPResponse, Error


# Tool Call Response
class ToolCallResponseBody(BaseModel):
    tool: str
    result: Any


class ToolCallResponse(MCPResponse):
    body: ToolCallResponseBody


# Error Response (for cases where a valid request leads to an error)
class ErrorResponse(MCPResponse):
    body: None = None  # An error response never has a body
    error: Error  # An error response must have an error object


# Union of all possible responses for server-side type hinting
ServerMessage = Union[ToolCallResponse, ErrorResponse]
