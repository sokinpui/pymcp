# src/pymcp/protocols/requests.py
from typing import Any, Dict

from pydantic import BaseModel, Field

from .base_msg import Header, MCPRequest


# Tool Call
class ToolCallRequestBody(BaseModel):
    tool: str
    args: Dict[str, Any]


class ToolCallRequest(MCPRequest):
    header: Header = Field(default_factory=lambda: Header(status="success"))
    body: ToolCallRequestBody


# The primary and only request type.
ClientMessage = ToolCallRequest
