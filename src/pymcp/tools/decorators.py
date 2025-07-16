# src/pymcp/tools/decorators.py
"""
Decorators for registering tools with the MCP framework.
"""

import inspect
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

TOOL_METADATA_ATTR = "_mcp_tool_meta"


def tool(name: str = None, description: Optional[str] = None) -> Callable[[F], F]:
    """
    A decorator to mark a function as an MCP tool.

    This decorator is stateless and simply attaches metadata to the function
    object, which is later discovered by the ToolLoader.

    Args:
        name: The name for the tool. If None, the function's `__name__` is used.
        description: A short description of what the tool does. If None, the
                     function's docstring is used.

    Returns:
        A decorator that attaches metadata and returns the function unmodified.
    """

    def decorator(func: F) -> F:
        tool_name = name or func.__name__
        tool_desc = description or inspect.getdoc(func)

        if not tool_desc:
            raise ValueError(
                f"Tool '{tool_name}' must have a description or a docstring."
            )

        setattr(
            func,
            TOOL_METADATA_ATTR,
            {"name": tool_name, "description": tool_desc.strip()},
        )
        return func

    # This logic handles both @tool and @tool(...)
    if callable(name):
        # The decorator was used as @tool without arguments.
        # 'name' is actually the function to be decorated.
        func = name
        name = None
        description = None
        return decorator(func)
    else:
        # The decorator was used as @tool(...) with arguments.
        return decorator
