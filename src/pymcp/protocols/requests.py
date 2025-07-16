# src/pymcp/protocols/requests.py
from typing import Any, Dict, Literal, Union

from pydantic import BaseModel, Field

from .base_msg import Header, MCPRequest


# Tool Call
class ToolCallRequestBody(BaseModel):
    tool_name: str
    args: Dict[str, Any]


class ToolCallRequest(MCPRequest):
    header: Header = Field(default_factory=lambda: Header(status="success"))
    type: Literal["tool_call"] = "tool_call"
    body: ToolCallRequestBody


# Union of all possible requests
ClientMessage = Union[ToolCallRequest]
