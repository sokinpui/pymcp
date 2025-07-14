# protocols/responses.py

from typing import Any, List, Literal, Union

from pydantic import BaseModel

from .base_msg import MCPResponse
from .tools_def import ToolDefinition


# List Tools Response
class ListToolsResponseBody(BaseModel):
    tools: List[ToolDefinition]


class ListToolsResponse(MCPResponse):
    type: Literal["list_tools_response"] = "list_tools_response"
    body: ListToolsResponseBody


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
ServerMessage = Union[ListToolsResponse, ToolCallResponse, ErrorResponse]
