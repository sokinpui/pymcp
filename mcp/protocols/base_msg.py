# protocols/base_msg.py
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Header(BaseModel):
    """
    Metadata for every MCP message.
    """

    correlation_id: UUID = Field(default_factory=uuid4)
    status: Literal["success", "error"] = "success"


class Error(BaseModel):
    """
    Standardized error format.
    """

    code: str
    message: str


class MCPRequest(BaseModel):
    """Base model for all client-to-server requests."""

    header: Header = Field(default_factory=Header)
    body: BaseModel


class MCPResponse(BaseModel):
    """Base model for all server-to-client responses."""

    header: Header
    body: Optional[BaseModel] = None
    error: Optional[Error] = None
