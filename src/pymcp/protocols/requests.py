# src/pymcp/protocols/requests.py
from typing import Any, Dict

from pydantic import BaseModel

from .base_msg import MCPRequest


# Tool Call
class ToolCallRequestBody(BaseModel):
    tool: str
    args: Dict[str, Any]


class ToolCallRequest(MCPRequest):
    # The header is inherited from MCPRequest and no longer needs a status.
    body: ToolCallRequestBody


ClientMessage = ToolCallRequest
