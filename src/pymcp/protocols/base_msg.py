# src/pymcp/protocols/base_msg.py
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Header(BaseModel):
    """
    Metadata for every MCP message.
    The 'status' field was removed, as it is a response-specific concept
    and is now a top-level field on response messages for discrimination.
    """

    correlation_id: UUID = Field(default_factory=uuid4)


class Error(BaseModel):
    """
    Standardized error format.
    """

    code: str
    message: str


class MCPRequest(BaseModel):
    """Base model for all client-to-server requests."""

    header: Header = Field(default_factory=Header)


class MCPResponse(BaseModel):
    """Base model for all server-to-client responses."""

    header: Header
