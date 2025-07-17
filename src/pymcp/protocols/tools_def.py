# src/pymcp/protocols/tools_def.py

from typing import List
from pydantic import BaseModel


class ToolArgument(BaseModel):
    """Describes a single argument for a tool."""

    name: str
    type: str
    required: bool = True


class ToolDefinition(BaseModel):
    """Describes a single available tool."""

    name: str
    description: str
    args: List[ToolArgument]
