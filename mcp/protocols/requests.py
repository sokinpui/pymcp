# protocols/requests.py

from typing import Any, Dict, Literal, Union

from pydantic import BaseModel, Field

from .base_msg import Header, MCPRequest


# List Tools
class ListToolsRequestBody(BaseModel):
    # NOTE: may support "categories" in the future
    pass


class ListToolsRequest(MCPRequest):
    header: Header = Field(default_factory=lambda: Header(status="success"))
    type: Literal["list_tools"] = "list_tools"
    body: ListToolsRequestBody = Field(default_factory=ListToolsRequestBody)


# Tool Call
class ToolCallRequestBody(BaseModel):
    tool_name: str
    args: Dict[str, Any]


class ToolCallRequest(MCPRequest):
    header: Header = Field(default_factory=lambda: Header(status="success"))
    type: Literal["tool_call"] = "tool_call"
    body: ToolCallRequestBody


# Union of all possible requests
ClientMessage = Union[ListToolsRequest, ToolCallRequest]
