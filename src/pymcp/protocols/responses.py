# src/pymcp/protocols/responses.py
from typing import Any, List, Literal, Union

from pydantic import BaseModel

from .base_msg import MCPResponse


# NOTE: ListToolsResponse has been removed.
# The list of tools is now returned in the body of a standard ToolCallResponse.


# Tool Call Response
class ToolCallResponseBody(BaseModel):
    tool_name: str
    result: Any


class ToolCallResponse(MCPResponse):
    type: Literal["tool_call_response"] = "tool_call_response"
    body: ToolCallResponseBody


# Error Response (for cases where a valid request leads to an error)
class ErrorResponse(MCPResponse):
    type: Literal["error_response"] = "error_response"
    body: None = None  # No body for a generic error response


# Union of all possible responses
ServerMessage = Union[ToolCallResponse, ErrorResponse]

