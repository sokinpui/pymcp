# protocols/tools_def.py

from typing import List, Optional
from pydantic import BaseModel


class ToolArgument(BaseModel):
    """Describes a single argument for a tool."""

    name: str
    type: str
    description: Optional[str] = None
    required: bool = True


class ToolDefinition(BaseModel):
    """Describes a single available tool."""

    name: str
    description: str
    args: List[ToolArgument]
